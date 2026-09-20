import json, time, urllib.request, urllib.parse, sys

UA = "bw-recon research contact@example.com"
BASE = "https://efts.sec.gov/LATEST/search-index"

def count(q, form, start, end):
    params = urllib.parse.urlencode({"q": q, "forms": form, "dateRange":"custom","startdt":start,"enddt":end})
    url = BASE + "?" + params
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept":"application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode())
            t = d["hits"]["total"]
            return {"value": t["value"], "relation": t.get("relation"), "status": 200}
        except Exception as e:
            time.sleep(2)
            err = str(e)
    return {"value": None, "status": "ERR:"+err}

def years():
    return [("2015-01-01","2015-12-31"),("2016-01-01","2016-12-31"),("2017-01-01","2017-12-31"),
            ("2018-01-01","2018-12-31"),("2019-01-01","2019-12-31"),("2020-01-01","2020-12-31"),
            ("2021-01-01","2021-12-31"),("2022-01-01","2022-12-31"),("2023-01-01","2023-12-31"),
            ("2024-01-01","2024-12-31"),("2025-01-01","2025-12-31"),("2026-01-01","2026-09-17")]

QUERIES = [
    ('"artificial intelligence"', "10-K"),
    ('"artificial intelligence"', "8-K"),
    ('"generative artificial intelligence"', "10-K"),
    ('"machine learning"', "10-K"),
    ('"artificial intelligence bubble"', "10-K"),
    ('bubble', "10-K"),
]

out = {}
try:
    out = json.load(open("census.json"))
except Exception:
    pass

for q, form in QUERIES:
    key = q + "|" + form
    out.setdefault(key, {})
    for s, e in years():
        y = s[:4]
        if y in out[key] and out[key][y].get("value") is not None:
            continue
        r = count(q, form, s, e)
        r["range"] = [s, e]
        out[key][y] = r
        print(key, y, r["value"], r.get("relation"), r["status"], flush=True)
        json.dump(out, open("census.json","w"), indent=1)
        time.sleep(0.6)
print("DONE")
