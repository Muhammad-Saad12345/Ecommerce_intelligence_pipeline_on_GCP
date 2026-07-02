Data Dictionary: bronze_products
Table
ecom_bronze.bronze_products
Purpose

Stores raw validated product records with ingestion metadata.

Grain

One row represents one product.

Source File
olist_products_dataset.csv
Source Columns
Column	Description
product_id	Product identifier
product_category_name	Product category
product_name_lenght	Product name length, misspelled in source
product_description_lenght	Product description length, misspelled in source
product_photos_qty	Number of product photos
product_weight_g	Product weight in grams
product_length_cm	Product length in centimeters
product_height_cm	Product height in centimeters
product_width_cm	Product width in centimeters
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

rename product_name_lenght to product_name_length
rename product_description_lenght to product_description_length
cast dimensions to numeric
handle missing product categories
standardize category names