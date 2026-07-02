{{ config(
    materialized='table'
) }}

with source as (

    select *
    from {{ source('bronze', 'bronze_products') }}

),

cleaned as (

    select
        cast(product_id as string) as product_id,

        coalesce(
            nullif(lower(trim(cast(product_category_name as string))), ''),
            'unknown'
        ) as product_category_name,

        safe_cast(product_name_lenght as int64) as product_name_length,
        safe_cast(product_description_lenght as int64) as product_description_length,
        safe_cast(product_photos_qty as int64) as product_photos_qty,
        safe_cast(product_weight_g as numeric) as product_weight_g,
        safe_cast(product_length_cm as numeric) as product_length_cm,
        safe_cast(product_height_cm as numeric) as product_height_cm,
        safe_cast(product_width_cm as numeric) as product_width_cm,

        cast(batch_id as string) as batch_id,
        cast(run_id as string) as run_id,
        cast(source_system as string) as source_system,
        cast(source_file_name as string) as source_file_name,
        cast(gcs_uri as string) as gcs_uri,
        cast(file_hash as string) as file_hash,
        safe_cast(load_date as date) as load_date,
        safe_cast(ingestion_timestamp as timestamp) as ingestion_timestamp

    from source

    where product_id is not null
      and trim(cast(product_id as string)) != ''

),

deduplicated as (

    select *
    from cleaned
    qualify row_number() over (
        partition by product_id
        order by ingestion_timestamp desc
    ) = 1

)

select *
from deduplicated