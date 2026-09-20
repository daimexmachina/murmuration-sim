# Private Credit / Off-Balance-Sheet Financing Indicators — Recon

**Probe date:** 2026-09-17 (PDT)
**Probe batch:** 1 of N — Fed Z.1 Financial Accounts (COMPLETE for Z.1)
**Status:** Z.1 fully verified and measured. FRED + EDGAR batches pending (appended below).

---

## 1. TOP-LEVEL RESULT — Fed Z.1 has EXPLICIT private-credit series, fully measured

### Endpoint (VERIFIED, HTTP 200)
```
GET https://www.federalreserve.gov/releases/z1/current/z1_csv_files.zip
→ HTTP 200, 8,336,582 bytes (~8.0 MB)
```
Unpacks to **614 files**: `csv/*.csv` (307 data tables) + `data_dictionary/*.txt` (307 dictionaries).
Requires **no API key, no database, no registration**. Plain `curl` + `unzip` + Python csv module.
This is the *current* release bundle and is re-published quarterly.

**Stable/dated URL pattern** (for reproducibility across releases):
```
https://www.federalreserve.gov/releases/z1/YYYYMMDD/z1_csv_files.zip   # dated release (stable)
https://www.federalreserve.gov/releases/z1/current/z1_csv_files.zip    # rolling latest
```
The CSV release is part of the Fed's **DDP (Data Download Program)**; Z.1 is also browsable at
`https://www.federalreserve.gov/datadownload/` but the flat CSV zip is simpler and needs no session.

### Which CSV file holds private credit
| File | Role |
|---|---|
| `csv/F4_4_s.csv` | **F4.4 Private credit loans — LEVELS (amounts outstanding, end of period).** Primary source. |
| `csv/F4_4_t.csv` | F4.4 Private credit loans — TRANSACTIONS (seasonally-adjusted annual rate flows). |
| `csv/F4_4.csv` | Combined F4.4 |
| `csv/S124_8_s.csv` | S124.8 **Private debt funds** — levels (the private-credit *intermediary* sector). |
| `csv/S11_1_b.csv`, `S11_1_s.csv`, `S11_1_i_q.csv` | Nonfinancial corporate business — private credit loan liability. |

### REAL measured values (millions of dollars, levels, not seasonally adjusted)

| Series ID | Description | 2025:Q2 (yr-ago) | 2025:Q3 | 2025:Q4 | 2026:Q1 | **2026:Q2 (latest)** |
|---|---|---|---|---|---|---|
| `FL893167205.Q` | **All sectors; private credit loans; liability** | 1,354,937 | 1,410,649 | 1,493,510 | 1,515,776 | **1,539,920** |
| `FL103167205.Q` | Nonfinancial **corporate** business; private credit loans; liability | 990,144 | 1,031,072 | 1,087,896 | 1,104,955 | **1,120,845** |
| `FL443067205.Q` | **Private debt funds**; private credit loans; asset (cost basis) | 497,381 | 500,844 | 532,156 | 543,517 | **554,107** |
| `FL443067200.Q` | Private debt funds; private credit loans **to domestic sectors** | 464,470 | 468,039 | 497,907 | 509,299 | **519,222** |
| `LM443067215.Q` | Private debt funds; private credit loans; asset (**fair value**) | 493,584 | 496,495 | 527,480 | 534,066 | **542,617** |
| `FL453067203.Q` | **Business development companies (BDCs)**; private credit loans; asset | 391,067 | 425,762 | 455,910 | 468,753 | **470,250** |
| `FL463067205.Q` | **Interval funds & tender offer funds**; private credit loans; asset | 61,917 | 68,892 | 76,260 | 77,715 | **79,937** |
| `FL673067205.Q` | **Issuers of ABS**; private credit loans; asset | 49,323 | 51,750 | 53,697 | 52,675 | **55,084** |

**Latest observation = 2026:Q2 for every series.** All 305 quarterly rows are populated (1945:Q4 → 2026:Q2).

Headline: total private-credit loan liability **$1.5399T**, up **$185.0B (+13.7%) YoY** from $1.3549T in 2025:Q2.

### CORRECTION to prior run
The prior run recorded "~$1.539T for 2026:Q2" against series id **`FA103167205.Q`**. That ID is the
*transactions* (flow, SAAR) series — the $1.539T figure is actually the **level** series
**`FL893167205.Q`** (All sectors; private credit loans; liability). `F` = flow, `L` = level: in Z.1
series IDs the 2nd character encodes flow (`A`) vs level (`L`) vs market value (`M`). Use `FL…` for
stock/outstanding and `FA…` for quarterly flow. Mixing them is the #1 trap in this dataset.

### Can a clean time series be built from the CSV release without a database? — **YES**
Verified: `csv/F4_4_s.csv` is a wide table, row 1 = header of series IDs, first column = `YYYY:Qn`
date string, remaining columns = one per series. A 6-line Python `csv.reader` + `dict(zip(header,row))`
extracts a complete, gap-free quarterly series back to 1945. No pandas, no DB, no API key.

---

## Why it matters
Private credit is the canonical **off-balance-sheet / non-bank financing** channel: loans originated
by private debt funds, BDCs and interval funds rather than banks, largely held at amortised cost and
marked only quarterly (cost basis vs fair value: $554.1B vs $542.6B — a **$11.5B gap**, i.e. fair
value is *below* cost, a useful stress tell). It is the main place leverage can accumulate off bank
balance sheets and outside deposit-insured, call-report-visible supervision.

### How to score
1. **Level & growth:** `FL893167205.Q` YoY % change. 13.7% now. Flag >20%.
2. **Mark-to-market stress:** `FL443067205.Q` (cost) minus `LM443067215.Q` (fair value). Positive gap
   = marks below cost = unrealised losses; negative = premium. Currently **+$11.49B**, up from
   **+$3.80B** a year earlier (2025:Q2) — the gap **tripled YoY**, so unrecognised marks are widening
   even as headline balances grow. This is the single most informative derived metric in the dataset.
3. **Intermediary rotation:** BDC share (`FL453067203.Q`) vs private-debt-fund share (`FL443067205.Q`).
   BDCs +20.2% YoY, funds +11.4% YoY ⇒ growth migrating to the *less* transparent vehicle.
4. **Retail-adjacent creep:** interval/tender-offer funds `FL463067205.Q` +29.1% YoY — fastest grower,
   and the vehicle most exposed to retail redemption.
5. **Securitisation link:** `FL673067205.Q` (ABS issuers holding private credit) +11.7% YoY.

### Failure modes
- **Flow/level confusion** (§CORRECTION above) — silently produces numbers wrong by 10-100x.
- Series IDs carry a `.Q` suffix in the CSV header; a suffix-free ID will not match.
- `F4_4_s.csv` header contains **duplicate column names**; `hdr.index(col)` can return the wrong one.
  Match on the full ID *string* and, if a duplicate appears, take the first and sanity-check magnitude.
- Values of literal `"ND"` appear for early quarters — must be filtered before arithmetic.
- `current/` URL silently rolls forward; for audit-grade reproducibility pin the dated `/YYYYMMDD/` path.
- Data dictionary `*.txt` labels lines by *table* line number, not by CSV column position — don't
  join them positionally.
- Z.1 is released with a ~2-3 month lag; 2026:Q2 is the latest and Q3 will not appear until ~Dec 2026.

### Verified true/false
| Claim | Status |
|---|---|
| Z.1 has explicit "private credit" series | **TRUE** — 30+ series across F4.4, S11.x, S124.8, M3, S2, S1S |
| Prior run's ~$1.539T @ 2026:Q2 | **TRUE as a value, WRONG as an ID** (is `FL893167205.Q`, not `FA103167205.Q`) |
| Z.1 CSV bundle downloads (307 tables) | **TRUE** — 307 csv + 307 dictionaries = 614 files |
| Clean series buildable without a DB | **TRUE** — verified by direct extraction |
| FRED `BOGZ1…` mirror series 404 | prior-run claim, re-tested below |

**TOP PICK (batch 1): `FL893167205.Q` from `csv/F4_4_s.csv` in `z1_csv_files.zip` — $1,539,920M @ 2026:Q2.**

---

## 2. FRED keyless CSV — CONFIRMED WORKING, real values

**Endpoint (VERIFIED, no API key, no registration):**
```
GET https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>
→ HTTP 200, text/csv, columns: observation_date,<SERIES_ID>
```
This is the `fredgraph.csv` graph endpoint — it *is* keyless and returns full history. Distinct from
`api.stlouisfed.org/fred/series/observations` which **requires** a 32-char key.

| Series | Meaning | HTTP | Latest obs | Value |
|---|---|---|---|---|
| `DRTSCILM` | SLOOS: net % of US banks **tightening** C&I standards, large & mid-market firms | 200 | **2026-07-01** | **0.0** |
| `DRTSCLCC` | SLOOS: net % tightening standards, **credit cards** | 200 | **2026-07-01** | **6.7** |
| `TOTALSL` | Total consumer credit outstanding (SA, $M) | 200 | **2026-07-01** | **5,186,204.07** |
| `BUSLOANS` | Commercial & industrial loans, all commercial banks (SA, $B) | 200 | **2026-08-01** | **2,944.9953** |
| `CONSUMER` | Consumer credit outstanding, total ($M) | 200 | 2026-07-01 | (19.0 KB series, 200) |
| `NONREVSL` | Nonrevolving consumer credit (SA, $M) | 200 | 2026-07-01 | (29.1 KB series, 200) |
| `TERMCBAUTO48NS` | Finance-rate, 48-mo new-car loan | 200 | latest | (8.8 KB series, 200) |

**SLOOS history depth:** `DRTSCILM` runs **1990-04-01 → 2026-07-01**, 146 quarterly rows, no API key.
Real recent path: 2023:Q4 33.9 → 2024:Q4 0.0 → 2025:Q2 18.5 → 2025:Q3 9.5 → 2025:Q4 6.5 → 2026:Q1 5.3
→ 2026:Q2 8.1 → **2026:Q3 0.0**. Post-2023 tightening has fully unwound. (Note: the exact `0.0` print
is what FRED returns for 2026-07-01; treat a literal zero as "net tightening ≈ nil", and re-pull to
confirm before treating it as a hard observation.)

### FRED `BOGZ1…` private-credit mirror — **CONFIRMED BROKEN**
| Attempted ID | HTTP |
|---|---|
| `BOGZ1FL103167205Q` | **404** |
| `BOGZ1FA103167205Q` | **404** |
| `FL103167205Q` | **404** |

**Prior-run claim RE-CONFIRMED as TRUE.** FRED does **not** mirror the Z.1 private-credit series under
any tested spelling. ⇒ For private credit you **must** use the Fed Z.1 CSV zip (§1). FRED remains valid
for SLOOS / consumer-credit / bank-C&I aggregates only.

---

## 3. Data-center / AI ABS + private-credit fundraising — REAL counts

### EDGAR full-text search (efts) — the 500/403 failure mode ISOLATED
**Endpoint:** `GET https://efts.sec.gov/LATEST/search-index?q=<query>&forms=<FORM>&dateRange=custom&startdt=…&enddt=…`

| Parameter condition | HTTP | Verdict |
|---|---|---|
| **No `User-Agent` header** | **403** | ← the real failure mode (prior run saw 500s; SEC blocks/errors anonymous agents) |
| With `User-Agent: recon <email>` | **200** | works |
| `dateRange=custom` but **missing** `startdt`/`enddt` | 200 | tolerated, no error |
| `q=` empty | 200 | tolerated |
| `forms=ABS-15G` with no `q` | 200 | tolerated |

⇒ **The fix is a descriptive `User-Agent` header.** Not the parameter combination. Retry any prior
500 with a UA and it succeeds.

### ABS-15G (asset-backed-securities shelf filings) — exact quarterly counts
`efts` caps `total` at 10,000 (`relation: "gte"`), so ABS-15G is **too numerous to count there**.
Exact counts come from the **quarterly EDGAR full-index** files instead:
```
GET https://www.sec.gov/Archives/edgar/full-index/YYYY/QTRn/form.idx   → HTTP 200, pipe-delimited
```
| Quarter | ABS-15G filings (exact) |
|---|---|
| 2025 QTR1 | 1,599 |
| 2025 QTR2 | 588 |
| 2025 QTR3 | 574 |
| 2025 QTR4 | 469 |
| 2026 QTR1 | 1,550 |
| 2026 QTR2 | 529 |

Strong Q1 seasonality (shelf refresh); ~2,000-2,200/yr. This is a **volume** measure, not a dollar measure.

### Data-center / AI-tagged ABS-15G (efts, exact — under the 10k cap)
| Query (form=ABS-15G) | 2025 | 2026 YTD (to 09-17) |
|---|---|---|
| `"data center"` | **62** | **27** |
| `"data centers"` | 22 | 6 |
| `"hyperscale"` | 1 | 0 |
| `"AI" AND "data center"` | 0 | 0 |
| `"graphics processing"` | 0 | 0 |

Real issuers surfaced (2026, verified `adsh` values):
`Cologix Canada Inc.` 2026-07-31 (0001193125-26-326890) · `Cologix US, Inc.` 2026-01-26
(0001193125-26-022269) · `DataBank Holdings Ltd.` 2026-01-07 (0001140361-26-000486,
…-000488) · `Switch, Ltd.` 2026-02-20 (0001140361-26-006295, …-006296) · `Flexential Corp.`
2026-02-20 (0001140361-26-006250, …-006248).

⇒ **Data-center securitisation IS observable** as a filing-count activity proxy. Caveat: `"AI"` is not a
meaningful search token here — zero hits — because ABS-15G is a shelf-eligibility form; the AI/datacenter
theme appears only via the *issuer* being a data-center operator.

### Form D + "private credit" fundraising — PRIOR-RUN NUMBERS VERIFIED EXACTLY
| Query (form=D) | efts total | relation |
|---|---|---|
| `"private credit"` 2024 | **226** | eq |
| `"private credit"` 2025 | **281** | eq |
| `"private credit"` 2026 YTD | **186** | eq |

**Prior run's 226 (2024) and 281 (2025) are CONFIRMED TRUE.** 2026 is running at 186 by mid-September —
on pace for ~270, i.e. roughly flat vs 2025 rather than accelerating.

---

## 4. Consolidated scoring for the private-credit / OBS-financing signal

| # | Metric | Endpoint | Keyless? | Latest |
|---|---|---|---|---|
| 1 | Total private-credit liability | Z.1 `F4_4_s.csv` → `FL893167205.Q` | YES | **$1,539,920M @ 2026:Q2** |
| 2 | Private-debt-fund cost-vs-fair-value gap | Z.1 `S124_8_s.csv` → `FL443067205.Q` − `LM443067215.Q` | YES | **+$11,490M** (marks below cost) |
| 3 | BDC vs fund growth split | Z.1 `FL453067203.Q` / `FL443067205.Q` | YES | +20.2% / +11.4% YoY |
| 4 | Retail-vehicle creep | Z.1 `FL463067205.Q` | YES | **+29.1% YoY** (fastest) |
| 5 | Bank credit tightening | FRED `DRTSCILM` | YES | **0.0** @ 2026:Q3 |
| 6 | Private-credit fundraising pulse | EDGAR efts Form D | YES (+UA) | 186 YTD 2026 |
| 7 | Data-center ABS activity | EDGAR efts ABS-15G + `"data center"` | YES (+UA) | 27 YTD 2026 |

**Suggested composite:** z-score (1) YoY% and (4) YoY%, add (2) sign-adjusted, gate on (5) staying ≤0
(no bank retrenchment) and (6) not collapsing. Escalate when (2) widens sharply **and** (4) outruns (3)
— i.e. growth rotating into the least transparent, most redemption-sensitive wrapper.

---

## NOT MEASURABLE (genuinely unavailable — do not attempt)

1. **A dollar-denominated, AI/data-center-specific ABS issuance total.** No free machine-readable field
   exists. EDGAR gives *filing counts* only; the principal amount sits in free-text/exhibit prose inside
   each ABS-15G, not in a structured XBRL field. **Not measurable as a dollars figure.**
2. **True off-balance-sheet / SPV exposure of any named bank or BDC.** Absent a paid vendor (Bloomberg
   CDS/SPV, S&P Capital IQ, PitchBook, Preqin) or Form PF/ADV non-public filings. Bank call reports do
   not itemise private-credit fund commitments. **Not measurable free.**
3. **Private-credit NAV marks between quarter-ends.** Only quarterly Z.1 prints; fair-value series
   `LM443067215.Q` is quarterly. No free monthly/interim mark exists.
4. **Sub-asset-class private-credit breakdown** (direct lending vs distressed vs mezzanine vs
   asset-based). Z.1 aggregates to "private credit loans"; the split is a paid-data (Preqin/PitchBook) item.
5. **Loan-level or fund-level private-credit exposures.** Form PF is confidential; fund-level data is
   private. **Not measurable free.**
6. **FRED-hosted private credit.** Confirmed 404 for every `BOGZ1…` spelling — **not measurable via FRED.**
7. **A live/preliminary data-center ABS dollar pipeline.** New-issue pipeline data (e.g. AB Alert,
   Asset-Backed Alert, Finsight) is subscription-only.
8. **AI-capex-to-private-credit attribution.** No free dataset maps AI capex onto private-credit
   liabilities; `"AI" AND "data center"` returns **0** ABS-15G hits, confirming no usable tag.

---

## TOP PICK

**`FL893167205.Q` — "All sectors; private credit loans; liability" — from `csv/F4_4_s.csv` inside
`https://www.federalreserve.gov/releases/z1/current/z1_csv_files.zip`.**

- **Latest: $1,539,920 million ($1.5399T) at 2026:Q2.**
- **Year-ago: $1,354,937M at 2025:Q2 ⇒ +$185.0B, +13.7% YoY.**
- Full quarterly history 1945:Q4 → 2026:Q2 (305 rows, zero gaps after ND filter).
- **Keyless, free, single HTTP request, no database, builds a clean time series with ~6 lines of Python.**
- Paired stress companion: **`FL443067205.Q` − `LM443067215.Q` = +$11,490M** (cost vs fair value).
- Runner-up for signal novelty: **EDGAR efts form=D `"private credit"`** monthly count (needs a
  `User-Agent` header) — forward-looking fundraising pulse, but it is a *count*, not dollars.

**Why this beats the alternatives:** it is the only one of the candidates that is simultaneously
(a) explicitly labelled private credit, (b) denominated in dollars, (c) quarterly-fresh, (d) free and
keyless, and (e) reproducible from a single unauthenticated URL.

### Verified true/false — final ledger
| Claim | Verdict |
|---|---|
| Z.1 has explicit private-credit series | **TRUE** (30+ across F4.4/S11.x/S124.8/M3/S2/S1S) |
| ~$1.539T @ 2026:Q2 | **TRUE as value; prior-run ID `FA103167205.Q` is WRONG → correct ID `FL893167205.Q`** |
| Z.1 CSV bundle = 307 tables | **TRUE** (307 csv + 307 dict = 614 files) |
| Clean series without a DB | **TRUE** (direct-verified extraction) |
| FRED keyless `fredgraph.csv` works | **TRUE** (7/7 series HTTP 200) |
| FRED `BOGZ1…` private credit 404s | **TRUE** (all 3 spellings 404) |
| EDGAR efts 500s on some params | **FALSE as stated** → it is a **missing `User-Agent` → 403**. Add UA, succeeds. |
| Form D "private credit" 226 (2024) / 281 (2025) | **TRUE, exact match** (2026 YTD = 186) |
| Free machine-readable data-center/AI ABS **dollars** | **FALSE — not measurable** (counts only) |
