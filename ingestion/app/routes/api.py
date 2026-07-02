from fastapi import APIRouter

from ..services.pipeline import ProcessRequest, run_pipeline

api_router = APIRouter()


@api_router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ecom-ingestion-service",
        "project_id": "ecom-intelligence-pipeline-001",
    }


@api_router.post("/process")
def process_file(request: ProcessRequest):
    return run_pipeline(request)
