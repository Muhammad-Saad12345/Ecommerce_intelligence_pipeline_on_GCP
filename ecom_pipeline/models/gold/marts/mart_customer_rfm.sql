{{ config(
    materialized='table',
    cluster_by=['customer_segment', 'customer_state']
) }}

with analysis_date as (

    select max(order_purchase_date) as max_order_date
    from {{ ref('fact_orders') }}

),

customer_orders as (

    select
        fo.customer_id,
        max(fo.order_purchase_date) as last_order_date,
        count(distinct fo.order_id) as frequency_orders,
        sum(fo.gross_order_value) as monetary_value
    from {{ ref('fact_orders') }} fo
    where fo.order_purchase_date is not null
    group by fo.customer_id

),

rfm as (

    select
        co.customer_id,
        dc.customer_unique_id,
        dc.customer_city,
        dc.customer_state,

        co.last_order_date,
        date_diff(ad.max_order_date, co.last_order_date, day) as recency_days,
        co.frequency_orders,
        co.monetary_value,

        case
            when date_diff(ad.max_order_date, co.last_order_date, day) <= 30 then 'recent'
            when date_diff(ad.max_order_date, co.last_order_date, day) <= 90 then 'warm'
            when date_diff(ad.max_order_date, co.last_order_date, day) <= 180 then 'at_risk'
            else 'dormant'
        end as recency_segment,

        case
            when co.frequency_orders >= 5 and co.monetary_value >= 1000 then 'champion'
            when co.frequency_orders >= 3 then 'loyal'
            when co.monetary_value >= 500 then 'high_value'
            when date_diff(ad.max_order_date, co.last_order_date, day) > 180 then 'churn_risk'
            else 'regular'
        end as customer_segment

    from customer_orders co
    cross join analysis_date ad
    left join {{ ref('dim_customer') }} dc
        on co.customer_id = dc.customer_id

)

select *
from rfm