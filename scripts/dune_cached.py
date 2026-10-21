"""Read latest *cached* results of existing public Dune queries (GET /query/<id>/results). No execution. Key from env."""
import os, sys, json, requests
H={"X-Dune-Api-Key":os.environ["DUNE_API_KEY"]}
def get(qid, limit=5, offset=0, **params):
    r=requests.get(f"https://api.dune.com/api/v1/query/{qid}/results",headers=H,params={"limit":limit,"offset":offset,**params},timeout=60)
    return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text[:300]
if __name__=="__main__":
    for q in sys.argv[1:]:
        s,j=get(q,limit=3)
        if s!=200: print(q,s,str(j)[:300]); continue
        res=j.get("result",{}); md=res.get("metadata",{})
        print(q,s,"state",j.get("state"),"ended",j.get("execution_ended_at"),"cols",md.get("column_names"),"total_rows",md.get("total_row_count"),
              "datapoints",md.get("datapoint_count"),"cost",{k:v for k,v in j.items() if "cost" in k or "credit" in k})
        print("  sample",json.dumps(res.get("rows",[])[:2])[:400])
