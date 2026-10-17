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

⚠ **I was wrong about why those entries missed — and the attempt to "fix" it failed, which is
the more useful finding.** I hypothesised that the CRWV/AMZN misses were caused by feeding Jev a
single `verbatim` disclosure while the human label rested on reading several excerpts together.
I rewrote the extractor to concatenate every excerpt each entry carries (`--enriched`), and
measured it:

| passage mode | accuracy | refutation separation | false-keeps @0.35 |
| --- | --- | --- | --- |
| `thin` — verbatim, else quoted spans (3 runs) | **19/23, 19/23, 19/23** | +0.58…+0.59 | 0/8 |
| `thin` — same code, re-measured | **18/23** | +0.61 | 0/8 |
| `enriched` — every excerpt concatenated | **17/23** | +0.62 | 0/8 |

Two conclusions, both against my hypothesis:

1. **Enriching the passage did not help.** It did not fix **any** of the 3 persistent misses
   (`CRWV x OpenAI`, `CRWV x MSFT`, `AMZN x OpenAI`), and it *broke* two entries that had been
   correct (`MSFT x OpenAI` → `supplier_guarantee_and_investment`; `NVDA x upstream supply chain`
   → `vendor_organised_third_party_capital`). Passage length does not predict correctness: mean
   655 ch when right, 700 ch when wrong. So the misses are a genuine classification disagreement
   over structure boundaries, not a passage-assembly artifact.
2. **Run-to-run variance is ±1 edge on n=23.** The identical `thin` code scored 19/23 on three
   consecutive runs and then **18/23**. So the 83% → 78% → 74% spread across all these runs is
   mostly noise, and it also means my earlier "3 of 4 misses are the benchmark's fault" claim was
   overstated — I asserted a mechanism I had not tested, and testing it refuted it.

**Therefore: treat this as ~78% ± 4% on n=23, single-shot.** The stable, reproducible result is
not the accuracy number — it is the **refutation separation** (+0.58…+0.62, 0/8 false-keeps in
every single run), which is what the triage actually uses.

Both modes remain runnable so the comparison is reproducible rather than asserted:
`python3 circular_pilot.py` (thin) / `python3 circular_pilot.py --enriched`.

**The useful reading at this stage:** Jev did not score these filings as a measurement — the
rubric keeps judgment out of the composite deliberately. But it is usable as a *triage* layer,
which is what the section below does with the real 67-edge scan and what now has a validated
control set.

⚠ **Cost:** ~2 API calls per edge in one request each; token usage was not tracked per edge in
this run. Measure real cost and latency before wiring it to 47+ edges.

## Edge triage against the real scan (`triage.py`) — the thing that gets used

Ran `bubble-watch circular --offline`: **67 edges across 20 filers, 0 failed queries**, all served
from the 889 cached search responses. Only **5** edges carry a hardcoded `verified_passage`, so
~62 are unread, and unread edges score ZERO (the rubric's own stated bias toward CALM).

`triage.py` closes that gap without classifying anything: for each edge it searches EDGAR
full-text for the filing behind the hit, **fetches the primary document** from
`sec.gov/Archives`, strips it to text, extracts a ~1,400-char window around the counterparty
mention, then asks Jev three things per edge — is this a financing entanglement, what kind, and
is it worth a human read. Real prose confirmed, e.g. NVDA FY2026 10-K: *"We are finalizing an
investment and partnership agreement with OpenAI."*

**Control validation** — the 5 hand-read edges were run through the pipeline as a blind check:

| edge | gold (human read) | Jev `financing_p` | rank |
| --- | --- | --- | --- |
| MSFT x OpenAI | real, ASC 850 revenue | 0.99 | 5/23 |
| AMD x OpenAI | real, warrant/8-K | 0.97 | 2/23 |
| SPCX x Tesla | real, related-party | 0.91 | 4/23 |
| SPCX x xAI | real, absorbed debt | 0.79 | 12/23 |
| **ORCL x OpenAI** | **REFUTATION** | **0.24** | **16/23** |

All four real structures land in the top 12; the refutation lands below **every** one of them
(separation +0.68). That is the specific false positive the project says keyword counting cannot
avoid — and the ranking did not reproduce it.

**Effect on the queue: 62 unread edges -> 12 above `financing_p` ≥ 0.8.**
At ≥0.5 it keeps 12 plus the same set; at ≥0.7, 12; at ≥0.8, 9. Use 0.8 as a starting cut.

⚠ **Rank, don't record.** `financing_p` is a usable *ranking* signal. The fine-grained `kind`
label is not: mean `kind_conf` across the top 12 was 0.71, as low as 0.22 (SPCX x xAI). Feed it
to a human as a reading order, never write `kind` down as a finding.

⚠ One suspicious result worth a human look: **INTC x NVIDIA scored 0.97 `financing_structure`** —
plausibly a misread (Intel naming NVIDIA as a competitor/customer), which is exactly the kind of
error the human read exists to catch. Verify that one first.

## Full sweep: all 64 edges, with cost measured (`--all`)

Ran the whole candidate set (`triage.py --all`, `triage_full.csv`). 64 of 65 judged — one edge
(`INTC x Tesla`) returned no locatable filing, which the tool reports rather than silently drops.

**Threshold ladder — what the human reading queue becomes:**

| cut | edges surviving | queue reduction |
| --- | --- | --- |
| `financing_p` ≥ 0.5 | 16/64 | 75% |
| ≥ 0.7 | 15/64 | 77% |
| **≥ 0.8** | **12/64** | **81%** |
| ≥ 0.9 | 10/64 | 84% |

Of the **59 edges nobody has ever read**, **9 score above 0.8** — that is the actual deliverable:
a 9-item reading list instead of a 62-item backlog. (The 0.8 tier is also where all four hand-read
real structures sit: 0.99, 0.97, 0.92, 0.78.)

**Control validation held on the full run** — real structures at ranks 4, 2, 3, 15; the ORCL
refutation at rank 23/64 with `financing_p` 0.25, below every one of them (separation +0.67).

**Measured cost, 64 edges:**

- **63,434 input / 10,176 output tokens total** — mean **991 in / 159 out per edge**
- **145 s** of Jev wall time (2.3 s/edge)
- EDGAR adds ~1.0 s/edge (3 full-text searches + 1 document fetch), not included above
- a nightly full sweep ≈ **23 M input tokens/year** — trivially affordable, and cheap enough
  that the binding constraint is the *human read*, not the API

**Where to spend the human attention** (rank order, all ≥0.8, never-read unless marked):

1. `CRWV x NVIDIA` 0.97 · 2. `AMD x OpenAI` 0.97 *(hand-read control)* · 3. `SPCX x Tesla` 0.92
*(control)* · 4. `MSFT x OpenAI` 0.99 *(control)* · 5. `SMCI x Crusoe` 0.94 · 6. `APLD x NVIDIA`
0.96 · 7. `INTC x NVIDIA` 0.97 · 8. `APLD x CoreWeave` 0.90 · 9. `AMZN x Anthropic` 0.98 ·
10. `CRWV x OpenAI` 0.83 · 11. `CRM x Anthropic` 0.93 · 12. `NVDA x OpenAI` 0.84

⚠ `INTC x NVIDIA` (rank 7) and `SMCI x Crusoe` / `CRM x Anthropic` are the untested ones; `INTC x
NVIDIA` is the least plausible of the twelve — Intel naming NVIDIA as competitor/customer would be
an ordinary mention, not a financing structure. Read that one first as a falsification test of the
whole ranking.

## v2 — after the passage-selector fix: what changed and what didn't

Re-ran the whole sweep with the fixed selector (`triage_full_v2.csv`, 65/65 edges — v2 also
located `INTC x Tesla`, which v1 could not).

**What didn't change:** the tier membership and the control separation are stable.

- `financing_p` identical on **28/64** edges; mean |Δ| **0.021**, max 0.24
- controls unmoved: MSFT×OpenAI 0.99, AMD×OpenAI 0.98, SPCX×Tesla 0.92, SPCX×xAI 0.77,
  **ORCL×OpenAI 0.25** (still below every real control)
- both previously mis-passaged edges held their scores (CRWV×NVIDIA 0.94, APLD×NVIDIA 0.97) —
  the fix corrected *which excerpt is shown*, not the judgment
- v1 ≥0.8 12/64 → v2 ≥0.8 **13/65**; ≥0.9 10 → 11

⚠ **What is NOT meaningful: the ordering inside the tier.** Nine edges sit between 0.90 and 0.99,
so ±0.02 of run-to-run noise reshuffles them — `APLD x CoreWeave` moved rank 8 → 1 and
`CRWV x NVIDIA` 1 → 7 while barely changing score. **Use the tier as a reading list, not the rank
order.** Reporting a "ranked 1st" here would be false precision, which is the same mistake as the
`noul`-as-strength reading earlier in this file.

**Measured cost, v2 (65 edges):** 74,834 in / 10,332 out tokens, 199 s (3 windows per edge instead
of 1, hence ~18% more input tokens than v1's 63,434). Still trivial at ~28 M in-tokens/year daily.

## Human adjudication of the ≥0.8 tier — I read every filing myself

The ranking is only worth anything if someone checks it, so I adjudicated all 9 never-read edges
at `financing_p` ≥ 0.8 against the primary filings.

**Result: 9/9 are real financing edges.** The ranking's precision on its own top tier is clean.

| edge | verdict | what the filing actually says |
| --- | --- | --- |
| `INTC x NVIDIA` | TRUE | "issue and sell **215 million shares** of our common stock to NVIDIA at $23.28/share … aggregate cash purchase price of **$5.0 billion**" (Sep 2025) |
| `SMCI x Crusoe` | TRUE | credit-agreement schedule: Supermicro holds **0.24% of Crusoe**, plus **4% / 13% of Lambda** Series C/D/E and a $12M Applied Digital SAFE |
| `CRM x Anthropic` | TRUE | `crm:AnthropicPBCMember` XBRL axis member + privately-held equity securities note |
| `APLD x CoreWeave` | TRUE | 15-yr lease, ~**$5.2 B** contracted revenue, high-investment-grade hyperscaler |
| `AMZN x Anthropic` | TRUE | nonvoting **preferred stock** in Anthropic + equity warrant valuations |
| `CRWV x OpenAI` | TRUE | credit-agreement definition of the Mar 2025 Master Services Agreement |
| `NVDA x OpenAI` | TRUE | "We are finalizing an **investment and partnership agreement with OpenAI**" |
| `CRWV x NVIDIA` | TRUE **(wrong passage)** | actually: "In January 2026, **NVIDIA Corporation invested $2 billion** in the Company's Class A common stock at $87.20/share" |
| `APLD x NVIDIA` | TRUE **(wrong passage)** | actually: NVIDIA was a **PIPE purchaser** in Applied Digital's Sep 2024 private placement of 49,382,720 shares at $3.24/share |

⚠ **The defect was passage selection, not ranking.** For 2 of 9 the tool found the right edge but
handed the human the wrong excerpt — `CRWV x NVIDIA`'s crop showed a revenue-by-geography table
merely because an unrelated "NVIDIA" mention sat near it. That is precisely the keyword-counting
failure mode this project criticises elsewhere, reproduced inside my own selector.

**Fixed** in `triage.py::passage_around`: windows are now scored by proximity to a *financial verb
or the disclosure's own heading* (weighted 3×) above generic finance words, and the top **3
non-overlapping** windows are returned joined, so the human sees the evidence instead of one
lucky/unlucky crop. Verified against both problem edges without spending an API call.

⚠ **Two confident predictions of mine were wrong here** — I expected `INTC x NVIDIA` to be a
misread, and when I first read it I concluded the opposite in the wrong direction again. Both
times the filing settled it. Worth noting because this thread has three separate cases now where I
asserted a mechanism before testing it and was wrong (the `noul` strength reading, the 83% miss
explanation, and this).

## Next

Done in this lab. Remaining if it goes further: wire the 9-item list into the bubble-watch run as
a *reading queue* (never into the composite — the rubric's own rule), and re-triage on a schedule
now that the cost is known.
