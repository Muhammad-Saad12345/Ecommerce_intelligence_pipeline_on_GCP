{{ config(
    materialized='table',
    cluster_by=['product_category_name']
) }}

with product_sales as (

    select
        foi.product_id,
        dp.product_category_name,

        count(distinct foi.order_id) as total_orders,
        count(*) as units_sold,

        sum(foi.item_revenue) as item_revenue,
        sum(foi.freight_value) as freight_revenue,
        sum(foi.gross_item_value) as gross_revenue,

        min(foi.order_purchase_date) as first_sale_date,
        max(foi.order_purchase_date) as last_sale_date

    from {{ ref('fact_order_items') }} foi
    left join {{ ref('dim_product') }} dp
        on foi.product_id = dp.product_id

    group by
        foi.product_id,
        dp.product_category_name

)

select
    *,
    rank() over (
        order by gross_revenue desc
    ) as revenue_rank

from product_sales