select day, curator, curator_name, sum(fees_usd) as fees_usd, sum(revenue_usd) as revenue_usd,
  sum(fees_supply_side_usd) as fees_supply_side_usd, count(*) as vaults
from {{ ref('vault_fees_daily') }} group by 1,2,3
