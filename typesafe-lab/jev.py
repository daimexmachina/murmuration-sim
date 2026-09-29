#!/usr/bin/env python3
"""jev.py - minimal CLI for TypeSafe System One (Jev): typed judgments from text.

Ask one or more questions about one piece of state and print typed answers.

Usage:
  python3 jev.py --demo
  python3 jev.py --state-file ticket.txt --noul "Is this urgent?" \
      --choice "Which team?" billing=Payment issues technical=Bugs sales=Pricing \
      --score "Frustration" calm:Calm "civil":Frustrated but civil angry:Very angry
  python3 jev.py --state '{"message":"..."}' --noul "Is this urgent?" --json

Key resolution: $TYPESAFE_API_KEY, else TYPESAFE_API_KEY= line in ~/.hermes/.env.
The value is never printed, logged, or passed on a command line.

Exit codes: 0 ok, 2 no key, 3 API/transport error, 4 bad usage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
ENV_FILE = os.path.expanduser("~/.hermes/.env")
TIMEOUT = 60


def load_key() -> str | None:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(ENV_FILE, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("TYPESAFE_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        return None
    return None


def build_questions(args) -> dict:
    q: dict = {}
    for i, instr in enumerate(args.noul or []):
        q[f"noul_{i}"] = {"type": "noul", "instructions": instr}
    for i, spec in enumerate(args.choice or []):
        instr, _, opts = spec.partition("|")
        criteria = {}
        for pair in opts.split(","):
            pair = pair.strip()
            if not pair:
                continue
            k, _, v = pair.partition("=")
            criteria[k.strip()] = v.strip() or None
        if not criteria:
            sys.exit("choice needs criteria as key=description,comma,separated")
        q[f"choice_{i}"] = {"type": "choice", "instructions": instr.strip(), "criteria": criteria}
    for i, spec in enumerate(args.score or []):
        instr, _, levels = spec.partition("|")
        criteria = [lv.strip() for lv in levels.split(",") if lv.strip()]
        if len(criteria) < 2:
            sys.exit("score needs 2+ levels, comma separated")
        q[f"score_{i}"] = {"type": "score", "instructions": instr.strip(), "criteria": criteria}
    return q


def call(state, questions, model=DEFAULT_MODEL, key=None):
    key = key or load_key()
    if not key:
        print(f"No TYPESAFE_API_KEY found (looked at $TYPESAFE_API_KEY and {ENV_FILE}).", file=sys.stderr)
        sys.exit(2)
    body = {"state": state, "model": model, "questions": questions}
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        print(f"API error HTTP {exc.code}: {detail}", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:  # transport / decode
        print(f"Request failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(3)


def fmt(label: str, ans: dict) -> str:
    """Render one typed answer, including the uncertainty that code should gate on."""
    kind = ans.get("type")
    lines = [f"  {label}:"]
    if kind == "noul":
        p = ans.get("noul")
        lines.append(f"    probability(yes) = {p}   -> {'YES' if (p or 0) >= 0.5 else 'NO'}")
        if p is not None and 0.4 <= p <= 0.6:
            lines.append("    (near 0.5: similar probability for yes and no, not 'medium intensity')")
    elif kind == "choice":
        lines.append(f"    choice      = {ans.get('choice')}")
        lines.append(f"    confidence  = {ans.get('confidence')}")
        probs = ans.get("probabilities") or {}
        for opt, pr in sorted(probs.items(), key=lambda kv: kv[1], reverse=True):
            lines.append(f"      {opt:<16} {pr}")
    elif kind == "score":
        lines.append(f"    score       = {ans.get('score')}")
        lines.append(f"    confidence  = {ans.get('confidence')}")
        legend = ans.get("legend") or {}
        probs = ans.get("probabilities") or {}
        for lvl, pr in sorted(probs.items(), key=lambda kv: str(kv[0])):
            desc = legend.get(str(lvl), "")
            lines.append(f"      {lvl}: {desc:<32} {pr}")
    else:
        lines.append(f"    {json.dumps(ans)}")
    return "\n".join(lines)


DEMO_STATE = {
    "ticket": {
        "subject": "Duplicate charge",
        "messages": [
            {"from": "customer", "text": "I've been charged twice for order A-104 and nobody has replied in 3 days. I'm losing sales. Please fix this ASAP."},
            {"from": "support", "text": "We are checking the charges."},
        ],
    },
    "order": {"id": "A-104", "charges": [{"amount_usd": 49, "status": "captured"}, {"amount_usd": 49, "status": "captured"}]},
    "refund_policy": "Duplicate charges are eligible for a refund.",
}

DEMO_QUESTIONS = {
    "is_billing": {"type": "noul", "instructions": "Is this ticket about billing or payment?"},
    "duplicate_confirmed": {"type": "noul", "instructions": "Do the order records confirm a duplicate charge for order A-104?"},
    "department": {
        "type": "choice",
        "instructions": "Which team should handle this ticket?",
        "criteria": {"billing": "Payment or subscription issues", "technical": "Bugs or integration problems", "sales": "Pricing or account questions"},
    },
    "frustration": {
        "type": "score",
        "instructions": "How frustrated does the customer appear?",
        "criteria": ["Calm, just stating facts", "Frustrated but civil", "Very angry, strong language"],
    },
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Ask Jev (TypeSafe System One) typed questions about a piece of state.")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--state", help="state as a literal string or JSON object/array")
    src.add_argument("--state-file", help="path to a file containing the state (JSON if it parses, else plain text)")
    src.add_argument("--demo", action="store_true", help="run the built-in duplicate-charge example")
    ap.add_argument("--noul", action="append", metavar="INSTRUCTION", help="yes/no question (repeatable)")
    ap.add_argument("--choice", action="append", metavar="INSTR|k=desc,k=desc", help="select one option (repeatable)")
    ap.add_argument("--score", action="append", metavar="INSTR|level,level", help="grade along ordered levels (repeatable)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--json", action="store_true", help="print the raw API response")
    args = ap.parse_args()

    if args.demo:
        state, questions = DEMO_STATE, DEMO_QUESTIONS
    else:
        questions = build_questions(args)
        if not questions:
            sys.exit("no questions: pass --noul, --choice and/or --score (or --demo)")
        if args.state_file:
            raw = open(args.state_file, encoding="utf-8").read()
            try:
                state = json.loads(raw)
            except json.JSONDecodeError:
                state = raw
        elif args.state:
            try:
                state = json.loads(args.state)
            except json.JSONDecodeError:
                state = args.state
        else:
            state = sys.stdin.read()
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                pass

    resp = call(state, questions, model=args.model)
    if args.json:
        print(json.dumps(resp, indent=2))
        return
    print(f"model: {resp.get('model')}")
    for label, ans in (resp.get("answers") or {}).items():
        print(fmt(label, ans))
    usage = resp.get("usage") or {}
    print(f"\nusage: in={usage.get('input_tokens')} out={usage.get('output_tokens')}")


if __name__ == "__main__":
    main()
