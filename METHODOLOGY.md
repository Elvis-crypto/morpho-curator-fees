# Methodology: Morpho curator vault fees

**Scope.** Three MetaMorpho **V1** vaults on Ethereum: Steakhouse USDC (`0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB`), Steakhouse ETH (`0xBEEf050ecd6a16c4e7bfFbB52Ebba7846C4b8cD4`), Gauntlet USDC Prime (`0xdd0f28e19C1780eb6396170735D45153D261490d`). Daily, UTC. Morpho Vault V2 is out of scope.

## Definitions (following Token Terminal's public metric definitions)
| Metric | Definition for a curator vault |
|---|---|
| **Fees** | Gross interest earned on the vault's assets: the interest Morpho Blue borrowers pay, attributed to this vault's supply. |
| **Supply-side fees** | The part of fees passed on to the vault's depositors. |
| **Revenue** | The part of fees the curator keeps (performance fee minted as vault shares to `feeRecipient`). |
| Identity | fees = revenue + supply-side fees |

Morpho Blue's own protocol fee would sit between borrowers and the vault. We checked it rather than assuming it: there are **0 `SetFee` events** on Morpho Blue (`0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb`) over its full history, and `market(id).fee` = 0 for all 27 markets in the three vaults' withdraw queues (`data/blue_market_fees.csv`).

## Formulas
A MetaMorpho vault stores `lastTotalAssets`. Each interaction first emits `AccrueInterest(newTotalAssets, feeShares)`:
- `interest_i = newTotalAssets_i − lastTotalAssets_(before i)`, where `lastTotalAssets` goes up by `assets` on each `Deposit`, down on each `Withdraw`, and resets to `newTotalAssets` on each accrual.
- `curator_fee_i = interest_i × fee / 1e18` (the contract's own `_accruedFeeShares` logic; `fee` = 5% for all three vaults).
- `supply_side_i = interest_i − curator_fee_i`.
- USD = asset amount × that UTC day's 00:00 price (DefiLlama), summed per vault and per curator.

## Data sources
- **Events:** `AccrueInterest`, `Deposit`, `Withdraw` logs for the three vaults from public Ethereum RPC (topics in `research.md`). The Dune `ethereum.logs` version is in `sql/`, so we can switch to it.
- **State:** archive `eth_call` reads of `lastTotalAssets()` at the end of each day, used only for checking.
- **Prices:** DefiLlama `coins.llama.fi` daily prices (USDC, WETH). `prices.day` on Dune is the equivalent.

## Quality checks (dbt tests)
1. fees = revenue + supply-side, exact in raw integer units.
2. **Independent reconciliation:** the running ledger built from events equals the on-chain `lastTotalAssets()` at every day-end block, exactly.
3. One row per vault per day; every row has a price.

## Caveats
- **Accrual timing:** interest is recorded when an on-chain accrual happens. Interest that builds up after a day's last interaction is counted on the next day, so daily figures for quiet vaults are lumpy. Totals over a period are unaffected, except for interest still pending at the period's end.
- Only **V1** vaults are covered. Assets curators manage in V2 vaults, or vaults that put money into other vaults, are not included.
- **Token incentives** (MORPHO, URD/Merkl rewards) are excluded, so earnings are not computed.
- The curator's fee shares are valued at the asset amount when they are created. Later changes in share price are not attributed.
- Unmodelled vault events, such as `ReallocateSupply`/`ReallocateWithdraw` (topic `0xdd8bf522…` = `ReallocateWithdraw(address,bytes32,uint256,uint256)`), move assets between markets and do not change `totalAssets`.
- **External cross-check:** our curator revenue for Steakhouse USDC matches Morpho's own public Dune query 5930091 to −0.025% over 85 days (`reports/dune_crosscheck.md`).
