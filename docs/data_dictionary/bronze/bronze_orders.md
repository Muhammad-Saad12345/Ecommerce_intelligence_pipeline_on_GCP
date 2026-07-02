Data Dictionary: bronze_orders
Table
ecom_bronze.bronze_orders
Purpose

Stores raw validated Olist order records with ingestion metadata.

Grain

One row represents one order record from the Olist orders CSV file.

Source File
olist_orders_dataset.csv

Source Columns
Column	Description
order_id	                    Customer identifier linked to the order
order_status	                Current order status
order_purchase_timestamp        Timestamp when order was placed
order_approved_at	            Timestamp when order was approved
order_delivered_carrier_date	Timestamp when order was handed to carrier
order_delivered_customer_date	Timestamp when order was delivered
order_estimated_delivery_date	Estimated delivery date

Metadata Columns
Column	Description
batch_id	File batch identifier
run_id	Cloud Run execution identifier
source_system	Source system name, currently olist
source_file_name	Original uploaded file name
gcs_uri	Raw GCS path of validated file
file_hash	SHA256 hash of file content
load_date	Date when file was loaded
ingestion_timestamp	Timestamp when row was ingested
Bronze Notes
Data is preserved close to raw format.
Type casting will happen in Silver.
Duplicate business records will be handled in Silver.
File-level duplicates are handled during ingestion using file_hash.