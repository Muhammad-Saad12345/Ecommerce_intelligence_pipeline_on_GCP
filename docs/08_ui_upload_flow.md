UI Upload Flow Documentation
Purpose

The UI upload feature allows users to upload Olist CSV files from a browser instead of using CLI commands.

The UI is mainly for:

Portfolio demo
Easier file upload
Showing end-to-end pipeline behavior
Demonstrating business-friendly ingestion
UI Endpoint
GET /

This opens the upload page.

Upload Endpoint
POST /upload-and-process

This receives the file and triggers the pipeline.

UI Fields

The UI contains:

Source System
Target Table
CSV File Upload
Upload and Process button
Source System

Current value:

olist

This is read-only in the UI because v1 supports only Olist CSV files.

Target Table Dropdown

Supported options:

orders
customers
order_items
products
payments
sellers

Dropdown is used instead of free text to avoid user mistakes.

Wrong table selection example:

Uploading customers file but selecting orders

This will fail schema validation.

UI Upload Flow
User opens Cloud Run URL
      ↓
User selects target table
      ↓
User chooses CSV file
      ↓
User clicks Upload and Process
      ↓
Cloud Run receives file
      ↓
File is saved to GCS tmp/
      ↓
Cloud Run pipeline runs
      ↓
Result page is displayed
Backend Flow After Upload
GCS tmp/
      ↓
File exists check
      ↓
File not empty check
      ↓
Duplicate file hash check
      ↓
Schema validation
      ↓
Valid file copied to raw/
      ↓
Data loaded to BigQuery Bronze
      ↓
Audit logs inserted
Success Result Page

Shows:

Status
Batch ID
Run ID
Table Name
Row Count
Raw GCS URI
Bronze Table
File Hash
Duplicate Result Page

Shows:

Status = skipped
Reason = duplicate_file

This means the file was already successfully processed before.

Failure Result Page

Shows:

Status = failed
Error message
Rejected GCS URI

Example failure:

Missing required columns
Correct Upload Rule

Files must go to:

tmp/

before validation.

Files should not be uploaded directly to:

raw/

Reason:

raw/ should contain only validated files.
UI Test Cases
Test 1: Duplicate File

Upload a file that was already processed.

Expected:

status = skipped
reason = duplicate_file
Test 2: Bad File

Upload a CSV with wrong columns.

Expected:

status = failed
error = Missing required columns
file copied to rejected/
rejected_records populated
Test 3: Valid New File

Upload a valid CSV with new content.

Expected:

status = success
row_count > 0
file copied to raw/
Bronze table loaded
audit logs populated
Production Improvements

Current UI is simple and synchronous.

Future improvements:

authentication
upload progress
status page
async processing
upload history
role-based access
signed URLs
file preview before upload
Current UI Status

The UI is suitable for portfolio v1 and internal demo.

It is not production-secure until authentication is added.