{{ config(
    materialized='table'
) }}

with source as (

    select *
    from {{ source('bronze', 'bronze_payments') }}

),

cleaned as (

    select
        cast(order_id as string) as order_id,
        safe_cast(payment_sequential as int64) as payment_sequential,
        lower(trim(cast(payment_type as string))) as payment_type,
        safe_cast(payment_installments as int64) as payment_installments,
        safe_cast(payment_value as numeric) as payment_value,

        cast(batch_id as string) as batch_id,
        cast(run_id as string) as run_id,
        cast(source_system as string) as source_system,
        cast(source_file_name as string) as source_file_name,
        cast(gcs_uri as string) as gcs_uri,
        cast(file_hash as string) as file_hash,
        safe_cast(load_date as date) as load_date,
        safe_cast(ingestion_timestamp as timestamp) as ingestion_timestamp

    from source

    where order_id is not null
      and trim(cast(order_id as string)) != ''
      and payment_sequential is not null

),

deduplicated as (

    select *
    from cleaned
    qualify row_number() over (
        partition by order_id, payment_sequential
        order by ingestion_timestamp desc
    ) = 1

)

select *
from deduplicated