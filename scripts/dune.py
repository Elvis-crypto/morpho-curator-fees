"""Minimal Dune API runner (ad-hoc SQL, no saved queries). Key from env DUNE_API_KEY; never printed."""
import os, time, sys, json, requests, csv
H={"X-Dune-Api-Key":os.environ["DUNE_API_KEY"],"content-type":"application/json"}
B="https://api.dune.com/api/v1"
def run(sql, out=None, perf="medium"):
    r=requests.post(f"{B}/sql/execute",headers=H,json={"sql":sql},timeout=60)
    if r.status_code>=300: raise SystemExit(f"execute failed {r.status_code}: {r.text[:300]}")
    eid=r.json()["execution_id"]
    while True:
        s=requests.get(f"{B}/execution/{eid}/status",headers=H,timeout=60).json()
        st=s.get("state")
        if st=="QUERY_STATE_COMPLETED": break
        if st in("QUERY_STATE_FAILED","QUERY_STATE_CANCELLED"): raise SystemExit(f"{st}: {json.dumps(s.get('error'))[:500]}")
        time.sleep(3)
    rows=[];off=0
    while True:
        j=requests.get(f"{B}/execution/{eid}/results",headers=H,params={"limit":10000,"offset":off},timeout=120).json()
        res=j["result"]; rows+=res["rows"]; cols=res["metadata"]["column_names"]
        if not j.get("next_offset"): break
        off=j["next_offset"]
    print("credits/meta:",{k:s.get(k) for k in("execution_cost_credits","result_metadata") if k in s and k!="result_metadata"},"rows",len(rows),file=sys.stderr)
    if out:
        with open(out,"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
    return rows
if __name__=="__main__":
    sql=open(sys.argv[1]).read(); rows=run(sql, sys.argv[2] if len(sys.argv)>2 else None)
    if len(sys.argv)<=2: [print(r) for r in rows[:50]]
