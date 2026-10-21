select vault, day, count(*) from {{ ref('vault_fees_daily') }} group by 1,2 having count(*) > 1
