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

## Measured pilot: circular-financing classification (`circular_pilot.py`)

The first **scored** test case, because bubble-watch already contains ground truth: 23 edges a
human read and classified from primary filings (`src/circular_rubric.rs`), each with citation,
magnitude and falsifier. Passages are extracted straight from that source (class criteria come
from the project's own enum doc comments, not my paraphrase).

| metric | run 1 | run 2 | run 3 |
| --- | --- | --- | --- |
| choice accuracy vs 23 human labels | 19/23 (83%) | 19/23 (83%) | 19/23 (83%) |
| mean `is_financing` on 14 real edges | 0.64 | 0.63 | 0.64 |
| mean `is_financing` on 8 refutations | 0.05 | 0.05 | 0.05 |
| false-keeps of refutations @ midpoint thr | 0/8 | 0/8 | 0/8 |
| wrong answers at confidence ≥ 0.7 | 3/4 | 3/4 | 3/4 |

**The separation is the real result.** Not one of the 8 hand-confirmed refutations (marketing,
model-integration lists, self-references) was kept as a financing structure, in any run. That is
the exact discrimination the project's author says keyword counting cannot do.

**All 4 misses were STABLE across runs** — same edges each time, so they are systematic:
`CRWV x OpenAI`, `CRWV x MSFT`, `AMZN x OpenAI` (all gold `vendor_financing_its_own_customer`),
and `ORCL x unnamed backlog counterparty` (gold `refuted`).

⚠ **Three of those four are probably label/passage conflicts, not model errors.** The extractor
takes `verbatim` when present, else the quoted fragments of `citation` + `magnitude`. For the
CRWV/AMZN entries the verbatim text is a single disclosure (a commitment, a revenue
concentration) while the human label rests on the *aggregate* reading — the project's own note
says the label comes from reading several passages together. Fed one passage in isolation, Jev
saw a supply commitment and said so, which is arguably correct. **Before citing 83% as Jev's
accuracy, fix the extraction so the model sees what the label was based on.** A benchmark whose
examples are mis-assembled measures the benchmark.

**The useful reading at this stage:** Jev did not score these filings as a measurement — the
rubric keeps judgment out of the composite deliberately. But it looks usable as a *triage* layer
for the 47-edge scan, where 24 edges are unread and every unread edge currently scores zero.

⚠ **Cost:** ~2 API calls per edge in one request each; token usage was not tracked per edge in
this run. Measure real cost and latency before wiring it to 47+ edges.

## Next

Nothing here is wired into a real project yet. The natural next step is fixing the passage
extraction above and re-measuring; after that, bubble-watch triage of the 24 unread edges.
