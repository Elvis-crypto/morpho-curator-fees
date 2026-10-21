select contract_address as asset, date(timestamp) as day, price as price_usd
from prices.day where blockchain='ethereum' and timestamp >= now() - interval '91' day
  and contract_address in (0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48, 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2)
