{{ config(
    materialized='table',
    partition_by={
      "field": "order_purchase_date",
      "data_type": "date"
    },
    cluster_by=['customer_id', 'order_status']
) }}

with orders as (

    select *
    from {{ ref('silver_orders') }}

),

items_agg as (

    select
        order_id,
        count(*) as total_order_items,
        sum(price) as item_revenue,
        sum(freight_value) as freight_revenue,
        sum(price + freight_value) as gross_order_value
    from {{ ref('silver_order_items') }}
    group by order_id

),

payments_agg as (

    select
        order_id,
        count(*) as payment_count,
        sum(payment_value) as total_payment_value
    from {{ ref('silver_payments') }}
    group by order_id

)

select
    o.order_id,
    o.customer_id,

    date(o.order_purchase_timestamp) as order_purchase_date,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    o.order_status,

    coalesce(i.total_order_items, 0) as total_order_items,
    coalesce(i.item_revenue, 0) as item_revenue,
    coalesce(i.freight_revenue, 0) as freight_revenue,
    coalesce(i.gross_order_value, 0) as gross_order_value,

    coalesce(p.payment_count, 0) as payment_count,
    coalesce(p.total_payment_value, 0) as total_payment_value,

    case
        when o.order_delivered_customer_date is not null
         and o.order_estimated_delivery_date is not null
         and o.order_delivered_customer_date > o.order_estimated_delivery_date
        then true
        else false
    end as is_late_delivery,

    case
        when o.order_delivered_customer_date is not null
         and o.order_purchase_timestamp is not null
        then date_diff(
            date(o.order_delivered_customer_date),
            date(o.order_purchase_timestamp),
            day
        )
        else null
    end as delivery_days,

    o.source_system,
    o.source_file_name,
    o.load_date,
    o.ingestion_timestamp

from orders o
left join items_agg i
    on o.order_id = i.order_id
left join payments_agg p
    on o.order_id = p.order_id