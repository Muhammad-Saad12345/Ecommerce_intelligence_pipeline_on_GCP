Current Limitations
Purpose

This document lists known limitations of the current pipeline.

Being clear about limitations is important for production-level thinking.

1. Cloud Run UI Is Public

Current deployment uses:

--allow-unauthenticated

This is acceptable for development and portfolio demo.

Production should use:

authentication
IAM-based access
Identity-Aware Proxy
signed URLs
2. UI Processing Is Synchronous

Current UI flow:

Upload file
Wait for Cloud Run processing
Return result

This is fine for small/medium CSV files.

Production should use asynchronous processing:

UI upload
→ GCS tmp/
→ Eventarc or Cloud Tasks
→ background processing
→ status page
3. Schema Rules Are Hardcoded

Current schema validation rules are inside Python code.

Production improvement:

Move schema rules to JSON/YAML files.
Version schema definitions.
Support schema evolution.
4. No Row-Level Rejection Yet

Current rejected_records table mostly handles file-level rejection.

Future improvement:

Reject invalid rows separately
Store row-level error reason
Load valid rows while quarantining bad rows
5. Bronze Tables May Contain Test Batches

During development, some test batches were inserted.

Before Silver, test/duplicate batches should be cleaned or filtered.

6. No dbt Silver Layer Yet

Current pipeline ends at Bronze.

Silver layer still needs:

type casting
deduplication
clean naming
null handling
accepted values
relationship tests
7. No Gold Layer Yet

Gold layer still needs:

dim_customer
dim_product
dim_date
fact_orders
fact_order_items
fact_payments
business marts
8. No Orchestration Yet

Current pipeline is triggered by:

CLI
UI upload

Airflow/Composer is not added yet.

This is intentional because Composer can be costly.

9. No Monitoring Alerts Yet

Audit tables exist, but automated alerts are not configured yet.

Future alerts:

pipeline_run_log status = FAILED
Cloud Run error rate > threshold
BigQuery job failure
Rejected file count > threshold
10. No Dashboard Yet

Looker Studio dashboards are planned after Gold tables are ready.

11. No AI Layer Yet

AI insights are planned only after Gold marts are stable.

AI should read Gold summaries and write output to:

ecom_gold.ai_daily_insights
12. Inventory Data Not Available in Olist

Olist dataset does not provide full inventory snapshot data.

Options:

skip inventory for v1
create synthetic inventory later
document inventory limitation clearly
Summary

The current pipeline is strong for Bronze ingestion but not yet a full analytics platform.

Next step is dbt Silver.