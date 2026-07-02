Cloud Run Service Documentation
Service Name
ecom-ingestion-service
Purpose

The Cloud Run service is responsible for:

Receiving file processing requests
Supporting UI file upload
Reading files from GCS tmp/
Validating file structure
Detecting duplicate files
Copying valid files to GCS raw/
Copying invalid files to GCS rejected/
Loading valid files to BigQuery Bronze
Writing audit logs
Runtime
Python 3.11
FastAPI
Uvicorn
Google Cloud Storage client
BigQuery client
Pandas
PyArrow
Main Endpoints
GET /health
Purpose

Checks if the service is running.

Example
curl -s "$SERVICE_URL/health"
Expected Response
{
  "status": "ok",
  "service": "ecom-ingestion-service"
}
GET /
Purpose

Shows the browser upload UI.

User can select:

source_system
table_name
CSV file

Then submit the file for upload and processing.

POST /process
Purpose

CLI/API endpoint for processing a file that already exists in GCS tmp/.

Request Example
{
  "bucket_name": "ecom-intelligence-pipeline-001-ecom-raw",
  "source_system": "olist",
  "table_name": "orders",
  "tmp_file_path": "tmp/source=olist/table=orders/upload_id=batch_001/olist_orders_dataset.csv",
  "batch_id": "batch_001"
}
Used For
CLI testing
Debugging
Manual pipeline testing
POST /upload-and-process
Purpose

Browser UI endpoint.

It performs:

1. Receives uploaded file
2. Saves file to GCS tmp/
3. Calls same pipeline logic as /process
4. Returns result page
Important Functions
get_blob_bytes()

Reads file bytes from GCS tmp/.

generate_file_hash()

Creates SHA256 hash of the file content.

Used for duplicate detection.

check_duplicate_file()

Checks file_upload_log to see if file hash already exists with upload_status = SUCCESS.

validate_schema()

Compares actual CSV columns with expected columns.

copy_to_raw()

Copies valid file from tmp to raw.

copy_to_rejected()

Copies failed file from tmp to rejected.

load_to_bronze()

Loads validated dataframe into BigQuery Bronze table.

log_file_upload()

Writes file-level status to file_upload_log.

log_pipeline()

Writes pipeline step status to pipeline_run_log.

log_quality()

Writes validation results to data_quality_log.

log_rejected()

Writes rejected file details to rejected_records.

Environment Variables
PROJECT_ID
BRONZE_DATASET
AUDIT_DATASET
RAW_BUCKET_NAME
MAX_UPLOAD_SIZE_BYTES
Deploy Command
cd ~/ecommerce-intelligence-pipeline/ingestion

gcloud run deploy ecom-ingestion-service \
  --source . \
  --region us-central1 \
  --service-account ecom-pipeline-sa@ecom-intelligence-pipeline-001.iam.gserviceaccount.com \
  --set-env-vars PROJECT_ID=ecom-intelligence-pipeline-001,BRONZE_DATASET=ecom_bronze,AUDIT_DATASET=ecom_audit,RAW_BUCKET_NAME=ecom-intelligence-pipeline-001-ecom-raw \
  --memory 1Gi \
  --cpu 1 \
  --timeout 900 \
  --allow-unauthenticated
Required Service Account Roles

Cloud Run service account:

BigQuery Data Editor
BigQuery Job User
Storage Object Admin
Logs Writer

Deployer user also needs:

Service Account User
Cloud Run Admin
Cloud Build permissions
Artifact Registry permissions
Current Security Status

Current service is deployed with:

--allow-unauthenticated

This is acceptable for development and demo, but not production.

Production should use:

authenticated access
IAM-based access
signed upload URLs or protected UI
rate limits
file size limits
Current Limitation

The pipeline is synchronous.

This means:

User uploads file
Cloud Run processes file
User waits for response

For larger production workloads, use asynchronous design:

UI upload → tmp/ → Eventarc or Cloud Tasks → processing → status page