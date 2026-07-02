{{ config(
    materialized='table'
) }}

with pipeline_runs as (

    select
        date(start_time) as run_date,
        count(*) as pipeline_steps,
        countif(status = 'FAILED') as failed_steps,
        countif(status = 'SUCCESS') as successful_steps
    from {{ source('audit', 'pipeline_run_log') }}
    group by run_date

),

quality_checks as (

    select
        date(created_at) as run_date,
        count(*) as total_quality_checks,
        countif(check_status = 'FAILED') as failed_quality_checks,
        countif(check_status = 'PASS') as passed_quality_checks
    from {{ source('audit', 'data_quality_log') }}
    group by run_date

),

rejected_files as (

    select
        date(created_at) as run_date,
        count(*) as rejected_file_count
    from {{ source('audit', 'rejected_records') }}
    group by run_date

),

file_uploads as (

    select
        date(created_at) as run_date,
        count(*) as total_file_uploads,
        countif(upload_status = 'SUCCESS') as successful_file_uploads,
        countif(upload_status = 'FAILED') as failed_file_uploads,
        countif(upload_status = 'DUPLICATE') as duplicate_file_uploads
    from {{ source('audit', 'file_upload_log') }}
    group by run_date

)

select
    coalesce(
        pr.run_date,
        qc.run_date,
        rf.run_date,
        fu.run_date
    ) as run_date,

    coalesce(fu.total_file_uploads, 0) as total_file_uploads,
    coalesce(fu.successful_file_uploads, 0) as successful_file_uploads,
    coalesce(fu.failed_file_uploads, 0) as failed_file_uploads,
    coalesce(fu.duplicate_file_uploads, 0) as duplicate_file_uploads,

    coalesce(pr.pipeline_steps, 0) as pipeline_steps,
    coalesce(pr.successful_steps, 0) as successful_steps,
    coalesce(pr.failed_steps, 0) as failed_steps,

    coalesce(qc.total_quality_checks, 0) as total_quality_checks,
    coalesce(qc.passed_quality_checks, 0) as passed_quality_checks,
    coalesce(qc.failed_quality_checks, 0) as failed_quality_checks,

    coalesce(rf.rejected_file_count, 0) as rejected_file_count

from pipeline_runs pr
full outer join quality_checks qc
    on pr.run_date = qc.run_date
full outer join rejected_files rf
    on coalesce(pr.run_date, qc.run_date) = rf.run_date
full outer join file_uploads fu
    on coalesce(pr.run_date, qc.run_date, rf.run_date) = fu.run_date