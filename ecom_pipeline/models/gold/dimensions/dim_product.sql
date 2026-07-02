{{ config(
    materialized='table',
    cluster_by=['product_category_name']
) }}

select
    product_id as product_key,
    product_id,
    product_category_name,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,

    source_system,
    load_date,
    ingestion_timestamp

from {{ ref('silver_products') }}