#!/usr/bin/env python3
"""ambiguity_demo.py - the two traps that bite in production, empirically checked.

Trap 1: confidence does NOT detect an under-specified input.
        A vague ticket still yields a concentrated distribution and
        confidence 1.00 - the model confidently picks *something*. You need a
        separate presence/sufficiency judgment to catch it.

Trap 2: a Noul near 0.5 is genuinely undecidable, not "medium".
        Jev does grade urgency across the range (~0.07 .. ~0.98 in testing),
        so the raw number is real signal - but in the 0.35-0.65 band the
        yes/no call is unreliable and should be corroborated or routed to review.

Run:  python3 ambiguity_demo.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, ".")
from jev import call  # noqa: E402

THRESHOLD = 0.7

TICKETS = {
    "mixed: billing vs technical": "I want to upgrade to Pro but the billing page errors out — is my card being declined or is the page broken?",
    "no information (vague)": "It doesn't work. Please help.",
    "clear (control)": "Please refund the duplicate $49 charge on order A-104.",
}

DEPT = {
    "type": "choice",
    "instructions": "Which team should handle this ticket?",
    "criteria": {
        "billing": "Payment, invoice, charge or subscription problems",
        "technical": "Bugs, errors, or integration problems",
        "sales": "Pricing, plans, quotes or account questions",
    },
}

# The separate judgment that catches what confidence cannot.
SUFFICIENT = {
    "type": "noul",
    "instructions": "Does this ticket contain enough specific detail to choose a responsible team for it?",
}

URGENCY = {"type": "noul", "instructions": "Does this message express urgency or time-sensitivity?"}


def main() -> None:
    print("=== Trap 1: confidence will not flag a vague ticket ===")
    print(f"(choice threshold = {THRESHOLD})\n")
    for label, text in TICKETS.items():
        ans = call(text, {"dept": DEPT, "enough": SUFFICIENT})["answers"]
        dept, conf, enough = ans["dept"], ans["dept"]["confidence"], ans["enough"]["noul"]
        by_conf = "AUTO-ROUTE" if conf >= THRESHOLD else "ESCALATE"
        by_suff = "OK" if enough >= 0.5 else "ESCALATE (insufficient detail)"
        print(f"  {label}")
        print(f"    chosen={dept['choice']:<10} confidence={conf:.2f} -> {by_conf}")
        print(f"    enough_detail={enough:.2f} -> {by_suff}")
        print(f"    verdict: {by_suff if enough < 0.5 else by_conf}\n")
    print("  Note the 'no information' row: confidence alone would auto-route")
    print("  garbage. The sufficiency Noul is what catches it.\n")

    print("=== Trap 2: where does urgency actually land? ===")
    samples = [
        "It'd be nice to have this sorted at some point, but no rush.",
        "Any update on my ticket?",
        "This is blocking our launch on Friday.",
    ]
    for text in samples:
        p = call(text, {"urgent": URGENCY})["answers"]["urgent"]["noul"]
        if abs(p - 0.5) < 0.15:
            note = "<== undecidable band: do not read as 'medium'"
        else:
            note = "clear call"
        print(f"    p={p:.2f}  {note}")
        print(f"          {text}")

    print("\n  Jev grades urgency across the range, so the number is real signal.")
    print("  But ~0.5 means the model cannot separate yes from no; treat it as")
    print("  'unknown' and corroborate (ask a Choice/Score for degree), rather")
    print("  than as 'moderately urgent'.")


if __name__ == "__main__":
    main()
