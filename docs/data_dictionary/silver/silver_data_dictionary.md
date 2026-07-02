# Silver Data Dictionary

## 1. Overview

This document describes all Silver layer tables created in BigQuery.

Dataset:

```text
ecom_silver
```

Silver tables are cleaned, typed, deduplicated, and validated versions of Bronze tables.

---

# 2. Table: silver_orders

## Purpose

Stores cleaned order-level data.

## Grain

```text
One row per order_id
```

## Source

```text
ecom_bronze.bronze_orders
```

## Columns

| Column                        | Type      | Description                                    |
| ----------------------------- | --------- | ---------------------------------------------- |
| order_id                      | STRING    | Unique order identifier                        |
| customer_id                   | STRING    | Customer identifier linked to the order        |
| order_status                  | STRING    | Standardized order status                      |
| order_purchase_timestamp      | TIMESTAMP | Timestamp when order was placed                |
| order_approved_at             | TIMESTAMP | Timestamp when order was approved              |
| order_delivered_carrier_date  | TIMESTAMP | Timestamp when order was handed to carrier     |
| order_delivered_customer_date | TIMESTAMP | Timestamp when order was delivered to customer |
| order_estimated_delivery_date | TIMESTAMP | Estimated delivery timestamp                   |
| batch_id                      | STRING    | Ingestion batch identifier                     |
| run_id                        | STRING    | Cloud Run execution identifier                 |
| source_system                 | STRING    | Source system name                             |
| source_file_name              | STRING    | Original uploaded file name                    |
| gcs_uri                       | STRING    | Raw file GCS URI                               |
| file_hash                     | STRING    | SHA256 file hash                               |
| load_date                     | DATE      | Date when file was loaded                      |
| ingestion_timestamp           | TIMESTAMP | Timestamp when row was ingested                |

## Tests

```text
order_id not_null
order_id unique
customer_id not_null
order_status not_null
order_status accepted_values
ingestion_timestamp not_null
```

---

# 3. Table: silver_customers

## Purpose

Stores cleaned customer-level data.

## Grain

```text
One row per customer_id
```

## Source

```text
ecom_bronze.bronze_customers
```

## Columns

| Column                   | Type      | Description                            |
| ------------------------ | --------- | -------------------------------------- |
| customer_id              | STRING    | Customer identifier used in orders     |
| customer_unique_id       | STRING    | Unique customer identity across orders |
| customer_zip_code_prefix | STRING    | Customer zip code prefix               |
| customer_city            | STRING    | Standardized customer city             |
| customer_state           | STRING    | Standardized customer state            |
| batch_id                 | STRING    | Ingestion batch identifier             |
| run_id                   | STRING    | Cloud Run execution identifier         |
| source_system            | STRING    | Source system name                     |
| source_file_name         | STRING    | Original uploaded file name            |
| gcs_uri                  | STRING    | Raw file GCS URI                       |
| file_hash                | STRING    | SHA256 file hash                       |
| load_date                | DATE      | Date when file was loaded              |
| ingestion_timestamp      | TIMESTAMP | Timestamp when row was ingested        |

## Tests

```text
customer_id not_null
customer_id unique
customer_unique_id not_null
customer_state not_null
ingestion_timestamp not_null
```

---

# 4. Table: silver_products

## Purpose

Stores cleaned product-level data.

## Grain

```text
One row per product_id
```

## Source

```text
ecom_bronze.bronze_products
```

## Columns

| Column                     | Type      | Description                     |
| -------------------------- | --------- | ------------------------------- |
| product_id                 | STRING    | Unique product identifier       |
| product_category_name      | STRING    | Standardized product category   |
| product_name_length        | INT64     | Product name length             |
| product_description_length | INT64     | Product description length      |
| product_photos_qty         | INT64     | Number of product photos        |
| product_weight_g           | NUMERIC   | Product weight in grams         |
| product_length_cm          | NUMERIC   | Product length in centimeters   |
| product_height_cm          | NUMERIC   | Product height in centimeters   |
| product_width_cm           | NUMERIC   | Product width in centimeters    |
| batch_id                   | STRING    | Ingestion batch identifier      |
| run_id                     | STRING    | Cloud Run execution identifier  |
| source_system              | STRING    | Source system name              |
| source_file_name           | STRING    | Original uploaded file name     |
| gcs_uri                    | STRING    | Raw file GCS URI                |
| file_hash                  | STRING    | SHA256 file hash                |
| load_date                  | DATE      | Date when file was loaded       |
| ingestion_timestamp        | TIMESTAMP | Timestamp when row was ingested |

## Important Transformation

Original Olist column names contain spelling mistakes:

```text
product_name_lenght
product_description_lenght
```

They were renamed in Silver as:

```text
product_name_length
product_description_length
```

## Tests

```text
product_id not_null
product_id unique
product_category_name not_null
product_weight_g non_negative
product_length_cm non_negative
product_height_cm non_negative
product_width_cm non_negative
ingestion_timestamp not_null
```

---

# 5. Table: silver_sellers

## Purpose

Stores cleaned seller-level data.

## Grain

```text
One row per seller_id
```

## Source

```text
ecom_bronze.bronze_sellers
```

## Columns

| Column                 | Type      | Description                     |
| ---------------------- | --------- | ------------------------------- |
| seller_id              | STRING    | Unique seller identifier        |
| seller_zip_code_prefix | STRING    | Seller zip code prefix          |
| seller_city            | STRING    | Standardized seller city        |
| seller_state           | STRING    | Standardized seller state       |
| batch_id               | STRING    | Ingestion batch identifier      |
| run_id                 | STRING    | Cloud Run execution identifier  |
| source_system          | STRING    | Source system name              |
| source_file_name       | STRING    | Original uploaded file name     |
| gcs_uri                | STRING    | Raw file GCS URI                |
| file_hash              | STRING    | SHA256 file hash                |
| load_date              | DATE      | Date when file was loaded       |
| ingestion_timestamp    | TIMESTAMP | Timestamp when row was ingested |

## Tests

```text
seller_id not_null
seller_id unique
seller_city not_null
seller_state not_null
ingestion_timestamp not_null
```

---

# 6. Table: silver_payments

## Purpose

Stores cleaned payment-level data.

## Grain

```text
One row per order_id + payment_sequential
```

## Source

```text
ecom_bronze.bronze_payments
```

## Columns

| Column               | Type      | Description                          |
| -------------------- | --------- | ------------------------------------ |
| order_id             | STRING    | Order identifier                     |
| payment_sequential   | INT64     | Payment sequence number for an order |
| payment_type         | STRING    | Standardized payment method          |
| payment_installments | INT64     | Number of payment installments       |
| payment_value        | NUMERIC   | Payment amount                       |
| batch_id             | STRING    | Ingestion batch identifier           |
| run_id               | STRING    | Cloud Run execution identifier       |
| source_system        | STRING    | Source system name                   |
| source_file_name     | STRING    | Original uploaded file name          |
| gcs_uri              | STRING    | Raw file GCS URI                     |
| file_hash            | STRING    | SHA256 file hash                     |
| load_date            | DATE      | Date when file was loaded            |
| ingestion_timestamp  | TIMESTAMP | Timestamp when row was ingested      |

## Tests

```text
order_id not_null
order_id relationship to silver_orders.order_id
payment_sequential not_null
payment_type not_null
payment_type accepted_values
payment_installments non_negative
payment_value not_null
payment_value non_negative
ingestion_timestamp not_null
```

---

# 7. Table: silver_order_items

## Purpose

Stores cleaned item-level order data.

## Grain

```text
One row per order_id + order_item_id
```

## Source

```text
ecom_bronze.bronze_order_items
```

## Columns

| Column              | Type      | Description                     |
| ------------------- | --------- | ------------------------------- |
| order_id            | STRING    | Order identifier                |
| order_item_id       | INT64     | Item sequence within the order  |
| product_id          | STRING    | Product identifier              |
| seller_id           | STRING    | Seller identifier               |
| shipping_limit_date | TIMESTAMP | Shipping deadline               |
| price               | NUMERIC   | Item price                      |
| freight_value       | NUMERIC   | Shipping/freight value          |
| batch_id            | STRING    | Ingestion batch identifier      |
| run_id              | STRING    | Cloud Run execution identifier  |
| source_system       | STRING    | Source system name              |
| source_file_name    | STRING    | Original uploaded file name     |
| gcs_uri             | STRING    | Raw file GCS URI                |
| file_hash           | STRING    | SHA256 file hash                |
| load_date           | DATE      | Date when file was loaded       |
| ingestion_timestamp | TIMESTAMP | Timestamp when row was ingested |

## Tests

```text
order_id not_null
order_id relationship to silver_orders.order_id
order_item_id not_null
product_id not_null
product_id relationship to silver_products.product_id
seller_id not_null
seller_id relationship to silver_sellers.seller_id
price not_null
price non_negative
freight_value not_null
freight_value non_negative
ingestion_timestamp not_null
```

---

# 8. Current Silver Quality Summary

Current Silver quality status:

```text
6 Silver models built successfully
45 dbt tests passed
0 dbt test errors
relationship tests passed
non-negative tests passed
accepted values tests passed
unique tests passed
not-null tests passed
```

## 9. Current Row Counts

Based on latest dbt output:

| Table              | Approximate Row Count |
| ------------------ | --------------------: |
| silver_orders      |                 99.4k |
| silver_customers   |                 99.4k |
| silver_products    |                 33.0k |
| silver_sellers     |                  3.1k |
| silver_payments    |                103.9k |
| silver_order_items |                112.7k |

## 10. Gold Layer Readiness

These Silver tables are now ready to support Gold modeling.

Gold layer will use Silver tables to create:

```text
dim_customer
dim_product
dim_seller
dim_date
fact_orders
fact_order_items
fact_payments
business marts
```

Gold should not directly read from Bronze. Gold should read from Silver.
