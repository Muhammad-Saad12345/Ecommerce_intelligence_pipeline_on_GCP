import hashlib
import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
from fastapi import HTTPException
from google.cloud import bigquery, storage
from pydantic import BaseModel


PROJECT_ID = os.getenv("PROJECT_ID", "ecom-intelligence-pipeline-001")
BRONZE_DATASET = os.getenv("BRONZE_DATASET", "ecom_bronze")
AUDIT_DATASET = os.getenv("AUDIT_DATASET", "ecom_audit")
RAW_BUCKET_NAME = os.getenv(
    "RAW_BUCKET_NAME",
    "ecom-intelligence-pipeline-001-ecom-raw"
)

MAX_UPLOAD_SIZE_BYTES = int(
    os.getenv("MAX_UPLOAD_SIZE_BYTES", str(100 * 1024 * 1024))
)


storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)


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


class ProcessRequest(BaseModel):
    bucket_name: str
    source_system: str
    table_name: str
    tmp_file_path: str
    batch_id: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_run_id() -> str:
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
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
            detail=f"File not found: gs://{bucket_name}/{file_path}",
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

    for col in df.columns:
        if col != "ingestion_timestamp":
            df[col] = df[col].astype(str)

    bronze_table = f"{PROJECT_ID}.{BRONZE_DATASET}.bronze_{table_name}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=True,
    )

    load_job = bq_client.load_table_from_dataframe(df, bronze_table, job_config=job_config)
    load_job.result()
    return len(df)


def run_pipeline(request: ProcessRequest):
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

            log_pipeline(run_id, request.batch_id, "process_completed", "SKIPPED")

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
