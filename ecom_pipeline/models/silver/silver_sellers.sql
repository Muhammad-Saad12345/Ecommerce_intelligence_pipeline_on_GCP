{{ config(
    materialized='table'
) }}

with source as (

    select *
    from {{ source('bronze', 'bronze_sellers') }}

),

cleaned as (

    select
        cast(seller_id as string) as seller_id,
        cast(seller_zip_code_prefix as string) as seller_zip_code_prefix,
        lower(trim(cast(seller_city as string))) as seller_city,
        upper(trim(cast(seller_state as string))) as seller_state,

        cast(batch_id as string) as batch_id,
        cast(run_id as string) as run_id,
        cast(source_system as string) as source_system,
        cast(source_file_name as string) as source_file_name,
        cast(gcs_uri as string) as gcs_uri,
        cast(file_hash as string) as file_hash,
        safe_cast(load_date as date) as load_date,
        safe_cast(ingestion_timestamp as timestamp) as ingestion_timestamp

    from source

    where seller_id is not null
      and trim(cast(seller_id as string)) != ''

),

deduplicated as (

    select *
    from cleaned
    qualify row_number() over (
        partition by seller_id
        order by ingestion_timestamp desc
    ) = 1

)

select *
from deduplicated