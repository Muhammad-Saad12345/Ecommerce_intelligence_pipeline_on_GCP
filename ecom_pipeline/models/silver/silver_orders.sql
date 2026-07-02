{{ config(
    materialized='table'
) }}

with source as (

    select *
    from {{ source('bronze', 'bronze_orders') }}

),

cleaned as (

    select
        cast(order_id as string) as order_id,
        cast(customer_id as string) as customer_id,
        lower(trim(cast(order_status as string))) as order_status,

        safe_cast(order_purchase_timestamp as timestamp) as order_purchase_timestamp,
        safe_cast(order_approved_at as timestamp) as order_approved_at,
        safe_cast(order_delivered_carrier_date as timestamp) as order_delivered_carrier_date,
        safe_cast(order_delivered_customer_date as timestamp) as order_delivered_customer_date,
        safe_cast(order_estimated_delivery_date as timestamp) as order_estimated_delivery_date,

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

),

deduplicated as (

    select *
    from cleaned
    qualify row_number() over (
        partition by order_id
        order by ingestion_timestamp desc
    ) = 1

)

select *
from deduplicated