-- Layer 2 decoded: typed MetaMorpho events. AccrueInterest(newTotalAssets, feeShares); Deposit/Withdraw(assets, shares)
select lower(vault) as vault, cast(day as date) as day, block_number, tx_hash, log_index, event,
  case when event = 'AccrueInterest' then cast(arg0 as hugeint) end as new_total_assets,
  case when event = 'AccrueInterest' then cast(arg1 as hugeint) end as fee_shares,
  case when event in ('Deposit','Withdraw') then cast(arg0 as hugeint) end as assets,
  case when event in ('Deposit','Withdraw') then cast(arg1 as hugeint) end as shares
from {{ ref('raw_logs') }}
