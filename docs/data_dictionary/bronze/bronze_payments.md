Data Dictionary: bronze_payments
Table
ecom_bronze.bronze_payments
Purpose

Stores raw validated Olist payment records with ingestion metadata.

Grain

One row represents one payment record for an order.

Source File
olist_order_payments_dataset.csv
Source Columns
Column	Description
order_id	Order identifier
payment_sequential	Payment sequence number
payment_type	Payment method type
payment_installments	Number of installments
payment_value	Payment amount
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

cast payment_value to numeric
cast payment_installments to integer
validate payment_value >= 0
validate accepted payment_type values
check relationship with silver_orders