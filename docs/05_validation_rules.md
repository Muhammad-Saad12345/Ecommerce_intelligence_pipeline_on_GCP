Validation Rules Documentation
Purpose

Validation ensures that only acceptable CSV files are moved into the raw zone and loaded into BigQuery Bronze.

Invalid files are copied to the rejected zone and logged in audit tables.

Validation Location

Validation is implemented inside the Cloud Run ingestion service.

Main validation checks:

File exists
File is not empty
File extension is CSV
Source system is supported
Table name is supported
Required columns exist
File is not duplicate
Supported Source System

Current supported source system:

olist

Any other source system should be rejected in v1.

Supported Tables
orders
customers
order_items
products
payments
sellers
File-Level Validation Rules
Rule	Description	Failure Action
File exists	GCS object must exist in tmp/	Reject
File not empty	File size must be greater than 0	Reject
CSV only	File must be a .csv file for UI uploads	Reject
Supported table	table_name must exist in allowed list	Reject
Required columns	CSV must contain expected columns	Reject
Duplicate file	file_hash must not already exist as SUCCESS	Skip Bronze load
Duplicate Detection

Duplicate detection uses:

SHA256 file_hash

If the same file content was already successfully loaded, the pipeline does not load it again.

Expected duplicate output:

status = skipped
reason = duplicate_file
upload_status = DUPLICATE
row_count = 0
Orders Required Columns
order_id
customer_id
order_status
order_purchase_timestamp
order_approved_at
order_delivered_carrier_date
order_delivered_customer_date
order_estimated_delivery_date
Customers Required Columns
customer_id
customer_unique_id
customer_zip_code_prefix
customer_city
customer_state
Order Items Required Columns
order_id
order_item_id
product_id
seller_id
shipping_limit_date
price
freight_value
Products Required Columns
product_id
product_category_name
product_name_lenght
product_description_lenght
product_photos_qty
product_weight_g
product_length_cm
product_height_cm
product_width_cm

Note: Olist uses misspelled column names like product_name_lenght. These are kept as-is in Bronze. They will be standardized in Silver.

Payments Required Columns
order_id
payment_sequential
payment_type
payment_installments
payment_value
Sellers Required Columns
seller_id
seller_zip_code_prefix
seller_city
seller_state
Bad File Handling

If a file fails validation:

1. File is copied to GCS rejected/
2. rejected_records table receives failure reason
3. data_quality_log receives FAILED check
4. file_upload_log receives FAILED status
5. pipeline_run_log receives FAILED status
6. API/UI returns error details
Example Bad File Test

Bad file:

wrong_col_1,wrong_col_2
1,test
2,test

Expected result:

Missing required columns
Example Rejected GCS Path
rejected/source=olist/table=orders/load_date=2026-06-06/batch_id=bad_test_xxxx/bad_orders_dataset.csv
Data Quality Log Examples

Successful validation:

file_not_empty = PASS
schema_validation = PASS
row_count_check = PASS

Failed validation:

file_validation = FAILED

Duplicate file:

duplicate_file_check = FAILED
upload_status = DUPLICATE
Production Improvement

Current schema rules are hardcoded in Python.

Future improvement:

Move schema rules into external JSON files:
ingestion/app/schemas/orders_schema.json
ingestion/app/schemas/customers_schema.json

This will make schema management cleaner and more production-ready.