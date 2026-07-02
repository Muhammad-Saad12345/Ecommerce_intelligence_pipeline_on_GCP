Data Dictionary: bronze_order_items
Table
ecom_bronze.bronze_order_items
Purpose

Stores raw validated order item records with ingestion metadata.

Grain

One row represents one item within an order.

Source File
olist_order_items_dataset.csv
Source Columns
Column	Description
order_id	Order identifier
order_item_id	Sequence number of item within order
product_id	Product identifier
seller_id	Seller identifier
shipping_limit_date	Shipping deadline
price	Item price
freight_value	Shipping/freight value
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

cast price to numeric
cast freight_value to numeric
validate price >= 0
validate freight_value >= 0
deduplicate order_id + order_item_id
check relationships with orders and products