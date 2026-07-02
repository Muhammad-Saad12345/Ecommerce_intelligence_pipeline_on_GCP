Data Dictionary: bronze_sellers
Table
ecom_bronze.bronze_sellers
Purpose

Stores raw validated seller records with ingestion metadata.

Grain

One row represents one seller.

Source File
olist_sellers_dataset.csv
Source Columns
Column	Description
seller_id	Seller identifier
seller_zip_code_prefix	Seller zip code prefix
seller_city	Seller city
seller_state	Seller state
Metadata Columns
Column	Description
batch_id	File batch identifier
run_id	Cloud Run execution identifier
source_system	Source system
source_file_name	Original file name
gcs_uri	Raw GCS path
file_hash	SHA256 file hash
load_date	Load date
ingestion_timestamp	Ingestion timestamp
Silver Plan

Silver will:

deduplicate seller_id
standardize city/state values
cast zip code as string
validate seller_id not null