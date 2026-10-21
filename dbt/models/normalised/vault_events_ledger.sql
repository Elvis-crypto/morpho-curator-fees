-- Transaction-level ledger: every event with running lastTotalAssets (for reconciliation exports)
with start as (
  select vault, last_total_assets as start_lta from {{ ref('decoded_vault_snapshots') }}
  qualify row_number() over (partition by vault order by block_number) = 1
), e as (
  select d.vault, d.day, d.block_number, d.tx_hash, d.log_index, d.event,
    case d.event when 'Deposit' then d.assets when 'Withdraw' then -d.assets else coalesce(i.interest_assets,0) end as delta_assets,
    coalesce(i.interest_assets,0) as interest_assets, coalesce(i.curator_fee_assets,0) as curator_fee_assets
  from {{ ref('decoded_vault_events') }} d
  left join {{ ref('vault_interest_accruals') }} i using (vault, block_number, log_index)
)
select e.*, s.start_lta + sum(delta_assets) over (partition by e.vault order by block_number, log_index rows unbounded preceding) as running_last_total_assets
from e join start s using (vault)
