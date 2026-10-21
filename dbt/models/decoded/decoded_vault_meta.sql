select lower(vault) as vault, slug, name, lower(asset) as asset, asset_decimals,
       cast(fee_wad as hugeint) as fee_wad, curator, curator_name, fee_recipient
from {{ ref('raw_meta') }}
