"""Verify Morpho Blue protocol fee: SetFee events (full history) + fee field of market(id) for every market in each vault's withdraw queue."""
from web3 import Web3
import csv
LOGS=Web3(Web3.HTTPProvider("https://rpc.mevblocker.io",request_kwargs={"timeout":120}))
W=Web3(Web3.HTTPProvider("https://eth.drpc.org",request_kwargs={"timeout":60}))
BLUE="0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
SETFEE="0x"+Web3.keccak(text="SetFee(bytes32,uint256)").hex().removeprefix("0x")
import time
def logs(q,tries=5):
    for t in range(tries):
        try: return LOGS.eth.get_logs(q)
        except Exception as e:
            if t==tries-1: raise
            time.sleep(2*(t+1))
head=LOGS.eth.block_number; n=0; out=[]
STEP=50000
for s in range(18883000,head+1,STEP):
    for l in logs({"address":BLUE,"topics":[SETFEE],"fromBlock":s,"toBlock":min(s+STEP-1,head)}):
        out.append(("0x"+l["topics"][1].hex().removeprefix("0x"),int.from_bytes(bytes(l["data"]),"big"),l["blockNumber"]))
print("Blue SetFee events:",len(out)); [print(" ",o) for o in out]
VAULTS={"steakhouse_usdc":"0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB","gauntlet_usdc_prime":"0xdd0f28e19C1780eb6396170735D45153D261490d","steakhouse_eth":"0xBEEf050ecd6a16c4e7bfFbB52Ebba7846C4b8cD4"}
vabi=[{"name":"withdrawQueueLength","type":"function","stateMutability":"view","inputs":[],"outputs":[{"type":"uint256"}]},
      {"name":"withdrawQueue","type":"function","stateMutability":"view","inputs":[{"type":"uint256"}],"outputs":[{"type":"bytes32"}]}]
babi=[{"name":"market","type":"function","stateMutability":"view","inputs":[{"type":"bytes32"}],"outputs":[{"type":"uint128"}]*4+[{"type":"uint128"},{"type":"uint128"}]}]
blue=W.eth.contract(address=BLUE,abi=babi); rows=[]
for slug,a in VAULTS.items():
    v=W.eth.contract(address=a,abi=vabi)
    for i in range(v.functions.withdrawQueueLength().call()):
        mid=v.functions.withdrawQueue(i).call(); m=blue.functions.market(mid).call()
        rows.append(dict(vault=slug,market_id="0x"+mid.hex(),total_supply_assets=m[0],total_borrow_assets=m[2],fee_wad=m[5]))
with open("data/blue_market_fees.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print("markets checked:",len(rows),"nonzero fee:",[r for r in rows if r["fee_wad"]])
