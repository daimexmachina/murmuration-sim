import json, time, urllib.request, urllib.parse
UA="bw-recon research contact@example.com"
BASE="https://efts.sec.gov/LATEST/search-index"
def count(q,form,s,e):
    url=BASE+"?"+urllib.parse.urlencode({"q":q,"forms":form,"dateRange":"custom","startdt":s,"enddt":e})
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: d=json.loads(r.read().decode())
        return d["hits"]["total"]
    except Exception as ex: return {"ERR":str(ex)}
Y=["2015","2016","2017","2018","2019","2020","2021","2022","2023","2024","2025","2026"]
out={}
for y in Y:
    s,e=(y+"-01-01",y+"-12-31") if y!="2026" else ("2026-01-01","2026-09-17")
    out[y]={"total_10K_the":count('"the"',"10-K",s,e),"AI_bare":count('"AI"',"10-K",s,e),"AI_10Q":count('"artificial intelligence"',"10-Q",s,e)}
    print(y,out[y],flush=True); time.sleep(0.5)
json.dump(out,open("census2.json","w"),indent=1); print("DONE")
