from web3 import Web3
w=Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com",request_kwargs={"timeout":60}))
k=lambda s:"0x"+Web3.keccak(text=s).hex().removeprefix("0x")
sigs={
"Blue.AccrueInterest":"AccrueInterest(bytes32,uint256,uint256,uint256)",
"MM.AccrueInterest":"AccrueInterest(uint256,uint256)",
"MM.UpdateLastTotalAssets":"UpdateLastTotalAssets(uint256)",
"ERC4626.Deposit":"Deposit(address,address,uint256,uint256)",
"ERC4626.Withdraw":"Withdraw(address,address,address,uint256,uint256)",
"MM.SetFee":"SetFee(address,uint256)",
"CreateMetaMorpho":"CreateMetaMorpho(address,address,address,uint256,address,string,string,bytes32)"}
for n,s in sigs.items(): print(n,s,k(s))
print("head",w.eth.block_number)
for a in ["0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb","0x1897A8997241C1cD4bD0698647e4EB7213535c24","0xA9c3D3a366466Fa809d1Ae982Fb2c46E5fC41101"]:
    print(a,"code bytes",len(w.eth.get_code(a)))
# range limit test on Blue
h=w.eth.block_number
for r in [100,1000,5000,10000,50000]:
    try: print("range",r,len(w.eth.get_logs({"address":"0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb","fromBlock":h-r,"toBlock":h})))
    except Exception as e: print("range",r,"ERR",str(e)[:150])
# factory logs full history
for f in ["0xA9c3D3a366466Fa809d1Ae982Fb2c46E5fC41101","0x1897A8997241C1cD4bD0698647e4EB7213535c24"]:
    try:
        L=w.eth.get_logs({"address":f,"fromBlock":18800000,"toBlock":h,"topics":[k(sigs["CreateMetaMorpho"])]})
        print(f,"CreateMetaMorpho logs",len(L))
    except Exception as e: print(f,"ERR",str(e)[:200])
