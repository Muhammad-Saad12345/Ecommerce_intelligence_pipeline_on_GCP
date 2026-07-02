{{ config(
    materialized='table',
    partition_by={
      "field": "order_purchase_date",
      "data_type": "date"
    },
    cluster_by=['product_id', 'seller_id']
) }}

with order_items as (

    select *
    from {{ ref('silver_order_items') }}

),

orders as (

    select
        order_id,
        customer_id,
        order_status,
        date(order_purchase_timestamp) as order_purchase_date
    from {{ ref('silver_orders') }}

)

select
    concat(oi.order_id, '-', cast(oi.order_item_id as string)) as order_item_key,

    oi.order_id,
    oi.order_item_id,
    o.customer_id,
    oi.product_id,
    oi.seller_id,

    o.order_purchase_date,
    o.order_status,
    oi.shipping_limit_date,

    oi.price as item_revenue,
    oi.freight_value,
    oi.price + oi.freight_value as gross_item_value,

    oi.source_system,
    oi.source_file_name,
    oi.load_date,
    oi.ingestion_timestamp

from order_items oi
left join orders o
    on oi.order_id = o.order_id