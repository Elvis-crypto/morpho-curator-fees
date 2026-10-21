# Cross-check vs Morpho's public Dune query (Steakhouse USDC)

Source: [query 5930091 "Vault Fees and Assets"](https://dune.com/queries/5930091), owner **morpho**, used in the [Single Vault Performance](https://dune.com/morpho/single-vault-performance) dashboard.
Only its latest **cached** result was read (`GET /api/v1/query/5930091/results`, filtered to our window and 4 columns): 86 rows, 344 datapoints, cached execution ended 2026-10-16 13:31 UTC. The cache exists only for the dashboard's default parameter (Steakhouse USDC), so Gauntlet USDC Prime and Steakhouse ETH cannot be cross-checked without running the query ourselves, which our Dune plan blocks (402).

What is compared: their `daily_fee_usd` (curator fee) against our `revenue_usd`, over 85 full days (2026-07-23 → 2026-10-15). The last cached day, 2026-10-16, is excluded because it was cached part-way through the day ($34.86 vs our $385.31).

| | Ours (dbt) | Dune (morpho) |
|---|---|---|
| Curator revenue, sum over 85 days | $33,868.95 | $33,860.41 |
| Difference | | -0.025% |
| Daily ratio dune/ours: median [p5, p95] | | 0.99972 [0.99957, 0.99995] |
| Largest daily deviation | | 0.05% |
| Day-end TVL ratio dune/ours: median [min, max] | | 0.9997 [0.9995, 1.0000] |

Why the numbers differ. Query 5930091 reads the materialised table `dune.morpho.result_vault_fees_historical_daily`, whose builder query is not public. The notes below come from Morpho's related public query [4940829 "Vault historical fee per curator"](https://dune.com/queries/4940829), which uses the same fee-share logic:
- **Valuation.** They value the *cumulative* fee shares at the share price at each snapshot (`feeShares × (totalAssets+1)/(totalSupply+10^(18−decimals))`) and take daily differences. We value each accrual's fee in assets when it happens (`interest × fee`). The two agree except for the small mark-to-market change on fee shares already minted.
- **Price.** They use a single latest USDC price from `result_morpho_api_prices_extended`; we use DefiLlama's daily price. USDC is about $1, so the effect is around 0.03%, which matches the median ratio of about 0.9997.
- **Timing.** The daily figures agree to within 0.05%, so the materialised table appears to use UTC calendar days and accrual events like ours. (Query 4940829 itself snapshots at 09:00 UTC.)
- **TVL.** Their `total_assets_usd` is cumulative events × latest price; ours is the on-chain `lastTotalAssets()` at the day-end block × the daily price.
