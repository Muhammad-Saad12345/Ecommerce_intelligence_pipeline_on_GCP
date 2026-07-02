E-Commerce Data Engineering Platform on GCP

1. Project Overview

This project is an end-to-end batch data engineering platform built on Google Cloud Platform for an e-commerce dataset.

The current version focuses on the Bronze ingestion layer using the Olist CSV dataset. Files are uploaded through a UI or CLI, stored in Google Cloud Storage, validated by a Cloud Run service, loaded into BigQuery Bronze tables, and tracked through audit logs.

The project follows a medallion architecture:

Raw Files → Bronze Layer → Silver Layer → Gold Layer → Dashboards → AI Insights

Current completed phase:

UI / CLI Upload
→ GCS tmp zone
→ Cloud Run validation
→ GCS raw or rejected zone
→ BigQuery Bronze tables
→ BigQuery audit logs


2. Business Problem

E-commerce companies generate data from orders, customers, products, sellers, and payments. When this data is stored in separate files or systems, reporting becomes slow, inconsistent, and difficult to trust.

This platform solves that problem by creating a centralized and traceable data pipeline where raw files are validated, stored, loaded, and prepared for analytics.

3. Current Scope

Current version includes:

Olist CSV dataset ingestion
Google Cloud Storage landing and raw zones
Cloud Run validation service
BigQuery Bronze tables
BigQuery audit logging
File duplicate detection
Rejected file handling
UI-based file upload
CLI-based pipeline testing

Not included yet:

dbt Silver transformations
Gold facts and dimensions
Looker Studio dashboards
Cloud Composer orchestration
AI insights layer
Real-time Pub/Sub/Dataflow
External APIs

4. Tech Stack
Layer	Technology
File Storage	Google Cloud Storage
Ingestion API	Cloud Run + FastAPI
Data Warehouse	BigQuery
Audit Logging	BigQuery Audit Tables
Transformation	dbt, planned next
Dashboard	Looker Studio, planned later
Orchestration	Cloud Composer/Airflow, planned later
AI Insights	Gemini/Vertex AI, planned later

5. GCP Resources
GCS Bucket
gs://ecom-intelligence-pipeline-001-ecom-raw

Main zones:

tmp/
raw/
rejected/
archive/
BigQuery Datasets
ecom_bronze
ecom_silver
ecom_gold
ecom_audit
Cloud Run Service
ecom-ingestion-service

Main endpoints:

GET  /health
GET  /
POST /process
POST /upload-and-process

6. Current Pipeline Flow
User uploads CSV file
      ↓
File lands in GCS tmp/
      ↓
Cloud Run reads file from tmp/
      ↓
Cloud Run validates:
  - file exists
  - file is not empty
  - schema is valid
  - file is not duplicate
      ↓
If valid:
  - file is copied to GCS raw/
  - data is loaded to BigQuery Bronze
  - audit logs are written

If invalid:
  - file is copied to GCS rejected/
  - failure reason is written to rejected_records


7. Completed Features
GCS bucket structure created
BigQuery datasets created
Audit tables created
Cloud Run service deployed
CLI pipeline testing completed
UI upload page added
Valid file load tested
Bad file rejection tested
Duplicate file handling tested
Bronze metadata columns added
Audit logs populated


8. Important Bronze Metadata Columns

Every Bronze record includes:

batch_id
run_id
source_system
source_file_name
gcs_uri
file_hash
load_date
ingestion_timestamp

These columns provide traceability from BigQuery rows back to the original source file and pipeline run.

9. How to Test the Pipeline
Health Check
SERVICE_URL=$(gcloud run services describe ecom-ingestion-service \
  --region us-central1 \
  --format="value(status.url)")

curl -s "$SERVICE_URL/health"
Check Audit Logs
bq query --use_legacy_sql=false "
SELECT
  table_name,
  source_file_name,
  upload_status,
  row_count,
  error_message,
  created_at
FROM \`ecom-intelligence-pipeline-001.ecom_audit.file_upload_log\`
ORDER BY created_at DESC
LIMIT 20;
"
Check Bronze Row Counts
bq query --use_legacy_sql=false "
SELECT
  batch_id,
  COUNT(*) AS row_count
FROM \`ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders\`
GROUP BY batch_id
ORDER BY batch_id;
"

10. Next Phase

The next phase is the Silver layer using dbt.

Silver layer goals:

Register Bronze tables as dbt sources
Clean and standardize data
Cast data types
Remove duplicate business records
Add dbt tests
Build clean Silver tables for Gold modeling

Do not move to Gold until Silver models and tests are complete.