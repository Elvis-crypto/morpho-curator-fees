"""Backfill N UTC days of MetaMorpho vault events + daily lastTotalAssets snapshots via free public RPCs,
plus daily asset prices from DefiLlama (public, keyless). Writes dbt/seeds/*.csv.
Usage: backfill_rpc.py END_DAY(YYYY-MM-DD, inclusive) N_DAYS"""
import csv, sys, time, json, datetime as dt, requests
from web3 import Web3
LOGS=Web3(Web3.HTTPProvider("https://rpc.mevblocker.io",request_kwargs={"timeout":120}))
ARCH=Web3(Web3.HTTPProvider("https://eth.drpc.org",request_kwargs={"timeout":60}))
VAULTS={"0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB":"steakhouse_usdc",
        "0xdd0f28e19C1780eb6396170735D45153D261490d":"gauntlet_usdc_prime",
        "0xBEEf050ecd6a16c4e7bfFbB52Ebba7846C4b8cD4":"steakhouse_eth"}
CURATOR_NAME={"0x827e86072b06674a077f592a531dce4590adecdb":"Steakhouse","0x9e33faae38ff641094fa68c65c2ce600b3410585":"Gauntlet"}
T=lambda s:"0x"+Web3.keccak(text=s).hex().removeprefix("0x")
TOP={T("AccrueInterest(uint256,uint256)"):"AccrueInterest",T("Deposit(address,address,uint256,uint256)"):"Deposit",
     T("Withdraw(address,address,address,uint256,uint256)"):"Withdraw"}
ABI=[{"name":n,"type":"function","stateMutability":"view","inputs":[],"outputs":[{"type":t}]} for n,t in
     [("name","string"),("fee","uint96"),("curator","address"),("feeRecipient","address"),("asset","address"),("decimals","uint8"),("lastTotalAssets","uint256"),("totalAssets","uint256")]]
def retry(f,*a,tries=6):
    for t in range(tries):
        try: return f(*a)
        except Exception as e:
            print("retry",t,repr(e)[:160],flush=True)
            if t==tries-1: raise
            time.sleep(2*(t+1))
HEAD=retry(lambda: ARCH.eth.block_number)
def block_at(ts):  # first block with timestamp >= ts
    lo,hi=HEAD-1_000_000,HEAD
    while lo<hi:
        m=(lo+hi)//2
        if retry(ARCH.eth.get_block,m).timestamp<ts: lo=m+1
        else: hi=m
    return lo
end=dt.date.fromisoformat(sys.argv[1]); n=int(sys.argv[2]); days=[end-dt.timedelta(days=i) for i in range(n-1,-1,-1)]
ts=lambda d:int(dt.datetime(d.year,d.month,d.day,tzinfo=dt.timezone.utc).timestamp())
import os
CACHE="data/day_bounds.json"; cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
bounds={}
for d in days+[end+dt.timedelta(days=1)]:
    k=d.isoformat()
    if k not in cache: cache[k]=block_at(ts(d)); json.dump(cache,open(CACHE,"w"))
    bounds[d]=cache[k]
blocks=[];meta=[];snap=[];rows=[]
for d in days: blocks.append(dict(day=d.isoformat(),first_block=bounds[d],last_block=bounds[d+dt.timedelta(days=1)]-1))
for a,slug in VAULTS.items():
    c=ARCH.eth.contract(address=a,abi=ABI); f=lambda nm,b="latest":retry(lambda: getattr(c.functions,nm)().call(block_identifier=b))
    asset=f("asset")
    meta.append(dict(vault=a.lower(),slug=slug,name=f("name"),asset=asset.lower(),
        asset_decimals=retry(ARCH.eth.contract(address=asset,abi=ABI).functions.decimals().call),
        fee_wad=f("fee"),curator=f("curator").lower(),curator_name=CURATOR_NAME.get(f("curator").lower(),"unknown"),fee_recipient=f("feeRecipient").lower()))
    # snapshot at end of the day before the window, then end of each day
    for b in [blocks[0]["first_block"]-1]+[x["last_block"] for x in blocks]:
        snap.append(dict(vault=a.lower(),block_number=b,last_total_assets=f("lastTotalAssets",b)))
    print("meta+snapshots",slug,flush=True)
for x in blocks:
    for s in range(x["first_block"],x["last_block"]+1,4000):
        for l in retry(LOGS.eth.get_logs,{"address":list(VAULTS),"fromBlock":s,"toBlock":min(s+3999,x["last_block"]),"topics":[list(TOP)]}):
            data=bytes(l["data"]); w=[int.from_bytes(data[i:i+32],"big") for i in range(0,len(data),32)]
            rows.append(dict(vault=l["address"].lower(),day=x["day"],block_number=l["blockNumber"],
                tx_hash="0x"+l["transactionHash"].hex().removeprefix("0x"),log_index=l["logIndex"],
                event=TOP["0x"+l["topics"][0].hex().removeprefix("0x")],arg0=w[0],arg1=w[1]))
    print(x["day"],len(rows),flush=True)
# prices: DefiLlama daily (00:00 UTC) chart
coins=",".join("ethereum:"+m["asset"] for m in {m["asset"]:m for m in meta}.values())
j=requests.get(f"https://coins.llama.fi/chart/{coins}",params={"start":ts(days[0]),"span":n+1,"period":"1d"},timeout=60).json()
prices=[]
for k,v in j["coins"].items():
    for p in v["prices"]:
        prices.append(dict(asset=k.split(":")[1].lower(),day=dt.datetime.fromtimestamp(p["timestamp"],dt.timezone.utc).date().isoformat(),price_usd=p["price"]))
for fn,data in [("raw_vault_logs",rows),("raw_vault_meta",meta),("raw_vault_snapshots",snap),("raw_day_blocks",blocks),("raw_prices_daily",prices)]:
    with open(f"dbt/seeds/{fn}.csv","w",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=list(data[0])); wr.writeheader(); wr.writerows(data)
print("done logs",len(rows),"prices",len(prices))
