#!/usr/bin/env python3
"""PH Archive dependency-free daily metadata collection (not full news articles).

Runs in GitHub Actions using the public PH Archive RSS feed aggregator.
Preserves versioned daily snapshots, normalized publisher URLs and pending-review
status. Does not independently establish allegations, findings or convictions.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, urlopen

AGGREGATOR = "https://ph-archive-feed.vercel.app/api/news"
ALLOWED = {
    "gmanetwork.com": "GMA News",
    "philstar.com": "The Philippine Star",
    "rappler.com": "Rappler",
    "inquirer.net": "INQUIRER.net",
}

def canonical(raw):
    try:
        u = urlsplit(str(raw or ""))
        if u.scheme not in {"https", "http"} or not u.hostname or u.username or u.password:
            return None
        if u.port not in {None, 80, 443}:
            return None
        host = u.hostname.lower().removeprefix("www.")
        if host not in ALLOWED and not any(host.endswith("." + s) for s in ALLOWED):
            return None
        params = [(k,v) for k,v in parse_qsl(u.query, keep_blank_values=True)
                  if not (k.lower().startswith("utm_") or k.lower() in {"fbclid","gclid","_ga"})]
        return urlunsplit(("https",host,u.path.rstrip("/") or "/",urlencode(params),""))
    except (TypeError,ValueError):
        return None

def normalized(item):
    url=canonical(item.get("originalUrl"))
    if not url:
        return None
    host=urlsplit(url).hostname
    publisher=ALLOWED.get(host) or next((v for d,v in ALLOWED.items() if host.endswith("."+d)), None)
    if publisher != item.get("sourceName"):
        return None
    title=str(item.get("title") or "").strip()[:290]
    if not title:
        return None
    try:
        when=datetime.fromisoformat(str(item.get("dateISO","")).replace("Z","+00:00"))
        if when.tzinfo is None:
            when=when.replace(tzinfo=timezone.utc)
        when=when.astimezone(timezone.utc)
    except ValueError:
        return None
    if not 1980 <= when.year <= 2100:
        return None
    officials=item.get("officials") if isinstance(item.get("officials"),list) else []
    tags=item.get("tags") if isinstance(item.get("tags"),list) else []
    if not officials and not tags:
        return None  # Exclude feed matches with no government-related tagging
    return {
        "id":hashlib.sha256(url.encode()).hexdigest()[:24],
        "originalUrl":url,"sourceName":publisher,"title":title,
        "dateISO":when.isoformat().replace("+00:00","Z"),
        "summary":str(item.get("summary") or "").strip()[:320],
        "officials":[str(s)[:100] for s in officials[:12] if isinstance(s,str)],
        "tags":[str(s)[:100] for s in tags[:10] if isinstance(s,str)],
        "editorialStatus":"pending","sourceType":"publisher-rss-metadata"
    }

def collect(payload,root,day):
    if not isinstance(payload,dict) or not isinstance(payload.get("entries"),list):
        raise ValueError("Expected entries[] JSON from PH Archive aggregator")
    parsed=[normalized(x) for x in payload["entries"] if isinstance(x,dict)]
    items=sorted({r["originalUrl"]:r for r in parsed if r}.values(),key=lambda r:r["originalUrl"])
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    index_path=root/"index.json"
    digest=hashlib.sha256(json.dumps(items,ensure_ascii=False,sort_keys=True).encode("utf8")).hexdigest()[:12]
    snapshot_path=root/"snapshots"/f"{day}-{digest}.json"
    data=json.loads(index_path.read_text(encoding="utf8")) if index_path.exists() else {"schemaVersion":2,"byUrl":{}}
    before=len(data["byUrl"])
    changed=0
    for rec in items:
        old=data["byUrl"].get(rec["originalUrl"])
        if old is not None:
            if any(old.get(k)!=rec[k] for k in ["title","summary","officials","tags","dateISO"]):
                rec["firstCapturedAt"]=old.get("firstCapturedAt",day)
                rec["editorialStatus"]="pending"
                data["byUrl"][rec["originalUrl"]]=rec
                changed+=1
        else:
            rec["firstCapturedAt"]=day
            data["byUrl"][rec["originalUrl"]]=rec
    data["schemaVersion"]=2
    output=json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    if not index_path.exists() or index_path.read_text(encoding="utf8")!=output:
        index_path.write_text(output,encoding="utf8")
    if items and not snapshot_path.exists():
        snapshot_path.parent.mkdir(parents=True,exist_ok=True)
        snapshot_path.write_text(json.dumps({
            "capturedOn":day,
            "source":"PH Archive public multi-publisher feed",
            "reviewStatus":"pending",
            "records":items
        },indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf8")
    return {"discovered":len(items),"new":len(data["byUrl"])-before,
            "changed":changed,"total":len(data["byUrl"]),"snapshotPath":str(snapshot_path)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",help="Optional local JSON response for offline testing")
    parser.add_argument("--root",default="data")
    parser.add_argument("--day",default=datetime.now(timezone.utc).date().isoformat())
    args=parser.parse_args()
    if args.input:
        payload=json.loads(Path(args.input).read_text(encoding="utf8"))
    else:
        req=Request(AGGREGATOR,headers={"User-Agent":"PHArchiveCollector/0.8 (+https://ph-archive-public.vercel.app/)"})
        with urlopen(req,timeout=30) as response:
            if response.status!=200:
                raise RuntimeError("Feed API unavailable: "+str(response.status))
            body=response.read(2_000_001)
            if len(body)>2_000_000:
                raise ValueError("Feed exceeds 2MB")
            payload=json.loads(body)
    print(json.dumps(collect(payload,args.root,args.day),indent=2))

if __name__=="__main__":
    main()
