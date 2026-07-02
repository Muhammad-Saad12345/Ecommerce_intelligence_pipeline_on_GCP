{{ config(
    materialized='table'
) }}

with source as (

    select *
    from {{ source('bronze', 'bronze_order_items') }}

),

cleaned as (

    select
        cast(order_id as string) as order_id,
        safe_cast(order_item_id as int64) as order_item_id,
        cast(product_id as string) as product_id,
        cast(seller_id as string) as seller_id,
        safe_cast(shipping_limit_date as timestamp) as shipping_limit_date,
        safe_cast(price as numeric) as price,
        safe_cast(freight_value as numeric) as freight_value,

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
      and order_item_id is not null
      and product_id is not null
      and trim(cast(product_id as string)) != ''
      and seller_id is not null
      and trim(cast(seller_id as string)) != ''

),

deduplicated as (

    select *
    from cleaned
    qualify row_number() over (
        partition by order_id, order_item_id
        order by ingestion_timestamp desc
    ) = 1

)

select *
from deduplicated