# typesafe-lab

Scratch harness for testing TypeSafe **System One** / **Jev** against real inputs.
Built 2026-09-28. The `typesafe-ai` skill (`~/.hermes/skills/typesafe-ai/`) is the
entry point; the live docs (https://docs.typesafe.ai/llms.txt) are the source of truth
and should be re-read before any real integration, because the API is versioned.

## What Jev is

Not a chat model. You send **state** (the material) plus **questions** (the judgments),
and get back typed answers with probabilities and confidence. Code owns the workflow;
Jev supplies programmable common sense. Three primitives:

| Primitive | Question shape | Answer |
| --- | --- | --- |
| `noul`   | yes/no ("Does this express urgency?") | `noul` = P(yes) |
| `choice` | one of a defined set | `choice`, per-option `probabilities`, `confidence` |
| `score`  | degree along ordered levels | `score` (probability-weighted position), `probabilities`, `confidence` |

Ask independent questions in **one** call — they run in parallel and cannot see each
other's answers. Response `model` was `jev-1.13.0` throughout.

## Setup

Key is in `~/.hermes/.env` as `TYPESAFE_API_KEY` (mode 600, gitignored, not tracked).
**Hermes exports `.env` into the agent environment**, so the SDK picks it up unprompted.
Outside an agent session, export it yourself. The value is never written into this repo.

```bash
# raw HTTP harness - no dependencies
python3 jev.py --demo
python3 jev.py --state-file ticket.json \
  --noul "Is this ticket about billing?" \
  --choice "Which team?|billing=Payment issues,technical=Bugs,sales=Pricing" \
  --score "Frustration|Calm,Frustrated but civil,Very angry"
echo "some text" | python3 jev.py --noul "Is this urgent?"
python3 jev.py --demo --json   # raw response

# official SDK (venv kept out of the workspace on purpose)
/home/daim/.hermes/venvs/typesafe-lab/bin/python sdk_smoke.py
```

## Demos

- `route_demo.py` — confidence-gated routing: answer says *what*, confidence says
  *whether to act*. Thresholds must be tuned on your own data.
- `ambiguity_demo.py` — the two traps below, empirically checked.

## Verified behaviour (2026-09-28, jev-1.13.0)

1. **The field is `instructions`, not `question`.** A wrong key name returns a JSON
   decode error, not a validation message.
2. **`score` is fractional** — a probability-weighted position (`0*0.00 + 1*0.98 + 2*0.02
   = 1.02`), not an integer index. Don't cast to int without thinking.
3. **Confidence does NOT detect an under-specified input.** "It doesn't work. Please help."
   returned `technical` at confidence **1.00** — a concentrated distribution over garbage.
   If you need to catch vagueness, ask a separate sufficiency Noul ("does this contain
   enough detail to choose a responsible team?"): it scored 0.05 there vs 0.81 on a clear
   ticket. This is the single most important trap here.
   *Caveat:* n=1, and per (6) runs vary. Re-measure on your own traffic before relying
   on it; the direction was clear (0.05 vs 0.81) but one sample is one sample.
4. **A Noul near 0.5 is undecidable, not "medium".** Jev does grade urgency across the
   range (0.07 … 0.98 observed), so the number is real signal — but in the ~0.35–0.65
   band it means it cannot separate yes from no. Read it as unknown and corroborate,
   or ask a Choice/Score when you need *degree*.
5. **A single-choice distribution is not a confidence measure of correctness.** Chosen
   option had 0.77/0.83 probability yet confidence 0.66/0.74 — confidence is spread
   across the option set, nothing more.
6. **Not deterministic run-to-run.** Identical input scored 0.64 then 0.65. Don't set a
   threshold exactly on an observed value; leave margin, and validate with repeated runs.
7. Mixing an obviously-easy set (see `route_demo.py`) will show 100% auto-route. That is
   a bad test set, not a working guardrail — deliberately include the hard cases.

## Next

Nothing here is wired into a real project yet. Candidates when it is: bubble-watch
item triage/reranking (the `rerank_typesafe` cookbook is the closest pattern) and the
bike-route legality checks (verification/citation pattern).
