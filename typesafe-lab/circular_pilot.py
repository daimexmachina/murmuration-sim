#!/usr/bin/env python3
"""circular_pilot.py - measure Jev against ground truth that already exists.

THE TEST CASE. bubble-watch's circular-financing rubric (src/circular_rubric.rs) contains 23
edges that a human READ AND CLASSIFIED from primary filings, each with a citation, a magnitude,
and a falsifier. Those are labels. Jev's job is to classify the same passages into the same
structure classes - including the hard negatives (`Refuted`: Oracle's OpenAI hits turned out to
be a model-integration list).

WHY THIS IS THE RIGHT TEST. The rubric states 47 real ecosystem edges exist and only 23 are read;
unread edges score ZERO, biasing the composite toward CALM. Reading is the bottleneck. So the
useful question is not "can Jev chat about finance" but "can Jev triage which passages deserve a
human read, and does its confidence tell us when it is out of its depth".

WHAT IT MEASURES.
  * choice accuracy vs the human labels;
  * the refutation test: does `is_financing` separate real structures from hard negatives?
  * calibration: do the wrong answers carry low confidence? (gating only works if they do)

HONEST LIMITS, printed at the end. n=23, one run, and ground truth comes from the same project
being piloted - so this is a pilot, not a validation.

Run:  python3 circular_pilot.py            # full run
      python3 circular_pilot.py --dry      # show extracted text only, no API calls
"""
from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, ".")
from jev import call  # noqa: E402

RUBRIC = "/home/daim/workspace/bubble-watch/src/circular_rubric.rs"


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def parse_entries() -> tuple[list[dict], dict[str, str]]:
    src = open(RUBRIC, encoding="utf-8").read()

    # Class descriptions come from the project's OWN doc comments on the enum, so the
    # criteria are the project's definitions rather than my paraphrase.
    enum_src = re.search(r"pub enum Structure \{(.*?)\n\}", src, re.S).group(1)
    classes, last_doc = {}, []
    for line in enum_src.splitlines():
        s = line.strip()
        if s.startswith("///"):
            last_doc.append(s[3:].strip())
        elif s and not s.startswith("#") and not s.startswith("//"):
            variant = s.split(",")[0].strip()
            if re.fullmatch(r"[A-Za-z]+", variant) and last_doc:
                # first sentence of the doc comment
                text = " ".join(last_doc)
                first = re.split(r"(?<=[a-z.)])\s+(?=[A-Z])", text)[0]
                classes[variant] = first.strip()
            last_doc = []

    body = re.search(r"const VERIFIED[^=]*=\s*&?\[(.*?)\n\];", src, re.S).group(1)
    entries = []
    for chunk in re.split(r"VerifiedEdge\s*\{", body)[1:]:
        rec = {}
        for field in ("filer", "counterparty", "structure", "scale", "citation", "magnitude", "falsifier", "verbatim"):
            m = re.search(rf"\b{field}:\s*(.+?)(?=\n\s{{8,}}[a-z_]+:\s|\n\s{{4}}\}}\s*,?\s*\n|\Z)", chunk, re.S)
            if not m:
                continue
            # join the Rust string literal(s), undoing line-continuations
            parts = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1), re.S)
            text = " ".join(parts) if len(parts) > 1 else (parts[0] if parts else "")
            # undo Rust string line-continuations and escaped quotes left by the literal join
            text = text.replace("\\\n", " ")
            text = text.replace('\\"', '"').replace("\\'", "'")
            text = re.sub(r"\\\s+", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if field == "structure":
                rec[field] = m.group(1).split("::")[-1].strip().rstrip(",")
            else:
                rec[field] = text
        if rec.get("structure"):
            # label this project uses
            rec["label"] = snake(rec["structure"])
            # the passage Jev gets: verbatim text when read word-for-word, else the
            # quoted material carried in the citation + magnitude.
            passage = rec.get("verbatim") or ""
            if len(passage) < 120:
                quoted = re.findall(r'"([^"]{25,})"', rec.get("citation", "") + " " + rec.get("magnitude", ""))
                passage = (passage + " " + " ".join(quoted)).strip()
            rec["passage"] = passage or rec.get("citation", "")
            entries.append(rec)
    return entries, classes


CRITERIA_EXTRA = {
    "refuted": "Read and found NOT to be a financing relationship — e.g. a model-integration or vendor list, marketing, self-reference, or an unrelated mention",
    "unsigned_supply_relationship": "A real, material, UNFINANCED supply commitment — a plain commercial relationship with no stake, facility or guarantee",
}


def main() -> None:
    entries, classes = parse_entries()
    dry = "--dry" in sys.argv

    print(f"parsed {len(entries)} labeled edges; {len(classes)} structure classes from the enum\n")
    from collections import Counter
    print("ground-truth label distribution:")
    for k, v in Counter(e["label"] for e in entries).most_common():
        print(f"  {v:>2}  {k}")
    print()

    if dry:
        for e in entries[:3]:
            print(f"--- {e['filer']} x {e['counterparty']} [{e['label']}] ---")
            print(f"  passage ({len(e['passage'])} ch): {e['passage'][:400]}\n")
        return

    criteria = {snake(k): v for k, v in classes.items()}
    criteria.update(CRITERIA_EXTRA)

    results = []
    for i, e in enumerate(entries, 1):
        state = {
            "filer": e["filer"],
            "counterparty": e["counterparty"],
            "passage": e["passage"],
        }
        questions = {
            "is_financing": {
                "type": "noul",
                "instructions": "Does this passage describe a vendor/circular FINANCING structure — where a company funds, guarantees, lends to, invests in, or is financially entangled with its own customer or supplier — as opposed to a plain commercial, marketing or unrelated relationship?",
            },
            "structure": {
                "type": "choice",
                "instructions": "Which structure class does this passage describe?",
                "criteria": criteria,
            },
        }
        ans = call(state, questions)["answers"]
        pred = ans["structure"]["choice"]
        rec = {
            "filer": e["filer"], "counterparty": e["counterparty"],
            "gold": e["label"], "pred": pred,
            "conf": ans["structure"]["confidence"],
            "financing_p": ans["is_financing"]["noul"],
            "correct": pred == e["label"],
        }
        results.append(rec)
        mark = "ok " if rec["correct"] else "MISS"
        print(f"[{i:>2}/{len(entries)}] {mark} gold={rec['gold']:<38} pred={pred:<38} conf={rec['conf']:.2f} fin={rec['financing_p']:.2f}")

    # ---- scoring ----
    n = len(results)
    correct = sum(r["correct"] for r in results)
    print(f"\n=== choice accuracy: {correct}/{n} = {correct/n:.0%} ===")

    ref = [r for r in results if r["gold"] == "refuted"]
    real = [r for r in results if r["gold"] not in ("refuted", "unsigned_supply_relationship")]
    print(f"\n=== the hard-negative test (does `is_financing` separate them?) ===")
    if ref:
        print(f"  REFUTED edges (n={len(ref)}): financing_p = {[round(r['financing_p'],2) for r in ref]}")
    if real:
        print(f"  REAL edges    (n={len(real)}): financing_p = {[round(r['financing_p'],2) for r in real]}")
    if ref and real:
        import statistics
        mr, mf = statistics.mean(r["financing_p"] for r in real), statistics.mean(r["financing_p"] for r in ref)
        print(f"  mean real {mr:.2f} vs mean refuted {mf:.2f}  (separation {mr-mf:+.2f})")
        thr = (mr + mf) / 2
        tp = sum(r["financing_p"] >= thr for r in real)
        fp = sum(r["financing_p"] >= thr for r in ref)
        print(f"  at midpoint threshold {thr:.2f}: {tp}/{len(real)} real kept, {fp}/{len(ref)} refutations wrongly kept")

    print(f"\n=== calibration: do the misses carry low confidence? ===")
    ok = [r["conf"] for r in results if r["correct"]]
    bad = [r["conf"] for r in results if not r["correct"]]
    if ok:
        print(f"  correct: n={len(ok)} mean conf {sum(ok)/len(ok):.2f}  min {min(ok):.2f}")
    if bad:
        print(f"  WRONG  : n={len(bad)} mean conf {sum(bad)/len(bad):.2f}  min {min(bad):.2f}")
        print(f"  wrong answers at conf >= 0.7 (would pass a gate): {sum(c>=0.7 for c in bad)}/{len(bad)}")
    else:
        print("  no misses in this run")

    out = "/home/daim/workspace/typesafe-lab/circular_pilot_results.json"
    json.dump(results, open(out, "w"), indent=2)
    print(f"\nwrote {out}")
    print("\nLIMITS: n=23, single run (Jev is not deterministic), and the labels come from the")
    print("same project being piloted. Treat as a pilot, not a validation.")


if __name__ == "__main__":
    main()
