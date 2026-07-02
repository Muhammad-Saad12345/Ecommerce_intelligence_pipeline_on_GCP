Data Dictionary: bronze_customers
Table
ecom_bronze.bronze_customers
Purpose

Stores raw validated Olist customer records with ingestion metadata.

Grain

One row represents one customer record.

Source File
olist_customers_dataset.csv
Source Columns
Column	Description
customer_id	Customer identifier used in orders
customer_unique_id	Unique customer identity across orders
customer_zip_code_prefix	Customer zip code prefix
customer_city	Customer city
customer_state	Customer state
Metadata Columns
Column	Description
batch_id	File batch identifier
run_id	Cloud Run execution identifier
source_system	Source system name
source_file_name	Original file name
gcs_uri	Raw file location
file_hash	SHA256 file hash
load_date	Load date
ingestion_timestamp	Ingestion timestamp
Silver Plan

Silver will:

deduplicate customer_id
standardize city/state values
cast zip code as string
validate customer_id not null