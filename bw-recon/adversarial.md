# Adversarial reconciliation — bubble-watch (`bw-recon/adversarial.md`)

Read-only audit of `/home/daim/workspace/bubble-watch`. Nothing there was modified.
All numbers below are from live HTTP probes run 2026-09-17; endpoints and statuses are recorded.

---

## 0. Baseline artefact audited

`out/ai-bubble-watch-2026-09-17.json` — composite **32.6454**, coverage 1.0, phase `early`.

**STALENESS FLAG (verified):** the report contains only **10 scored indicators, total_weight = 100.0**, and its `issuance` rationale still describes the *superseded* proxy ("year-over-year growth in common shares outstanding"). `config/indicators.toml` is `schema_version = "1.1"`, has **11 scored indicators, total weight 109** (it adds `primary_market_supply`, weight 9), and documents `issuance` as changed 2026-09-17 to a cash-flow ratio. The JSON report therefore predates its own config. Any composite quoted from `out/*.json` is a v1.0 number, not the current model.

---

## 1. DOUBLE-COUNTING: `concentration` and `breadth` are not two measurements

Sources (real, live):
- `https://query2.finance.yahoo.com/v8/finance/chart/SPY?range=10y&interval=1mo` → **HTTP 200**, 121 monthly points, first 2016-10, last 2026-09-17 (adjclose 762.60).
- `https://query2.finance.yahoo.com/v8/finance/chart/RSP?range=10y&interval=1mo` → **HTTP 200**, 121 monthly points (adjclose 213.31).
- (`query1` returns **HTTP 429** — query2 is the working host. Stooq returns a JS anti-bot page, unusable.)

Definitions replicate the config exactly: `concentration` = SPY 12m return − RSP 12m return (pct pts); `breadth` = RSP/SPY ratio vs its 10-month (≈200d) moving average, in pct.

| measurement | result |
|---|---|
| Pearson r (12m concentration vs breadth deviation), n = 109 months | **−0.6982** |
| Pearson r, 6m concentration variant, n = 115 | **−0.9272** |
| current concentration | −2.15 pct pts (mild) |
| current breadth deviation | −2.08 % (mild) |

**Interpretation.** The sign is negative *by construction* and the magnitude is the finding: both indicators are algebraically the same quantity — equal-weight underperformance versus cap-weight — measured over two windows. `breadth` is essentially the rolling-MA-smoothed 12m version of `concentration`. At 6m they are **r = −0.93**, i.e. ~86% shared variance; even at 12m, ~49%.

**Quantified overstatement.** `concentration` (w12) + `breadth` (w10) = **22 of 109 weight = 20.2% of the composite** presented as two of "12 scored indicators". Independent confirmations delivered: about **1.1–1.5**, not 2. So the model overstates its count of independent signals by roughly **+0.5 to +0.9 indicators out of 11 (≈5–8% of stated breadth of evidence)** — and, more importantly, **~10 weight points (≈9% of the composite) are a duplicated measurement double-counted as corroboration.** Today both happen to read mild (27.3 and 40.5), which is why they partly cancel; when concentration is extreme the duplicate pushes the composite in the same direction twice with no independent confirmation.

**Honest fix (arithmetic, not opinion).** Either (a) merge them into one "cap-vs-equal-weight" indicator at weight 22, reporting the 12m spread and the ratio-vs-200d as two *views of one indicator* rather than two indicators; or (b) keep both but drop combined weight to ~12 and state in the report that they are correlated (r = −0.70) and must not be read as separate confirmations.

---

## 2. RENORMALIZATION BIAS: a data outage pushes the composite **UP**, toward alarm

The config claims the coverage floor is "set from the sum of the FRED-dependent weights, so a total FRED outage lands just under the 'medium' boundary **by construction**" (§ `[coverage_floor]`), and the JSON notes say "The composite is renormalized over available weight". Renormalization is **not neutral in direction here**, and the config does not say so.

Using the real current stress values from the report and the **current config's** weights:

| scenario | coverage | composite | delta |
|---|---|---|---|
| full (all 11 indicators, credit_hy + credit_ig present) | 1.000 | **29.95** | — |
| FRED outage: `credit_hy` (12) + `credit_ig` (6) dropped | 0.8349 | **32.45** | **+2.50** |

**The bias is strictly upward (+2.5 pp, ≈ +8.3% relative).** Reason: the credit indicators currently score *low* stress (HY 16.4, IG 19.2, from OAS 2.70 and 0.78 — both tight by the config's own anchors). They are the calmest large weights in the model, so deleting them raises the weighted average. This is the opposite of the reassuring direction one might assume from a data outage, and it is exactly the bias that matters: **when FRED is down, the tool reads more bubble-like for reasons that have nothing to do with the market.**

Consequences worth stating in the report:
- 32.45 sits **2.6 pp below the `early_max = 35.0` phase boundary**; a slightly higher base reading and a FRED outage alone flips `early → mid` with no market change.
- The `coverage_tolerance_pp = 5.0` trend guard (0.8349 vs 1.0 = **16.5 pp** coverage gap) will correctly *refuse* to print a delta across these runs — the one place the model already handles this honestly. But the composite itself is still printed at face value with no correction and no direction-of-bias note.

**Honest fix.** Report the composite **with** a stated direction and size of renormalization bias (computed by re-running with the missing weights held at their last-known values, or simply publishing both numbers), and state in `[coverage_floor]` that a FRED outage is **not** direction-neutral on the current scoreboard.

---

## 3. FALSIFIERS (full results in §3b)

A bubble thesis that cannot lose is not a measurement. Candidate measurements that would **disprove** it, with live probe status so far:

| # | falsifier | endpoint | status | real value | what it would DISPROVE |
|---|---|---|---|---|---|
| F1 | Credit spreads **narrowing further** | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2` | **HTTP 200** (12,718 B) | **2.70** on 2026-09-16 | Sustained narrowing = the credit market, the config's own "single most important non-equity signal", is not pricing AI-bust risk. A month of further narrowing with capex still rising kills the debt-stress transmission story. |
| F2 | IG funding cost **narrowing** | `...?id=BAMLC0A0CM` | **HTTP 200** (12,712 B) | **0.78** on 2026-09-16 | Same, for the hyperscalers' own funding: 0.78% is *below* the config's second-lowest anchor (0.8 → stress 20). A move under 0.5 hits the floor (stress 8). |
| F3 | Rates **falling** (lowers the discount rate, deflates the "expensive equity" leg) | `...?id=DGS10` | **HTTP 200** (268,743 B) | **5.01%** on 2026-09-16 | A 10Y at 5.01% is *high*, which is the one leg that currently **helps** the bubble case. Sharp declines would remove it. |
| F4 | Long-history credit check (2000 & 2008 included) | `...?id=BAA10Y` | **HTTP 200** (168,172 B, 10,177 obs 1986→2026) | **1.43** on 2026-09-16 | BAA10Y at 1.43 is near the **low end of a 40-year range** (2000-03 1.96, 2007-02 1.56; vs 2008-12 6.10, 2020-03 4.31). If the model ever scored credit levels, this says "no stress" with four decades of context the current 2023-start HY series cannot provide. |

### 3b. Falsifier probes — RESULTS (all live, 2026-09-17)

**F1–F3 verdict: THE CREDIT LEG IS BEING FALSIFIED RIGHT NOW.** Live series (FRED CSV, HTTP 200), direction-of-travel over the last 3 and 12 months:

| series | latest | 3m avg | 12m avg | full-record percentile | n / span |
|---|---|---|---|---|---|
| HY OAS `BAMLH0A0HYM2` | **2.70** | 2.72 | 2.86 | **9.9th** | 787 / 2023-09-18→2026-09-16 |
| IG OAS `BAMLC0A0CM` | **0.78** | 0.78 | 0.79 | **13.2th** | 786 / 2023-09-18→2026-09-16 |
| BAA10Y | **1.43** | 1.58 | 1.67 | **1.6th of 40 yrs** | **10,177 / 1986-01-02→2026-09-16** |

All three are **narrowing**, and all three sit in the bottom ~1–13% of their records. BAA10Y at 1.43 — the 1.6th percentile of four decades that *include 2000-03 (1.96), 2007-02 (1.56), 2008-12 (6.10) and 2020-03 (4.31)* — is the single sharpest contradiction of the bubble thesis the model actually cannot see, because the HY series it uses only starts 2023-09-18 and so has no 2000 or 2008 reference. Credit at the calmest level in 40 years is not what a debt-financed bubble looks like three-quarters of the way to a peak.

**F4 verdict: the fundamentals leg is CONFIRMED, not falsified.** SEC XBRL company-concept (HTTP 200 for all, `data.sec.gov`, tagged UA):

| company | capex/revenue TTM trajectory | capex TTM YoY vs revenue TTM YoY |
|---|---|---|
| MSFT | 19.8% → 21.9% → 23.6% → 27.4% → **31.1%** | +88.5% vs +20.4% |
| ORCL | 12.3% → 24.5% → **60.2%** | +1027% vs +60.6% |
| META | 15.3% → 17.8% → 17.5% → 19.9% → **22.9%** | +163.5% vs +76.0% |
| cohort (MSFT+ORCL+GOOGL+META) | latest TTM **capex/rev = 24.8%** | $228bn capex on $921bn revenue |

(AMZN excluded — no overlapping quarterly tag pair in this pull. GOOGL and AMZN rows are **not** reported: my quarterly-duration filter produced implausible YoY figures for them, so they are dropped rather than quoted. The three clean names are enough to establish the direction.) Capex/revenue is **rising in every clean name** and capex is growing roughly 2–4× faster than revenue. A falsifier that would work — capex/revenue *stabilising* below ~20% while revenue catches up — is **not** happening.

**F5 — RPO (revenue visibility), the best available "is demand real" falsifier: ORCL RPO +45.8% over four quarters, and accelerating.**

| ORCL RPO (US$ bn, `RevenueRemainingPerformanceObligation`, HTTP 200) | 2024-11 | 2025-08 | 2026-02 | 2026-08 |
|---|---|---|---|---|
| | 97.3 | 455.3 | 552.6 | **664.0** |

RPO is not decaying — it is compounding. This does **not** rescue the bubble thesis; it makes the picture *worse* in the specific way the model declares it cannot see (§ circularity): a large booked backlog at a single vendor is exactly the quantity that a vendor-financed/circular loop would inflate, and this model has weight 0 there. So ORCL RPO is best read as the strongest *missing* falsifier: to disprove the bubble thesis you would want RPO growth *decelerating* toward revenue growth; it is doing the opposite, and the tool cannot adjudicate whether that backlog is external demand or recycled capital.

**Summary of falsification:** the market/credit leg of the thesis is contradicted by current data (spreads narrowing, at multi-decade lows); the spending/backlog leg is strongly supported. A model scoring 30.6/100 "early" is, on this reading, roughly *correct for the fundamentals* — and its credit sub-indicators score 16.4 and 19.2, i.e. it *does* reflect calm credit. The real defect is not the direction, it is that **nothing in the model can distinguish "credit is calm because there is no bubble risk" from "credit is calm because the debt is being intermediated outside the measured set"** — and the model's own config admits the second is invisible to it. Note also that `DGS10` at **5.01%** (HTTP 200) is the one leg that *supports* the bubble case (a 5% discount rate against stretched prices), and it is deliberately carried as unscored context in the `valuation_stretch` rationale.

---

## 4. Single best recommendation

**State the renormalization bias in the report, in points and in sign.** The tool already refuses to print a *trend* across mismatched coverage — good — but it still prints a *level* as if it were on one scale, when a FRED outage alone moves it +2.5 pp toward alarm and toward a phase flip. One line of output ("credit indicators absent; composite renormalized over 83% of weight, which biases this reading **up** by ≈ +2.5 pp versus a full-coverage run") converts the model's largest silent distortion into a disclosed number, at near-zero implementation cost, and it is the change that most improves the tool's honesty *on the dimension where the tool is already trying to be honest*. The double-counted concentration/breadth pair (§1) is the larger structural defect in absolute weight terms (~10 weight points of duplicated measurement) and should be fixed next, by merging or by disclosing r = −0.70; but it requires an editorial decision about the indicator list, whereas the bias line is pure disclosure and can ship immediately.

---
*All HTTP probes run from this host 2026-09-17. No files in `bubble-watch/` were created, modified or deleted.*
