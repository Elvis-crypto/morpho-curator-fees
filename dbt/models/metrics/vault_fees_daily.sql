-- Layer 4 (TT definitions, per vault per UTC day): fees = gross interest earned by depositors' assets;
-- revenue = curator performance fee; fees_supply_side = interest passed to depositors. USD at daily price.
with d as (
  select b.day, m.vault, m.slug, m.name, m.curator, m.curator_name, m.asset, m.asset_decimals
  from {{ ref('raw_blocks') }} b cross join {{ ref('decoded_vault_meta') }} m
), a as (
  select vault, day, sum(interest_assets) as fees_raw, sum(curator_fee_assets) as revenue_raw, count(*) as accruals
  from {{ ref('vault_interest_accruals') }} group by 1,2
)
select cast(d.day as date) as day, d.vault, d.slug, d.name, d.curator, d.curator_name, d.asset,
  coalesce(a.fees_raw,0) as fees_raw, coalesce(a.revenue_raw,0) as revenue_raw,
  coalesce(a.fees_raw,0) - coalesce(a.revenue_raw,0) as fees_supply_side_raw, coalesce(a.accruals,0) as accruals,
  p.price_usd,
  cast(coalesce(a.fees_raw,0) as double) / pow(10, d.asset_decimals) * p.price_usd as fees_usd,
  cast(coalesce(a.revenue_raw,0) as double) / pow(10, d.asset_decimals) * p.price_usd as revenue_usd,
  cast(coalesce(a.fees_raw,0) - coalesce(a.revenue_raw,0) as double) / pow(10, d.asset_decimals) * p.price_usd as fees_supply_side_usd
from d left join a on a.vault = d.vault and a.day = cast(d.day as date)
-- as-of join: latest DefiLlama daily price on or before the day (a few days have no point at the day itself)
asof left join {{ ref('decoded_prices_daily') }} p on p.asset = d.asset and cast(d.day as date) >= p.day
