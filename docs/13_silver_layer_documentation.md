Silver Layer Documentation
1. Purpose

The Silver layer is the cleaned and trusted layer of the e-commerce data platform.

Bronze tables store validated raw data with metadata. Silver tables transform that raw data into clean, deduplicated, type-casted, and testable datasets.

The Silver layer is the foundation for the Gold layer, where facts, dimensions, and business marts will be created.

2. Silver Layer Objective

The objective of the Silver layer is to:

Clean raw Bronze data
Standardize column values
Cast columns into correct data types
Remove duplicate business records
Enforce table grain
Validate important business keys
Add dbt tests for data quality
Prepare clean data for Gold modeling
3. Current Silver Dataset
ecom_silver
4. Silver Models Created

The following Silver models have been created:

silver_orders
silver_customers
silver_products
silver_sellers
silver_payments
silver_order_items
5. Silver Layer Flow
BigQuery Bronze Tables
        ↓
dbt Silver Models
        ↓
BigQuery Silver Tables
        ↓
dbt Tests
        ↓
Gold Layer Preparation
6. Source Tables

Silver models read from:

ecom_bronze.bronze_orders
ecom_bronze.bronze_customers
ecom_bronze.bronze_products
ecom_bronze.bronze_sellers
ecom_bronze.bronze_payments
ecom_bronze.bronze_order_items

These sources are defined in:

models/silver/sources.yml
7. Silver Models and Grain
Silver Model	Grain
silver_orders	One row per order_id
silver_customers	One row per customer_id
silver_products	One row per product_id
silver_sellers	One row per seller_id
silver_payments	One row per order_id + payment_sequential
silver_order_items	One row per order_id + order_item_id
8. Why Grain Matters

Grain defines what one row represents in a table.

Without a clear grain:

Duplicate records can enter the model
Gold facts can double count revenue
Dashboard metrics can become incorrect
Relationship tests become confusing
Business users lose trust in reports

For this reason, grain was defined before building each Silver model.

9. dbt Materialization

Current Silver models are materialized as:

table

This means dbt creates physical BigQuery tables in the ecom_silver dataset.

This is suitable for the current project because:

Olist dataset size is manageable
Tables are easy to inspect in BigQuery
Performance is better than repeatedly querying views
It keeps the project simple for v1

Future improvement:

Convert selected models to incremental materialization after Gold layer is stable.
10. Silver Transformation Rules
silver_orders

Responsibilities:

Cast order_id and customer_id to string
Standardize order_status
Cast order date columns to timestamp
Remove rows with null or empty order_id
Deduplicate by order_id
Keep latest record using ingestion_timestamp
Preserve ingestion metadata

Tests:

order_id not null
order_id unique
customer_id not null
order_status not null
order_status accepted values
ingestion_timestamp not null
silver_customers

Responsibilities:

Cast customer identifiers to string
Standardize city and state values
Keep zip code as string
Remove rows with null or empty customer_id
Deduplicate by customer_id
Preserve ingestion metadata

Tests:

customer_id not null
customer_id unique
customer_unique_id not null
customer_state not null
ingestion_timestamp not null
silver_products
Responsibilities:

Cast product_id to string
Standardize product category name
Replace missing category with unknown
Rename misspelled Olist columns:
product_name_lenght to product_name_length
product_description_lenght to product_description_length
Cast product measurements to numeric
Deduplicate by product_id
Preserve ingestion metadata

Tests:

product_id not null
product_id unique
product_category_name not null
Product numeric fields non-negative
ingestion_timestamp not null
silver_sellers

Responsibilities:

Cast seller_id to string
Standardize seller city and state
Keep seller zip code as string
Remove rows with null or empty seller_id
Deduplicate by seller_id
Preserve ingestion metadata

Tests:

seller_id not null
seller_id unique
seller_city not null
seller_state not null
ingestion_timestamp not null
silver_payments

Responsibilities:

Cast order_id to string
Cast payment_sequential to integer
Standardize payment_type
Cast payment_installments to integer
Cast payment_value to numeric
Remove rows with missing order/payment sequence
Deduplicate by order_id + payment_sequential
Preserve ingestion metadata

Tests:

order_id not null
payment_sequential not null
payment_type not null
payment_type accepted values
payment_installments non-negative
payment_value not null
payment_value non-negative
Relationship to silver_orders.order_id
ingestion_timestamp not null
silver_order_items

Responsibilities:

Cast order_id to string
Cast order_item_id to integer
Cast product_id and seller_id to string
Cast shipping_limit_date to timestamp
Cast price and freight_value to numeric
Remove rows with missing key fields
Deduplicate by order_id + order_item_id
Preserve ingestion metadata

Tests:

order_id not null
order_item_id not null
product_id not null
seller_id not null
price not null
price non-negative
freight_value not null
freight_value non-negative
Relationship to silver_orders.order_id
Relationship to silver_products.product_id
Relationship to silver_sellers.seller_id
ingestion_timestamp not null
11. dbt Tests Implemented

The Silver layer includes the following test types:

not_null
unique
accepted_values
relationships
custom non_negative test

Total tests executed:

45 dbt tests

Final result:

PASS = 45
WARN = 0
ERROR = 0
SKIP = 0
12. Final dbt Execution Result

Final Silver model build:

dbt run --select silver

Result:

PASS = 6
WARN = 0
ERROR = 0
TOTAL = 6

Final Silver test execution:

dbt test --select silver

Result:

PASS = 45
WARN = 0
ERROR = 0
TOTAL = 45
13. Issue Found During Silver Testing

During testing, this command produced an error:

dbt test --select silver_sellers

Error summary:

silver_order_items table was not found

Root cause:

The silver_sellers test selection also triggered a relationship test from silver_order_items.seller_id to silver_sellers.seller_id.

At that time, silver_order_items had not been created yet.

Resolution:

The dependent model silver_order_items was created, and then the full Silver layer was run and tested again.

Final result:

dbt run --select silver  → passed
dbt test --select silver → passed

This was not a data quality failure. It was a build order and dependency testing issue.

14. Current Silver Layer Status

Current status:

Silver layer completed for v1.
All 6 Silver models created.
All 45 dbt tests passed.
Silver is ready for Gold layer planning.
15. Known Limitations

The current Silver layer is strong for v1, but it has some limitations:

No staging layer yet
Models are materialized as full tables, not incremental
Composite uniqueness tests should be strengthened
Source freshness is not configured yet
dbt run and dbt test are separate; dbt build should be used before final sign-off
No automated Composer orchestration yet
No Gold facts/dimensions yet
16. Recommended Improvements Before Production

Future improvements:

Add staging models between Bronze and Silver
Add dbt build --select silver as final validation command
Add composite uniqueness tests for:
silver_order_items: order_id + order_item_id
silver_payments: order_id + payment_sequential
Add source freshness checks
Convert large models to incremental materialization
Add dbt documentation generation
Integrate dbt run/test into Airflow/Cloud Composer
Add monitoring alerts for dbt failures
17. Silver Exit Criteria

The Silver layer is considered complete when:

All Silver models are created
All dbt tests pass
Key business entities are deduplicated
Data types are standardized
Relationship tests pass
Row counts are verified
Silver documentation is updated
Code is committed to GitHub

Current status:

Silver exit criteria completed for v1, except optional improvements such as composite uniqueness tests and dbt build final validation.
18. Next Phase

The next phase is the Gold layer.

Gold layer will create:

Dimension tables
Fact tables
Business marts
Dashboard-ready models

Recommended Gold build order:

1. dim_date
2. dim_customer
3. dim_product
4. dim_seller
5. fact_orders
6. fact_order_items
7. fact_payments
8. mart_sales_performance
9. mart_customer_rfm
10. mart_product_performance

Do not start dashboards or AI until the Gold layer is stable and tested.