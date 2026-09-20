# RPO + Depreciation "Capital Subsidy" — Candidate Recon (COMPLETE)

Run: 2026-09-17. All values USD, pulled live from SEC XBRL `companyconcept` API.
Auth: requires a descriptive `User-Agent` header. No key. Cache-friendly (rate-limit ~10 req/s).

## Endpoints under test

| Purpose | Endpoint | Status |
|---|---|---|
| RPO series | `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/RevenueRemainingPerformanceObligation.json` | **HTTP 200** |
| Gross PP&E | `.../us-gaap/PropertyPlantAndEquipmentGross.json` | **HTTP 200** |
| Depreciation | `.../us-gaap/Depreciation.json` | **HTTP 200** |
| Cross-check | `.../us-gaap/ContractWithCustomerLiability.json` | **HTTP 200** |

Tag availability (404 = absent for that filer, do NOT retry as an error):
`DepreciationDepletionAndAmortization` -> 404 for ORCL/MSFT/GOOGL/META/AMZN.
`DepreciationAmortizationAndAccretionNet` -> 404 for all five.
`RevenueRemainingPerformanceObligation` -> **404 for META and AAPL** (they do not tag it).
=> `us-gaap:Depreciation` is the only workable depreciation tag in this cohort.

---

## FINDING 1 — RPO (us-gaap:RevenueRemainingPerformanceObligation)

### GOOGL full series (27 facts, all 10-K/10-Q, NO reporting gap)

| Period end | RPO | Form | | Period end | RPO | Form |
|---|---|---|---|---|---|---|
| 2019-12-31 | 11.4B | 10-K | | 2024-06-30 | 78.8B | 10-Q |
| 2020-12-31 | 29.8B | 10-K | | 2024-12-31 | 93.2B | 10-K |
| 2021-12-31 | 51.0B | 10-K | | 2025-03-31 | 92.4B | 10-Q |
| 2022-12-31 | 64.3B | 10-K | | 2025-06-30 | 108.2B | 10-Q |
| 2023-12-31 | 74.1B | 10-K | | 2025-09-30 | 157.7B | 10-Q |
| 2024-03-31 | 72.5B | 10-Q | | 2025-12-31 | 242.8B | 10-K |
| | | | | **2026-03-31** | **467.6B** | 10-Q `0001652044-26-000048` |
| | | | | 2026-06-30 | 519.5B | 10-Q `0001652044-26-000071` |

QoQ: +16.5% (Q3-25) -> +54% (Q4-25) -> **+92.6% (Q1-26)** -> +11.1% (Q2-26).

### Anomaly RESOLVED — real wins; the definition change is trivially small

GOOGL Q1-2026 10-Q, verbatim:

> "As of March 31, 2026, we had $467.6 billion of remaining performance obligations
> ("revenue backlog"), **of which $462.3 billion related to Google Cloud**. ... We expect to
> recognize just over 50% of the revenue backlog as revenues over the next 24 months ...
> Revenue backlog includes related deferred revenue currently recorded as well as amounts that
> will be invoiced in future periods and **excludes cancellable contracts** ...
> **In the first quarter of 2026, we elected to change our reporting of revenue backlog to now
> also include contracts with an original expected term of one year or less. As of
> March 31, 2026, the portion of our revenue backlog related to contracts with an original
> expected term of one year or less was approximately $7.3 billion.**"

**VERIFIED: the +$224.8B QoQ jump is REAL, not definitional.** The single definition change is
quantified by the company at **$7.3B = 1.6% of the balance, 3.2% of the move.** The other
~$217.5B is genuine backlog. Corroboration: **MSFT jumped independently in the same window**
(398B @2025-09-30 -> 631B @2025-12-31), so this is a sector-wide hyperscaler AI-compute
contracting wave, not one filer's accounting choice. RPO is tagged at 10-K AND 10-Q with no gap.

**The real risk is concentration, not definition.** $462.3B of $467.6B (**98.9%**) is Google
Cloud. GOOGL RPO is now a *single-segment* AI-compute bet: trustworthy as a series, treacherous
as a diversified-demand signal.

### RPO / trailing-twelve-month revenue (real ratios)

| Date | ORCL | MSFT | GOOGL |
|---|---|---|---|
| FY2017-18 | 0.83x | 0.59x | — |
| 2020-12-31 | 0.89x | 0.76x | 0.18x |
| 2022-12-31 | 1.37x | 0.95x | 0.24x |
| 2024-12-31 | 1.82x | 1.17x | 0.28x |
| 2025-06-30 | 2.52x | 1.40x | 0.31x |
| 2025-09-30 | **8.07x** | 1.41x | 0.46x |
| 2025-12-31 | 8.84x | **2.11x** | 0.71x |
| 2026-03-31 | 8.87x | 2.03x | **1.36x** |
| 2026-06-30 | **9.83x** | **2.19x** | **1.51x** |

ORCL 0.83x -> 9.83x (11.8x in 8y). MSFT 0.59x -> 2.19x (3.7x). GOOGL 0.18x -> 1.51x (8.4x).

### Is a rising RPO/revenue a bubble signal? — genuinely critical answer

**On its own, NO — and this indicator is mostly a Rorschach test.** Reasoning:

1. **RPO is a stock; revenue is a flow.** A rising ratio is arithmetically guaranteed whenever
   backlog grows faster than current recognition. Any company signing long-dated contracts shows
   this. A high ratio is equally consistent with (a) a healthy multi-year backlog, and
   (b) a vendor granting deep discounts for long commitments and financing customers' purchases.
   The ratio cannot distinguish them.
2. **A 20-year prepay is only worth face value if the counterparty survives and honors it.**
   None of these contracts are tagged with counterparty credit quality, cancellation economics,
   or termination-for-convenience clauses. `$664B of ORCL RPO` and `$664B of cash` are not the
   same asset and this metric will not tell you the difference.
3. **Hard falsification test — RPO vs cash actually collected.** If bookings are real, billings
   should follow into deferred revenue. They did not:

   | Company | 2025-12-31 RPO | Deferred revenue (total) | Ratio |
   |---|---|---|---|
   | ORCL | 523.3B | 11.2B | **47x** |
   | MSFT | 631.0B | 54.0B | 11.7x |
   | GOOGL | 242.8B | 8.6B | 28x |

   ORCL's deferred revenue is **9.9B @2026-05-31, 9.9B @2026-02-28, 9.9B @2025-11-30 — flat to
   the tenth of a billion while RPO went 97B -> 664B.** Cash collection did not track the backlog
   at all. That is the signature of non-cash consideration (prepaid GPU/cloud capacity the vendor
   itself funds) and/or non-standard contract terms — precisely the configuration that has
   historically preceded AI-capex write-downs. GOOGL's position is the *most* conservative of the
   three (deferred revenue rising 6.6 -> 10.1B, still growing, and ~50% of backlog recognisable
   within 24 months).

**Verdict:** usable as a *divergence/screening* indicator (flag when RPO/revenue inflects
violently OR when RPO outruns deferred revenue by >20x). **Not** usable alone as a bubble
verdict — it produces a false positive on every long-contract software business. Do not ship
it as a standalone signal.

### Scoring approach (concrete)
Compute `R = RPO / TTM revenue` at each quarter-end (TTM = sum of last 4 *quarterly* facts of
`RevenueFromContractWithCustomerExcludingAssessedTax`, falling back to `Revenues`).
Then emit a flag on the **derivative**, not the level:
- `z = (R_t - median(R_{t-12..t-1})) / MAD(...)`
- FLAG_HIGH if `z > 4` **or** QoQ growth of RPO `> 40%` **or** `RPO/DeferredRevenue > 20x`
- FLAG_LOW (backlog erosion) if RPO declines QoQ for 2 consecutive quarters.
Require >= 8 consecutive quarters present and staleness <= 120 days (else withhold).
Never compare RPO levels across companies without normalising by TTM revenue (see table above:
raw ORCL and GOOGL levels are not comparable).

### Failure modes
- **META and AAPL do not tag RPO at all (HTTP 404).** Absence must be reported as
  "no data", never as zero or as a decline.
- **Definition drift within a continuous tag is invisible to XBRL.** GOOGL's Q1-26 change
  (adding <=1yr contracts) was a pure text disclosure; the tag looked continuous throughout. A
  purely XBRL-driven pipeline would have silently mixed two definitions. Only the filing text
  catches it — so a text-diff check ("revenue backlog"/"remaining performance obligation"
  paragraph year-over-year) is mandatory companion logic.
- **RPO tags are frequently not in the XBRL for Q1-Q3** for smaller filers; only annual.
- RPO includes deferred revenue, so it double-counts against balance-sheet metrics if summed.

---

## FINDING 2 — Depreciation "capital subsidy" (us-gaap:Depreciation / PropertyPlantAndEquipmentGross)

### The prior finding's data bug, CORRECTED (worse than reported)

The prior run described META's gross PP&E as "frozen at 56.43B across three years (stale tag)".
Real failure: **the tag was ABANDONED.** META's last `PropertyPlantAndEquipmentGross` fact is
**2020-09-30 = 56.428B** and there is *nothing* after it for ~6 years. META migrated to
`PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetBeforeAccumulatedDepreciationAndAmortization`
(24 facts, latest 2026-06-30 = **292.9B**).

**AMZN's 3.3x break is now explained.** AMZN's gross tag has a **literal 5-year hole**
(2020-01-01 -> 2024-12-30 absent; 16 facts total). At 2024-12-31, **394.055B is byte-identical
to AMZN's finance-lease-ROU-inclusive tag at the same date.** So 2019 (119.7B, PP&E only) and
2024 (394.1B, PP&E **including finance-lease ROU**) are two different metrics under one tag
name. The "jump" is a definition swap, not a build-out.

**GOOGL's gross tag is unusable too (new).** Last fact **2025-03-31 = 213.199B** (~18 months
stale) and internally inconsistent (2024-06-30 = 224.0B -> 2024-12-31 = 199.8B, a *decrease*).

### Depreciation-rate table (only for series that PASS the guard)

| Company | Period end | Gross PP&E | Depreciation | Rate | Implied life |
|---|---|---|---|---|---|
| ORCL | 2024-05-31 | 34.8B | 3.13B | 8.99% | 11.1y |
| ORCL | 2025-05-31 | 59.6B | 3.87B | 6.49% | 15.4y |
| ORCL | 2026-05-31 | 122.7B | 7.62B | **6.22%** | **16.1y** |
| MSFT | 2024-06-30 | 212.0B | 15.20B | 7.17% | 13.9y |
| MSFT | 2025-06-30 | 298.6B | 22.00B | 7.37% | 13.6y |
| MSFT | 2026-06-30 | 431.8B | 34.30B | **7.94%** | 12.6y |
| AAPL | 2024-09-28 | 119.1B | 8.20B | 6.88% | 14.5y |
| AAPL | 2025-09-27 | 125.8B | 8.00B | **6.36%** | 15.7y |
| NVDA | 2025-01-26 | 10.7B | 1.30B | 12.17% | 8.2y |
| NVDA | 2026-01-25 | 17.0B | 2.40B | **14.14%** | 7.1y |
| AVGO | 2024-11-03 | 7.0B | 0.59B | 8.44% | 11.8y |
| AVGO | 2025-11-02 | 7.4B | 0.57B | **7.73%** | 12.9y |

Confirmed: ORCL's rate FELL 8.99% -> 6.22% (life 11.1y -> 16.1y) while gross PP&E grew 3.5x.
MSFT ROSE 7.17 -> 7.94. NVDA ROSE 12.17 -> 14.14.

**Honest caveat (do not oversell):** AAPL's rate also fell (6.88 -> 6.36) and AVGO's fell
(8.44 -> 7.73) with **no AI-capex story whatsoever** — AAPL's gross PP&E barely moved
(119.1 -> 125.8B). A mechanical ratio like this drifts from mix shift (older fully-depreciated
assets aging in the denominator) alone. So the ORCL *level* is not, by itself, evidence of
aggressive extension; only the *magnitude and speed* (a 31% rate cut in 2 years) is anomalous.
Also note MSFT's `Depreciation` series is non-monotonic (9.40% -> 6.71% at FY2023) — a likely
mid-series tag switch, so MSFT's own rate must be read with care.

### Scoring approach (concrete)
`rate_t = Depreciation_t / PP&E_gross_t`; `life_t = 1 / rate_t`.
Per company, z-score `rate_t` against its own trailing 8-observation mean/MAD, and emit
FLAG when BOTH hold: `(rate_t - mean_8)/MAD_8 < -3` **AND** `PP&E_gross_t / PP&E_gross_{t-4} > 1.5`.
The AND is load-bearing: it suppresses AAPL/AVGO-style benign drift, which has the rate move but
NOT the capex surge. Only then is the "capital subsidy" (extending useful life precisely while
the asset base explodes) a genuine anomaly rather than arithmetic.

### Failure modes
- **Abandoned tag** (META): series ends years ago -> nonsense implied life.
- **Definition swap under one tag name** (AMZN): PP&E-only vs PP&E+finance-lease-ROU.
- **Multi-year gaps** (AMZN: 5 years absent) silently bridged by sorted-series arithmetic.
- **Non-monotonic / mid-series tag switch** (MSFT) producing fake rate reversals.
- **Benign mean reversion misread as subsidy** (AAPL, AVGO) — the largest false-positive source.
- Numerator/denominator from different tags with different scopes (a filer can tag
  `Depreciation` as D&A-including-amortisation-of-intangibles).

---

## Q3 — Per-company verdict: is there a USABLE gross PP&E series?

Guard applied to annual (`form=10-K, fp=FY`) `us-gaap:PropertyPlantAndEquipmentGross`,
as of 2026-09-17:

| Company | # annual facts | Last date | Last value | Max gap | Max growth | Staleness | VERDICT |
|---|---|---|---|---|---|---|---|
| ORCL | 17 | 2026-05-31 | 122.7B | 366d | 2.06x | 3.6mo | **USABLE** |
| MSFT | 18 | 2026-06-30 | 431.8B | 366d | 1.45x | 2.6mo | **USABLE** |
| AAPL | 15 | 2025-09-27 | 125.8B | 371d | 1.86x | 11.7mo | USABLE (but flat base — no signal) |
| NVDA | 17 | 2026-01-25 | 17.0B | 371d | 1.59x | 7.7mo | **USABLE** |
| AVGO | 9 | 2025-11-02 | 7.4B | 371d | 1.14x | 10.5mo | USABLE (small base, thin) |
| GOOGL | 11 | 2024-12-31 | 199.8B | 366d | 1.38x | **20.5mo** | **REJECT — stale** |
| META | 8 | 2018-12-31 | 31.6B | 366d | 1.72x | **92.5mo** | **REJECT — abandoned** |
| AMZN | 13 | 2025-12-31 | 534.1B | **1827d** | **3.29x** | 8.5mo | **REJECT — gap + definition swap** |
| TSLA | 14 | 2024-12-31 | 51.4B | 366d | 2.41x | **20.5mo** | **REJECT — stale** |

**Only 5 of 9 are usable, and only 3 of those (ORCL, MSFT, NVDA) carry real capex-cycle signal.**
A naive implementation emits a number for all 9 and produces at least 4 false positives.
Note ORCL's 2.06x single-year growth is the *real* observation (59.6 -> 122.7B) and must be
allowed through — which is why the growth ceiling alone is insufficient and the gap/staleness
tests are mandatory.

---

## VERIFIED TRUE/FALSE

| Claim | Status |
|---|---|
| RPO tag returns real, usable data via SEC XBRL | **TRUE** (HTTP 200; ORCL/MSFT/GOOGL) |
| GOOGL RPO Q1-26 jump is a definitional/reporting artifact | **FALSE** — real; definition change is only $7.3B of a $224.8B move |
| RPO is a trustworthy *series* for hyperscalers | **TRUE** |
| RPO/revenue alone identifies an AI bubble | **FALSE** — cannot distinguish backlog from vendor-financed commitments |
| ORCL deferred revenue corroborates its RPO ramp | **FALSE** — deferred rev flat at ~9.9B while RPO went 97B -> 664B |
| META gross PP&E is "frozen" (stale tag) | **FALSE as described** — tag was *abandoned* after 2020-09-30 |
| AMZN gross PP&E 3.3x jump is real build-out | **FALSE** — definition swap to PP&E+finance-lease-ROU after a 5-year gap |
| Gross PP&E tag is usable across the cohort | **FALSE** — 4 of 9 fail; only ORCL/MSFT/NVDA carry signal |
| ORCL useful-life extension is real vs. comparable peers | **PARTIALLY TRUE** — rate 8.99%->6.22% is real, but AAPL/AVGO show similar drift without capex, so magnitude+speed is the only anomaly, not direction |

## TOP PICK

**RPO, as a *divergence screening* indicator — not a bubble verdict.** It is the only candidate
here with clean, continuous, machine-readable history for the three names that matter
(ORCL/MSFT/GOOGL: 12x / 3.7x / 8.4x expansion in RPO/revenue), the GOOGL anomaly is now
**resolved as real**, and it survives the tag-discontinuity problem that destroys the
depreciation indicator. Depreciation/"capital subsidy" is the **second** choice and must ship
behind the guard rule below or it will report four false positives out of nine. The killer
companion metric for either one is **RPO vs DeferredRevenue** (ORCL 47x): that ratio, not the
RPO level, is where the actual fragility shows.

## RECOMMENDED GUARD RULE

Before emitting ANY level from a stock-based XBRL tag, require ALL of:

1. **Continuity** — every consecutive annual observation (10-K/FY) is <= 400 days apart.
   Rejects AMZN (1827-day hole) and any silently-bridged gap.
2. **Recency** — latest fact is <= 15 months before the run date.
   Rejects META (92.5mo) and GOOGL (20.5mo) and TSLA (20.5mo).
3. **Density** — >= 4 annual observations available. Rejects thin/single-period series.
4. **Definition stability** — no single-period growth > 2.5x. Rejects AMZN (3.29x).
   Exempt a break only if the same value appears under a *more specific* tag at the same date
   (the AMZN 394.055B == finance-lease-ROU tag test) — in which case re-BASE the series with an
   explicit recorded break instead of emitting a growth rate.
5. **Cross-tag substitution before failure** — if the primary tag fails 1-3, attempt the
   finance-lease-ROU-inclusive variant (`PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAsset
   BeforeAccumulatedDepreciationAndAmortization`), re-run 1-3, and label the output
   `metric=PP&E_incl_ROU` so the definition is never silently mixed.
6. **Text-diff companion (mandatory for RPO)** — diff the filing's
   "remaining performance obligation" / "revenue backlog" paragraph against the prior year's.
   Any "we elected to change"/"beginning in" language forces the series to be flagged with the
   quantified delta (GOOGL: $7.3B) and forbids silent splice.
7. **Withhold, don't guess** — on failure emit `null` plus a reason code
   (`STALE|ABANDONED|GAP|DEFINITION_SWAP|THIN`). Never emit zero, never carry forward, never
   interpolate. A missing number is a result; a fabricated one is a liability.
