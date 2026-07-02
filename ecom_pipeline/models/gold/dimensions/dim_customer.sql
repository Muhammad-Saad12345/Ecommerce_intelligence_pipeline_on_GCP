{{ config(
    materialized='table',
    cluster_by=['customer_state']
) }}

with customer_dim as (
    select
        customer_id as customer_key,
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        source_system,
        load_date,
        ingestion_timestamp
    from {{ ref('silver_customers') }}
    where customer_id is not null

    union distinct

    select
        customer_id as customer_key,
        customer_id,
        null as customer_unique_id,
        null as customer_zip_code_prefix,
        null as customer_city,
        null as customer_state,
        null as source_system,
        null as load_date,
        current_timestamp() as ingestion_timestamp
    from {{ ref('silver_orders') }}
    where customer_id is not null
      and customer_id not in (
          select customer_id from {{ ref('silver_customers') }} where customer_id is not null
      )
)

select *
from customer_dim