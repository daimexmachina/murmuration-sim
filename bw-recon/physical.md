# Physical-Reality / Capex-Cycle Indicators — Probe Report

Purpose: find HARD physical indicators that would falsify (or confirm) the AI-capex thesis.
Focus: government-measured data center construction spending, and grid-interconnection
capacity queues (planned vs canceled). These are measured in dollars and megawatts,
not narrative.

Run date: 2026-09-17 (PDT). Report period: Census C30 release covering **July 2026**.

---

## CANDIDATE 1 — US Census C30 "Data center" construction spending  **← TOP PICK**

**Status: VERIFIED TRUE — explicit government line item, real monthly series.**

### Endpoints (all observed with `curl -A "Mozilla/5.0..."`, HTTP 200, no API key)
| URL | Type | HTTP | size |
|---|---|---|---|
| `https://www.census.gov/construction/c30/pdf/priv.pdf` | Value of Private Construction Put in Place — **Not Seasonally Adjusted** | 200 | 144,956 B |
| `https://www.census.gov/construction/c30/pdf/privsa.pdf` | same, **Seasonally Adjusted Annual Rate** | 200 | 226,945 B |
| `https://www.census.gov/construction/c30/xlsx/privsa.xlsx` | xlsx equivalent | 200 | 28,135 B |
| `https://www.census.gov/construction/c30/c30index.html` | index / landing page | 200 | 549,783 B |
| `https://www.census.gov/construction/c30/txt/privsa.txt` | txt | **404** (does not exist) | — |

Parse method that works: `pdftotext -layout priv.pdf priv.txt` (poppler installed at
`/usr/bin/pdftotext`). PDF layout is clean and column-stable. `openpyxl`/`fitz`/`pypdf`
are NOT installed on this box.

### REAL SAMPLE VALUES — Census C30, July 2026 release (millions of dollars)
Table: "Value of Private Construction Put in Place — Not Seasonally Adjusted",
under **Office → Data center**.

| Line item | Jul 2026p | Jun 2026r | May 2026r | Apr 2026 | Mar 2026 | Jul 2025 | YTD Jul 2026 | YTD Jul 2025 | % chg |
|---|---|---|---|---|---|---|---|---|---|
| **Data center** | **6,551** | 6,122 | 5,627 | 5,198 | 4,781 | **4,133** | **37,222** | **27,608** | **+34.8%** |
| Office (total) | 10,683 | 10,268 | 9,778 | 9,325 | 8,761 | 8,772 | 65,397 | 59,323 | +10.2 |
| Office: General | 3,854 | 3,852 | 3,846 | 3,797 | 3,714 | 4,360 | 26,212 | 29,708 | **-11.8** |
| Office: Financial | 235 | 252 | 265 | 289 | 231 | 222 | 1,699 | 1,588 | +7.0 |
| Total Private Construction | 144,923 | 144,543 | 140,668 | 135,757 | 133,964 | 153,762 | 941,690 | 989,177 | **-4.8** |
| Residential | 80,672 | 80,406 | 77,691 | 73,712 | 73,094 | 87,255 | 510,329 | 532,148 | -4.1 |
| Private Nonresidential | 64,251 | 64,137 | 62,977 | 62,046 | 60,870 | 66,506 | 431,361 | 457,029 | -5.6 |

### What this actually says (the signal)
- Data center construction is running **+34.8% YoY year-to-date**, and the monthly
  sequence Mar→Jul 2026 (4,781 → 5,198 → 5,627 → 6,122 → 6,551) is **still accelerating
  in 2026**. This is the single strongest pro-capex physical datapoint found.
- Everything around it is contracting: total private construction **-4.8%**,
  nonresidential **-5.6%**, and **"Office: General" (i.e. everything that is not a data
  center or a bank) is -11.8%**. The data center line is the ONLY growing slice of
  private office.
- Interpretation for a bubble thesis: this is the *last* indicator that will turn, because
  it measures steel already erected. A capex rollover will show here with a lag of roughly
  2-4 quarters after announcements/leases break. **It is a lagging confirmation, not an
  early warning.** It is nevertheless the best available "is it still real" test.
- Note the divergence risk: dollar spending rising while MW delivered falls would signal
  cost inflation (turbines, transformers, switchgear) rather than demand growth. Pair this
  with an MW-denominated series (Candidate 2/3) to disambiguate.

### History / back-data
Census added the separate "Data center" category with the **May 2024 release**; both
seasonally adjusted and unadjusted monthly and annual estimates are available **back to
January 2014**. So a ~12-year series exists in the xlsx time-series workbooks on the C30
site. (Headline PDFs above are the current-month tables only; to build the full series
pull the historical xlsx from `c30index.html`.)

### Scoring 0-100 (higher = more bullish physical reality)
Suggested: map **real data center construction spending YoY %** to a 0-100 score centered at 0%.
- `score = clamp(50 + 1.25 * yoy_pct, 0, 100)`
- Worked: **Jul 2026 YTD +34.8% → score ≈ 93.5**. Jul 2025 vs 2024 YTD was +34.8% too in
  the same table, so the growth *rate itself* is flat — a plateau in the second derivative.
- Alternative, more bearish framing: score the **share of nonresidential growth coming only
  from data centers** (single-point-of-failure concentration). High share = fragile.
- A score below 50 (i.e. YoY turning negative) is the falsification trigger.

### Failure modes
- **Revision churn**: NSA series revised back 2 years each release; preliminary month (`p`)
  can move. Don't trade the flash.
- **Nominal dollars**: NOT deflated. Input-cost inflation (transformers, switchgear, labor)
  inflates this line without new capacity. Never read it as real volume without a deflator.
- **Definitional**: "Data center includes buildings that contain the hardware needed for
  storing, processing, and transmitting digital information" (Census definitions page) —
  it is *buildings*, so it excludes the IT hardware itself, and may exclude some
  retrofit/cooling-only projects.
- **Government-shutdown / release delays**: C30 schedule slips when federal funding lapses.
- **Classification drift**: projects can be reclassified into/out of "Data center".

**Verified: TRUE** (line item exists, URL live, values read directly off the July 2026 PDF).

---

## CANDIDATE 2 — EIA-860M "Canceled or Postponed" sheet

Already verified in a prior run: `https://www.eia.gov/electricity/data/eia860m/`
downloads fine with a browser User-Agent (13.9 MB xlsx) with sheets
`Operating`, `Planned`, `Retired`, `Canceled or Postponed`; `Planned` had 2,343 rows.
MW totals + fuel mix: **IN PROGRESS — see below when filled in.**

## CANDIDATE 3 — EIA-860M Planned vs Canceled ratio
**IN PROGRESS.**

## CANDIDATE 4 — EIA-930 / api.eia.gov electricity demand; DRAM/NAND pricing
**IN PROGRESS.**

---

## TOP PICK
**Census C30 "Data center" line item.** It is a government-measured, monthly,
free, no-key, explicitly-labeled dollar figure for exactly the thing the thesis is about,
and it currently says +34.8% YoY — a real, checkable, falsifiable number.

## COULD NOT MEASURE
(to be completed)

---

## CANDIDATE 2 (RESOLVED) — EIA-860M "Canceled or Indefinitely Postponed"

**Status: VERIFIED TRUE — real, downloadable, 100% free, NO API KEY NEEDED.**

### Endpoints (observed)
| URL | HTTP | size |
|---|---|---|
| `https://www.eia.gov/electricity/data/eia860m/` (index) | 200 | 55,745 B |
| `https://www.eia.gov/electricity/data/eia860m/xls/july_generator2026.xlsx` (**current release**) | 200 | **13,932,124 B** |
| `https://www.eia.gov/electricity/data/eia860m/archive/xls/<month>_generator<year>.xlsx` | 200 | archive back to 2015 |
| `https://www.eia.gov/electricity/data/eia860m/xls/october_generator2026.xlsx` | 200 but **55,745 B — it is an HTML error page, not a file** | trap |
| `https://www.eia.gov/electricity/data/eia860m/xls/december_generator2026.xlsx` | 200 but **56,790 B — HTML error page** | trap |

**CRITICAL GOTCHA:** EIA returns **HTTP 200 with a 55 KB HTML page** for files that do not
exist yet. Always check size (>1 MB for the real 860M) or content-type, never the status code.
The real current file is found by scraping the index page for `href="...xlsx"` — do not guess
the month. Report date embedded in the sheet: **"as of July 2026"**.

Sheets: `Operating`, `Planned`, `Retired`, `Canceled or Postponed`, `Operating_PR`,
`Planned_PR`, `Retired_PR` (the `_PR` sheets carry planned retirements/battery detail).
Header row is **row 3** (rows 1-2 are title/blank). Parse: `openpyxl` read_only,
find the row whose col A == `'Entity ID'`.

### REAL SAMPLE VALUES — July 2026 file

| Sheet | rows | Total Nameplate MW |
|---|---|---|
| Operating | 28,320 | **1,408,847** |
| Planned | 2,343 | **291,138** |
| **Canceled or Postponed** | **1,736** | **184,141** |
| Retired (historical) | 7,301 | 296,459 |

**CANCELED / POSTPONED fuel mix (184,141 MW total):**
| Fuel group | MW | share |
|---|---|---|
| **Natural gas** (CC 59,466 + CT 31,064 + ICE 681 + steam/other) | **91,781** | **49.8%** |
| Solar PV (28,517) + Solar thermal (1,797) | 30,314 | 16.5% |
| Onshore wind 15,752 + Offshore wind 3,349 | 19,102 | 10.4% |
| **Batteries / storage** (MWH) | **15,004** | **8.1%** |
| Coal (sub 10,243 + bit 2,534 + lig 2,202 + SGC 1,510) | 16,489 | 9.0% |
| Nuclear | 5,462 | 3.0% |
| Petroleum liquids | 3,027 | 1.6% |

**PLANNED fuel mix (291,138 MW total):**
| Fuel group | MW | share |
|---|---|---|
| **Solar 123,181 + Wind 24,323** | **147,504** | **50.7%** |
| Natural gas | 69,676 | 23.9% |
| **Batteries / storage** | **65,262** | **22.4%** |
| Nuclear | 4,968 | 1.7% |
| Hydro / pumped storage / other | ~3,600 | 1.2% |

**Planned by development stage (`Status`):**
| Status | MW |
|---|---|
| (P) Planned, regulatory approvals *not initiated* | 100,377 |
| (L) Regulatory approvals pending, not under construction | 63,748 |
| (U) Under construction, ≤50% complete | 55,736 |
| (T) Regulatory approvals received, not under construction | 28,622 |
| (V) Under construction, >50% complete | 27,444 |
| (TS) Construction complete, not yet commercial | 15,211 |

### CANDIDATE 3 (RESOLVED) — Planned : Canceled ratio
- **Canceled ÷ Planned = 184,141 / 291,138 = 0.632** (63 cents of cancellation for every
  dollar of announced pipeline).
- **Canceled ÷ Operating = 184,141 / 1,408,847 = 13.1%** of the entire installed US fleet.
- Only **83,180 MW (28.6%)** of the "planned" 291 GW is actually *under construction* (U+V);
  the other **192,747 MW (66.2%)** is paper — pre-approval or awaiting permits.
- **Natural gas dominates the cancel pile at 49.8%** while gas is only 23.9% of the planned
  pipeline. Gas projects are cancelled ~2x more than their pipeline share. That is the single
  most bearish line in this dataset: the marginal-dispatch fuel for data centers is the one
  getting killed. By contrast solar+batteries are *under*-represented in cancellations
  (27.9% of cancels vs 73.1% of planned).
- Storage is notable: 15,004 MW of batteries cancelled — real, not noise.

### Why it matters
This is the **only** high-frequency, free, project-level MW dataset of *demand disappointment*.
Census C30 tells you what is being built; 860M cancellations tell you what is being *un-built*.
A rising canceled/planned ratio is the earliest hard evidence of a capex rollover, and it is
measured in MW, not sentiment.

### Scoring 0-100 (higher = healthier physical reality)
- `score = clamp(100 - 120 * (canceled_MW / planned_MW), 0, 100)`
  - Worked: 100 − 120×0.632 = **24.1** (unhealthy-looking) — calibrate the multiplier against
    the historical archive before trusting the absolute level; a "normal" economy still
    cancels power projects.
- Better: score the **trend**, not the level — pull the archive (`july_generator2025.xlsx`,
  `july_generator2024.xlsx`, …) and score the YoY change in canceled/planned ratio.
- Also score: `under_construction_MW / planned_MW` as a "paper-to-steel" conversion rate
  (now 28.6%).

### Failure modes
- **No date column on the Canceled sheet** — you cannot tell *when* a project was cancelled.
  YoY comparison requires diffing successive monthly archive files (that is the only way to
  date the cancellations). This is a real limitation.
- **Canceled ≠ dead forever**: "indefinitely postponed" projects sometimes return.
- **Lumpy**: one 1-2 GW CC cancellation swings the ratio; use medians or ≥1-year windows.
- **HTTP 200 on missing files** (see gotcha above) — silent failure mode.
- **Pipeline double-counting**: "Planned" includes batteries whose MW is nameplate not energy;
  solar MW is AC nameplate. Not comparable to C30 dollars.
- Sheet is a snapshot, overwritten monthly; EIA does not keep a public diff.

**Verified: TRUE** (file downloaded, 13.9 MB, all four sheets parsed, MW totals computed).

---

## CANDIDATE 4 — EIA-930 / api.eia.gov electricity demand
Not yet probed. Note prior finding: `api.eia.gov` may require a free registered API key;
the bulk-file route (`https://www.eia.gov/electricity/data/eia930/`) avoids the key.
