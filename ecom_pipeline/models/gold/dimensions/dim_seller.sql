{{ config(
    materialized='table',
    cluster_by=['seller_state']
) }}

select
    seller_id as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state,

    source_system,
    load_date,
    ingestion_timestamp

from {{ ref('silver_sellers') }}