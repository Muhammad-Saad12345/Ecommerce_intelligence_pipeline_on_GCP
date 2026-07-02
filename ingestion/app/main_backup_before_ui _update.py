import hashlib
import html
import io
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List

import pandas as pd
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from google.cloud import bigquery, storage
from pydantic import BaseModel


# ============================================================
# Environment Config
# ============================================================

PROJECT_ID = os.getenv("PROJECT_ID", "ecom-intelligence-pipeline-001")
BRONZE_DATASET = os.getenv("BRONZE_DATASET", "ecom_bronze")
AUDIT_DATASET = os.getenv("AUDIT_DATASET", "ecom_audit")
RAW_BUCKET_NAME = os.getenv(
    "RAW_BUCKET_NAME",
    "ecom-intelligence-pipeline-001-ecom-raw"
)

MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(100 * 1024 * 1024)))  # 100 MB


# ============================================================
# Google Cloud Clients
# ============================================================

storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)

app = FastAPI(title="Ecommerce GCS to BigQuery Ingestion Service")


# ============================================================
# Expected Source Schemas
# ============================================================

EXPECTED_COLUMNS: Dict[str, List[str]] = {
    "orders": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "customers": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "order_items": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    "products": [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "payments": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    "sellers": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
}


# ============================================================
# Request Model
# ============================================================

class ProcessRequest(BaseModel):
    bucket_name: str
    source_system: str
    table_name: str
    tmp_file_path: str
    batch_id: str


# ============================================================
# Utility Functions
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_run_id() -> str:
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """
    Keeps file name safe for GCS paths.
    Removes directory paths and replaces risky characters.
    """
    filename = filename.split("/")[-1].split("\\")[-1]
    filename = filename.replace(" ", "_")

    safe_chars = []
    for char in filename:
        if char.isalnum() or char in ["_", "-", "."]:
            safe_chars.append(char)
        else:
            safe_chars.append("_")

    safe_name = "".join(safe_chars)

    if not safe_name:
        safe_name = f"uploaded_file_{str(uuid.uuid4())[:8]}.csv"

    return safe_name


def get_blob_bytes(bucket_name: str, file_path: str) -> bytes:
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    if not blob.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: gs://{bucket_name}/{file_path}"
        )

    return blob.download_as_bytes()


def upload_bytes_to_tmp(
    bucket_name: str,
    file_bytes: bytes,
    source_system: str,
    table_name: str,
    batch_id: str,
    source_file_name: str,
) -> str:
    """
    Uploads UI file bytes to GCS tmp/ zone.
    Returns tmp_file_path.
    """
    tmp_file_path = (
        f"tmp/source={source_system}/table={table_name}/"
        f"upload_id={batch_id}/{source_file_name}"
    )

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(tmp_file_path)
    blob.upload_from_string(file_bytes, content_type="text/csv")

    return tmp_file_path


def generate_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def insert_bq_rows(table_id: str, rows: List[dict]) -> None:
    errors = bq_client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert failed for {table_id}: {errors}")


# ============================================================
# Audit Logging Functions
# ============================================================

def log_pipeline(
    run_id: str,
    batch_id: str,
    step_name: str,
    status: str,
    error_message: str = None,
) -> None:
    table_id = f"{PROJECT_ID}.{AUDIT_DATASET}.pipeline_run_log"

    row = {
        "run_id": run_id,
        "batch_id": batch_id,
        "pipeline_name": "gcs_to_bronze_ingestion",
        "step_name": step_name,
        "status": status,
        "start_time": utc_now().isoformat(),
        "end_time": utc_now().isoformat(),
        "error_message": error_message,
    }

    insert_bq_rows(table_id, [row])


def log_quality(
    run_id: str,
    batch_id: str,
    table_name: str,
    check_name: str,
    check_status: str,
    expected_value: str = None,
    actual_value: str = None,
    failed_count: int = 0,
) -> None:
    table_id = f"{PROJECT_ID}.{AUDIT_DATASET}.data_quality_log"

    row = {
        "check_id": str(uuid.uuid4()),
        "run_id": run_id,
        "batch_id": batch_id,
        "table_name": table_name,
        "check_name": check_name,
        "check_status": check_status,
        "expected_value": expected_value,
        "actual_value": actual_value,
        "failed_count": failed_count,
        "created_at": utc_now().isoformat(),
    }

    insert_bq_rows(table_id, [row])


def log_file_upload(
    run_id: str,
    batch_id: str,
    source_system: str,
    table_name: str,
    source_file_name: str,
    gcs_uri: str,
    file_hash: str,
    row_count: int,
    upload_status: str,
    error_message: str = None,
) -> None:
    table_id = f"{PROJECT_ID}.{AUDIT_DATASET}.file_upload_log"

    row = {
        "upload_id": str(uuid.uuid4()),
        "run_id": run_id,
        "batch_id": batch_id,
        "source_system": source_system,
        "table_name": table_name,
        "source_file_name": source_file_name,
        "gcs_uri": gcs_uri,
        "file_hash": file_hash,
        "row_count": row_count,
        "upload_status": upload_status,
        "created_at": utc_now().isoformat(),
        "error_message": error_message,
    }

    insert_bq_rows(table_id, [row])


def log_rejected(
    run_id: str,
    batch_id: str,
    source_file_name: str,
    gcs_uri: str,
    rejection_reason: str,
    payload: dict,
) -> None:
    table_id = f"{PROJECT_ID}.{AUDIT_DATASET}.rejected_records"

    row = {
        "rejected_id": str(uuid.uuid4()),
        "run_id": run_id,
        "batch_id": batch_id,
        "source_file_name": source_file_name,
        "gcs_uri": gcs_uri,
        "rejection_level": "FILE",
        "rejection_reason": rejection_reason,
        "rejected_payload": json.dumps(payload),
        "created_at": utc_now().isoformat(),
    }

    insert_bq_rows(table_id, [row])


# ============================================================
# Validation and Storage Logic
# ============================================================

def check_duplicate_file(file_hash: str) -> bool:
    query = f"""
    SELECT COUNT(*) AS cnt
    FROM `{PROJECT_ID}.{AUDIT_DATASET}.file_upload_log`
    WHERE file_hash = @file_hash
      AND upload_status = 'SUCCESS'
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("file_hash", "STRING", file_hash)
        ]
    )

    result = bq_client.query(query, job_config=job_config).result()
    row = list(result)[0]

    return row["cnt"] > 0


def validate_schema(table_name: str, actual_columns: List[str]) -> None:
    expected_columns = EXPECTED_COLUMNS.get(table_name)

    if not expected_columns:
        raise ValueError(f"Unsupported table_name: {table_name}")

    missing_columns = [col for col in expected_columns if col not in actual_columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def copy_to_raw(
    bucket_name: str,
    tmp_file_path: str,
    source_system: str,
    table_name: str,
    batch_id: str,
    source_file_name: str,
) -> str:
    load_date = utc_now().date().isoformat()

    raw_path = (
        f"raw/source={source_system}/table={table_name}/"
        f"load_date={load_date}/batch_id={batch_id}/{source_file_name}"
    )

    bucket = storage_client.bucket(bucket_name)
    source_blob = bucket.blob(tmp_file_path)

    if not source_blob.exists():
        raise ValueError(f"Source file does not exist in tmp: gs://{bucket_name}/{tmp_file_path}")

    bucket.copy_blob(source_blob, bucket, raw_path)

    return raw_path


def copy_to_rejected(
    bucket_name: str,
    tmp_file_path: str,
    source_system: str,
    table_name: str,
    batch_id: str,
    source_file_name: str,
) -> str:
    load_date = utc_now().date().isoformat()

    rejected_path = (
        f"rejected/source={source_system}/table={table_name}/"
        f"load_date={load_date}/batch_id={batch_id}/{source_file_name}"
    )

    bucket = storage_client.bucket(bucket_name)
    source_blob = bucket.blob(tmp_file_path)

    if source_blob.exists():
        bucket.copy_blob(source_blob, bucket, rejected_path)

    return rejected_path


def load_to_bronze(df: pd.DataFrame, table_name: str, metadata: dict) -> int:
    for key, value in metadata.items():
        df[key] = value

    # Bronze layer: preserve raw data mostly as STRING.
    # Silver layer will handle type casting and business cleaning.
    for col in df.columns:
        if col != "ingestion_timestamp":
            df[col] = df[col].astype(str)

    bronze_table = f"{PROJECT_ID}.{BRONZE_DATASET}.bronze_{table_name}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=True,
    )

    load_job = bq_client.load_table_from_dataframe(
        df,
        bronze_table,
        job_config=job_config,
    )

    load_job.result()

    return len(df)


# ============================================================
# Shared Pipeline Logic
# ============================================================

def run_pipeline(request: ProcessRequest):
    """
    Shared pipeline function.
    Used by:
    - CLI/API endpoint: POST /process
    - UI endpoint: POST /upload-and-process

    This keeps CLI and UI behavior consistent.
    """
    run_id = create_run_id()
    source_file_name = request.tmp_file_path.split("/")[-1]
    tmp_gcs_uri = f"gs://{request.bucket_name}/{request.tmp_file_path}"

    try:
        log_pipeline(run_id, request.batch_id, "process_started", "STARTED")

        file_bytes = get_blob_bytes(request.bucket_name, request.tmp_file_path)
        file_hash = generate_file_hash(file_bytes)

        if len(file_bytes) == 0:
            raise ValueError("File is empty")

        log_quality(
            run_id,
            request.batch_id,
            request.table_name,
            "file_not_empty",
            "PASS",
            expected_value="file_size > 0",
            actual_value=str(len(file_bytes)),
        )

        if check_duplicate_file(file_hash):
            log_quality(
                run_id,
                request.batch_id,
                request.table_name,
                "duplicate_file_check",
                "FAILED",
                expected_value="unique file_hash",
                actual_value=file_hash,
                failed_count=1,
            )

            log_file_upload(
                run_id,
                request.batch_id,
                request.source_system,
                request.table_name,
                source_file_name,
                tmp_gcs_uri,
                file_hash,
                0,
                "DUPLICATE",
                "Duplicate file detected. Bronze load skipped.",
            )

            log_pipeline(
                run_id,
                request.batch_id,
                "duplicate_check",
                "SKIPPED",
                "Duplicate file detected",
            )

            return {
                "status": "skipped",
                "reason": "duplicate_file",
                "run_id": run_id,
                "batch_id": request.batch_id,
                "table_name": request.table_name,
                "tmp_gcs_uri": tmp_gcs_uri,
                "file_hash": file_hash,
                "row_count": 0,
            }

        df = pd.read_csv(io.BytesIO(file_bytes))

        if df.empty:
            raise ValueError("CSV has header but no rows")

        validate_schema(request.table_name, list(df.columns))

        log_quality(
            run_id,
            request.batch_id,
            request.table_name,
            "schema_validation",
            "PASS",
            expected_value=str(EXPECTED_COLUMNS[request.table_name]),
            actual_value=str(list(df.columns)),
        )

        raw_path = copy_to_raw(
            request.bucket_name,
            request.tmp_file_path,
            request.source_system,
            request.table_name,
            request.batch_id,
            source_file_name,
        )

        raw_gcs_uri = f"gs://{request.bucket_name}/{raw_path}"

        metadata = {
            "batch_id": request.batch_id,
            "run_id": run_id,
            "source_system": request.source_system,
            "source_file_name": source_file_name,
            "gcs_uri": raw_gcs_uri,
            "file_hash": file_hash,
            "load_date": utc_now().date().isoformat(),
            "ingestion_timestamp": utc_now(),
        }

        row_count = load_to_bronze(df, request.table_name, metadata)

        log_file_upload(
            run_id,
            request.batch_id,
            request.source_system,
            request.table_name,
            source_file_name,
            raw_gcs_uri,
            file_hash,
            row_count,
            "SUCCESS",
        )

        log_quality(
            run_id,
            request.batch_id,
            request.table_name,
            "row_count_check",
            "PASS",
            expected_value="row_count > 0",
            actual_value=str(row_count),
        )

        log_pipeline(run_id, request.batch_id, "bronze_load", "SUCCESS")
        log_pipeline(run_id, request.batch_id, "process_completed", "SUCCESS")

        return {
            "status": "success",
            "run_id": run_id,
            "batch_id": request.batch_id,
            "table_name": request.table_name,
            "raw_gcs_uri": raw_gcs_uri,
            "bronze_table": f"{PROJECT_ID}.{BRONZE_DATASET}.bronze_{request.table_name}",
            "row_count": row_count,
            "file_hash": file_hash,
        }

    except Exception as e:
        error_message = str(e)

        rejected_path = copy_to_rejected(
            request.bucket_name,
            request.tmp_file_path,
            request.source_system,
            request.table_name,
            request.batch_id,
            source_file_name,
        )

        rejected_gcs_uri = f"gs://{request.bucket_name}/{rejected_path}"

        try:
            log_rejected(
                run_id,
                request.batch_id,
                source_file_name,
                rejected_gcs_uri,
                error_message,
                request.model_dump(),
            )

            log_quality(
                run_id,
                request.batch_id,
                request.table_name,
                "file_validation",
                "FAILED",
                expected_value="valid file",
                actual_value=error_message,
                failed_count=1,
            )

            log_file_upload(
                run_id,
                request.batch_id,
                request.source_system,
                request.table_name,
                source_file_name,
                rejected_gcs_uri,
                "UNKNOWN",
                0,
                "FAILED",
                error_message,
            )

            log_pipeline(run_id, request.batch_id, "process_failed", "FAILED", error_message)

        except Exception as audit_error:
            # Do not hide the original pipeline error.
            print(f"Audit logging failed after pipeline error: {audit_error}")

        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "run_id": run_id,
                "batch_id": request.batch_id,
                "table_name": request.table_name,
                "error": error_message,
                "rejected_gcs_uri": rejected_gcs_uri,
            },
        )


# ============================================================
# API Endpoints
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ecom-ingestion-service",
        "project_id": PROJECT_ID,
        "bronze_dataset": BRONZE_DATASET,
        "audit_dataset": AUDIT_DATASET,
        "raw_bucket": RAW_BUCKET_NAME,
    }


@app.post("/process")
def process_file(request: ProcessRequest):
    """
    CLI/API endpoint.
    This preserves your existing pipeline testing flow.
    """
    return run_pipeline(request)


# ============================================================
# UI Endpoints
# ============================================================

@app.get("/", response_class=HTMLResponse)
def upload_page():
    table_options = "".join(
        [f'<option value="{table}">{table}</option>' for table in EXPECTED_COLUMNS.keys()]
    )

    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>E-Commerce Data Pipeline Upload</title>
        <style>
          body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #1f2937;
          }}
          .container {{
            max-width: 900px;
            margin: 60px auto;
            padding: 0 20px;
          }}
          .card {{
            background: white;
            border-radius: 14px;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
          }}
          .header {{
            border-bottom: 1px solid #e5e7eb;
            margin-bottom: 28px;
            padding-bottom: 20px;
          }}
          h1 {{
            margin: 0;
            font-size: 28px;
            color: #111827;
          }}
          .subtitle {{
            margin-top: 10px;
            color: #6b7280;
            line-height: 1.6;
          }}
          label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
          }}
          input[type="text"], select, input[type="file"] {{
            width: 100%;
            padding: 12px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 15px;
            box-sizing: border-box;
            background: white;
          }}
          .form-group {{
            margin-bottom: 22px;
          }}
          .note {{
            background: #eff6ff;
            border-left: 4px solid #2563eb;
            padding: 14px 16px;
            border-radius: 8px;
            color: #1e3a8a;
            margin-bottom: 24px;
            line-height: 1.5;
          }}
          .button {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 14px 22px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
          }}
          .button:hover {{
            background: #1d4ed8;
          }}
          .pipeline {{
            margin-top: 24px;
            font-size: 14px;
            color: #6b7280;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            padding: 14px;
            border-radius: 8px;
          }}
          .footer {{
            margin-top: 20px;
            color: #9ca3af;
            font-size: 13px;
          }}
        </style>
      </head>

      <body>
        <div class="container">
          <div class="card">
            <div class="header">
              <h1>E-Commerce Data Pipeline Upload</h1>
              <p class="subtitle">
                Upload Olist CSV files into the GCP ingestion pipeline. Files first land in the GCS tmp zone,
                then Cloud Run validates the file, loads valid data into BigQuery Bronze, and writes audit logs.
              </p>
            </div>

            <div class="note">
              <b>Pipeline Flow:</b> UI Upload → GCS tmp/ → Validation → GCS raw/ or rejected/ → BigQuery Bronze → Audit Logs
            </div>

            <form action="/upload-and-process" enctype="multipart/form-data" method="post">
              <div class="form-group">
                <label>Source System</label>
                <input type="text" name="source_system" value="olist" readonly>
              </div>

              <div class="form-group">
                <label>Target Table</label>
                <select name="table_name" required>
                  {table_options}
                </select>
              </div>

              <div class="form-group">
                <label>CSV File</label>
                <input name="file" type="file" accept=".csv" required>
              </div>

              <button class="button" type="submit">Upload and Process File</button>
            </form>

            <div class="pipeline">
              <b>Supported tables:</b> {", ".join(EXPECTED_COLUMNS.keys())}<br>
              <b>Max upload size:</b> {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB
            </div>

            <div class="footer">
              Development version. For production, authentication and async processing should be added.
            </div>
          </div>
        </div>
      </body>
    </html>
    """


@app.post("/upload-and-process", response_class=HTMLResponse)
async def upload_and_process(
    source_system: str = Form(...),
    table_name: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        # Basic UI-level validation
        if source_system != "olist":
            raise ValueError("Only source_system='olist' is supported in v1.")

        if table_name not in EXPECTED_COLUMNS:
            raise ValueError(f"Unsupported table_name: {table_name}")

        if not file.filename:
            raise ValueError("No file selected.")

        if not file.filename.lower().endswith(".csv"):
            raise ValueError("Only .csv files are allowed.")

        source_file_name = sanitize_filename(file.filename)
        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")

        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(
                f"File size exceeds {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB limit."
            )

        batch_id = f"ui_{utc_now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        tmp_file_path = upload_bytes_to_tmp(
            bucket_name=RAW_BUCKET_NAME,
            file_bytes=file_bytes,
            source_system=source_system,
            table_name=table_name,
            batch_id=batch_id,
            source_file_name=source_file_name,
        )

        request = ProcessRequest(
            bucket_name=RAW_BUCKET_NAME,
            source_system=source_system,
            table_name=table_name,
            tmp_file_path=tmp_file_path,
            batch_id=batch_id,
        )

        result = run_pipeline(request)

        return render_result_page(result)

    except HTTPException as e:
        detail = e.detail
        if isinstance(detail, dict):
            result = detail
        else:
            result = {
                "status": "failed",
                "error": str(detail),
            }
        return render_result_page(result, failed=True)

    except Exception as e:
        result = {
            "status": "failed",
            "error": str(e),
        }
        return render_result_page(result, failed=True)


def render_result_page(result: dict, failed: bool = False) -> str:
    status = html.escape(str(result.get("status", "unknown")))
    batch_id = html.escape(str(result.get("batch_id", "")))
    run_id = html.escape(str(result.get("run_id", "")))
    table_name = html.escape(str(result.get("table_name", "")))
    row_count = html.escape(str(result.get("row_count", "")))
    raw_gcs_uri = html.escape(str(result.get("raw_gcs_uri", "")))
    tmp_gcs_uri = html.escape(str(result.get("tmp_gcs_uri", "")))
    bronze_table = html.escape(str(result.get("bronze_table", "")))
    file_hash = html.escape(str(result.get("file_hash", "")))
    reason = html.escape(str(result.get("reason", "")))
    error = html.escape(str(result.get("error", "")))
    rejected_gcs_uri = html.escape(str(result.get("rejected_gcs_uri", "")))

    if status == "success":
        badge_color = "#16a34a"
        title = "Pipeline Completed Successfully"
    elif status == "skipped":
        badge_color = "#f59e0b"
        title = "File Skipped"
    else:
        badge_color = "#dc2626"
        title = "Pipeline Failed"

    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Pipeline Result</title>
        <style>
          body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #1f2937;
          }}
          .container {{
            max-width: 900px;
            margin: 60px auto;
            padding: 0 20px;
          }}
          .card {{
            background: white;
            border-radius: 14px;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
          }}
          h1 {{
            margin: 0 0 16px 0;
            color: #111827;
          }}
          .badge {{
            display: inline-block;
            background: {badge_color};
            color: white;
            padding: 8px 14px;
            border-radius: 999px;
            font-weight: 700;
            margin-bottom: 20px;
            text-transform: uppercase;
            font-size: 13px;
          }}
          .grid {{
            display: grid;
            grid-template-columns: 220px 1fr;
            gap: 12px;
            margin-top: 18px;
          }}
          .key {{
            font-weight: 700;
            color: #374151;
          }}
          .value {{
            color: #111827;
            word-break: break-all;
          }}
          .error {{
            margin-top: 18px;
            background: #fef2f2;
            border-left: 4px solid #dc2626;
            padding: 14px;
            color: #7f1d1d;
            border-radius: 8px;
            word-break: break-word;
          }}
          .warning {{
            margin-top: 18px;
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 14px;
            color: #78350f;
            border-radius: 8px;
            word-break: break-word;
          }}
          .success {{
            margin-top: 18px;
            background: #f0fdf4;
            border-left: 4px solid #16a34a;
            padding: 14px;
            color: #14532d;
            border-radius: 8px;
          }}
          .button {{
            display: inline-block;
            margin-top: 28px;
            background: #2563eb;
            color: white;
            text-decoration: none;
            padding: 12px 18px;
            border-radius: 8px;
            font-weight: 600;
          }}
        </style>
      </head>

      <body>
        <div class="container">
          <div class="card">
            <span class="badge">{status}</span>
            <h1>{title}</h1>

            <div class="grid">
              <div class="key">Batch ID</div><div class="value">{batch_id}</div>
              <div class="key">Run ID</div><div class="value">{run_id}</div>
              <div class="key">Table Name</div><div class="value">{table_name}</div>
              <div class="key">Row Count</div><div class="value">{row_count}</div>
              <div class="key">Raw GCS URI</div><div class="value">{raw_gcs_uri}</div>
              <div class="key">Tmp GCS URI</div><div class="value">{tmp_gcs_uri}</div>
              <div class="key">Bronze Table</div><div class="value">{bronze_table}</div>
              <div class="key">File Hash</div><div class="value">{file_hash}</div>
              <div class="key">Rejected URI</div><div class="value">{rejected_gcs_uri}</div>
            </div>

            {f'<div class="warning"><b>Reason:</b> {reason}</div>' if reason else ''}
            {f'<div class="error"><b>Error:</b> {error}</div>' if error else ''}
            {f'<div class="success">Check BigQuery audit tables for full traceability.</div>' if status == "success" else ''}

            <a class="button" href="/">Upload Another File</a>
          </div>
        </div>
      </body>
    </html>
    """