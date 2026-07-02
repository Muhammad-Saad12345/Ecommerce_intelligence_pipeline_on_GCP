Silver dbt Runbook
1. Purpose

This runbook explains how to run, test, validate, and troubleshoot the Silver dbt layer.

It is used by developers and data engineers to operate the dbt transformation layer safely.

2. Project Location

Local project path example:

C:\Users\KOS Knowledge\Desktop\ecommerce-intelligence-pipeline-main\ecom_pipeline

dbt project folder:

ecom_pipeline
3. dbt Version

Current dbt version used:

dbt = 1.11.11
bigquery adapter = 1.11.1
4. Target Warehouse

dbt connects to:

Google BigQuery

Project:

ecom-intelligence-pipeline-001

Silver dataset:

ecom_silver

Bronze source dataset:

ecom_bronze
5. Authentication

Local dbt communicates with BigQuery using the dbt BigQuery adapter.

Typical local authentication method:

OAuth / Application Default Credentials

The dbt command runs locally, but the SQL executes inside BigQuery.

Flow:

Local dbt command
      ↓
profiles.yml
      ↓
Google authentication
      ↓
BigQuery SQL job
      ↓
BigQuery creates/updates ecom_silver tables
6. Important dbt Files
dbt_project.yml
models/silver/sources.yml
models/silver/schema.yml
models/silver/silver_orders.sql
models/silver/silver_customers.sql
models/silver/silver_products.sql
models/silver/silver_sellers.sql
models/silver/silver_payments.sql
models/silver/silver_order_items.sql
tests/generic/non_negative.sql
7. Run Individual Models
silver_orders
dbt run --select silver_orders
dbt test --select silver_orders
silver_customers
dbt run --select silver_customers
dbt test --select silver_customers
silver_products
dbt run --select silver_products
dbt test --select silver_products
silver_sellers
dbt run --select silver_sellers
dbt test --select silver_sellers
silver_payments
dbt run --select silver_payments
dbt test --select silver_payments
silver_order_items
dbt run --select silver_order_items
dbt test --select silver_order_items
8. Recommended Build Order

Use this order when building manually:

1. silver_orders
2. silver_customers
3. silver_products
4. silver_sellers
5. silver_payments
6. silver_order_items

Reason:

silver_payments depends on silver_orders
silver_order_items depends on silver_orders, silver_products, and silver_sellers
Relationship tests need referenced models to exist
9. Run All Silver Models
dbt run --select silver

Expected result:

PASS = 6
ERROR = 0
10. Test All Silver Models
dbt test --select silver

Expected result:

PASS = 45
ERROR = 0
11. Recommended Final Validation Command

Before marking Silver complete, run:

dbt build --select silver

Why dbt build is recommended:

It runs selected models and tests together
It respects dbt dependencies
It is closer to production-style execution
It avoids some manual run/test ordering issues
12. Common Error: Dependent Table Not Found

Example error:

Table ecom_silver.silver_order_items was not found

Cause:

A relationship test tried to validate a model before the dependent table existed.

Fix:

Run the dependent model first or run the full Silver layer:

dbt run --select silver
dbt test --select silver

Better:

dbt build --select silver
13. Common Error: Relationship Test Fails

Example:

relationships_silver_order_items_order_id__order_id__ref_silver_orders

Meaning:

Some rows in child table do not have matching parent keys.

Example:

silver_order_items.order_id not found in silver_orders.order_id

Debug query:

SELECT child.order_id
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_order_items` child
LEFT JOIN `ecom-intelligence-pipeline-001.ecom_silver.silver_orders` parent
ON child.order_id = parent.order_id
WHERE parent.order_id IS NULL
LIMIT 100;
14. Common Error: Accepted Values Test Fails

Example:

order_status accepted_values failed

Debug query:

SELECT order_status, COUNT(*) AS row_count
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_orders`
GROUP BY order_status
ORDER BY row_count DESC;

Fix:

Check if the value is valid but missing from accepted values
Or clean/standardize the invalid value
Or document it as rejected/unknown
15. Common Error: Non-Negative Test Fails

Example:

price < 0

Debug query:

SELECT *
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_order_items`
WHERE price < 0
LIMIT 100;

Fix options:

Reject the row
Set value to null
Keep row and document anomaly
Fix transformation logic if casting is wrong
16. BigQuery Row Count Verification

Run after Silver build:

SELECT 'silver_orders' AS table_name, COUNT(*) AS row_count
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_orders`
UNION ALL
SELECT 'silver_customers', COUNT(*)
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_customers`
UNION ALL
SELECT 'silver_products', COUNT(*)
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_products`
UNION ALL
SELECT 'silver_sellers', COUNT(*)
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_sellers`
UNION ALL
SELECT 'silver_payments', COUNT(*)
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_payments`
UNION ALL
SELECT 'silver_order_items', COUNT(*)
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_order_items`;
17. Expected Current Row Counts

Based on latest successful dbt output:

silver_orders       ~99.4k rows
silver_customers    ~99.4k rows
silver_products     ~33.0k rows
silver_sellers      ~3.1k rows
silver_payments     ~103.9k rows
silver_order_items  ~112.7k rows
18. Check Duplicate Business Keys
silver_orders
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT order_id) AS distinct_orders
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_orders`;

Expected:

total_rows = distinct_orders
silver_customers
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT customer_id) AS distinct_customers
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_customers`;

Expected:

total_rows = distinct_customers
silver_products
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT product_id) AS distinct_products
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_products`;

Expected:

total_rows = distinct_products
silver_sellers
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT seller_id) AS distinct_sellers
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_sellers`;

Expected:

total_rows = distinct_sellers
19. Check Composite Keys
silver_order_items
SELECT
  order_id,
  order_item_id,
  COUNT(*) AS row_count
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_order_items`
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1;

Expected:

0 rows
silver_payments
SELECT
  order_id,
  payment_sequential,
  COUNT(*) AS row_count
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_payments`
GROUP BY order_id, payment_sequential
HAVING COUNT(*) > 1;

Expected:

0 rows
20. Check Relationship Integrity
order_items to orders
SELECT COUNT(*) AS missing_orders
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_order_items` oi
LEFT JOIN `ecom-intelligence-pipeline-001.ecom_silver.silver_orders` o
ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

Expected:

0
order_items to products
SELECT COUNT(*) AS missing_products
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_order_items` oi
LEFT JOIN `ecom-intelligence-pipeline-001.ecom_silver.silver_products` p
ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

Expected:

0
order_items to sellers
SELECT COUNT(*) AS missing_sellers
FROM `ecom-intelligence-pipeline-001.ecom_silver.silver_order_items` oi
LEFT JOIN `ecom-intelligence-pipeline-001.ecom_silver.silver_sellers` s
ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL;

Expected:

0
21. GitHub Commit

After final validation:

git status
git add .
git commit -m "Complete silver dbt models, tests, and documentation"
git push origin main
22. Silver Sign-Off Checklist

Before moving to Gold:

dbt run --select silver passes
dbt test --select silver passes
dbt build --select silver passes
Row counts are documented
Composite key checks are completed
Relationship tests pass
Silver documentation is updated
Code is pushed to GitHub