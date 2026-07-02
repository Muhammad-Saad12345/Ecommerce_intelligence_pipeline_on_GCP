{{ config(
    materialized='table'
) }}

with date_spine as (

    select date_day
    from unnest(generate_date_array('2016-01-01', '2026-12-31', interval 1 day)) as date_day

)

select
    date_day as date_key,
    date_day,

    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    format_date('%B', date_day) as month_name,

    extract(week from date_day) as week_of_year,
    extract(day from date_day) as day_of_month,
    extract(dayofweek from date_day) as day_of_week,
    format_date('%A', date_day) as day_name,

    case
        when extract(dayofweek from date_day) in (1, 7) then true
        else false
    end as is_weekend

from date_spine