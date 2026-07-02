from pathlib import Path
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..services.pipeline import (
    EXPECTED_COLUMNS,
    MAX_UPLOAD_SIZE_BYTES,
    ProcessRequest,
    RAW_BUCKET_NAME,
    sanitize_filename,
    run_pipeline,
    utc_now,
    upload_bytes_to_tmp,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def get_status_class(status: str) -> str:
    status = (status or "").lower()
    if status == "success":
        return "status-success"
    if status == "skipped":
        return "status-warning"
    return "status-failed"


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "E-Commerce Intelligence Portal",
        },
    )


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "title": "Upload Data",
            "tables": list(EXPECTED_COLUMNS.keys()),
            "max_upload_size_mb": MAX_UPLOAD_SIZE_BYTES // (1024 * 1024),
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    dashboards = [
        ("Executive Overview", "https://datastudio.google.com/embed/reporting/a431a472-6c1d-41c4-8530-647518b36f7d/page/b1l0F"),
        ("Sales Overview 1", "https://datastudio.google.com/embed/reporting/a431a472-6c1d-41c4-8530-647518b36f7d/page/p_y87wdssg4d"),
        ("Customer Intelligence", "https://datastudio.google.com/embed/reporting/a431a472-6c1d-41c4-8530-647518b36f7d/page/p_8hxnecth4d"),
        ("Sales Overview 2", "https://datastudio.google.com/embed/reporting/a431a472-6c1d-41c4-8530-647518b36f7d/page/p_vs7mvsvh4d"),
        ("Pipeline Health", "https://datastudio.google.com/embed/reporting/a431a472-6c1d-41c4-8530-647518b36f7d/page/p_uxezotwh4d"),
    ]
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Looker Studio Dashboard",
            "dashboards": dashboards,
        },
    )


@router.get("/ai-chat", response_class=HTMLResponse)
def ai_chat_page(request: Request):
    return templates.TemplateResponse(
        "ai_chat.html",
        {
            "request": request,
            "title": "AI Chatbot",
        },
    )


@router.post("/upload-and-process", response_class=HTMLResponse)
async def upload_and_process(
    request: Request,
    source_system: str = Form(...),
    table_name: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        if source_system != "olist":
            raise ValueError("Only source_system='olist' is supported in v1.")

        if table_name not in EXPECTED_COLUMNS:
            raise ValueError(f"Unsupported table_name: {table_name}")

        if not file.filename:
            raise ValueError("No file selected.")

        if not file.filename.lower().endswith(".csv"):
            raise ValueError("Only .csv files are allowed.")

        file_bytes = await file.read()
        source_file_name = sanitize_filename(file.filename)

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

        request_model = ProcessRequest(
            bucket_name=RAW_BUCKET_NAME,
            source_system=source_system,
            table_name=table_name,
            tmp_file_path=tmp_file_path,
            batch_id=batch_id,
        )

        result = run_pipeline(request_model)

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "title": "Pipeline Result",
                "result": result,
                "status_class": get_status_class(result.get("status")),
            },
        )

    except HTTPException as exc:
        detail = exc.detail
        if isinstance(detail, dict):
            result = detail
        else:
            result = {"status": "failed", "error": str(detail)}

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "title": "Pipeline Result",
                "result": result,
                "status_class": get_status_class(result.get("status")),
            },
        )

    except Exception as exc:
        result = {"status": "failed", "error": str(exc)}
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "title": "Pipeline Result",
                "result": result,
                "status_class": get_status_class(result.get("status")),
            },
        )
