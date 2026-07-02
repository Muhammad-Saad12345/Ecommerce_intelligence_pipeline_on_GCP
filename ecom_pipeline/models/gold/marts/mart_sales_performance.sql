{{ config(
    materialized='table',
    partition_by={
      "field": "order_purchase_date",
      "data_type": "date"
    },
    cluster_by=['product_category_name']
) }}

select
    foi.order_purchase_date,
    dp.product_category_name,

    count(distinct foi.order_id) as total_orders,
    count(*) as total_items_sold,

    sum(foi.item_revenue) as item_revenue,
    sum(foi.freight_value) as freight_revenue,
    sum(foi.gross_item_value) as gross_revenue,

    safe_divide(
        sum(foi.gross_item_value),
        count(distinct foi.order_id)
    ) as average_order_value

from {{ ref('fact_order_items') }} foi
left join {{ ref('dim_product') }} dp
    on foi.product_id = dp.product_id

where foi.order_purchase_date is not null

group by
    foi.order_purchase_date,
    dp.product_category_name