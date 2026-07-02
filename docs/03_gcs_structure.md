GCS Folder Structure
Bucket
gs://ecom-intelligence-pipeline-001-ecom-raw
Main Zones
tmp/
raw/
rejected/
archive/
Zone Responsibilities
Zone	Purpose
tmp/	Temporary landing zone for uploaded files before validation
raw/	Validated immutable source files
rejected/	Invalid files that failed validation
archive/	Future zone for long-term processed file storage
tmp Zone

Files uploaded from UI or CLI first land in tmp.

Path format:

tmp/source={source_system}/table={table_name}/upload_id={batch_id}/{file_name}

Example:

tmp/source=olist/table=orders/upload_id=ui_20260606_151736/olist_orders_dataset.csv

Purpose:

Store file before validation
Allow Cloud Run to inspect file
Prevent invalid files from entering raw zone
raw Zone

Only validated files are copied to raw.

Path format:

raw/source={source_system}/table={table_name}/load_date={YYYY-MM-DD}/batch_id={batch_id}/{file_name}

Example:

raw/source=olist/table=orders/load_date=2026-06-06/batch_id=success_test_20260606_151736/olist_orders_sample_new.csv

Purpose:

Store validated original files
Support traceability
Allow reprocessing if needed
Preserve source file history
rejected Zone

Files that fail validation are copied to rejected.

Path format:

rejected/source={source_system}/table={table_name}/load_date={YYYY-MM-DD}/batch_id={batch_id}/{file_name}

Example:

rejected/source=olist/table=orders/load_date=2026-06-06/batch_id=bad_test_20260606_151445/bad_orders_dataset.csv

Purpose:

Preserve invalid files
Support debugging
Keep failure evidence
Help explain pipeline issues
archive Zone

Current status:

archive/ is created but not actively used yet.

Future use:

Store files after successful downstream processing
Separate active raw files from processed historical files
Support lifecycle management
Naming Convention

Use partition-style folder naming:

source=olist
table=orders
load_date=YYYY-MM-DD
batch_id=unique_batch_id

This style is easy to query, debug, and understand.

Important Rules
Do not upload directly to raw.
Always upload to tmp first.
Only validated files should be copied to raw.
Failed files should be copied to rejected.
Do not delete rejected files during development.
Every file path should include source, table, date, and batch id.
Example End-to-End GCS Flow
tmp/source=olist/table=orders/upload_id=ui_001/olist_orders_dataset.csv
      ↓ validation passes
raw/source=olist/table=orders/load_date=2026-06-06/batch_id=ui_001/olist_orders_dataset.csv

Failure flow:

tmp/source=olist/table=orders/upload_id=bad_001/bad_orders_dataset.csv
      ↓ validation fails
rejected/source=olist/table=orders/load_date=2026-06-06/batch_id=bad_001/bad_orders_datase