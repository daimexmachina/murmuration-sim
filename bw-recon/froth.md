# bubble-watch — Market-Structure / Froth Indicators Recon

Probe date: 2026-09-17 UTC. All HTTP statuses are observed, not assumed.
Prior-run verified facts are marked [PRIOR] and were not redone.

---

## CANDIDATE F1 — CBOE per-symbol options volume (live only)

- **Endpoint (only one that works):**
  `https://www.cboe.com/us/options/market_statistics/symbol_data/csv/?dt=YYYY-MM-DD`
- **HTTP status observed:** `200`, 4,632,807 bytes, `content-type: text/csv`
- **VERIFIED TRUE — historical `dt` is IGNORED (the archive does not exist):**
  - `?dt=2020-01-02` and `?dt=2026-09-16` returned **byte-identical files**
    (`md5 496d590a2a14b727c9dcfcd698d08194` for both).
  - Therefore the endpoint always serves the **current trading day** regardless of `dt`.
- **Archive / alternate paths probed:**
  - `https://www.cboe.com/us/options/market_statistics/` → **302** redirect (no usable index page)
  - `https://www.cboe.com/us/options/market_statistics/ovprev/` → **404** (612,867-byte error page)
    — `ovprev` is NOT a live endpoint
  - `https://www.cboe.com/us/options/market_statistics/volume/` → **404**
  - `https://cdn.cboe.com/data/us/options/market_statistics/daily_option_volume.csv` → **403**
    (CloudFront denial, `application/xml`) — does not exist publicly
- **REAL sample value:** current-day file, 89,056 data rows (89,057 lines incl. header).
  - Header: `Symbol,Call/Put,Expiration,Strike Price,Volume,Matched,Routed,Bid Size,Bid Price,Ask Size,Ask Price,Last Price`
  - First real rows: `SPY,C,2026-09-17,763.0000,27643,26317,1326,...` / `SPY,P,2026-09-17,763.0000,27497,26889,608,...`
- **MAJOR LIMITATION — no `mkt` param means NO SPX:** this default file contains **2,961 symbols
  and ZERO SPX rows** (`grep -c "^SPX," = 0`). It covers ETFs and single names only
  (SPY, QQQ, MU, AMD, INTC, TSLA, META, NVDA, SNDK, DELL, SPCX, SOXL, AAPL, …).
  For SPX/SPXW you MUST pass `mkt=cone` — see F4.
- **Bottom line (acceptable and useful answer):** there is **NO obtainable historical per-symbol
  options volume from CBOE for free**. This indicator can only be built **forward from today** by
  snapshotting the CSV daily (e.g. cron at ~22:00 ET, append aggregates to the vault).
  Mark F1 as `historical=false`, `forward-buildable=true`.
- **Why it matters for this bubble:** per-symbol option volume + the expiration column is the raw
  material for 0DTE share, call/put skew, and retail-speculation concentration.
- **Score 0-100:** once ≥30 daily snapshots exist, score on call/put volume ratio and on
  single-name call volume as a share of total; below 30 snapshots the indicator is unscorable.
- **Failure modes:** silent `dt` ignoring (already bitten — always verify by MD5 before trusting a
  date param); the site is behind a WAF and may 403 without a browser UA; volume is current-session
  only and is not restated later; the file is ~4.6-8 MB/day, so reduce to aggregates at snapshot
  time rather than storing raw.

### ACTION ITEM
Add a daily snapshot cron for F1/F1b starting immediately — every day of delay is a day of history
that cannot be recovered.

---

## CANDIDATE F2 — Nasdaq short interest (per-symbol, free, ~1yr window)

- **Endpoint:** `https://api.nasdaq.com/api/quote/{SYMBOL}/short-interest?assetClass={etf|stocks}`
- **HTTP status observed:** `200` (TQQQ, 3,033 bytes; AAPL, 3,053 bytes)
- **Required headers:** `User-Agent: Mozilla/5.0 (…) Chrome/...` + `Accept: application/json`.
  Without a browser UA this API is known to reject; it worked with the UA set.
- **VERIFIED TRUE — exact history depth: 24 settlement dates, ~12 months.**
  - Response shape: `data.symbol`, `data.shortInterestTable.rows[]`, each row
    `{settlementDate, interest, avgDailyShareVolume, daysToCover}`.
  - All symbols tested returned exactly **24 rows**, newest `08/31/2026`, oldest `09/15/2025`.
  - `?assetClass` does NOT extend history — it only changes validation.
- **REAL samples (observed 2026-09-17):**

  | symbol | settlementDate | interest | avgDailyShareVolume | daysToCover |
  |---|---|---|---|---|
  | TQQQ | 08/31/2026 | 23,896,976 | 47,238,159 | 1.0 |
  | TQQQ | 08/14/2026 | 26,639,138 | 54,246,427 | 1.0 |
  | TQQQ | 07/31/2026 | 25,803,330 | 67,978,199 | 1.0 |
  | TQQQ | 06/30/2026 | 18,940,189 | 72,492,841 | 1.0 |
  | AAPL | 08/31/2026 | (24 rows, same window) | — | — |

- **HARD LIMITATION — Nasdaq-listed only:** `SPY` returns
  `{"data":null,"message":"Short interest is not available. Short interest is only supported for Nasdaq Listed stocks"}`
  at **HTTP 200 with a null payload** — **a 200 does NOT mean success here; always check `data`.**
- **For multi-year history:** use the FINRA short-interest route `[PRIOR: POST compareFilters]` —
  that is the archive; the Nasdaq endpoint is only the recent-12-month convenience window.
- **Why it matters for this bubble:** short interest on leveraged/speculative vehicles (TQQQ, SOXL)
  is a direct read on two-sided speculation. TQQQ short interest *rising* into a rally
  (18.9M Jun → 26.6M mid-Aug) alongside a 1.0 days-to-cover is a classic melt-up signature.
- **Score 0-100:** normalize interest/market-cap (or interest vs its own 12-month max) plus
  days-to-cover. Low days-to-cover (<1.5) + rising interest = crowded two-sided froth = high score.
  Use the 12-month high as the 100 anchor.
- **Failure modes:** `data:null` at HTTP 200 (check payload, not status); 24-row cap makes it
  unusable for long-horizon baselines; TQQQ `daysToCover` is returned **truncated to 1.0**, so do
  not score from it — recompute from `interest / avgDailyShareVolume`.

---

## CANDIDATE F3 — FINRA margin debt  ✅ STRONGEST FINDING

- **Discovery path:** `finra.org/investors/learn-to-invest/advanced-investing/margin-statistics`
  **301-redirects**; the real page is at the final URL
  `https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics`
  (**HTTP 200**, 90,630 bytes). The investor-facing URL is NOT the data page.
- **Real free endpoint (the only data file on the page):**
  `https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx`
- **HTTP status observed:** `200`, 20,460 bytes,
  `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (confirmed `file` →
  "Microsoft Excel 2007+"). Downloaded with a browser UA and `-L`. **No API key, no login, no payment.**
- **Sheet layout:** single sheet (`xl/worksheets/sheet1.xml`), 357 rows, 4 columns, header row 1:
  `Year-Month | Debit Balances in Customers' Securities Margin Accounts | Free Credit Balances in
  Customers' Cash Accounts | Free Credit Balances in Customers' Securities Margin Accounts`.
  **Units: millions of dollars.** Rows are newest-first. No shared-strings table (values are inline).
- **VERIFIED TRUE — 356 monthly observations, 1997-01 → 2026-08** (no gaps).
- **REAL values (millions of USD):**

  | month | margin debt |
  |---|---|
  | **2026-08 (latest)** | **$1,453,832M = $1.4538T** |
  | 2026-07 | $1,417,225M |
  | **2026-06 (ALL-TIME PEAK)** | **$1,502,061M = $1.5021T** |
  | 2026-05 | $1,415,600M |
  | 2026-04 | $1,304,300M |
  | 2026-01 | $1,279,000M |
  | 2025-12 | $1,225,600M |

- **Derived stats (computed, not asserted):**
  - latest is at the **99.7th percentile** of all 356 months
  - **MoM +2.58%**, **YoY +37.19%**
  - The 8 highest months in 30 years are **all in 2026** — the entire top decile is this episode.
  - All-time peak 2026-06 $1.5021T was followed by a modest de-lever (Jul $1.4172T) then a
    re-lever to $1.4538T — this is the **froth signature to watch**.
- **Why it matters for this bubble:** margin debt is the single best free proxy for *leveraged*
  speculative exposure. +37% YoY with an all-time high set two months ago is the highest-quality
  froth confirmation available at zero cost. Debit vs free-credit balances gives a crude leverage
  ratio, and the free-credit columns ship in the same file.
- **Score 0-100:**
  `score = 0.5*pctile(margin_debt, full history) + 0.3*clip(yoy_growth/40%, 0, 1) + 0.2*clip(drawdown_from_peak/10%, 0, 1)`
  Anchors: ≥99th percentile ≈ 95-100 (we are here); fresh all-time high plus >40% YoY = 100.
  A >10% drop from peak with falling YoY is the de-froth signal — currently NOT triggered.
- **Failure modes:** published with a **~3-6 week lag** (2026-08 is newest as of mid-Sept 2026), so
  it is not a tactical signal; the URL is **year-stamped (`2021-03`)** and FINRA has historically
  moved it — the scraper must re-discover the link from the page each run, never hardcode it; it is
  `.xlsx` so the reader needs openpyxl **or** a stdlib zip+XML parse (openpyxl was NOT installed on
  this host — the stdlib parse works and should be the fallback); units are millions, and a naive
  read produces a 1,000x error; pre-2003 observations come from a different reporting regime and
  should not anchor the score.

---

## CANDIDATE F4 — 0DTE share of SPX options volume  ✅ DERIVABLE, NO FREE SOURCE PUBLISHES IT

- **Answer to Q4: no free source exposes machine-readable 0DTE share. It MUST be derived from the
  CBOE per-symbol + expiration file.** VERIFIED by probing:
  - `https://www.cboe.com/us/options/market_statistics/volume/` → **404**
  - `https://cdn.cboe.com/data/us/options/market_statistics/daily_option_volume.csv` → **403**
    (CloudFront `application/xml` denial — does not exist publicly)
  - CBOE publishes 0DTE share only as **prose in editorial Insights posts and PDFs** (e.g.
    "0DTEs Decoded", "SPX 0DTE Options Jump to 61% Share") — *monthly* shares with a lag, not a feed.
  - Third-party (SpotGamma, Concretum, ZeroGEX) quote the same CBOE numbers; none is a free
    machine-readable feed.
- **CRITICAL DISCOVERY — `mkt=cone` is required to see SPX/SPXW:**
  - `.../symbol_data/csv/?dt=YYYY-MM-DD` (no `mkt`) → 4,632,807 bytes, **2,961 symbols, ZERO SPX rows**.
  - `.../symbol_data/csv/?dt=YYYY-MM-DD&mkt=cone` → **8,003,567 bytes, 3,113 symbols, 153,086 rows,
    and it DOES contain SPX (3,444 rows), SPXW (7,923), XSP, RUT, VIX, RUTW.**
  - **The `mkt=cone` file ALSO ignores `dt`** — `dt=2020-01-02` and `dt=2026-09-17` returned
    byte-identical files (`md5 d505420f756e3b96e739af5637b0f588`). Same live-only rule as F1.
- **REAL derived 0DTE arithmetic on the 2026-09-17 file (contracts):**

  ```
  0DTE_share = sum(Volume where Symbol in (SPX,SPXW) and Expiration == session_date)
             / sum(Volume where Symbol in (SPX,SPXW))
  ```

  | bucket | volume | share |
  |---|---|---|
  | SPX+SPXW total | 5,121,916 | 100% |
  | **0DTE (2026-09-17)** | **2,999,000** | **58.55%** |
  | 1DTE (2026-09-18) | 886,568 | 17.31% |
  | 2026-12-18 (quarterly) | 219,829 | 4.29% |
  | 2026-10-16 | 162,728 | 3.18% |

  - **Per-root breakdown (important nuance):** `SPX` (AM-settled, 3rd-Friday) has **0.00%** 0DTE —
    it simply has no same-day expiry. **`SPXW` (PM-settled weeklies/dailies) = 71.30% 0DTE**
    (4,206,445 total, 2,999,000 same-day).
  - Comparison ETFs: **SPY 64.95%** 0DTE, **QQQ 64.87%** 0DTE.
  - Sanity check vs public reporting: the 58.55% blend combines SPXW's 71.3% with SPX's 0%,
    consistent with CBOE's published ~61% (May) / 66.2% (July 2026) monthly figures for SPXW-led
    0DTE share. **Independent derivation ≈ published value → arithmetic is correct.**
- **Why it matters for this bubble:** 0DTE concentration is the purest measure of short-horizon,
  high-turnover speculation and of the gamma-hedging feedback loop that amplifies intraday moves.
  A share near 60-70% means most index options flow expires the same day — structurally reflexive,
  a marker of late-cycle froth.
- **Score 0-100:**
  `score = 100 * clip((spxw_0dte_share - 30%) / (75% - 30%), 0, 1)`
  Anchors: <30% healthy (score 0); ~50% elevated (≈45); **71.3% today ≈ score 92**; >75% = max (100).
  Use **SPXW-only** as the primary series, SPX+SPXW as the headline; a 5-day MA removes
  expiration-calendar noise.
- **Failure modes:** **live-only — no history exists**, so build forward from today; the file is
  final only after the close, so snapshot ≥22:00 ET or the 0DTE number reads low; sum **contracts**,
  not rows; on a market holiday "today" has no expiry → ratio 0, a false de-froth signal that must be
  masked; never use `SPX` alone (permanent 0.00%); ~8 MB/day raw, so store derived aggregates only.

---

## ADDENDUM — CBOE historical archive: one archive exists, but it is EQUITIES, not options

- `https://www.cboe.com/markets/us/equities/market-statistics/historical-market-volume`
  → **200** (411,765 bytes)
- Exposes genuine dated archives:
  `https://cdn.cboe.com/resources/us/equities/market-statistics/historical-market-volume/market_history_YYYY.csv`
  for **2009, 2010, … 2023** (all present in the page HTML).
- **VERIFIED FALSE as a fix for F1/F4:** these are **equities exchange market share / volume**
  files, **not options per-symbol volume**, and they stop at 2023. They do **not** solve the
  options-history gap. Do not use them for froth scoring.

---

## SUMMARY TABLE

| id | indicator | endpoint | HTTP | history | verified | real sample |
|---|---|---|---|---|---|---|
| F1 | CBOE per-symbol options volume (no `mkt`) | `/us/options/market_statistics/symbol_data/csv/?dt=…` | 200 | **live only** | ✔ true (no history) | 89,056 rows, SPY C 763 vol 27,643 |
| F1b | CBOE per-symbol **incl. SPX** (`mkt=cone`) | `…symbol_data/csv/?dt=…&mkt=cone` | 200 | **live only** | ✔ true (no history) | 153,086 rows, SPXW 2026-09-17 |
| F2 | Nasdaq short interest | `api.nasdaq.com/api/quote/{S}/short-interest?assetClass=…` | 200 | 24 pts / ~1 yr | ✔ true | TQQQ 08/31/2026 = 23,896,976 |
| F3 | **FINRA margin debt** | `finra.org/sites/default/files/2021-03/margin-statistics.xlsx` | 200 | **1997-01→2026-08** | ✔ true | **2026-08 = $1.4538T** |
| F4 | 0DTE share of SPX volume | derived from F1b | 200 | **live only** | ✔ true (derived) | **58.55%** (SPXW 71.30%) |
| — | CBOE equity volume archive | `cdn.cboe.com/resources/us/equities/…market_history_YYYY.csv` | 200 | 2009-2023 | ✔ true but **wrong asset class** | n/a |

---

## TOP PICK

**F3 — FINRA margin debt.** The only candidate that is simultaneously **free, unauthenticated,
already carrying 30 years of history (356 months, 1997-01 → 2026-08), and printing an extreme
current value: $1.4538T for 2026-08, the 99.7th percentile of all history, +37.19% YoY, with the
all-time peak ($1.5021T) set just two months earlier.** No forward-building, no live-only endpoint,
and the score is already actionable. Ship it first.

**Strong second / immediate action item: F1b + F4.** 0DTE share is the highest-signal froth metric
conceptually (**58.55%** of SPX+SPXW, **71.30%** of SPXW today) but **has no history and never
will** — every day without a snapshot is permanently lost. Start the daily `mkt=cone` snapshot cron
now and store only derived aggregates.

---

## COULD NOT MEASURE

- **Historical per-symbol options volume (F1/F1b).** No CBOE archive endpoint exists. Probed:
  `?dt=2020-01-02` (identical MD5 → `dt` ignored), `…/market_statistics/` (302),
  `…/market_statistics/ovprev/` (404), `…/market_statistics/volume/` (404),
  `cdn.cboe.com/…/daily_option_volume.csv` (403). The date parameter is **silently ignored**, so no
  past session is retrievable. Historical options data is a paid CBOE DataShop product.
- **Historical 0DTE share (F4).** Cannot be backfilled for the same reason. Only CBOE's editorial
  *monthly* prose figures exist (61% May, 66.2% July 2026); not a machine-readable series.
- **CFTC TFF futures-only for equity futures.** [PRIOR] looked stale at 2022. **I did not
  re-verify this in this run** — flagged as unresolved, not confirmed-stale. Re-probe before use;
  do not score it.
- **NYSE-listed single-name short interest** (e.g. SPY) via Nasdaq — explicitly rejected by the API
  (`data:null`, "only supported for Nasdaq Listed stocks"). Multi-year single-name history requires
  the FINRA `compareFilters` route [PRIOR], not exercised here.
- **Days-to-cover quality (F2).** Nasdaq returns `daysToCover` rounded to 1.0 on every TQQQ row, so
  the field is unusable as delivered; must be recomputed from `interest / avgDailyShareVolume`.
  Not independently validated against a second source.
- **Openpyxl availability.** NOT installed on this host; the FINRA `.xlsx` had to be parsed with
  stdlib `zipfile` + `xml.etree`. Any production reader must install openpyxl or use that stdlib parse.
