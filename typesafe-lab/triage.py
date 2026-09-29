#!/usr/bin/env python3
"""triage.py - rank bubble-watch's unread circular-financing edges by whether they
deserve a human read.

THE PROBLEM. `bubble-watch circular` finds 67 disclosure edges across 20 filers, but the
rubric only carries 5 hand-read passages. Unread edges score ZERO, which biases the
composite toward CALM. Reading is the bottleneck, so the useful job is not "classify the
structure" (only a human reading the filing can do that) but "which of these 62 unread
edges should a human open first".

VALIDATION BUILT IN. The 5 edges already read by hand are a control set: a 10-K revenue
disclosure (MSFT x OpenAI), an 8-K warrant (AMD x OpenAI), a related-party purchase
(SPCX x Tesla), a merger with absorbed debt (SPCX x xAI), and one REFUTATION (ORCL x
OpenAI, where the name is only a model-integration list). A ranking that puts the
refutation at the top is worse than no ranking - it reproduces exactly the false positive
the project says keyword counting cannot avoid.

Usage:
  python3 triage.py --edges edges.json --limit 20            # rank top 20 edges by hits
  python3 triage.py --edges edges.json --limit 20 --csv out.csv
"""
from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, ".")
from jev import call  # noqa: E402

UA = "bubble-watch-triage/0.1 (research; contact: research@example.invalid)"
PAUSE = 0.25  # EDGAR allows ~10 req/s
WINDOW = 700  # chars either side of the name
MAX_DOC = 4_000_000

# The rubric's own exclusions: companies naming THEMSELVES.
SELF_MATCHES = {("CRWV", "CoreWeave"), ("NVDA", "NVIDIA")}


def fetch(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read(MAX_DOC)
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", "replace")
    except Exception as e:
        print(f"    fetch failed: {type(e).__name__} {e}", file=sys.stderr)
        return None


def search_filings(cik: str, name: str, start: str, end: str) -> list[dict]:
    """Return filing hits for this filer/counterparty pair (all three forms, like the scan)."""
    out = []
    for form in ("10-K", "8-K", "10-Q"):
        q = urllib.parse.quote(f'"{name}"')
        url = (f"https://efts.sec.gov/LATEST/search-index?q={q}&forms={form}"
               f"&dateRange=custom&startdt={start}&enddt={end}&ciks={cik}")
        body = fetch(url)
        time.sleep(PAUSE)
        if not body:
            continue
        try:
            d = json.loads(body)
        except json.JSONDecodeError:
            continue
        for h in (d.get("hits", {}).get("hits") or []):
            src = h.get("_source", {})
            fid = h.get("_id") or h.get("id") or ""
            if ":" not in fid:
                continue
            adsh, doc = fid.split(":", 1)
            out.append({
                "form": form,
                "date": src.get("file_date"),
                "adsh": adsh,
                "doc": doc,
                "cik_nolead": str(int(cik)),
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{adsh.replace('-', '')}/{doc}",
            })
        if out:
            break  # prefer the most specific form that answered
    return out


def strip_html(s: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip()


def passage_around(text: str, name: str) -> str:
    """The primary-source excerpt a human would read: text around the name mention."""
    hits = [m.start() for m in re.finditer(re.escape(name), text, re.I)]
    if not hits:
        return ""
    # a mention with finance-ish words nearby is more informative than the first one
    keys = ("invest", "equity", "warrant", "loan", "guarantee", "revenue", "related part",
            "commit", "convertible", "stake", "purchase", "agreement", "note")
    best, best_score = hits[0], -1
    for h in hits[:40]:
        seg = text[max(0, h - WINDOW): h + WINDOW].lower()
        score = sum(k in seg for k in keys)
        if score > best_score:
            best, best_score = h, score
    seg = text[max(0, best - WINDOW): best + WINDOW]
    return seg.strip()


QUESTIONS = {
    "looks_like_financing": {
        "type": "noul",
        "instructions": "Does this passage describe a FINANCIAL entanglement between the filer and the named counterparty — an investment, equity stake, warrant, loan, guarantee, revenue concentration, related-party transaction, or the filer funding/financing the counterparty — as opposed to a product mention, competitor comparison, marketing or model-integration list, or unrelated reference?",
    },
    "mention_kind": {
        "type": "choice",
        "instructions": "What is the nature of the named counterparty in this passage?",
        "criteria": {
            "financing_structure": "The filer invests in, funds, guarantees, lends to, or holds equity in the counterparty",
            "customer_concentration": "The counterparty is disclosed as a major customer or revenue source",
            "supply_agreement": "A supply, purchase or services agreement with stated commitments",
            "related_party_transaction": "A related-party transaction with a named magnitude",
            "absorbed_debt_or_merger": "The filer carries the counterparty's debt, or has merged with it",
            "product_or_model_mention": "A product, model or platform is named, not a business relationship",
            "competitor_or_marketing": "Competitive comparison, marketing, or a list of vendors",
            "self_reference": "The filer naming itself",
            "other_unrelated": "None of the above / incidental mention",
        },
    },
    "worth_human_read": {
        "type": "noul",
        "instructions": "Would a financial analyst tracking circular-financing risk in AI capital expenditure want to read this disclosure in full?",
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", default="edges.json")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2026-09-20")
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    edges = json.load(open(args.edges))
    # CIKs per ticker, read from the project's own FILERS table
    src = open("/home/daim/workspace/bubble-watch/src/sources/circularity.rs", encoding="utf-8").read()
    cikblock = src[src.index("const FILERS"):]
    ciks = dict(re.findall(r'\(\s*"([A-Z]+)",\s*"(\d+)"', cikblock, re.S))

    cand = [e for e in edges if (e["filer"], e["counterparty"]) not in SELF_MATCHES]
    cand.sort(key=lambda e: -e["hits"])
    sample = cand[: args.limit]
    # Always include the 5 hand-read edges so the ranking has a control set in it.
    controls = {("MSFT", "OpenAI"), ("AMD", "OpenAI"), ("SPCX", "Tesla"),
                ("SPCX", "xAI"), ("ORCL", "OpenAI")}
    have = {(e["filer"], e["counterparty"]) for e in sample}
    for e in cand:
        if (e["filer"], e["counterparty"]) in controls and (e["filer"], e["counterparty"]) not in have:
            sample.append(e)
    print(f"{len(edges)} edges; excluding {len(SELF_MATCHES)} self-matches -> {len(cand)} candidates; "
          f"triaging top {args.limit} by hit count + {len(controls)} hand-read controls "
          f"= {len(sample)} edges\n")

    rows = []
    for i, e in enumerate(sample, 1):
        filer, cp = e["filer"], e["counterparty"]
        print(f"[{i}/{len(sample)}] {filer} x {cp} (hits={e['hits']})")
        cik = ciks.get(filer)
        if not cik:
            print("    no CIK"); continue
        filings = search_filings(cik, cp, args.start, args.end)
        if not filings:
            print("    no filing located"); continue
        f = filings[0]
        doc = fetch(f["url"])
        time.sleep(PAUSE)
        if not doc:
            continue
        text = strip_html(doc)
        passage = passage_around(text, cp)
        if len(passage) < 80:
            print("    passage too short to judge")
            continue
        ans = call({"filer": filer, "counterparty": cp, "passage": passage}, QUESTIONS)["answers"]
        row = {
            "filer": filer, "counterparty": cp, "hits": e["hits"],
            "form": f["form"], "filing_date": f["date"], "url": f["url"],
            "passage_chars": len(passage),
            "financing_p": ans["looks_like_financing"]["noul"],
            "kind": ans["mention_kind"]["choice"],
            "kind_conf": ans["mention_kind"]["confidence"],
            "worth_read_p": ans["worth_human_read"]["noul"],
        }
        rows.append(row)
        print(f"    financing={row['financing_p']:.2f}  kind={row['kind']}  "
              f"worth_read={row['worth_read_p']:.2f}  [{f['form']} {f['date']}]")

    rows.sort(key=lambda r: -(r["financing_p"] * r["worth_read_p"]))
    print("\n=== TRIAGE RANKING (financing_p x worth_read_p) ===")
    print(f"{'RANK':<5}{'FILER':<7}{'COUNTERPARTY':<13}{'FIN':>6}{'READ':>6}  KIND")
    for n, r in enumerate(rows, 1):
        print(f"{n:<5}{r['filer']:<7}{r['counterparty']:<13}{r['financing_p']:>6.2f}"
              f"{r['worth_read_p']:>6.2f}  {r['kind']}")

    print("\n=== CONTROL: the 5 that WERE read by hand (must not sink) ===")
    for r in rows:
        if (r["filer"], r["counterparty"]) in {
            ("MSFT", "OpenAI"), ("AMD", "OpenAI"), ("SPCX", "Tesla"), ("SPCX", "xAI"), ("ORCL", "OpenAI"),
        }:
            tag = "REFUTATION - must rank LOW" if (r["filer"], r["counterparty"]) == ("ORCL", "OpenAI") else "real structure - must rank HIGH"
            print(f"  {r['filer']} x {r['counterparty']:<10} financing={r['financing_p']:.2f} "
                  f"worth_read={r['worth_read_p']:.2f} kind={r['kind']}   <-- {tag}")

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
