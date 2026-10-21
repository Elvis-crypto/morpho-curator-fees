-- Optional independent cross-check: Morpho's public Dune query 5930091 (cached results, Steakhouse USDC only).
-- Curator revenue per full day must agree within 0.5% (differences: price source, fee-share mark-to-market).
select f.day, f.revenue_usd, d.daily_fee_usd
from {{ ref('vault_fees_daily') }} f
join {{ ref('dune_q5930091_daily') }} d on cast(d.day as date) = f.day
where f.slug = 'steakhouse_usdc' and not d.partial_day_in_dune_cache
  and abs(d.daily_fee_usd / nullif(f.revenue_usd, 0) - 1) > 0.005
