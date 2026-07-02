Next Phase: Silver Layer Plan
Purpose

The Silver layer will clean, standardize, deduplicate, and type-cast Bronze data.

Bronze stores raw validated data. Silver creates clean analytical tables.

Silver Goals
Create dbt project structure
Register Bronze sources
Build Silver models
Apply data cleaning
Cast data types
Remove duplicates
Add dbt tests
Validate row counts
Prepare for Gold modeling
Silver Dataset
ecom_silver
Planned Silver Models
silver_orders
silver_customers
silver_order_items
silver_products
silver_payments
silver_sellers
dbt Folder Structure
dbt/
└── models/
    └── silver/
        ├── sources.yml
        ├── silver_orders.sql
        ├── silver_customers.sql
        ├── silver_order_items.sql
        ├── silver_products.sql
        ├── silver_payments.sql
        ├── silver_sellers.sql
        └── schema.yml
Silver Model Responsibilities
silver_orders

Responsibilities:

cast timestamps
validate order_status
deduplicate by order_id
remove rows with null order_id
standardize timestamp columns

Important columns:

order_id
customer_id
order_status
order_purchase_timestamp
order_approved_at
order_delivered_carrier_date
order_delivered_customer_date
order_estimated_delivery_date
silver_customers

Responsibilities:

deduplicate customer_id
standardize city/state values
cast zip code to string
remove null customer_id
silver_order_items

Responsibilities:

cast price to numeric
cast freight_value to numeric
validate price >= 0
validate freight_value >= 0
deduplicate order_id + order_item_id
silver_products

Responsibilities:

standardize product category
cast product dimensions
handle null category values
rename misspelled Olist columns in Silver

Example:

product_name_lenght → product_name_length
product_description_lenght → product_description_length
silver_payments

Responsibilities:

cast payment_value to numeric
cast payment_installments to integer
validate payment_value >= 0
validate accepted payment_type values
silver_sellers

Responsibilities:

deduplicate seller_id
standardize city/state
cast zip code to string
dbt Tests

Required tests:

not_null
unique
accepted_values
relationships
custom non-negative tests
Example Tests
silver_orders
order_id not_null
order_id unique
customer_id not_null
order_status accepted_values

Accepted order status values:

created
approved
invoiced
processing
shipped
delivered
unavailable
canceled
silver_customers
customer_id not_null
customer_id unique
silver_order_items
order_id not_null
product_id not_null
price >= 0
freight_value >= 0
relationship to silver_orders.order_id
relationship to silver_products.product_id
silver_payments
order_id not_null
payment_value >= 0
payment_type accepted_values
Incremental Logic

Start simple with full-refresh models first.

After Silver logic is stable, add incremental logic to high-volume models such as:

silver_orders
silver_order_items
silver_payments
Silver Verification Checklist

Before moving to Gold:

dbt run --select silver succeeds
dbt test --select silver succeeds
row counts make sense
duplicates are removed
data types are correct
relationships pass
data_quality_log updated or dbt test results documented
Commands
cd dbt

dbt run --select silver
dbt test --select silver
Silver Exit Criteria

Move to Gold only when:

all Silver models build successfully
all dbt tests pass
critical columns are not null
business keys are unique
relationships are valid
row counts are documented
Important Rule

Do not build Gold before Silver is tested.

Gold depends on clean Silver tables.