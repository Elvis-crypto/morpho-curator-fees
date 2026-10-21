-- Independent RPC check: for every daily snapshot (archive eth_call lastTotalAssets at the day's last block),
-- the running ledger built from events must equal the on-chain value exactly.
with s as (select * from {{ ref('decoded_vault_snapshots') }}
           qualify row_number() over (partition by vault order by block_number) > 1),
l as (select s.vault, s.block_number, s.last_total_assets,
        (select running_last_total_assets from {{ ref('vault_events_ledger') }} x
         where x.vault = s.vault and x.block_number <= s.block_number order by block_number desc, log_index desc limit 1) as ledger,
        (select last_total_assets from {{ ref('decoded_vault_snapshots') }} f where f.vault=s.vault order by block_number limit 1) as start_lta
      from s)
select * from l where coalesce(ledger, start_lta) <> last_total_assets
