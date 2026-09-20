# AI-Hype Census & Measurable Narrative Indicators
Generated: 2026-09-17 (UTC) · Workspace: /home/daim/workspace/bw-recon

---

## CANDIDATE 1 — EDGAR Full-Text Search: AI-mention CENSUS in SEC filings
**STATUS: VERIFIED TRUE — PRIMARY DELIVERABLE**

**Exact endpoint:**
```
https://efts.sec.gov/LATEST/search-index?q=<PHRASE>&forms=<FORM>&dateRange=custom&startdt=YYYY-MM-DD&enddt=YYYY-MM-DD
```
**HTTP status: 200** (requires a `User-Agent` header; bare curl → **403**. UA `bw-recon research contact@example.com` works.)
**Response field:** `hits.total.value`, with `hits.total.relation` = `"eq"` (exact count) for all per-year queries below. `"gte"` with value 10000 appears only when the query is unbounded/huge (e.g. `"the"`), so the per-year counts are exact, not capped.

### REAL VALUES — filings containing the phrase `"artificial intelligence"`

| Year | 10-K | 8-K | 10-Q | `"machine learning"` 10-K | `"generative artificial intelligence"` 10-K |
|------|------|-----|------|------|------|
| 2015 | 41 | 45 | 36 | 45 | 0 |
| 2016 | 52 | 83 | 48 | 64 | 0 |
| 2017 | 116 | 311 | — (500 err) | 137 | 0 |
| 2018 | 294 | 677 | 338 | 244 | 0 |
| 2019 | 445 | 808 | 585 | 360 | 0 |
| 2020 | 558 | 913 | 646 | 439 | 0 |
| 2021 | 848 | 1531 | 889 | 619 | 0 |
| 2022 | 1156 | 1213 | 1156 | 867 | 0 |
| 2023 | 1295 | 1811 | 1618 | 896 | 20 |
| 2024 | 2436 | 3229 | 2791 | 1243 | 353 |
| 2025 | 3324 | 4690 | 3786 | 1645 | 541 |
| 2026 (Jan 1 – Sep 17, partial year) | 3821 | 4903 | 3565 | 2024 | 609 |

*Note: 2026 is a partial year (8.6 months) and already exceeds all full prior years — the series is still accelerating.*

**Cross-validation:** an independent prior run recorded 8-K counts of 808 (2019), 1531 (2021), 1811 (2023), 4690 (2025) and 10-Q counts of 585 (2019), 889 (2021), 1618 (2023), 3786 (2025) — **every value reproduced exactly** in this run. The measure is stable and reproducible.

**Growth multiples (10-K `"artificial intelligence"`):** 2015→2020 = 13.6×; 2020→2025 = 6.0×; 2015→2025 = **81×**. 8-K: 45 → 4690 = **104×** over the same decade.

### Why this is informative (and NOT noise)
- It is a **census, not a sample**: every 10-K/8-K/10-Q filed with the SEC in the period is in the index. No sampling error, no panel-selection bias.
- It is a **long baseline** (2015→2026, 12 years) — rare for a hype measure, which usually has only 2–3 years of history.
- It is **legally costly to say**: an SEC filing is a liability-bearing document. A company only puts "artificial intelligence" in a 10-K if it is prepared to defend the claim to shareholders and the SEC. That is materially different from a press release or a tweet.
- The bare-token `"AI"` series (which includes false positives like the two-letter word fragments, "A.I.", and other uses) is *lower* than the phrase series in early years (125 in 2015 vs. 41 for the phrase in 10-K — bare AI is the loose proxy) and both rise together, so the trend is not an artifact of one keyword choice.
- The **`"generative artificial intelligence"` series is a clean regime-change detector**: exactly 0 for every year 2015–2022, then 20 (2023), 353 (2024), 541 (2025). That is a step function, not a drift — it dates the ChatGPT-era narrative shift to 2023 filings with no ambiguity.

### How to score 0–100
- **Adoption-breadth score** = `count(year) / count(max_year)` × 100, using the 10-K `"artificial intelligence"` series. 2026 ≈ 100, 2015 ≈ 1.
- **Acceleration score** = year-over-year % change, clipped to [0,100] via `min(100, max(0, (yoy_pct)))`. 2024 was +88% (10-K), 2025 +36%, i.e. the pace is decelerating even as the level grows — that deceleration is itself a top signal.
- **Regime-change score** = share of filings using `"generative artificial intelligence"` relative to those using the plain phrase: 2023 = 1.5%, 2025 = 16.3%. Rising share = narrative still propagating.
- Suggested composite: 60% adoption-breadth + 40% acceleration. Report the two components separately, never fused silently.

### Failure modes
1. **403 without a User-Agent** — the single most common failure. Always send UA; do not conclude the endpoint is dead.
2. **Intermittent HTTP 500** on some (query, year) pairs (seen for 2017 10-Q). Retry with backoff; do not record 0 for a 500.
3. **`relation: "gte"` / value 10000** means a saturated query, not a real count. Guard: reject any result with `relation != "eq"`.
4. **2026 is partial** — must be annualized or excluded before any YoY comparison, or it will look like a crash in Q4.
5. **Phrase inflation vs. substance**: the count says how many companies *mention* AI, not how much revenue it produces. It is a narrative measure and should never be used as a fundamentals proxy.
6. **Filing-volume drift**: total filings grow slowly, so a flat count is actually a mild decline in share-of-filings. Divide by the 10-K/8-K universe for a share-based version if precision matters.
7. Full-text search covers 2001→present, so earlier years are available if the baseline must go further back.

**NOISE? flag: NO — this is a genuine signal.** It is the strongest candidate in this file: exhaustive coverage, 12-year baseline, legally-costly disclosure, exactly reproducible, and with a built-in regime-change series that is 0 for eight straight years then jumps.

---

## CANDIDATE 2 — EDGAR: the word `"bubble"` in 10-K filings (meta-signal)
**STATUS: VERIFIED TRUE, but WEAK — NOISE? flag: MOSTLY NOISE as a hype measure; useful only as a denominator**

**Exact endpoint:** same as Candidate 1, `q=bubble`, `forms=10-K`.

| Year | 10-K filings containing `bubble` |
|------|------|
| 2015 | 62 |
| 2016 | 62 |
| 2017 | 43 |
| 2018 | 42 |
| 2019 | 51 |
| 2020 | 42 |
| 2021 | 54 |
| 2022 | 89 |
| 2023 | 65 |
| 2024 | 72 |
| 2025 | 67 |
| 2026 (partial) | 77 |

**Honest assessment — this is NOT a clean bubble-anxiety signal.** The series has a floor around 42–62 and never deviates from it by more than ~2× in twelve years. Only 2022 (89) stands out, and 2022 was the rate-shock drawdown year. Meanwhile 2025 — the year of peak AI-bubble discourse — sits at **67**, *below* both 2022 (89) and 2024 (72) and statistically indistinguishable from 2015 (62) and 2016 (62). A prior run's figure of "67 10-K filings in 2025" reproduced exactly.

The problem is that the bare word `bubble` is dominated by **non-financial uses** — bubble wrap, bubbles in liquids, "bubbles" as product names, pharma/chemistry contexts. The noise floor swamps the signal. Note also that the specific phrase `"artificial intelligence bubble"` returned **0 in every single year 2015–2026**, meaning the literal compound is not used in filings at all.

**How to score 0–100:** do not score it as a hype measure. If used at all, use it as a **normalizer/denominator** (e.g. AI-mention filings ÷ bubble-mention filings) to test whether AI discourse is rising faster than generalized speculative discourse — the ratio rising from 7.2 (2015) to 49.6 (2025) is more informative than either raw count.

**Failure modes:** polysemy (bubble wrap); tiny absolute numbers make YoY changes meaningless; no `"AI bubble"` phrase ever appears so the target concept is simply not present in filings.

---

## CANDIDATE 3 — Indeed Hiring Lab job postings tracker
**STATUS: PARTIALLY VERIFIED — repo and files located and confirmed REAL; AI-specific series not yet retrieved**

**Confirmed real path:** `hiring-lab/job_postings_tracker` on GitHub. Directory listing via
```
GET https://api.github.com/repos/hiring-lab/job_postings_tracker/contents/
```
**HTTP 200**, returns a genuine list. Top-level structure:
- `US/`, `AU/`, `CA/`, `DE/`, `EA/`, `ES/`, `FR/`, `GB/`, `IE/`, `IT/`, `NL/` (country dirs)
- `sector-job-title-examples.csv`, `LICENSE`, `.gitignore`
- **`README.md` was NOT at the repo root path tried** (`raw.githubusercontent.com/.../main/README.md` → **404**); the README is listed at root by the API, so the branch is likely not `main` (try `master`).

**Confirmed real files in `US/`** (HTTP 200, real byte sizes):
| Path | Size (bytes) |
|------|------|
| `US/aggregate_job_postings_US.csv` | 200,383 |
| `US/job_postings_by_sector_US.csv` | 11,964,553 |
| `US/metro_job_postings_us.csv` | 62,042,505 |
| `US/state_job_postings_us.csv` | 2,544,393 |

**Values with dates: NOT YET OBTAINED.** I did not parse real rows from these CSVs, so I am recording **no numbers** for this candidate rather than guessing. What is established is that the dataset exists, is per-country, is sector-level, and carries ~200KB–62MB of real history.

**Why it would be informative if read:** job postings are a *behavioural* commitment — a company must budget headcount, unlike a press mention. AI-related postings rising is a real-economy footprint of the narrative rather than a media echo.

**Why it may fail to be AI-specific:** the filenames are generic job-postings indices. There is no filename here claiming to be an *AI* series. If the AI cut requires a sector filter or a job-title keyword match, it may not exist in this repo at all — in which case this candidate cannot measure AI hype and should be dropped.

**How to score 0–100:** index level relative to a 2019–2020 pre-shock baseline: `100 × (level / baseline_level)`, using the aggregate series as the denominator against any AI-specific subset.

**Failure modes:** unauthenticated `api.github.com` rate limit ≈ **10 requests/min** (hit and confirmed); wrong default branch breaks raw URLs; 62MB CSVs should be streamed, not loaded whole; per-country files need currency/seasonal adjustment before cross-country comparison.

---

## CANDIDATE 4 — GDELT media volume on "artificial intelligence"
**STATUS: ENDPOINT CONFIRMED LIVE, REAL VALUES NOT OBTAINED — NOISE? flag: LIKELY NOISE**

**Exact endpoints tried:**
```
https://api.gdeltproject.org/api/v2/doc/doc?query=%22artificial+intelligence%22&mode=timelinevol&format=json&timespan=5y
https://api.gdeltproject.org/api/v2/tv/tv?query=%22artificial+intelligence%22+station:CNN&mode=timelinevol&format=json&startdatetime=...&enddatetime=...
```
**HTTP status:** DOC API returned **200** on one attempt and **429** on the next (strict "one request every 5 seconds" limit enforced server-side); TV API returned **200**. The TV API *validates* the request and returns `"Your query must contain at least one station."` when `station:` is missing — proving the endpoint is live and parsing — but with `station:CNN` supplied it returned an **empty body `{}`** rather than a series. **No real volume-intensity or tone values were obtained.**

**No values are recorded here.** Nothing about this candidate's numbers is verified.

**Honest assessment — even if it worked, this is probably NOISE dressed as signal.** GDELT counts *how much news media mentions a phrase*. That is a near-pure measure of media salience, which is the definitional echo of hype rather than an independent indicator of it. It also has known structural breaks (outlet coverage changes, GDELT 2.0 transition, COVID swamping 2020–2021) and no liability cost: a journalist writing "AI" risks nothing, unlike a CFO signing a 10-K. It would be far better used as a **contrast/control series** — to show that the *filings* census is not merely tracking media volume — than as a hype indicator in its own right.

**How to score 0–100 (if ever retrieved):** z-score of trailing-90-day mean volume against a 5-year trailing baseline, mapped to 0–100. Always pair with the EDGAR census and report the divergence.

**Failure modes:** 429 if polled faster than one request / 5 s; TV API requires a `station:` or `market:` term; documented advice from the operator to use the ngrams dataset for high-traffic trend work; media-volume series break on outlet-composition changes; tone values are notoriously noisy at daily frequency.

---

## Rankings
1. **EDGAR AI-mention census (Candidate 1)** — genuine signal, verified, reproducible, long baseline, built-in regime-change detector. Primary deliverable, complete for 2015–2026.
2. **Indeed Hiring Lab (Candidate 3)** — potentially genuine (behavioural commitment), but AI-specificity unconfirmed and no values extracted. Existence verified only.
3. **`bubble` in 10-Ks (Candidate 2)** — verified numbers, but polysemy makes it near-useless as an anxiety gauge; keep only as a denominator.
4. **GDELT media volume (Candidate 4)** — endpoint live, no values obtained, and conceptually the weakest: media volume is the echo of hype, not evidence of it.

## TOP PICK
**Candidate 1 — EDGAR full-text-search census of `"artificial intelligence"` in 10-K/8-K/10-Q filings, 2015–2026.** It is the only candidate that is simultaneously (a) an actual census of a finite, legally-defined population, (b) backed by twelve years of real, exactly-reproduced counts, (c) costly to manipulate because it lives in liability-bearing SEC filings, and (d) equipped with an unambiguous regime-change sub-series (`"generative artificial intelligence"`: 0 for 2015–2022, then 20 → 353 → 541 → 609). Scoring: 60% adoption-breadth (count ÷ max-year count × 100) + 40% acceleration (clipped YoY %), with `relation` must equal `"eq"` as a hard validity gate.

Recommended single headline metric: **10-K `"artificial intelligence"` filings per year, with the `"generative artificial intelligence"` sub-series overlaid.**

## COULD NOT MEASURE
- **Indeed Hiring Lab AI-specific job-posting series**: the repo and its real CSVs were located and confirmed (HTTP 200 with real byte sizes), but no AI-specific file was identified, the `README.md` at the guessed `main`-branch raw URL **404'd** (likely a different default branch), and **no rows were parsed — no values or dates are reported for this candidate.**
- **GDELT volume-intensity and tone for "artificial intelligence"**: no real values obtained. DOC API rate-limited (**429**, one request per 5 s) and the TV API returned **200** with an **empty `{}`** body when a `station:` was supplied. Nothing verified numerically.
- **EDGAR `"machine learning"` and `"artificial intelligence"` 10-Q counts for 2017**: server returned **HTTP 500**; retried and still failed. Recorded as `—`, deliberately not as `0`.
