"""Export metrics models -> dashboard/data/*.json, reports/*.csv|md, and chart PNG. Run after dbt build."""
import duckdb, json, shutil, sys, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
RECON_DAY=sys.argv[1] if len(sys.argv)>1 else "2026-10-19"
c=duckdb.connect("morpho.duckdb", read_only=True)
q=lambda s:c.sql(s).df()
vault=q("select day::varchar as day, slug, name, curator_name, fees_usd, revenue_usd, fees_supply_side_usd, accruals from vault_fees_daily order by day, slug")
cur=q("select day::varchar as day, curator_name, fees_usd, revenue_usd, fees_supply_side_usd from curator_fees_daily order by day, curator_name")
tot=q("""select name, curator_name, min(day)::varchar as first_day, max(day)::varchar as last_day, count(*) as n_days,
  sum(fees_usd) fees_usd, sum(revenue_usd) revenue_usd, sum(fees_supply_side_usd) fees_supply_side_usd
  from vault_fees_daily group by 1,2 order by fees_usd desc""")
led=q(f"""select l.day::varchar as day, m.name, l.block_number, l.tx_hash, l.log_index, l.event,
  l.delta_assets::double / pow(10,m.asset_decimals) delta_assets, l.interest_assets::double/pow(10,m.asset_decimals) interest_assets,
  l.curator_fee_assets::double/pow(10,m.asset_decimals) curator_fee_assets,
  l.running_last_total_assets::double/pow(10,m.asset_decimals) running_last_total_assets
  from vault_events_ledger l join decoded_vault_meta m using (vault) where l.day = '{RECON_DAY}' order by m.name, block_number, log_index""")
snap=q(f"""with b as (select * from raw_blocks where day::varchar='{RECON_DAY}')
  select m.name, (select last_total_assets from decoded_vault_snapshots s where s.vault=m.vault and s.block_number=(select last_block from b))::double/pow(10,m.asset_decimals) onchain_end,
  (select running_last_total_assets from vault_events_ledger l where l.vault=m.vault and l.block_number<=(select last_block from b) order by block_number desc, log_index desc limit 1)::double/pow(10,m.asset_decimals) ledger_end
  from decoded_vault_meta m""")
snap["diff"]=snap.ledger_end-snap.onchain_end
for name,df in [("vault_daily",vault),("curator_daily",cur),("totals",tot),("recon_ledger",led),("recon_summary",snap)]:
    df.to_json(f"dashboard/data/{name}.json",orient="records",double_precision=10)
led.to_csv(f"reports/reconciliation_{RECON_DAY}.csv",index=False)
with open(f"reports/reconciliation_{RECON_DAY}.md","w") as f:
    f.write(f"# Transaction-level reconciliation — {RECON_DAY} (UTC)\n\nEnd-of-day ledger vs on-chain `lastTotalAssets()` (archive eth_call):\n\n")
    f.write(snap.to_markdown(index=False)+"\n\nEvents (asset units):\n\n"+led.to_markdown(index=False)+"\n")
shutil.copy("METHODOLOGY.md","dashboard/METHODOLOGY.md")
fig,ax=plt.subplots(figsize=(11,5))
for n,g in cur.groupby("curator_name"):
    d=pd.to_datetime(g.day); ax.plot(d,g.fees_usd,label=f"{n} fees"); ax.plot(d,g.revenue_usd,"--",label=f"{n} revenue")
ax.set_title("Morpho V1 curator vaults (3 Ethereum vaults): daily fees & curator revenue, USD"); ax.set_ylabel("USD"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig("reports/curator_fees_daily.png",dpi=130)
print(tot.to_string()); print(snap.to_string())
