select lower(asset) as asset, cast(day as date) as day, avg(price_usd) as price_usd from {{ ref('raw_prices') }} group by 1,2
