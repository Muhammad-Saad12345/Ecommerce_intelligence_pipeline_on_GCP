Bronze Ingestion Documentation
Purpose

The Bronze layer stores validated raw source data in BigQuery with additional metadata columns.

The goal of the Bronze layer is not to clean business logic. The goal is to preserve source data and make it traceable.

Cleaning, deduplication, type casting, and business rules will be handled in the Silver layer using dbt.

Current Bronze Flow
CSV file uploaded
      ↓
GCS tmp/
      ↓
Cloud Run validation
      ↓
GCS raw/
      ↓
BigQuery Bronze table
      ↓
Audit logs
Bronze Dataset
ecom_bronze
Bronze Tables

Current planned Bronze tables:

bronze_orders
bronze_customers
bronze_order_items
bronze_products
bronze_payments
bronze_sellers

Future optional Bronze tables:

bronze_order_reviews
bronze_geolocation
Bronze Table Naming Standard

Format:

bronze_{entity_name}

Examples:

bronze_orders
bronze_customers
bronze_products
Metadata Columns

Each Bronze table should include these metadata columns:

batch_id
run_id
source_system
source_file_name
gcs_uri
file_hash
load_date
ingestion_timestamp
Metadata Column Purpose
Column	Purpose
batch_id	Identifies a file batch or pipeline upload
run_id	Identifies one Cloud Run execution
source_system	Identifies source system, currently olist
source_file_name	Original uploaded file name
gcs_uri	Raw GCS location of validated file
file_hash	SHA256 file fingerprint for duplicate detection
load_date	Date when file was processed
ingestion_timestamp	Timestamp when data was loaded
Why Metadata Matters

Metadata allows engineers to answer:

Which file created this row?
When was this row ingested?
Which pipeline run loaded this row?
Was this file uploaded before?
Where is the original raw file stored?
Can we trace a dashboard number back to source?
Current Load Strategy

Current Bronze load uses:

WRITE_APPEND

This means each valid file batch appends rows into the target Bronze table.

Duplicate Protection

Duplicate file detection is based on:

file_hash

If the same file content already exists in file_upload_log with upload_status = SUCCESS, the pipeline skips Bronze load.

Expected duplicate behavior:

upload_status = DUPLICATE
row_count = 0
Bronze rows do not increase
Important Current Risk

Earlier testing created duplicate Bronze batches due to audit table schema mismatch and testing iterations.

Before moving to Silver, duplicate or failed test batches should be cleaned or clearly documented.

Recommended check:

SELECT
  batch_id,
  COUNT(*) AS row_count
FROM `ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders`
GROUP BY batch_id
ORDER BY batch_id;
Recommended Cleanup Before Silver

Keep one clean full orders batch and remove failed duplicate test batches if needed.

Example:

DELETE FROM `ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders`
WHERE batch_id IN ('manual_clean_001', 'duplicate_test_001');

Only run cleanup after verifying which batches are test or failed batches.

Bronze vs Silver Responsibility
Layer	Responsibility
Bronze	Raw validated data + metadata
Silver	Cleaned, typed, deduplicated data
Gold	Business-ready facts, dimensions, marts
Verification Queries
Count rows by batch
SELECT
  batch_id,
  COUNT(*) AS row_count
FROM `ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders`
GROUP BY batch_id
ORDER BY batch_id;
Check metadata
SELECT
  batch_id,
  run_id,
  source_system,
  source_file_name,
  gcs_uri,
  file_hash,
  load_date,
  ingestion_timestamp
FROM `ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders`
LIMIT 10;
Check source file
SELECT
  source_file_name,
  COUNT(*) AS row_count
FROM `ecom-intelligence-pipeline-001.ecom_bronze.bronze_orders`
GROUP BY source_file_name
ORDER BY row_count DESC;
Current Completion Status

Bronze ingestion is working for orders and tested with:

Valid file load
Bad file rejection
Metadata check
Audit logs
UI upload flow
CLI test flow

Before Silver, all required Olist files should be uploaded and verified.