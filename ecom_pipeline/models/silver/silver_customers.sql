{{ config(
    materialized='table'
) }}

with source as (

    select *
    from {{ source('bronze', 'bronze_customers') }}

),

cleaned as (

    select
        cast(customer_id as string) as customer_id,
        cast(customer_unique_id as string) as customer_unique_id,
        cast(customer_zip_code_prefix as string) as customer_zip_code_prefix,
        lower(trim(cast(customer_city as string))) as customer_city,
        upper(trim(cast(customer_state as string))) as customer_state,

        cast(batch_id as string) as batch_id,
        cast(run_id as string) as run_id,
        cast(source_system as string) as source_system,
        cast(source_file_name as string) as source_file_name,
        cast(gcs_uri as string) as gcs_uri,
        cast(file_hash as string) as file_hash,
        safe_cast(load_date as date) as load_date,
        safe_cast(ingestion_timestamp as timestamp) as ingestion_timestamp

    from source

    where customer_id is not null
      and trim(cast(customer_id as string)) != ''

),

deduplicated as (

    select *
    from cleaned
    qualify row_number() over (
        partition by customer_id
        order by ingestion_timestamp desc
    ) = 1

)

select *
from deduplicated