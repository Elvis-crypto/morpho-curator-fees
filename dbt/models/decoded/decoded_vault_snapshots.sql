select lower(vault) as vault, block_number, cast(last_total_assets as hugeint) as last_total_assets
from {{ ref('raw_snapshots') }}
