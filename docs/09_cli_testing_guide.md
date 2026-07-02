CLI Testing Guide
Purpose

This guide explains how to test the ingestion pipeline using CLI commands.

CLI testing is important because it gives exact errors and outputs when something breaks.

Step 1: Set Variables
cd ~/ecommerce-intelligence-pipeline

export PROJECT_ID=ecom-intelligence-pipeline-001
export REGION=us-central1
export BUCKET_NAME=ecom-intelligence-pipeline-001-ecom-raw
export SERVICE_NAME=ecom-ingestion-service
export SOURCE_SYSTEM=olist
export TABLE_NAME=orders
export LOCAL_FILE=data/raw/olist_orders_dataset.csv
Step 2: Get Cloud Run URL
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format="value(status.url)")

echo $SERVICE_URL
Step 3: Health Check
curl -s "$SERVICE_URL/health"

Expected:

{
  "status": "ok",
  "service": "ecom-ingestion-service"
}

If health check fails, do not continue.

Step 4: Upload File to GCS tmp/
export BATCH_ID=cli_test_$(date +%Y%m%d_%H%M%S)
export GCS_TMP_PATH=tmp/source=olist/table=orders/upload_id=$BATCH_ID/olist_orders_dataset.csv

gsutil cp $LOCAL_FILE gs://$BUCKET_NAME/$GCS_TMP_PATH

Verify:

gsutil ls gs://$BUCKET_NAME/$GCS_TMP_PATH
Step 5: Trigger Cloud Run /process
curl -s -X POST "$SERVICE_URL/process" \
  -H "Content-Type: application/json" \
  -d "{
    \"bucket_name\": \"$BUCKET_NAME\",
    \"source_system\": \"$SOURCE_SYSTEM\",
    \"table_name\": \"$TABLE_NAME\",
    \"tmp_file_path\": \"$GCS_TMP_PATH\",
    \"batch_id\": \"$BATCH_ID\"
  }"
Expected Results

If file is new and valid:

status = success
row_count > 0
raw_gcs_uri populated
bronze_table populated

If file is duplicate:

status = skipped
reason = duplicate_file

If file is invalid:

status = failed
error message returned
rejected_gcs_uri populated
Step 6: Verify GCS raw Path
gsutil ls -r gs://$BUCKET_NAME/raw/source=olist/table=orders/
Step 7: Verify Bronze Table
bq query --use_legacy_sql=false "
SELECT
  batch_id,
  COUNT(*) AS row_count
FROM \`$PROJECT_ID.ecom_bronze.bronze_orders\`
GROUP BY batch_id
ORDER BY batch_id;
"
Step 8: Verify Metadata
bq query --use_legacy_sql=false "
SELECT
  batch_id,
  run_id,
  source_system,
  source_file_name,
  gcs_uri,
  file_hash,
  load_date,
  ingestion_timestamp
FROM \`$PROJECT_ID.ecom_bronze.bronze_orders\`
WHERE batch_id = '$BATCH_ID'
LIMIT 10;
"
Step 9: Verify file_upload_log
bq query --use_legacy_sql=false "
SELECT
  batch_id,
  table_name,
  source_file_name,
  row_count,
  upload_status,
  error_message,
  created_at
FROM \`$PROJECT_ID.ecom_audit.file_upload_log\`
WHERE batch_id = '$BATCH_ID'
ORDER BY created_at DESC;
"
Step 10: Verify pipeline_run_log
bq query --use_legacy_sql=false "
SELECT
  batch_id,
  step_name,
  status,
  error_message,
  start_time
FROM \`$PROJECT_ID.ecom_audit.pipeline_run_log\`
WHERE batch_id = '$BATCH_ID'
ORDER BY start_time;
"

Expected successful steps:

process_started
bronze_load
process_completed
Step 11: Verify data_quality_log
bq query --use_legacy_sql=false "
SELECT
  batch_id,
  table_name,
  check_name,
  check_status,
  actual_value,
  failed_count,
  created_at
FROM \`$PROJECT_ID.ecom_audit.data_quality_log\`
WHERE batch_id = '$BATCH_ID'
ORDER BY created_at;
"

Expected successful checks:

file_not_empty = PASS
schema_validation = PASS
row_count_check = PASS
Bad File Test

Create bad file:

cat > data/raw/bad_orders_dataset.csv <<EOF
wrong_col_1,wrong_col_2
1,test
2,test
EOF

Upload and process:

export BATCH_ID=bad_test_$(date +%Y%m%d_%H%M%S)
export LOCAL_FILE=data/raw/bad_orders_dataset.csv
export GCS_TMP_PATH=tmp/source=olist/table=orders/upload_id=$BATCH_ID/bad_orders_dataset.csv

gsutil cp $LOCAL_FILE gs://$BUCKET_NAME/$GCS_TMP_PATH

curl -s -X POST "$SERVICE_URL/process" \
  -H "Content-Type: application/json" \
  -d "{
    \"bucket_name\": \"$BUCKET_NAME\",
    \"source_system\": \"$SOURCE_SYSTEM\",
    \"table_name\": \"$TABLE_NAME\",
    \"tmp_file_path\": \"$GCS_TMP_PATH\",
    \"batch_id\": \"$BATCH_ID\"
  }"

Verify rejected records:

bq query --use_legacy_sql=false "
SELECT
  batch_id,
  source_file_name,
  gcs_uri,
  rejection_level,
  rejection_reason,
  created_at
FROM \`$PROJECT_ID.ecom_audit.rejected_records\`
WHERE batch_id = '$BATCH_ID'
ORDER BY created_at DESC;
"
Duplicate File Test

Upload the same successful file again.

Expected:

status = skipped
reason = duplicate_file
upload_status = DUPLICATE
row_count = 0
Testing Rule

Do not test all files together.

Recommended order:

orders
customers
order_items
products
payments
sellers

Test one file, verify audit logs, then move to the next file.