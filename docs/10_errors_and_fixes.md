Errors and Fixes
Purpose

This document records major errors faced during development, their root causes, fixes, and prevention steps.

This is important because real data engineering projects require debugging history and operational knowledge.

Error 1: iam.serviceaccounts.actAs Permission Denied
Error
Permission 'iam.serviceaccounts.actAs' denied on service account
Root Cause

The user deploying Cloud Run did not have permission to attach the service account to the Cloud Run service.

Fix

Granted Service Account User role:

gcloud iam service-accounts add-iam-policy-binding \
  ecom-pipeline-sa@ecom-intelligence-pipeline-001.iam.gserviceaccount.com \
  --member="user:alyan2001ali@gmail.com" \
  --role="roles/iam.serviceAccountUser"
Prevention

Before deploying Cloud Run with a custom service account, ensure deployer has:

roles/iam.serviceAccountUser
Error 2: Cloud Build Could Not Read Source Zip
Error
storage.objects.get denied on run-sources bucket
Root Cause

The Cloud Build/Compute service account did not have permission to read source files uploaded by gcloud run deploy --source.

Fix

Granted required storage/build permissions to the build service account.

Prevention

Make sure Cloud Build service account has access to:

source upload bucket
Artifact Registry
Cloud Build builder role
Error 3: Missing fsspec Dependency
Error
Missing optional dependency 'fsspec'
Root Cause

Pandas tried to read directly from a gs:// path.

Fix

Changed code to download GCS object bytes first, then read with:

pd.read_csv(io.BytesIO(file_bytes))
Prevention

For Cloud Run MVP, read files from GCS using the Google Cloud Storage client and pass bytes to Pandas.

Error 4: Cloud Run Deploy Failed from Wrong Folder
Error
Build failed
Building using Buildpacks
Root Cause

Deploy command was run from the project root instead of the ingestion/ folder where Dockerfile exists.

Fix

Run deploy from:

cd ~/ecommerce-intelligence-pipeline/ingestion
Prevention

Always verify folder before deploy:

ls

Expected:

Dockerfile
requirements.txt
app/
Error 5: file_upload_log Missing source_file_name
Error
no such field: source_file_name
Root Cause

Cloud Run code attempted to insert source_file_name, but the BigQuery file_upload_log table schema did not contain that column.

Fix

Added missing column to file_upload_log.

Example:

ALTER TABLE `ecom-intelligence-pipeline-001.ecom_audit.file_upload_log`
ADD COLUMN source_file_name STRING;
Prevention

Keep audit table DDL scripts version-controlled.

Do not manually change audit table structure without updating code.

Error 6: File Not Found in tmp/
Error
404: File not found: gs://.../tmp/...
Root Cause

Cloud Run was triggered with a tmp path where the file did not exist.

Fix

Verified the file exists before calling /process.

gsutil ls gs://$BUCKET_NAME/$GCS_TMP_PATH
Prevention

Always upload and verify file before triggering Cloud Run manually.

Error 7: Duplicate Bronze Loads During Testing
Problem

Multiple batches were loaded into bronze_orders during early testing.

Example:

manual_003
manual_clean_001
duplicate_test_001
Root Cause

Duplicate detection was not fully reliable while audit logging schema was broken.

Fix

Clean duplicate test batches after verifying audit history.

Example:

DELETE FROM `ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders`
WHERE batch_id IN ('manual_clean_001', 'duplicate_test_001');
Prevention

Fix audit logging before running duplicate tests.

Always verify:

file_upload_log
pipeline_run_log
data_quality_log
Error 8: Wrong Table Selected in UI
Problem

If a user uploads customers file but selects orders, schema validation fails.

Fix

Use dropdown list and select correct target table.

Prevention

Future improvement: infer table name from file name and warn user before processing.

Current Learning

Most pipeline issues came from:

IAM permissions
wrong folder deployment
schema mismatch
wrong GCS path
duplicate test batches

These are common real-world data engineering issues.