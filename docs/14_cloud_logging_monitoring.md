# Cloud Logging and Monitoring Documentation

## E-Commerce Data Engineering Platform on GCP

**Project ID:** `ecom-intelligence-pipeline-001`  
**Cloud Run service:** `ecom-ingestion-service`  
**Region:** `us-central1`  
**Environment:** `dev`  
**Document version:** 1.0  
**Prepared:** 12 June 2026

---

## 1. Document Purpose

This document describes the Cloud Logging, Cloud Monitoring, alerting, uptime-check, and operational-dashboard implementation for the E-Commerce Data Engineering Platform on Google Cloud Platform.

It covers:

- the business and technical purpose of observability;
- the architecture before and after monitoring;
- structured application logging added to the Cloud Run ingestion service;
- monitored events, severity levels, and correlation fields;
- notification channels and alert policies;
- log-based metrics and the Cloud Monitoring dashboard;
- the end-to-end test strategy;
- operational incident investigation procedures;
- known limitations and future production improvements.

This document reflects the implemented v1 batch pipeline. It does not claim that Cloud Composer, Dataflow, clickstream processing, or real-time analytics are already implemented.

---

## 2. Current Pipeline Architecture

```text
UI upload
  -> GCS tmp zone
  -> Cloud Run ingestion and validation
  -> GCS raw or rejected zone
  -> BigQuery Bronze tables and audit tables
  -> dbt Silver models and tests
  -> dbt Gold facts, dimensions, and marts
  -> Looker Studio dashboards
```

The observability layer is cross-cutting and does not replace the data flow:

```text
Cloud Run
  |-- request and application logs -> Cloud Logging
  |-- service metrics -> Cloud Monitoring
  |-- unexpected failures -> alert policies -> email
  |-- /health endpoint -> uptime check -> availability alert
```

---

## 3. Why Logging and Monitoring Are Required

A working pipeline is not production-ready unless engineers can detect failures, investigate root causes, measure service health, and notify the responsible person without manually checking every service.

### Cloud Logging answers

- What happened?
- Which batch, run, table, and source file were involved?
- Which stage failed?
- What exception or validation error occurred?
- How long did the pipeline run?

### Cloud Monitoring answers

- Is the service available?
- How many requests are being processed?
- Are HTTP 5xx errors occurring?
- Is latency increasing?
- How many pipeline runs succeeded?
- How many files were rejected or detected as duplicates?

### BigQuery audit tables remain the durable audit source

- `ecom_audit.file_upload_log`
- `ecom_audit.pipeline_run_log`
- `ecom_audit.data_quality_log`
- `ecom_audit.rejected_records`

Cloud Logging provides technical event detail. Cloud Monitoring provides metrics, dashboards, uptime checks, and alerts. The BigQuery audit tables provide durable process history. These components complement each other.

---

## 4. Implemented Observability Outcomes

The completed monitoring phase provides:

1. Cloud Run request and container logs in Cloud Logging.
2. Structured JSON application events searchable through `jsonPayload`.
3. Correlation by `run_id`, `batch_id`, table, file, and environment.
4. A notification channel for operational email alerts.
5. A log-based alert for unexpected `pipeline_failed` events.
6. A metric-based alert for Cloud Run HTTP 5xx responses.
7. A public uptime check for the `/health` endpoint.
8. An availability alert for uptime-check failures.
9. Log-based counter metrics for successful pipelines, rejected files, and duplicate files.
10. A Cloud Monitoring dashboard for request count, error count, latency, instances, pipeline events, and uptime.
11. Controlled tests covering healthy requests, duplicates, invalid files, synthetic failure alerts, and uptime-check failure behavior.

---

## 5. Structured Logging Design

### 5.1 Selected implementation approach

The Cloud Run service writes one-line JSON objects to standard output or standard error. Cloud Run automatically collects these streams and Cloud Logging parses valid JSON into `jsonPayload`.

This approach was selected because it:

- requires no additional logging client dependency;
- uses Cloud Run's native log collection;
- creates searchable structured fields;
- is simple and appropriate for the current v1 service.

An alternative is the `google-cloud-logging` Python client. That is useful when explicit API-based logging or advanced resource configuration is required, but it is unnecessary for this service at the current scale.

### 5.2 Core helper

```python
import sys
import time
from typing import Any


def emit_log(
    severity: str,
    event: str,
    message: str,
    **context: Any,
) -> None:
    normalized_severity = severity.upper()

    log_entry = {
        "severity": normalized_severity,
        "event": event,
        "message": message,
        "service": "ecom-ingestion-service",
        "environment": os.getenv("ENVIRONMENT", "dev"),
        "timestamp": utc_now().isoformat(),
        **context,
    }

    stream = (
        sys.stderr
        if normalized_severity in {"ERROR", "CRITICAL"}
        else sys.stdout
    )

    print(
        json.dumps(log_entry, default=str),
        file=stream,
        flush=True,
    )
```

### 5.3 Required context fields

| Field | Purpose |
|---|---|
| `event` | Stable machine-readable event name |
| `severity` | Operational importance |
| `message` | Human-readable explanation |
| `service` | Producing service |
| `environment` | Separates dev/test/prod behavior |
| `timestamp` | Event time in UTC |
| `run_id` | Correlates all events from one execution |
| `batch_id` | Correlates the source file batch |
| `table_name` | Target business entity |
| `source_file_name` | Original file being processed |
| `row_count` | Number of rows processed or loaded |
| `duration_ms` | End-to-end processing duration |
| `error_type` | Exception class for technical failures |
| `error_message` | Root-cause detail |

### 5.4 Event catalog

| Event | Severity | Meaning | Alert behavior |
|---|---|---|---|
| `pipeline_started` | INFO | Processing began | No alert |
| `schema_validation_passed` | INFO | Required CSV schema passed | No alert |
| `duplicate_file_detected` | WARNING | File hash already loaded; Bronze load skipped | Dashboard metric only |
| `bronze_load_completed` | INFO | Rows loaded to BigQuery Bronze | No alert |
| `pipeline_completed` | INFO | Pipeline completed successfully | Success metric |
| `file_validation_failed` | WARNING | Input failed an expected data-quality rule | No urgent infrastructure alert |
| `file_rejected` | WARNING | Invalid file copied to the rejected zone | Rejected-file metric |
| `pipeline_failed` | ERROR | Unexpected service, dependency, code, or processing failure | Email alert |

### 5.5 HTTP status classification

Expected input or validation failures return HTTP 400. Unexpected service or pipeline failures return HTTP 500.

```text
400 = client/source-data problem
500 = unexpected server or pipeline problem
```

This distinction ensures that the 5xx alert represents real technical incidents rather than ordinary invalid-file handling.

---

## 6. Logging Queries and CLI Commands

### 6.1 Set the active project

```bash
export PROJECT_ID=ecom-intelligence-pipeline-001
export REGION=us-central1
export SERVICE_NAME=ecom-ingestion-service
gcloud config set project "$PROJECT_ID"
```

### 6.2 Enable APIs

```bash
gcloud services enable   logging.googleapis.com   monitoring.googleapis.com
```

### 6.3 Read Cloud Run logs with CLI

```bash
gcloud run services logs read "$SERVICE_NAME"   --region "$REGION"   --limit=50
```

### 6.4 Logs Explorer: all service logs

```text
resource.type="cloud_run_revision"
resource.labels.service_name="ecom-ingestion-service"
```

### 6.5 Logs Explorer: unexpected pipeline failures

```text
resource.type="cloud_run_revision"
resource.labels.service_name="ecom-ingestion-service"
jsonPayload.event="pipeline_failed"
```

### 6.6 Logs Explorer: trace one batch

```text
resource.type="cloud_run_revision"
resource.labels.service_name="ecom-ingestion-service"
jsonPayload.batch_id="PASTE_BATCH_ID"
```

### 6.7 Logs Explorer: HTTP 5xx

```text
resource.type="cloud_run_revision"
resource.labels.service_name="ecom-ingestion-service"
httpRequest.status>=500
```

---

## 7. Notification Channel and Alert Policies

### 7.1 Notification channel

A monitored email notification channel was configured through:

```text
Monitoring -> Alerting -> Notification channels -> Email
```

Display name:

```text
E-Commerce Pipeline Alerts
```

### 7.2 Unexpected pipeline-failure alert

Source: Cloud Logging event

Filter:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="ecom-ingestion-service"
jsonPayload.environment="dev"
jsonPayload.event="pipeline_failed"
```

Purpose: notify the engineer when the application reports an unexpected pipeline failure.

The alert documentation instructs the engineer to inspect:

- `run_id`
- `batch_id`
- `table_name`
- `source_file_name`
- `error_type`
- `error_message`

### 7.3 Cloud Run HTTP 5xx alert

Resource: Cloud Run Revision  
Metric: Request count  
Filters:

```text
service_name = ecom-ingestion-service
response_code_class = 5xx
```

Current low-traffic policy:

```text
Threshold: above 0
Window: 5 minutes
```

This approach is selected because percentage-based alerts are misleading when request volume is very small. With higher production traffic, a 5xx error-rate threshold would be more appropriate.

### 7.4 Availability alert

A public uptime check monitors:

```text
HTTPS $SERVICE_URL/health
```

Frequency:

```text
5 minutes
```

The related alert notifies the same email channel when the endpoint becomes unavailable.

---

## 8. Log-Based Metrics

The following counter metrics were created:

| Metric | Event filter | Purpose |
|---|---|---|
| `ecom_pipeline_success_count` | `jsonPayload.event="pipeline_completed"` | Counts successful pipeline runs |
| `ecom_rejected_file_count` | `jsonPayload.event="file_rejected"` | Counts rejected files |
| `ecom_duplicate_file_count` | `jsonPayload.event="duplicate_file_detected"` | Counts duplicate upload attempts |

High-cardinality values such as `batch_id` and `run_id` are not used as metric labels. Adding them as labels would create excessive time-series cardinality, increase cost, and reduce dashboard usefulness.

---

## 9. Cloud Monitoring Dashboard

Dashboard name:

```text
E-Commerce Pipeline Operations
```

Implemented widgets:

| Widget | Source | Purpose |
|---|---|---|
| Cloud Run Request Count | Cloud Run metric | Shows service usage |
| Cloud Run 5xx Errors | Cloud Run request metric filtered to 5xx | Detects server errors |
| Cloud Run p95 Latency | Cloud Run latency metric | Tracks slow requests |
| Active Cloud Run Instances | Cloud Run instance metric | Shows scaling behavior |
| Successful Pipeline Runs | Log-based metric | Tracks completed ingestions |
| Rejected Files | Log-based metric | Tracks invalid source files |
| Duplicate File Attempts | Log-based metric | Tracks idempotency events |
| Service Availability | Uptime-check metric | Shows `/health` availability |

The Cloud Monitoring dashboard is an operational dashboard. It is separate from the Looker Studio business dashboard and from the Gold `mart_pipeline_quality` table.

---

## 10. Testing and Verification

### 10.1 Health test

```bash
curl -i "$SERVICE_URL/health"
```

Expected:

```text
HTTP 200
Request visible in Cloud Logging
Uptime check remains Passing
```

### 10.2 Duplicate-file test

Expected behavior:

```text
API result: skipped / duplicate
Structured event: duplicate_file_detected
Severity: WARNING
Bronze rows for new batch: 0
file_upload_log status: DUPLICATE
No urgent email alert
```

### 10.3 Invalid-schema test

Expected behavior:

```text
HTTP status: 400
Events: pipeline_started, file_validation_failed, file_rejected
Invalid file copied to GCS rejected zone
No Bronze rows for the batch
rejected_records populated
Rejected-file metric increases
No unexpected-pipeline email alert
```

### 10.4 Synthetic pipeline-failure alert test

A clearly marked synthetic `pipeline_failed` log was written to verify the log-based alert without breaking the live service.

Expected:

```text
Log visible in Logs Explorer
Incident opened in Cloud Monitoring
Email notification received
Synthetic event distinguishable from a real incident
```

### 10.5 Uptime-alert test

A temporary uptime check used an invalid path, such as `/health-does-not-exist`, to generate a controlled failure.

Expected:

```text
Temporary uptime check fails
Availability incident opens
Email notification received
Temporary check and policy deleted after testing
Real /health check remains unchanged
```

### 10.6 Audit correlation

For any batch, Cloud Logging and BigQuery audit tables can be compared by `batch_id` and `run_id`.

```sql
SELECT
  batch_id,
  step_name,
  status,
  error_message,
  start_time
FROM `ecom-intelligence-pipeline-001.ecom_audit.pipeline_run_log`
WHERE batch_id = 'PASTE_BATCH_ID'
ORDER BY start_time;
```

---

## 11. Operational Incident Runbook

When an alert email is received:

1. Open Cloud Monitoring and review the incident name and condition.
2. Open Logs Explorer from the incident or use the service filter.
3. Extract `run_id`, `batch_id`, `table_name`, and `source_file_name`.
4. Search all structured events for the same `batch_id`.
5. Query `ecom_audit.pipeline_run_log` and `file_upload_log`.
6. Inspect `data_quality_log` for validation failures.
7. Inspect `rejected_records` and the referenced GCS URI when a file was quarantined.
8. Classify the failure:
   - source-data or schema issue;
   - missing file/path issue;
   - BigQuery or GCS dependency issue;
   - permission/IAM issue;
   - application/code issue;
   - quota or capacity issue.
9. Apply the corrective action.
10. Re-run only when idempotency and file-hash behavior have been verified.
11. Confirm the pipeline completes and audit status is correct.
12. Record the root cause and prevention action in project documentation.

---

## 12. Security and Privacy Requirements

Logs must not contain:

- passwords;
- OAuth tokens;
- authorization headers;
- service-account private keys;
- complete CSV contents;
- unnecessary customer information;
- full payment or personal records.

Only technical identifiers and operational context should be logged.

Current security limitation: the Cloud Run service remains publicly accessible for development/demo purposes. Production should add authenticated access, signed upload URLs or a protected UI, rate limiting, and stricter IAM.

---

## 13. Cost and Reliability Considerations

### Cost controls

- Avoid unnecessary DEBUG logs in normal operation.
- Do not create a custom metric for every event.
- Avoid high-cardinality metric labels.
- Review log retention and exclusions before production scale.
- Keep billing-budget alerts enabled.
- Review Cloud Monitoring and Logging usage when traffic increases.

### Alert quality

Alerts should be actionable. Expected data-quality conditions such as duplicates and invalid input files are not treated as urgent system incidents. Unexpected application failures, HTTP 5xx responses, and service unavailability are alert-worthy.

This separation prevents alert fatigue.

---

## 14. Current Limitations

The observability phase is complete for v1, but the complete platform still has the following production gaps:

1. dbt Silver and Gold builds are not yet orchestrated automatically.
2. Cloud Composer/Airflow has not yet been implemented.
3. The Cloud Run upload UI is unauthenticated.
4. The ingestion request is synchronous rather than asynchronous.
5. Retry and exponential-backoff logic is limited or absent.
6. Development, test, and production resources are not fully separated.
7. Schema contracts are primarily hardcoded rather than externally versioned.
8. Data freshness SLOs and automated freshness alerts are not yet defined.
9. Infrastructure and alert policies are not yet fully managed as code.
10. CI/CD deployment is not yet implemented.

---

## 15. Recommended Next Improvements

### Immediate next phase

Implement orchestration after confirming billing alerts:

```text
Cloud Composer / Airflow
  -> trigger or verify ingestion
  -> wait for Bronze readiness
  -> run dbt build for Silver
  -> run dbt build for Gold
  -> execute tests
  -> notify on success or failure
```

### Production improvements

- Use Cloud Run Jobs or dbt Cloud/Composer for non-local dbt execution.
- Add retries with bounded exponential backoff.
- Add dev/test/prod isolation.
- Add schema-contract files and schema-version metadata.
- Add data-freshness metrics and SLOs.
- Add Composer task-failure callbacks to Cloud Logging and Monitoring.
- Manage dashboards, alerts, and uptime checks with Terraform.
- Add CI/CD for Cloud Run and dbt code.
- Secure the upload service.
- Consider Cloud Trace or Error Reporting only when operational complexity justifies them.

Clickstream, Pub/Sub, and Dataflow remain v2 scope and are not part of this completed monitoring phase.

---

## 16. Production Readiness Assessment

| Area | Status after this phase |
|---|---|
| Ingestion functionality | Implemented |
| Audit history | Implemented |
| Structured application logs | Implemented |
| Cloud service metrics | Implemented |
| Email alerting | Implemented |
| Uptime monitoring | Implemented |
| Operations dashboard | Implemented |
| Controlled observability testing | Completed |
| Automated dbt orchestration | Pending |
| Authentication hardening | Pending |
| Retry framework | Pending |
| Environment isolation | Pending |
| CI/CD and infrastructure as code | Pending |

The platform is now functional and observable. It is not yet fully automated or fully production-hardened.

---

## 17. Interview Explanation

A concise interview explanation:

> I added an observability layer around the Cloud Run ingestion service without changing the core data flow. The application emits structured JSON events containing run and batch identifiers, processing stage, row count, duration, and error context. Cloud Logging stores the detailed events, while Cloud Monitoring tracks service metrics, uptime, log-based counters, and alert conditions. Expected data-quality failures are warnings and are quarantined, while unexpected pipeline failures generate error events and email alerts. BigQuery audit tables remain the durable process history, so an incident can be traced from an alert to logs, audit records, and the original GCS file.

---

## 18. Completion Checklist

- [x] Logging and Monitoring APIs enabled
- [x] Existing Cloud Run request logs verified
- [x] Structured JSON logging added
- [x] Environment field added to logs
- [x] Expected validation failures separated from unexpected failures
- [x] HTTP 400 and 500 behavior separated
- [x] Structured events tested
- [x] Email notification channel configured
- [x] Unexpected pipeline-failure alert configured
- [x] Cloud Run 5xx alert configured
- [x] `/health` uptime check configured
- [x] Availability alert configured
- [x] Success, rejected-file, and duplicate-file metrics created
- [x] Cloud Monitoring operations dashboard created
- [x] Duplicate and invalid-file tests completed
- [x] Synthetic alert test completed
- [x] Temporary uptime failure test completed
- [x] BigQuery audit correlation verified
- [x] Code and documentation version-controlled

---

## 19. Repository Documentation Location

Recommended repository path:

```text
docs/14_cloud_logging_monitoring.md
```

Main implementation file:

```text
ingestion/app/main.py
```

Environment variable added:

```text
ENVIRONMENT=dev
```
