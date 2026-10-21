-- Layer 3: interest per accrual. lastTotalAssets evolves: Deposit +assets, Withdraw -assets,
-- AccrueInterest resets it to newTotalAssets. interest = newTotalAssets - lastTotalAssets just before.
-- Curator fee assets = interest * fee / 1e18 (MetaMorpho _accruedFeeShares, fee in WAD).
with start as (
  select vault, last_total_assets as start_lta from {{ ref('decoded_vault_snapshots') }}
  qualify row_number() over (partition by vault order by block_number) = 1
),
ev as (
  select e.*,
    case event when 'Deposit' then assets when 'Withdraw' then -assets else 0 end as flow,
    sum(case when event = 'AccrueInterest' then 1 else 0 end)
      over (partition by vault order by block_number, log_index rows unbounded preceding) as accrual_seq
  from {{ ref('decoded_vault_events') }} e
),
acc as (
  select a.vault, a.day, a.block_number, a.tx_hash, a.log_index, a.accrual_seq, a.new_total_assets, a.fee_shares,
    coalesce(lag(a.new_total_assets) over (partition by a.vault order by a.accrual_seq), s.start_lta) as prev_anchor
  from ev a join start s using (vault) where a.event = 'AccrueInterest'
),
flows as (select vault, accrual_seq + 1 as accrual_seq, sum(flow) as net_flow from ev where event <> 'AccrueInterest' group by 1, 2)
select acc.*, coalesce(f.net_flow, 0) as net_flow_before,
  acc.new_total_assets - (acc.prev_anchor + coalesce(f.net_flow, 0)) as interest_assets,
  (acc.new_total_assets - (acc.prev_anchor + coalesce(f.net_flow, 0))) * m.fee_wad // cast(1e18 as hugeint) as curator_fee_assets
from acc left join flows f using (vault, accrual_seq)
join {{ ref('decoded_vault_meta') }} m using (vault)
