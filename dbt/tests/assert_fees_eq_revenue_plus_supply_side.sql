-- TT identity (raw integer units, exact) and in USD (tolerance 1e-6)
select * from {{ ref('vault_fees_daily') }}
where fees_raw <> revenue_raw + fees_supply_side_raw or abs(fees_usd - revenue_usd - fees_supply_side_usd) > 1e-6
