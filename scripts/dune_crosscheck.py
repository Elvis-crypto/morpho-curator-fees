"""Optional independent cross-check vs Morpho's public Dune query 5930091 ("Vault Fees and Assets", owner: morpho),
reading only its latest CACHED results (no execution; ~4 datapoints/row). Cached parameter = Steakhouse USDC only.
Usage: dune_crosscheck.py [--fetch]   (--fetch needs DUNE_API_KEY; otherwise uses data/dune/q5930091_steakhouse_usdc.csv)"""
import sys, csv, pandas as pd, duckdb
SRC="data/dune/q5930091_steakhouse_usdc.csv"
if "--fetch" in sys.argv:
    sys.path.insert(0,"scripts"); from dune_cached import get
    s,j=get(5930091,limit=200,columns="day,metamorpho,daily_fee_usd,total_assets_usd",filters="day >= '2026-07-23' and day <= '2026-10-20'")
    assert s==200, j
    res=j["result"]; print("cached execution ended",j.get("execution_ended_at"),"datapoints",res["metadata"].get("datapoint_count"))
    pd.DataFrame(res["rows"]).to_csv(SRC,index=False)
d=pd.read_csv(SRC); d["day"]=pd.to_datetime(d.day).dt.date.astype(str)
c=duckdb.connect("morpho.duckdb",read_only=True)
o=c.sql("""select f.day::varchar as day, revenue_usd, fees_usd, price_usd,
  (select last_total_assets from decoded_vault_snapshots s where s.vault=f.vault and s.block_number=b.last_block)::double/1e6*price_usd as our_end_tvl_usd
  from vault_fees_daily f join raw_blocks b on cast(b.day as date)=f.day where slug='steakhouse_usdc'""").df()
m=o.merge(d,on="day").sort_values("day")
last=m.day.max(); m["partial_day_in_dune_cache"]=m.day==last   # cache executed mid-day on its last date
m["rev_diff_usd"]=m.daily_fee_usd-m.revenue_usd; m["rev_ratio"]=m.daily_fee_usd/m.revenue_usd
m["tvl_ratio"]=m.total_assets_usd/m.our_end_tvl_usd
m[["day","revenue_usd","daily_fee_usd","rev_diff_usd","rev_ratio","our_end_tvl_usd","total_assets_usd","tvl_ratio","partial_day_in_dune_cache"]].to_csv("reports/dune_crosscheck.csv",index=False)
m[["day","daily_fee_usd","partial_day_in_dune_cache"]].to_csv("dbt/seeds/dune_q5930091_daily.csv",index=False)
f=m[~m.partial_day_in_dune_cache]
s=dict(days=len(f),our=f.revenue_usd.sum(),dune=f.daily_fee_usd.sum(),med=f.rev_ratio.median(),p5=f.rev_ratio.quantile(.05),p95=f.rev_ratio.quantile(.95),
       maxabs=(f.rev_ratio-1).abs().max(),tvlmed=f.tvl_ratio.median(),tvlmin=f.tvl_ratio.min(),tvlmax=f.tvl_ratio.max())
md=f"""# Cross-check vs Morpho's public Dune query (Steakhouse USDC)

Source: [query 5930091 "Vault Fees and Assets"](https://dune.com/queries/5930091), owner **morpho**, used in the [Single Vault Performance](https://dune.com/morpho/single-vault-performance) dashboard.
Only its latest **cached** result was read (`GET /api/v1/query/5930091/results`, filtered to our window and 4 columns): 86 rows, 344 datapoints, cached execution ended 2026-10-16 13:31 UTC. The cache exists only for the dashboard's default parameter (Steakhouse USDC), so Gauntlet USDC Prime and Steakhouse ETH cannot be cross-checked without running the query ourselves, which our Dune plan blocks (402).

What is compared: their `daily_fee_usd` (curator fee) against our `revenue_usd`, over {s['days']} full days (2026-07-23 → 2026-10-15). The last cached day, 2026-10-16, is excluded because it was cached part-way through the day ($34.86 vs our $385.31).

| | Ours (dbt) | Dune (morpho) |
|---|---|---|
| Curator revenue, sum over {s['days']} days | ${s['our']:,.2f} | ${s['dune']:,.2f} |
| Difference | | {100*(s['dune']/s['our']-1):+.3f}% |
| Daily ratio dune/ours: median [p5, p95] | | {s['med']:.5f} [{s['p5']:.5f}, {s['p95']:.5f}] |
| Largest daily deviation | | {100*s['maxabs']:.2f}% |
| Day-end TVL ratio dune/ours: median [min, max] | | {s['tvlmed']:.4f} [{s['tvlmin']:.4f}, {s['tvlmax']:.4f}] |

Why the numbers differ. Query 5930091 reads the materialised table `dune.morpho.result_vault_fees_historical_daily`, whose builder query is not public. The notes below come from Morpho's related public query [4940829 "Vault historical fee per curator"](https://dune.com/queries/4940829), which uses the same fee-share logic:
- **Valuation.** They value the *cumulative* fee shares at the share price at each snapshot (`feeShares × (totalAssets+1)/(totalSupply+10^(18−decimals))`) and take daily differences. We value each accrual's fee in assets when it happens (`interest × fee`). The two agree except for the small mark-to-market change on fee shares already minted.
- **Price.** They use a single latest USDC price from `result_morpho_api_prices_extended`; we use DefiLlama's daily price. USDC is about $1, so the effect is around 0.03%, which matches the median ratio of about 0.9997.
- **Timing.** The daily figures agree to within 0.05%, so the materialised table appears to use UTC calendar days and accrual events like ours. (Query 4940829 itself snapshots at 09:00 UTC.)
- **TVL.** Their `total_assets_usd` is cumulative events × latest price; ours is the on-chain `lastTotalAssets()` at the day-end block × the daily price.
"""
open("reports/dune_crosscheck.md","w").write(md); print(md)
