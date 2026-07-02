Audit Logging Documentation
Purpose

Audit logging provides full traceability for every file and pipeline run.

The pipeline should answer:

Which file was uploaded?
Which table was targeted?
Was the file valid?
Was it duplicate?
How many rows were loaded?
Which pipeline step failed?
Why was a file rejected?
Where is the raw or rejected file stored?
Audit Dataset
ecom_audit
Audit Tables
file_upload_log
pipeline_run_log
data_quality_log
rejected_records
1. file_upload_log
Purpose

Tracks file-level ingestion status.

Typical Status Values
SUCCESS
FAILED
DUPLICATE
Key Columns
upload_id
run_id
batch_id
source_system
table_name
source_file_name
gcs_uri
file_hash
row_count
upload_status
created_at
error_message
Example Success Record
table_name = orders
source_file_name = olist_orders_sample_new.csv
row_count = 101
upload_status = SUCCESS
error_message = NULL
Example Duplicate Record
upload_status = DUPLICATE
row_count = 0
error_message = Duplicate file detected. Bronze load skipped.
Query
SELECT
  table_name,
  source_file_name,
  upload_status,
  row_count,
  error_message,
  created_at
FROM `ecom-intelligence-pipeline-001.ecom_audit.file_upload_log`
ORDER BY created_at DESC
LIMIT 20;
2. pipeline_run_log
Purpose

Tracks pipeline execution steps.

Expected Steps
process_started
bronze_load
process_completed
process_failed
duplicate_check
Key Columns
run_id
batch_id
pipeline_name
step_name
status
start_time
end_time
error_message
Example Successful Pipeline
process_started   STARTED
bronze_load       SUCCESS
process_completed SUCCESS
Query
SELECT
  batch_id,
  step_name,
  status,
  error_message,
  start_time
FROM `ecom-intelligence-pipeline-001.ecom_audit.pipeline_run_log`
ORDER BY start_time DESC
LIMIT 50;
3. data_quality_log
Purpose

Tracks validation checks and data quality results.

Common Checks
file_not_empty
schema_validation
duplicate_file_check
row_count_check
file_validation
Key Columns
check_id
run_id
batch_id
table_name
check_name
check_status
expected_value
actual_value
failed_count
created_at
Example Successful Checks
file_not_empty = PASS
schema_validation = PASS
row_count_check = PASS
Example Failed Check
file_validation = FAILED
actual_value = Missing required columns
failed_count = 1
Query
SELECT
  batch_id,
  table_name,
  check_name,
  check_status,
  actual_value,
  failed_count,
  created_at
FROM `ecom-intelligence-pipeline-001.ecom_audit.data_quality_log`
ORDER BY created_at DESC
LIMIT 50;
4. rejected_records
Purpose

Stores rejected file details and failure reasons.

Key Columns
rejected_id
run_id
batch_id
source_file_name
gcs_uri
rejection_level
rejection_reason
rejected_payload
created_at
Rejection Level

Current rejection level:

FILE

Future possible level:

ROW
Example Rejection
source_file_name = bad_orders_dataset.csv
rejection_level = FILE
rejection_reason = Missing required columns
Query
SELECT
  batch_id,
  source_file_name,
  gcs_uri,
  rejection_level,
  rejection_reason,
  created_at
FROM `ecom-intelligence-pipeline-001.ecom_audit.rejected_records`
ORDER BY created_at DESC
LIMIT 20;
Important Production Issue Found

During development, the pipeline failed because file_upload_log did not have the expected source_file_name column.

Error:

no such field: source_file_name

Root cause:

Cloud Run code and BigQuery audit table schema were not aligned.

Fix:

Added source_file_name column to file_upload_log.

Prevention:

Keep all audit table DDL scripts version-controlled.
Never manually change audit schemas without updating code.
Audit Logging Best Practices
Every pipeline run should have a run_id.
Every file should have a batch_id.
Every file should have one clear final status.
Every failure should have an error reason.
Rejected files should not be silently deleted.
Audit logs should be checked before moving to Silver.