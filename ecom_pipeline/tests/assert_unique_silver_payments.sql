select
  order_id,
  payment_sequential,
  count(*) as row_count
from {{ ref('silver_payments') }}
group by order_id, payment_sequential
having count(*) > 1