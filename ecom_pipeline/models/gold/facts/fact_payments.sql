{{ config(
    materialized='table',
    partition_by={
      "field": "order_purchase_date",
      "data_type": "date"
    },
    cluster_by=['payment_type']
) }}

with payments as (

    select *
    from {{ ref('silver_payments') }}

),

orders as (

    select
        order_id,
        customer_id,
        date(order_purchase_timestamp) as order_purchase_date,
        order_status
    from {{ ref('silver_orders') }}

)

select
    concat(p.order_id, '-', cast(p.payment_sequential as string)) as payment_key,

    p.order_id,
    o.customer_id,
    p.payment_sequential,
    p.payment_type,
    p.payment_installments,
    p.payment_value,

    o.order_purchase_date,
    o.order_status,

    p.source_system,
    p.source_file_name,
    p.load_date,
    p.ingestion_timestamp

from payments p
left join orders o
    on p.order_id = o.order_id