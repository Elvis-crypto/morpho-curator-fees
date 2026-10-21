"""Pull one UTC day of MetaMorpho vault logs + totalAssets snapshots from public RPC -> dbt seeds CSV."""
import csv, sys, datetime as dt
from web3 import Web3
RPC="https://ethereum-rpc.publicnode.com"
w=Web3(Web3.HTTPProvider(RPC,request_kwargs={"timeout":60}))
ARCH=Web3(Web3.HTTPProvider("https://eth.drpc.org",request_kwargs={"timeout":60}))  # archive eth_call (publicnode blocks historical state)
LOGS=Web3(Web3.HTTPProvider("https://rpc.mevblocker.io",request_kwargs={"timeout":60}))  # full-day getLogs worked here
DAY=sys.argv[1] if len(sys.argv)>1 else "2026-10-19"
VAULTS={"0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB":"steakhouse_usdc",
        "0xdd0f28e19C1780eb6396170735D45153D261490d":"gauntlet_usdc_prime",
        "0xBEEf050ecd6a16c4e7bfFbB52Ebba7846C4b8cD4":"steakhouse_eth"}
T=lambda s:"0x"+Web3.keccak(text=s).hex().removeprefix("0x")
TOP={T("AccrueInterest(uint256,uint256)"):"AccrueInterest",
     T("Deposit(address,address,uint256,uint256)"):"Deposit",
     T("Withdraw(address,address,address,uint256,uint256)"):"Withdraw"}
ABI=[{"name":n,"type":"function","stateMutability":"view","inputs":[],"outputs":[{"type":t}]} for n,t in
     [("name","string"),("fee","uint96"),("curator","address"),("feeRecipient","address"),("totalAssets","uint256"),("totalSupply","uint256"),("asset","address"),("decimals","uint8"),("lastTotalAssets","uint256")]]
def block_at(ts):
    lo,hi=w.eth.block_number-400000,w.eth.block_number
    while lo<hi:
        m=(lo+hi)//2
        if w.eth.get_block(m).timestamp<ts: lo=m+1
        else: hi=m
    return lo
d=dt.datetime.fromisoformat(DAY).replace(tzinfo=dt.timezone.utc)
b0=block_at(int(d.timestamp())); b1=block_at(int((d+dt.timedelta(days=1)).timestamp()))-1
print("blocks",b0,b1)
meta=[];snap=[]
for a,slug in VAULTS.items():
    c=ARCH.eth.contract(address=a,abi=ABI)
    f=lambda n,b="latest":getattr(c.functions,n)().call(block_identifier=b)
    meta.append(dict(vault=a.lower(),slug=slug,name=f("name"),asset=f("asset").lower(),decimals=f("decimals"),
        fee_wad=f("fee"),curator=f("curator").lower(),fee_recipient=f("feeRecipient").lower(),
        asset_decimals=ARCH.eth.contract(address=f("asset"),abi=ABI).functions.decimals().call()))
    for b in (b0-1,b1):
        snap.append(dict(vault=a.lower(),block_number=b,total_assets=f("totalAssets",b),total_supply=f("totalSupply",b),last_total_assets=f("lastTotalAssets",b)))
rows=[]
for s in range(b0,b1+1,8000):
    for l in LOGS.eth.get_logs({"address":list(VAULTS),"fromBlock":s,"toBlock":min(s+7999,b1),"topics":[list(TOP)]}):
        t0="0x"+l["topics"][0].hex().removeprefix("0x"); data=bytes(l["data"])
        words=[int.from_bytes(data[i:i+32],"big") for i in range(0,len(data),32)]
        rows.append(dict(vault=l["address"].lower(),block_number=l["blockNumber"],tx_hash="0x"+l["transactionHash"].hex().removeprefix("0x"),
            log_index=l["logIndex"],event=TOP[t0],arg0=words[0],arg1=words[1] if len(words)>1 else None))
for fn,data in [("raw_vault_logs",rows),("raw_vault_meta",meta),("raw_vault_snapshots",snap)]:
    with open(f"dbt/seeds/{fn}.csv","w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(data[0])); wr.writeheader(); wr.writerows(data)
print("logs",len(rows)); [print(m) for m in meta]
from collections import Counter; print(Counter((r["vault"][:8],r["event"]) for r in rows))
