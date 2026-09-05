# Bike Route Pool Expansion — Plan

**Goal:** Massively grow the daily bike-route pool with heavy bias toward **off-road / pathway rides**, **genuine loops** (not out-and-back), and **ocean routes**. E-bikes mean elevation is no longer a constraint. Weather is de-prioritized.

## Current state (verified)
- Pool: 7 routes, only 1 genuine loop (Sand Point, 13.7mi/4,964ft endurance). Other 6 are out-and-back road rides, trail_ratio 0.26–0.49.
- Discovery (`bike_route_pool.py discover`) only produces out-and-back road routes via bearing-grid OSRM.
- OSRM bicycle profile **does** route on Nisene Marks fire roads + singletrack (tested: trail_ratio 0.39–0.52, genuine loops confirmed).
- Coastal network (Capitola/Seacliff/Rio Del Mar) has cycleways, bike paths, beach trails, pedestrian bridges — routable.

## What I'll build

### 1. New loop generator: `build_offroad_loops.py`
Multi-waypoint OSRM routing (up one trail, down a different one) to force genuine loops. Sources:
- **Nisene Marks fire-road loops** — up Aptos Creek Fire Rd, down West Ridge / Loma Prieta / Porter / Bridge Creek / Trout Gulch / Aptos Creek Trail / Millpond. (Tested: 9.3–18.8mi, trail 0.39–0.52, all genuine loops.)
- **Deep park loops** — extend to West Ridge deep point, Hinckley Basin, Olive Springs, Rusk Grade, Fern Flat (28mi+).
- **Coastal loops** — Capitola/Seacliff/Rio Del Mar via cycleways, Peery Park bike path, East Cliff Drive Parkway, beach trails, pedestrian bridges. Ocean-adjacent.
- **Mixed loops** — park climb + coastal return for variety.

### 2. Rewrite discovery to prefer loops + off-road
- `bike_route_pool.py discover` gains a **loop-first** mode: probe multi-waypoint trail combos before falling back to out-and-back.
- Score each candidate: `trail_ratio` (off-road fraction) + `loop` (start≈end) + `ocean` (proximity to coast). Sort pool by composite score so the daily rotation serves the best rides first.

### 3. Raise elevation ceiling
- `MAX_CLIMB_FT` 1000 → **~4000** (e-bikes). Opens the deep park and ridge routes.

### 4. Expand the pool massively
- Target **25–40 routes** (from 7), spanning: short park loops (9–12mi), mid loops (12–20mi), deep/endurance loops (20–30mi), coastal loops (8–15mi), mixed park+coast.
- Each tagged: `park`, `coastal`, `trail_ratio`, `loop`, `distance`, `gain_ft`, `endurance`.

### 5. Daily selection: variety + preference
- Rotation stays (ISO week × weekday) but now cycles across a large, diverse pool.
- **Preference weighting** so off-road loops and coastal rides surface more often than road out-and-backs.

### 6. Weather: de-prioritized
- Drop weather from the daily brief (or keep as a one-line optional note only). No weather-driven route selection.

## Feature list (deliverables)
- [ ] `build_offroad_loops.py` — generates Nisene + coastal + mixed loops, legality-gated, deduped, added to pool.
- [ ] `bike_route_pool.py` — loop-first discovery, composite scoring (trail/loop/ocean), raised climb ceiling, preference-weighted daily pick.
- [ ] Pool grown to 25–40 routes with tags.
- [ ] Daily brief updated: reports off-road %, loop status, coastal proximity; weather removed/de-prioritized.
- [ ] Legality re-verified on all new routes (Overpass gate).
- [ ] Vault note + skill updated.

## Open questions for you
1. **Distance range** — target daily rides around 8mi, or is 9–20mi fine given e-bikes? (I lean: keep a spread, 8–20mi, with a few 25–30mi endurance options.)
2. **Ocean definition** — "near the ocean" = within ~1mi of coastline, or actually riding along the coast (Capitola/Seacliff esplanade)? I'll tag both.
3. **Keep the existing 6 road out-and-backs** in the pool (de-prioritized), or purge them for a fully off-road/loop pool?
