Architecture Documentation
High-Level Architecture

The current pipeline follows this architecture:

Website UI / CLI Upload
        ↓
Cloud Run Ingestion Service
        ↓
Google Cloud Storage tmp/
        ↓
Validation + Duplicate Check
        ↓
Valid File → GCS raw/
        ↓
BigQuery Bronze Table
        ↓
Audit Tables

Invalid File → GCS rejected/
             → rejected_records
Architecture Layers
1. Data Source Layer

The current source is the Olist e-commerce CSV dataset.

Supported files in current version:

olist_orders_dataset.csv
olist_customers_dataset.csv
olist_order_items_dataset.csv
olist_products_dataset.csv
olist_order_payments_dataset.csv
olist_sellers_dataset.csv

Future files may include:

olist_order_reviews_dataset.csv
olist_geolocation_dataset.csv
2. Upload Layer

Files can be uploaded in two ways:

CLI Upload

Used for development and debugging.

Local CSV → GCS tmp/ → Cloud Run /process
UI Upload

Used for demo and portfolio presentation.

Browser Upload Form → Cloud Run /upload-and-process → GCS tmp/
3. Temporary Landing Zone

All uploaded files first land in:

gs://ecom-intelligence-pipeline-001-ecom-raw/tmp/

Purpose:

Store uploaded files before validation
Prevent invalid files from entering raw zone
Keep upload process separated from validated raw storage
4. Validation Layer

Cloud Run validates:

File exists
File is not empty
File extension is CSV
Source system is supported
Table name is supported
Required columns exist
Duplicate file hash does not already exist
5. Raw Zone

Valid files are copied to:

gs://ecom-intelligence-pipeline-001-ecom-raw/raw/

Path format:

raw/source=olist/table={table_name}/load_date={YYYY-MM-DD}/batch_id={batch_id}/{file_name}

Example:

raw/source=olist/table=orders/load_date=2026-06-06/batch_id=ui_20260606_xxxx/olist_orders_dataset.csv
6. Rejected Zone

Invalid files are copied to:

gs://ecom-intelligence-pipeline-001-ecom-raw/rejected/

Path format:

rejected/source=olist/table={table_name}/load_date={YYYY-MM-DD}/batch_id={batch_id}/{file_name}

Rejected files are not deleted. They are retained for debugging and audit.

7. Bronze Layer

Validated files are loaded into BigQuery Bronze tables:

ecom_bronze.bronze_orders
ecom_bronze.bronze_customers
ecom_bronze.bronze_order_items
ecom_bronze.bronze_products
ecom_bronze.bronze_payments
ecom_bronze.bronze_sellers

Bronze tables store raw source data with metadata.

8. Audit Layer

Audit tables are stored in:

ecom_audit

Tables:

file_upload_log
pipeline_run_log
data_quality_log
rejected_records

These tables provide traceability, debugging support, and pipeline observability.

9. Future Silver Layer

Silver layer will be built using dbt.

Silver responsibilities:

Type casting
Deduplication
Standard naming
Null handling
Relationship checks
Business rule validation
10. Future Gold Layer

Gold layer will contain:

Dimension tables
Fact tables
Business marts
Dashboard-ready models
Design Decision

Files do not go directly into raw storage from the UI. They first land in tmp, then Cloud Run validates the file. Only valid files are copied to raw.

This is an intentional industry-style decision to protect the raw zone from invalid uploads.