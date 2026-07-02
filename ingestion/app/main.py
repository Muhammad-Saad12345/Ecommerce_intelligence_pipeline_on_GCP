import os

from fastapi import FastAPI

from .routes.api import api_router
from .routes.ui import router as ui_router

app = FastAPI(title="Ecommerce GCS to BigQuery Ingestion Service")
app.include_router(api_router)
app.include_router(ui_router)
