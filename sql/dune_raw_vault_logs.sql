-- Dune equivalent of the RPC raw layer (prepared; not executed: Dune API returned 402 datapoint limit).
-- Narrow: 3 vault addresses, 3 topics, 90 days. Uses ethereum.logs (no decoded vault-event tables confirmed).
select contract_address as vault, date(block_time) as day, block_number, tx_hash, index as log_index,
  case topic0 when 0xf66f28b40975dbb933913542c7e6a0f50a1d0f20aa74ea6e0efe65ab616323ec then 'AccrueInterest'
              when 0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7 then 'Deposit'
              else 'Withdraw' end as event,
  bytearray_to_uint256(bytearray_substring(data, 1, 32))  as arg0,
  bytearray_to_uint256(bytearray_substring(data, 33, 32)) as arg1
from ethereum.logs
where block_time >= now() - interval '90' day
  and contract_address in (0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB, 0xdd0f28e19C1780eb6396170735D45153D261490d, 0xBEEf050ecd6a16c4e7bfFbB52Ebba7846C4b8cD4)
  and topic0 in (0xf66f28b40975dbb933913542c7e6a0f50a1d0f20aa74ea6e0efe65ab616323ec,
                 0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7,
                 0xfbde797d201c681b91056529119e0b02407c7bb96a4a2c75c01fc9667232c8db)
