#!/usr/bin/env python3
"""route_demo.py - the pattern behind most useful Jev integrations.

Answer tells you WHAT; confidence tells you WHETHER TO ACT.
Code owns the workflow (thresholds, routing, escalation); Jev supplies the judgment.

Run:  python3 route_demo.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, ".")
from jev import call  # noqa: E402  (reads the key from ~/.hermes/.env)

# Deliberately includes one vague ticket: the interesting case is what happens
# when the model is NOT sure, not when it is.
TICKETS = [
    "I've been charged twice for order A-104 and nobody has replied in 3 days.",
    "The checkout button does nothing on Safari. Two customers complained this morning.",
    "Hi, quick question about my account.",
    "Does the Pro plan include API access, and what would 20 seats cost?",
]

QUESTIONS = {
    "department": {
        "type": "choice",
        "instructions": "Which team should handle this ticket?",
        "criteria": {
            "billing": "Payment, invoice, charge or subscription problems",
            "technical": "Bugs, errors, or integration problems",
            "sales": "Pricing, plans, quotes or account questions",
        },
    },
    "needs_reply_today": {
        "type": "noul",
        "instructions": "Does this ticket need a reply today rather than this week?",
    },
}

THRESHOLD = 0.7  # tune on YOUR data; 0.7 here is an example, not a rule


def main() -> None:
    routed, review = [], []
    for i, text in enumerate(TICKETS, 1):
        resp = call(text, QUESTIONS)
        ans = resp["answers"]
        dept, conf = ans["department"]["choice"], ans["department"]["confidence"]
        urgent = ans["needs_reply_today"]["noul"]
        usage = resp.get("usage") or {}

        if conf < THRESHOLD:
            review.append((i, dept, conf))
            action = f"-> HUMAN REVIEW (confidence {conf:.2f} < {THRESHOLD})"
        else:
            routed.append((dept, conf))
            action = f"-> {dept.upper()}" + (" [reply today]" if urgent >= 0.5 else "")

        print(f"[{i}] {text[:62]:<62}")
        print(f"    {dept} | confidence {conf:.2f} | urgent {urgent:.2f}  {action}")

    print("\n--- summary ---")
    print(f"auto-routed : {len(routed)}  {[d for d, _ in routed]}")
    print(f"to a person : {len(review)}  {[f'#{i} ({d}, {c:.2f})' for i, d, c in review]}")

    # The judgment is reusable data: changing the threshold or the display
    # needs no new inference call, because evidence and question meaning are unchanged.


if __name__ == "__main__":
    main()
