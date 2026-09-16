# Context — CEVA Hackathon

Note for Claude: read this file at the start of the conversation to resume
work without redoing the same analysis from scratch.

## Goal

Team of 8, hackathon with the CEVA/FVL dataset on vehicle transport in
Europe. Need to identify ONE problem, prove it with real numbers (not
invented), and build a 7-minute pitch around it (context → problem →
evidence → solution → value → feasibility → closing).

Relevant judging criterion: 20% of the score is on analysis, and criterion
03 requires never inventing a value and disclosing data limitations. So:
verify what the data actually says first, then pick the problem — not the
other way around.

## STATUS — verification done, problem selected (see below)

The original Excel file (`FVL - Transport Operations 2026.xlsx`, sheet
`Data`, 399,718 rows) was converted to `data/fvl_transport_2026.csv` and
`analyze.py` was run on the real data. Key findings, with numbers:

- **GLOSSARY sheet** (in the original Excel file) defines every column —
  primary source, check it there when in doubt, don't re-guess.
- **Empty Kilometers / Trip Distance KM are in METERS, not km**, despite the
  column name. Proof: `Trip Distance KM / 1000` has mean 423, max 3497 —
  plausible European km. This resolves the initial mystery (372,954 "km" on
  Le Havre→Lanester = actually 372.9 km, consistent with the real route).
  **Always divide these two fields by 1000 before using them.**
- **Trip Distance KM already includes the empty km** (per glossary: "Total
  distance of the trip (loaded and empty)"). So `empty/trip` is the share of
  empty km over the total distance driven, not a comparison of two
  independent distances.
- **Empty km and Trip Distance are repeated for every VIN in the same trip**
  (Trip Leg Number): 399,718 rows but only 106,553 unique Trip Leg Numbers
  (~3.75 VINs/trip on average). For any absolute total in km/€/CO2 you must
  deduplicate by Trip Leg Number BEFORE summing — summing raw rows multiplies
  the result by the number of vehicles on the truck. The empty/trip ratio
  itself is robust even without dedup (it cancels out).
- **Central number confirmed, at trip level (deduplicated):**
  across 41,197 trips with valid distance, **16.8M total km driven, of which
  5.79M empty km → 34.45% of all distance driven is empty.**
  Same figure (33.96%) at raw-row level too — the ratio is robust. **This is
  the number to pitch for problem 1.**
  Note: only 273,170 of 399,718 rows (68%) have non-null Trip Distance KM,
  and only 41,197 of 106,553 Trip Leg Numbers have a value — reason not yet
  fully confirmed (possibly: empty km requires knowing the truck's NEXT
  trip by construction, so the last trip of each truck in the observed
  period stays NaN — plausible but not 100% verified).
- **Loading Factor**: it's the SUM of the individual Loading Factors of all
  VINs in the trip (not a vehicle count), with max truck capacity ~10. Real
  mean 9.1, median 9.3 → trucks already run ~91% loaded on average.
  **Problem 2 (under-filling) is therefore weak**: little room to improve
  loading, the real issue is trucks driving many km empty between loads
  (= problem 1), not driving half-empty while loaded.
- **Delays (problem 3)**: median delay = 0 days, mean 0.66 days, only 1.45%
  of trips delayed more than 30 days, 0.017% more than a year (rare extreme
  outliers, e.g. max 2649 days — an isolated data error, not
  representative). **Deliveries are essentially on-time in aggregate:
  problem 3 is weak**, doesn't hold up as a headline.
  Oddly high (46%) is the share of rows where Target Delivery Date precedes
  Departure Real date — not yet understood whether this is normal process
  (target set at order time, before the real departure) or an anomaly;
  either way it doesn't translate into significant real delays, so low
  priority.

**Conclusion: the problem to pitch is #1 (empty km / zero-load
repositioning), with the number 34.45% of total distance driven as the
central evidence.** Natural next step: translate empty km into € (fuel/wear
cost per km) and CO2 (emission factor per km), with explicitly declared
assumptions (judging criterion 03: never invent a value without disclosing
the assumption).

## Folder structure (as of this update)

```
data/
  xlsx/   raw Excel originals (all 6 files, gitignored)
  csv/    converted CSVs, one per sheet (gitignored)
```

`convert_xlsx.py` (`make convert`) converts every sheet of every xlsx in
`data/xlsx/` into `data/csv/<file>__<sheet>.csv`, except
`FVL - Transport Operations 2026.xlsx`, whose `Data` sheet is the main
dataset and stays at the fixed path `data/csv/fvl_transport_2026.csv` (all
scripts import/reference this exact path — don't rename it without updating
`analyze.py`, `cost_estimate.py`, `dashboard.py`).

All 6 files now converted:
- `fvl_transport_2026.csv` — main transport dataset (see above)
- `light_vehicle_production_forecast_08_26_2026_04_35_pm__data.csv`
- `light_vehicle_sales_forecast_brand_segment_08_26_2026_04_37_pm__data.csv`
- `vehicle_production_export_08_26_2026_04_36_pm__data.csv` — the S&P
  production-by-plant/destination file discussed earlier (dataset #5 below)
- `donnees_immat_regions_departement_vp_v2__*.csv` (4 sheets: new/used ×
  department/region) — likely dataset #4/#5 (deliveries vs registrations by
  department)
- `statistiques_sdes_immatriculations_2025_france_entiere_donnees_v4__*.csv`
  (11 sheets) — the SDES registrations file (dataset #3 below), including an
  energy-mix-by-year breakdown (`vp_energie`, etc.) relevant to problem 4
  (electric transition)

None of these 5 extra files have been analyzed yet — only converted and
inventoried. They're not needed for the core problem-1 pitch (already
built), only for the optional problem-4/5 narrative layer.

## Known datasets (from conversation context, not all loaded yet)

1. **FVL transport CSV** (~400k rows) — the main dataset, now provided in
   `data/`. Relevant columns:
   `Empty Kilometers in the trip`, `Trip Distance KM`, `Loading Factor`,
   `Number of Vehicle per Truck`, `Departure Real date`, `Real Delivery Date`,
   `Target Delivery Date`, plus departure/delivery compound and French
   delivery department. See findings above for resolved anomalies.
2. **S&P energy-mix file** — ICE vs electric/multi-energy projections
   through 2033 (for the "network not ready for the electric transition"
   thesis).
3. **SDES file** — vehicle registrations by French department, data through
   2025 (for comparing territorial demand vs deliveries). Careful with the
   time mismatch vs the 2026 CSV: use only for trend/geography, not an
   exact year-by-year comparison.
4. **Deliveries-by-department CSV** — probably the same as file #1 (it has a
   delivery-department field), to be confirmed.
5. **S&P Vehicle Production Export** — production by plant (plant, country,
   region) with destination (region/market/country) and annual volumes
   CY2026→CY2033. Useful for the "where do cars flow in Europe" narrative,
   less so for the main quantitative problem.
6. (a possible other file mentioned but not yet detailed)

## The 5 candidate problems discussed

1. **Empty km / zero-load repositioning** — strongest candidate (measurable
   in €, data available), confirmed by the analysis above.
2. **Under-filled trucks (loading factor)** — checked and ruled out as weak
   (see findings above): trucks already run ~91% loaded.
3. **Delivery delays** — checked and ruled out as weak: deliveries are
   essentially on-time in aggregate.
4. **Network not ready for the electric transition** — strategic thesis
   (crossing S&P mix + operations), weak on the "found in the data" side,
   strong as narrative layered on top of a quantitative problem.
5. **Delivery / territorial demand mismatch** — crossing deliveries by
   department (CSV) vs registrations by department (SDES). Limitation: SDES
   stops at 2025, the CSV is 2026 → trend/geography only, not an exact
   comparison.

**Decision: problem 1 (empty km) is confirmed as the one to pitch.** 4 and 5
can still be used as narrative/context layered on top of the chosen number.

## Analysis done so far

1. `make run` (`analyze.py`) — sanity checks: empty km vs trip distance,
   loading factor, date quality. See findings above.
2. `make cost` (`cost_estimate.py`) — translates empty km into € and CO2
   using declared assumptions (fuel 0.55 EUR/km, all-in 1.20 EUR/km, CO2 900
   g/km): **5,786,232 empty km → ~€3.18M fuel-only / ~€6.94M all-in / ~5,208
   t CO2 per year.**
3. **Concentration by origin** (`dashboard.py`, `compute_summary`): 55
   distinct origins, but **81% of total empty km comes from just 10 of
   them** (top: CEVA MARCKOLSHEIM 1.64M km, CEVA LE HAVRE 946K km, CEVA
   BLYES 489K km, ...). Data-quality flag: CEVA HORDAIN shows an
   empty/total share above 100% for that origin — physically impossible,
   isolated bad data, exclude it from headline claims.
4. `make dashboard` (`dashboard.py`) — generates a static, self-contained
   local `dashboard.html` (no server, no external assets) with KPI tiles,
   a ranked bar chart of top origins, a detail table, and the assumptions
   disclosed in a footnote.

5. **Delay vs. vehicles-per-truck** (`dashboard.py`, `delay_by_vehicle_count`):
   **no meaningful relationship** (Pearson r ≈ -0.03). Mean delay stays
   between 0.2 and 2 days across the common range (1-10 vehicles/truck,
   >99% of rows). A spike at 12/14 vehicles/truck (mean delay 6-7 days) is
   based on only ~580 rows out of 273k — not statistically reliable, don't
   pitch it.

6. **Other candidate problems checked** (`fleet_analysis.py`):
   - **Cross-border share: ~0%** (dataset is FR→FR only) — not a usable angle
     with this file.
   - **Vehicle model (`Code Model CEVA`)**: codes are anonymized, no way to
     identify EVs or link to the S&P powertrain-mix file — not usable without
     more data.
   - **Fleet concentration (real trucks only)**: `Transport Truck Licence
     Plate` has 3 impossible placeholder values (one alone covers 32% of all
     trips — not a real truck). Excluding those, 11,667 real trucks handle
     67,797 trips, and **the top 10% of trucks carry 76% of all trips** — a
     genuine second concentration finding, complementary to the origin
     concentration (problem 1 fixes have outsized impact if targeted at this
     core fleet).
   - **Route-level delay hotspots**: Saint-Vulbas → Colombes stands out —
     3,589 trips (high volume, not noise) with 16.4 days average delay. Best
     candidate if you want a second, delay-specific pilot corridor.
   - **Same-city trips** (Departure City == Delivery City): 2.6% of trips
     (2,769) — likely legitimate intra-compound moves, kept as a caveat, not
     a headline number.

6. **Matching-opportunity simulation** (`matching_opportunity.py`, new
   "solution" section on the dashboard) — this is the innovative,
   demoable solution, not just a proposal. For every empty-running trip, we
   checked whether a compatible departure request already existed nearby
   (same French department, from the delivery zip code) within 3 days of
   the delivery that freed the truck. Result, on the real 41,197 trips:
   **33.5% of empty trips (11,880 of 35,410) had a real, pre-existing
   match — 29.5% of all empty km (1,696,184 of 5,751,244 km)**. This is a
   measured lower bound (no truck-capacity assignment, just demand
   presence), disclosed as such. It reframes the solution from "we
   recommend backhaul matching" (generic) to "we proved on your own data
   that ~30% of the problem is solvable with better dispatch, not more
   trucks or route redesign" — this is what should anchor the "quality and
   originality of the solution" (15%) and "feasibility" (15%) criteria.
   The pilot at Le Havre should now be framed as deploying this exact
   matching engine as a live dispatch-assist tool.

7. **Interactive matching demo** (`matching_opportunity.demo_data`, "Try it"
   section on the dashboard) — a client-side, no-backend tool: pick one of
   the 50 biggest real empty-running trips, it searches the same historical
   data (embedded as JSON, ~3.5MB) for compatible nearby departures within
   the window, showing "without matching: X km empty" vs "with matching:
   these departures were available". Honest about no-match cases too (not
   rigged to always find one) — verified with node that 11/50 curated
   examples find a match, consistent with the ~33.5% overall rate.

8. **Geographic demand mismatch** (`geo_mismatch.py`, second differentiator
   angle, requested explicitly because other hackathon teams likely share
   the empty-km problem) — crossed FVL delivery volume by department
   against SDES new-car registration volume by department (2025, national).
   Correlation across 94 departments: **r = 0.63** (moderate, not tight).
   Two outliers: **Hauts-de-Seine (92) is over-served 3.6×** (16.5% of FVL
   deliveries vs 4.55% of national registrations) while **Paris (75) is
   under-served to 0.19×** (1.2% of deliveries vs 6.6% of registrations —
   the largest registration share in France). Two honest competing
   explanations disclosed on the dashboard: (a) truck access restrictions
   in central Paris route deliveries through a 92 hub with an untracked
   last mile, or (b) French corporate/leasing fleets are often registered
   at a Paris head-office address regardless of actual usage location —
   can't distinguish between them with this data alone. Caveat: SDES 2025
   vs FVL 2026, used as a geography proxy not an exact year match.

## MAJOR PIVOT — agentic Streamlit dashboard (local LLM + LangGraph)

The static `dashboard.html` demo (empty-km narrative, matching demo, geo
mismatch) was retired as the primary live surface — replaced by an
interactive app: `make agent` launches a Streamlit app (`app.py`) with two
tabs:
1. **Dispatcher check** — the flagship feature: a form (pick a real truck +
   enter a Loading Factor), checked against `loading_factor_alert.py`'s
   `check_alert()`: alerts when `entered_lf < that truck's historical max
   Loading Factor - 0.5`, and suggests an alternative truck from real
   history whose own max comfortably fits the load. Mirrors the real
   dispatcher workflow described by the user.
2. **Ask the data** — a chat box; a local Ollama model (`qwen2.5:3b-instruct`)
   picks one of 6 fixed tools via constrained JSON-schema decoding
   (`agent/graph.py`, `agent/llm.py`), covering the 5 existing analyses
   (empty_km_cost, matching_opportunity, geo_mismatch, fleet_concentration,
   delay_analysis) plus loading_factor_alert.

**Critical design decision, found through testing, not assumed upfront**:
the 3B local model is reliable at *picking* the right tool (8/8 on a mixed
IT/EN test set including deliberately out-of-scope questions like "what's
the weather in Paris?") but was **unreliable at freely narrating the
result** — in testing it invented a wrong currency ("yuan"), hallucinated a
nonexistent truck suggestion ("CEVA MARCKOLSHEIM" — not even a valid plate
format), and tagged "EUR" onto Loading Factor values (not a currency). So
the answer text is generated by a **deterministic Python template per tool**
(`agent/tools.py`'s `narrate()`), not a second LLM call — this guarantees
every number/word shown is exactly what the analysis function returned,
preserving criterion 03 even with an LLM in the loop. This also roughly
halved per-turn latency (~28s → ~14s for a chat question; the dispatcher
form path skips the LLM router entirely when the tool is already known via
form submission, so it's near-instant, ~0.2s).

**Real bug found and fixed**: `app.py`'s data loader was first decorated
`@st.cache_data`, which hashes/pickles the return value — on ~400k-row
DataFrames this made the app balloon to 6.3GB+ RSS and nearly exhaust the
machine's 7.6GB RAM (only 326MB free at one point) while appearing to hang.
Fixed by switching to `@st.cache_resource` (holds a reference, no
hashing/copying) — memory settled back to a healthy few GB used with
multiple GB free.

**Environment notes for next session**:
- Ollama server must be running (`make agent`/`ollama-serve` target starts
  it) and `qwen2.5:3b-instruct` must be pulled (`ollama list` to check) —
  pull needs internet, do it before a demo, not during.
- Machine is WSL2, 7.6GB RAM, no GPU — inference is CPU-only. Keep prompts
  short; avoid re-adding a free-text narrator LLM call without similar
  templating safeguards if that path is revisited.
- Automated headless-browser screenshot verification of the Streamlit app
  was attempted (6 different approaches: legacy/new headless mode,
  virtual-time-budget, dump-dom, CDP via remote-debugging-port, playwright
  CLI) and never reliably captured post-WebSocket-render content — likely a
  limitation of this sandboxed environment's headless browser vs
  Streamlit's WebSocket-driven rendering, not necessarily an app bug (the
  backend was separately verified thoroughly via direct Python calls: all 6
  tools, the full LangGraph graph end-to-end, router accuracy, latency). A
  human should do one manual visual check of http://localhost:8501 before
  relying on it for a live demo.

Files added this pivot: `agent/__init__.py`, `agent/schema.py`,
`agent/tools.py`, `agent/llm.py`, `agent/graph.py`, `loading_factor_alert.py`,
`app.py`. `Makefile` gained `ollama-serve`, `ollama-pull`, `agent` targets;
`all` now ends in `agent` instead of the old static `serve`.

**Cleanup pass (after the pivot settled)**: `dashboard.py` and the generated
`dashboard.html` (5MB, stale JS demo) were deleted — fully superseded by the
Streamlit app. The 2 functions from `dashboard.py` still needed by
`agent/tools.py` (`compute_summary`, `delay_by_vehicle_count`) were moved to
a new, honestly-named `stats.py`. `matching_opportunity.py`'s `demo_data()`
was also deleted (only used by the old JS client-side demo, dead since the
real matching tool now lives in the agent). Every file is back within
CLAUDE.md's soft guideline (≤5 functions/file): `stats.py` has 2,
`matching_opportunity.py` has 3. `Makefile`'s `dashboard`/`serve` targets
were removed along with the file they ran.

## Dispatcher simulation, Step 1 — lot composition (mock data)

Added a more realistic front-end to the "Dispatcher check" tab, above the
existing truck+alert form (untouched, not yet wired to this): a simulation
of the dispatcher picking cars into a batch before assigning a truck.

- `mock_fleet.py` — fictional but realistic car/trip data (we don't have a
  real per-vehicle compound inventory). 50 seeded cars (reproducible across
  runs) across 3 compounds — reusing the **real** top-3 empty-km origins
  (CEVA MARCKOLSHEIM, CEVA LE HAVRE, CEVA BLYES) so the simulation stays
  tied to the actual analyzed problem. Each car: fake VIN (real WMI prefixes
  per brand), model/category/loadingRatio (citadine 0.8, berline 1.0, SUV
  1.3, utilitaire 1.8, ± small jitter), a French-city destination with
  lat/lng, compound, and disponible/reservee status. 2 predefined trips per
  compound (`TRIP_STOPS`), each with stops + cumulative km.
- `lot_builder.py` — `render_lot_builder()`: compound selector → `st.data_editor`
  checklist of that compound's available cars (checkbox column) → trip
  selector → live "LOT LOADING" total (sum of checked cars' loadingRatio),
  styled monospace/bold/red as the hero figure. State kept in
  `st.session_state` (`lot_car_ids`, `lot_trip_id`, `lot_loading`) for later
  steps to consume.
- Wired into `app.py`'s `render_dispatcher_form()` as step "1. Compose the
  lot", followed by a divider and the pre-existing step "2. Assign a truck"
  (renamed from its old lone heading, content otherwise untouched — the
  manual "Loading Factor entered" number input is NOT yet replaced by
  `lot_loading`, on purpose — that wiring is a future step, not built yet
  per explicit instruction).

Kept out of app.py itself (which was already at 6 functions, over
CLAUDE.md's 5-function-per-file guideline) to avoid making that worse — new
logic lives in the 2 new files above instead.

Verified: `generate_cars()`/`generate_trips()` produce sane distributions
(50 cars, 42 disponible/8 reservee, spread across the 3 compounds and 4
categories); screenshot-confirmed the UI renders and the table/trip
selector/total display correctly.

**Next steps (not built yet, per instructions)**: step 2 = truck choice
UI grounded in this lot (probably suggest trucks whose historical max fits
`lot_loading`); step 3 = wire `lot_loading` into the existing
`loading_factor_alert` check instead of the manual number input.

## Dispatcher simulation, Step 2 & 3 — truck picker + under-loading alert

- `mock_fleet.py` gained `MOCK_TRUCKS`: 6 hardcoded fictional trucks
  ({id, plate, model, maxLoading, type}), maxLoading in {8.5, 9.0, 10.0}.
- `truck_picker.py` (`render_truck_picker()`) — step "2. Assign a truck":
  dropdown over `MOCK_TRUCKS`, a recap card (plate/model/type), and
  LOT LOADING vs TRUCK MAX LOADING side by side in monospace. Stores
  `st.session_state.picked_truck`. **This replaced** the old ad-hoc
  real-truck dropdown + manual Loading Factor number input + inline
  `loading_factor_alert` tool call that used to live directly in
  `app.py`'s `render_dispatcher_form()` — removed per explicit instruction
  when building this step (the real `check_alert()`/`loading_factor_alert`
  tool is untouched and still reachable via the "Ask the data" chat tab,
  just no longer wired into the dispatcher form).
- `loading_check.py` — pure logic: `LOADING_ALERT_THRESHOLD = 0.5` (named,
  easy to change) and `check_loading(lot_loading, truck_max) -> dict`
  (`gap = truck_max - lot_loading`, `alert = gap > LOADING_ALERT_THRESHOLD`
  — exclusive, so gap == 0.5 does NOT alert, tested).
- `alert_ui.py` (`render_loading_alert()`) — step "3. Loading check": red
  (`#E20101`) alert card with CURRENT LOADING / MAX LOADING / GAP in
  monospace + a fill gauge when `alert` is true; a discreet green one-liner
  when not. "See cars to add" button sets
  `st.session_state.want_car_suggestions = True` — a hook for step 4
  (not built yet), nothing reads that flag currently.

All three wired in sequence inside `app.py`'s `render_dispatcher_form()`
(lot builder → divider → truck picker → divider → loading alert).

**Recurring gotcha this session**: when a new module-level constant/list is
added to a file already imported by a long-running Streamlit process (e.g.
adding `MOCK_TRUCKS` to `mock_fleet.py` after it was already imported),
Streamlit's poll-based file watcher can leave a stale cached module in
memory → `ImportError` on rerun even though the file on disk is correct. A
clean process restart (`pkill -f "streamlit run app.py"`, relaunch) always
fixes it. Budget for this after every step that touches `mock_fleet.py` or
any other already-imported module.

**Next step (not built yet, per instructions)**: step 4 = a table of
candidate cars to add to the lot to close the gap, triggered by the
"See cars to add" button.

## Dispatcher simulation grounded in real data (trucks + aggregate check)

Two additions, both using real FVL data instead of mocks:

1. **Real trucks in step 2** (`loading_factor_alert.truck_options()`) —
   the truck picker no longer uses `MOCK_TRUCKS`; it lists real license
   plates from the 2026 data (excluding the 3 placeholder plates), each
   with its real historical max Loading Factor and trip count, top 50 by
   activity (of 656 trucks with ≥5 trips). `truck_picker.py` updated to
   match (no more fake model/type — just plate + real max + trip count).
   `mock_fleet.MOCK_TRUCKS` is now unused dead code (kept for now, not
   deleted — cars/trips still use mocks).

2. **Aggregate real-data validation** (`underloading_stats.py`) — applied
   the dispatcher alert's own rule (gap > 0.5 vs. a truck's historical
   reference) to all 40,841 real 2026 trips. **Important finding, caught
   before shipping it**: using each truck's single best-ever Loading
   Factor as the reference flags 94% of trips — a statistical artifact
   (comparing every trip to a truck's all-time peak necessarily flags
   most trips, like comparing every day to the year's hottest day). Using
   the truck's **median** Loading Factor instead gives a defensible
   **28%** — the number now shown, with the 94% figure disclosed
   alongside as a labeled upper bound, not hidden. Both computed and
   verified via `uv run python -c "..."` before writing any UI, same
   methodology as every other finding in this project (check before you
   pitch). Displayed as a caption under the dispatcher form in `app.py`.

Both verified via `streamlit.testing.v1.AppTest` (zero exceptions, real
truck plate "TransportTruck_596661 (max 13.4, 340 trips on record)" loads
correctly, full click-through of Select still updates the lot live).

## Four more feature additions (A/B/C/D), all verified via AppTest

- **A — real trip options**: `mock_fleet.TRIP_STOPS` no longer invented.
  Each compound's 2 trip options are now the real top-2 most frequent
  Delivery City destinations from that compound in the 2026 data (checked
  via groupby before writing: e.g. Le Havre → Rouen 101km / Boissy-sous-
  Saint-Yon 299km), single-stop (real data is point-to-point, not
  multi-stop — the old 2-stop invented routes were themselves a
  simplification that didn't map to reality). `CITIES` extended with the
  new real destination coordinates.
- **B — adjustable alert threshold**: `loading_check.check_loading()` and
  `underloading_stats.compute_underloading_stats()` both take an optional
  `threshold` param (default still `LOADING_ALERT_THRESHOLD`). A slider in
  `alert_ui.py` (key `alert_threshold` in session_state) drives both the
  step-3 alert AND the real-data caption together — moving it to e.g. 1.5
  correctly drops the caption to 11%/72% (verified).
- **C — real truck trip history**: `truck_picker.py` gained
  `_truck_history()` and an expander showing the selected real truck's own
  last 15 trips (date + Loading Factor) — makes the median-vs-max point
  visually obvious (a single outlier day stands out in the list instead of
  being an abstract number).
- **D — Le Havre as default compound**: `COMPOUNDS` reordered
  (`["CEVA LE HAVRE", "CEVA MARCKOLSHEIM", "CEVA BLYES"]`) to match the
  pilot site already chosen in the pitch (highest empty-km share).

`mock_fleet.MOCK_TRUCKS` removed (confirmed unused — trucks are 100% real
now via `loading_factor_alert.truck_options()`). Cars in step 1 are still
mock (no real per-vehicle compound inventory exists in the source data).

**Bug found right after shipping the real trucks, fixed same session**: of
the 656 qualifying real trucks, **582 (89%) have a historical max Loading
Factor above 10** — and in the top-50-by-activity list actually shown in
the picker, 49/50 exceeded it. The FVL glossary calls 10 a "general rule"
capacity, not a hard physical ceiling (a truck full of compact cars can
legitimately sum past 10), so this isn't confidently labeled a data error —
but it made the simulation incoherent: the mock cars in step 1 are
calibrated to loadingRatio ~0.8-1.8 (sized for a ~9-10 max truck), so a
truck with a real max of 13-16 produced an unclosable gap and a "cars to
add" step that couldn't do its job. Fixed by adding `max_loading_cap=10.0`
to `truck_options()` — the picker now only lists real trucks whose own
historical max is ≤10, keeping the simulation demo-coherent without
overclaiming a data-quality verdict on the excluded trucks. Verified via
AppTest: default truck went from an outlier (max 13.4) to a representative
one (TransportTruck_53016, max 7.0, 227 trips).

## Third tab: "Features & Roadmap" (pitch-facing, static)

Added for the demo/pitch, not for the analysis — `features_ui.py`
(`render_features()`), a third app.py tab alongside "Dispatcher check" and
"Ask the data". Two sections:
1. **"What we built"** — 6 feature cards, each with a one-line proof point
   AND which judging criterion it supports (e.g. "Matching engine, tested
   on real data... Proves: Solution quality · Feasibility") — deliberately
   not a bare feature list, tied to the actual rubric.
2. **"Where we're taking it"** — the Now/Next/Later roadmap drafted with
   the user: pilot at Le Havre (now) → roll out to the rest of the top-10 +
   real car inventory + chat-agent/dispatcher integration (next) → TMS
   integration, EV-fleet extension, capacity-as-business-lever (later).

Pure static content, no data dependency — safe, fast, can't break from a
data/model issue. Verified via Playwright (real click on the tab, DOM
positions confirm the 3-column roadmap grid renders side-by-side
correctly, not stacked).

**Follow-up — each roadmap card got a working "Try it" demo**, per
explicit request, not left as pure text:
- **NOW**: real live metric — Le Havre's actual empty-km share (41.5%,
  computed via new `stats.origin_empty_share()`), not a static number.
- **NEXT**: real side-by-side empty-km share for all 3 dispatcher
  compounds (Le Havre 41.5%, Marckolsheim 36.1%, Blyes ~39.7%) proving
  "ready to scale" isn't aspirational — plus a genuine cross-tab
  connection: if a truck was picked in "Dispatcher check"
  (`st.session_state.picked_truck`, shared across tabs since it's one
  running app), this card shows its real historical max live — a working
  preview of "chat ↔ dispatcher" integration using data that already
  exists, not a mock.
- **LATER**: explicitly labeled illustrative/sample — an ICE/EV mix
  slider and a sample "capacity marketplace" table, clearly stamped
  "SAMPLE — not connected to any real system", per the user's explicit
  choice (asked directly: mock it clearly rather than leave it text-only).

All 3 verified via AppTest, including the cross-tab truck connection
(picked truck in the dispatcher shows up correctly in the Features tab's
NEXT card on rerun).

## LangGraph gets a real cycle: "Auto-optimize" (agent/autofill_graph.py)

The user correctly pushed back that the chat graph (`agent/graph.py`) was
basically a single-step LLM classifier + dispatch table — genuinely thin
use of a graph-orchestration library, no cycles, no real multi-step
reasoning. Fix: recognized that the dispatcher's own "check gap -> propose
-> add -> recheck" loop (previously done by hand, one "Select" click at a
time) *is* the natural fit for LangGraph's cyclic graphs.

`agent/autofill_graph.py` — `build_autofill_graph(all_cars, trip)`: a
2-node cycle, `check` (evaluate gap via the same `loading_check.check_loading`;
done=True on optimized / no remaining candidate / `MAX_ITERATIONS=10` hit)
and `pick_best` (calls `proposals.compute_proposals(..., limit=1)` — same
function step 4's manual table already uses, no new selection logic) which
adds the best-fit car and loops back to `check`. Conditional edge on
`check` routes to `pick_best` or `END`.

New "Auto-optimize (agent)" button in `alert_ui.py`, next to the existing
manual "See cars to add" — the dispatcher can either browse proposals by
hand or let the agent iterate automatically; both stay available. Result
(cars added, in order, running total, and why it stopped: `optimized` /
`no_candidates` / `max_iterations`) shown once after the rerun via a
session_state-popped log.

Verified: direct graph test (6 iterations, gap closed 0→6.78 vs 7.0 max);
edge cases (unreachable target correctly stops at `no_candidates` after
exhausting 9 candidates, not an infinite loop; already-optimized start
stops instantly at 0 iterations); full AppTest click-through (button →
lot updates → alert flips to the OK state → log displays correctly).

## Fourth compound (CEVA MARSEILLE) + Leaflet trip map

Added a real 4th compound and a route map, per explicit request ("aggiungi
CEVA Marseille, macchine per Toulon/Cannes/Nizza, e un Leaflet che mostra il
percorso con numeri e km totali").

- `mock_fleet.py`: `COMPOUNDS` gained `"CEVA MARSEILLE"` (confirmed a real
  `Departure Name` in the 2026 data before adding it). New `COMPOUND_COORDS`
  dict (real lat/lng for all 4 compounds) so the map can plot the origin.
  `CITIES` extended with Toulon/Cannes. `TRIP_STOPS["CEVA MARSEILLE"]` is a
  genuine multi-stop route (the only multi-stop entry — the other 3
  compounds' routes are single-stop, per the earlier real-data-only pass):
  Toulon (66km) → Cannes (175km) → Nice (205km cumulative), real road
  distances, cross-checked against haversine as a sanity check before use.
  `EXTRA_CARS`: 4 explicit cars (one per stop, including a short local
  Marseille delivery) so the compound has cars to compose a lot with,
  merged into `MOCK_CARS = generate_cars() + EXTRA_CARS`.
- `trip_map.py` (new, `render_trip_map(compound, trip)`) — embeds a
  folium/Leaflet map (`streamlit-folium`) in the lot builder: numbered
  markers, compound = 1 (dark) through the last stop (accent red),
  connected by a polyline, bounds auto-fit. Beside the map: `st.metric`
  for stop count and total km. Wired into `lot_builder.py` right after the
  trip selector.
- **Bug caught before shipping**: `folium.Map(..., tiles="CartoDB positron")`
  triggers `UserWarning: CartoDB tiles now require an API key` — the base
  map would not actually render for a real user without one. Switched to
  `tiles="OpenStreetMap"` (free, no key required) before finalizing.
- **Follow-up fix, explicit user request**: the first version connected the
  4 stops with a straight line (great-circle-ish), not an actual road path.
  `trip_map._road_route()` now calls the public OSRM routing API
  (`router.project-osrm.org`, free, no key) with all stop coordinates in
  order and draws the returned road geometry instead — verified it returns
  ~3,920 points tracing the real Marseille→Toulon→Cannes→Nice road corridor
  (not a straight line). Cached with `st.cache_data(ttl=3600)` so it's one
  network call per trip per hour, not one per rerun. Falls back to the old
  straight-line points if OSRM is unreachable (`try/except` around the
  request) — the map still renders without internet, just without the road
  curve; this is a real, likely failure mode (venue wifi), not a
  speculative one, so the fallback is warranted. The "Stops"/"Total
  distance" metrics are untouched — they still come from the real
  `TRIP_STOPS` km data, not from OSRM's own distance estimate (which
  differs slightly, ~223km via roads vs the dataset's 205km, expected since
  one is an actual routing engine and the other real historical trip data).
- New deps: `uv add folium streamlit-folium requests` (folium 0.20.0,
  streamlit-folium 0.27.4, requests already a transitive dep, now explicit).

**Second follow-up fix, explicit user request**: the trip was still a
separate pre-selected dropdown ("Toulon → Cannes → Nice"), disconnected
from which cars the dispatcher actually checked into the lot — exactly the
disconnect the user called out ("il trip non deve essere già scelto ma
deve essere creato in funzione delle macchine che scelgo"). Fixed by
building the trip live from the selected cars' own destinations instead:
- `mock_fleet.py`: removed `TRIP_STOPS`, `generate_trips()`, `MOCK_TRIPS`
  entirely (orphaned by this change — no longer any predefined route list).
  Car destinations were already a random pick from the real 18-city
  `CITIES` list per car, independent of compound — that part is unchanged,
  it's the map/route that now reacts to it instead of ignoring it.
- `trip_map.render_trip_map(compound, destinations)` signature changed:
  takes the list of the *currently selected* cars' destination dicts
  (deduped by city) instead of a fixed trip object. Internally calls
  OSRM's **Trip service** (`/trip/v1/driving/...?source=first&roundtrip=false`)
  which solves the visiting order (a small TSP) AND returns the road
  geometry AND the total distance in one call — verified it reorders an
  intentionally-scrambled Marseille/Nice/Toulon/Cannes input back into the
  correct coastal order (Marseille→Toulon→Cannes→Nice). Falls back to
  input order + straight lines + summed haversine distance if OSRM is
  unreachable (`_fallback_trip`). Returns the resulting
  `{"stops": [...], "totalKm": ...}` dict so the caller can store it.
- `lot_builder.py`: new `_selected_destinations(ids)` (dedupes selected
  cars' destinations by city); trip selectbox removed entirely; the
  returned trip dict is stored as `st.session_state.lot_trip` (replaces
  the old `lot_trip_id` + `MOCK_TRIPS` lookup pattern). No car selected ->
  no map, just a caption prompting selection (a real, reachable state, not
  a speculative one).
- `alert_ui.py` and `proposals_ui.py` updated to read
  `st.session_state.get("lot_trip")` directly instead of searching
  `MOCK_TRIPS` by a now-nonexistent `lot_trip_id` — both the manual
  "See cars to add" (step 4) and the LangGraph "Auto-optimize" cycle
  (`agent/autofill_graph.py`) now score detours against whatever route the
  currently-selected cars actually produce, not a fixed pre-picked one.

Verified via `AppTest`: zero exceptions with no car selected (shows the
caption, no map); zero exceptions after selecting the Toulon+Cannes+Nice
Marseille cars (map metrics: Stops 4, Total distance 223.6 km — OSRM's
live road distance for that specific selection, close to but not identical
to the earlier fixed 205 km figure, expected since that number no longer
comes from a static dataset lookup but from live routing); the "Trip"
selectbox is confirmed gone (`at.selectbox` labels now only "Departure
compound" and "Truck"); full click-through re-verified end to end (pick
car → pick truck → alert → "See cars to add" renders step 4 with no
exceptions).

**Third follow-up, explicit user request**: numbering changed to be
0-indexed with the origin hidden — "gli stop falli partire da 0 e lo zero
non mostrarlo così la prima macchina che selezioniamo è 1". The compound
is now stop 0 on the map (still plotted, dark marker, but with no digit in
it — just a plain dot, tooltip still shows its name on hover), and the
first selected car's destination is marker 1, second is 2, etc. (shifted
down by one from the previous 1-indexed-including-origin scheme). The
"Stops" metric now counts only actual destinations (`len(coords) - 1`),
consistent with the origin no longer counting as a numbered stop — e.g.
the Toulon+Cannes+Nice Marseille selection now shows "Stops: 3" (was 4).
Verified both via `AppTest` (Stops metric = 3) and by calling
`trip_map._solve_trip` directly to confirm marker labels: Marseille = ''
(hidden), Toulon = '1', Cannes = '2', Nice = '3'.

Verified via `AppTest`: zero exceptions on default load and after switching
to CEVA MARSEILLE; compound dropdown lists all 4; trip dropdown shows
"Toulon → Cannes → Nice (205 km)"; map metrics show Stops: 4, Total
distance: 205 km — exactly the numbering the user asked for (Marseille=1,
Toulon=2, Cannes=3, Nice=4).

## Features & Roadmap tab hidden

Per explicit request, the 3rd tab is no longer shown in `app.py` — `st.tabs`
now only has "Dispatcher check" and "Ask the data". `features_ui.py`,
`stats.origin_empty_share()`, and the demo logic inside them are untouched
on disk (not deleted, just unreferenced) in case the roadmap pitch section
is wanted back later; `app.py`'s now-unused `render_features`/
`origin_empty_share` imports were removed since they were orphaned by this
change. Verified via `AppTest`: zero exceptions, `at.tabs` labels confirm
only the 2 remaining tabs.

## Chat answers now disclose their data + assumptions

Per explicit request ("vorrei che mi rispondesse con i dati che ha usato,
dati veri, come ha calcolato il costo della benzina") the "Ask the data"
chat answers now have an optional "Data & assumptions used" expander under
each result, not just the one-line templated answer.

- `agent/tools.py` gained `methodology(name, result) -> str | None`
  (3rd function in the file, still within the 5-function guideline) —
  returns None where the answer is already fully self-explaining, or a
  markdown block for tools with non-obvious inputs:
  - `empty_km_cost`: real trip/km counts used, then the 3 declared cost
    assumptions from `cost_estimate.py` (fuel 0.55 EUR/km, all-in 1.20
    EUR/km, CO2 900 g/km) with a one-line worked calculation
    (empty_km × all-in rate = the displayed cost).
  - `matching_opportunity`: states the real matching rule (same French
    department, within `WINDOW_DAYS=3` of the delivery) and that it's a
    measured lower bound, not a promise.
- `app.py`'s `render_result()` calls it after the existing metrics/chart
  and wraps the result in `st.expander("Data & assumptions used")` —
  applies to both a live answer and replayed history turns (same render
  path). No expander appears for tools where `methodology()` returns None.

**On the "why is chat slow" question asked alongside this**: not a bug —
the router step is a real CPU-only local LLM call (qwen2.5:3b via Ollama,
no GPU, WSL2), ~10-15s per turn; explained to the user directly rather than
changed, since local-only inference was an explicit earlier design choice
(no data leaves the laptop). The answer-text generation itself is instant
(deterministic Python template, no second LLM call — see the "LLM narrator
hallucination" fix elsewhere in this file).

Verified: `agent/tools.methodology()` tested directly against real
`run_tool()` output (correct real n_trips/km numbers, correct assumption
values); full `AppTest` pass injecting a chat turn into
`session_state.history` (bypassing the slow LLM call, mirroring how a real
chat turn ends up in state) — zero exceptions, expander
"Data & assumptions used" renders with the exact same real numbers.

## Visual redesign — enterprise CEVA branding (dataviz skill applied)

Full visual pass across the whole app for a management/jury demo, following
a detailed creative brief (graphics-only parts of it — the brief also had
non-graphics rigor/correctness constraints already satisfied by existing
behavior, left untouched). Used the `dataviz` skill's color-formula and
mark-spec references rather than eyeballing colors.

**Official logo, real colors**: `assets/ceva_logo.svg` downloaded from
Wikimedia Commons (`Logo_of_CEVA_Logistics_(2023).svg`, the current mark —
official brand-center page 403'd on fetch, so Commons was the next-best
verifiable official-looking source), kept unmodified (no recreation). Its
exact fill hexes were extracted directly from the file: navy `#1d2546`,
red `#ff0000`. `theme.py`'s `NAVY`/`ACCENT` and `.streamlit/config.toml`'s
`primaryColor` now use those real values — `ACCENT` is stepped down to
`#D6001C` (not the pure `#ff0000`) because white-on-`#ff0000` is 4.0:1
contrast, under the 4.5:1 WCAG AA text minimum; `#D6001C` clears 5.4:1
while still reading as the same hue next to the mark in the header. This
replaces the earlier `#A6192E` approximation used throughout the session
before the real logo was found.

**theme.py rewritten** as the single source of style, not just color
constants: `logo_data_uri()` (base64-embeds the SVG so it can sit in a flex
header next to text — `st.image` can't do that layout), `inject_base_css()`
(one `<style>` block, called once in `app.py:main()`, defining reusable
classes used across every component file instead of each file repeating
inline CSS: `.ceva-header`, `.ceva-steps` (the 4-step flow strip), `.ceva-card`,
`.ceva-stat-label/-value` (hero figures — switched from monospace to the
default proportional sans per the dataviz skill's figure spec: "hero figure
uses the same sans as everything else... proportional figures for big
numbers, tabular-nums only in table columns"), `.ceva-meter-track/-fill`
(the loading-gap gauge), `.ceva-badge` (+`-real`/`-mock`/`-estimate`
modifiers — the data-provenance labels), `.ceva-empty` (empty states)),
`stat_tile()` and `badge()` helper functions used by every component file.
Old names (`ACCENT`, `TEXT_PRIMARY`, `TEXT_SECONDARY`, `BORDER`,
`DOT_ON_ROUTE`, `DOT_DETOUR`) kept so existing call sites didn't all need
import changes — only values were refined.

**Header + step flow** (`app.py`): real logo + "FVL Dispatch Intelligence"
+ a "Hackathon Demo — Prototype" tag (never implies a shipped product).
A `Compose lot → Assign truck → Check loading → Optimize` strip sits above
the dispatcher tab — kept intentionally simple/honest: only step 1 lights
up as "done" (a real, unambiguous signal — at least one car checked into
the lot); steps 2-4 aren't fake-tracked as done since Streamlit's
selectbox always has a default selection, so "truck picked" isn't a
meaningful completion signal. No new session-state progress-tracking logic
was added beyond this one real check.

**Dispatcher components restyled** (`lot_builder.py`, `truck_picker.py`,
`alert_ui.py`, `proposals_ui.py`, `trip_map.py`): hero numbers (lot
loading, truck max, gap) now use `stat_tile()`; the loading-gap alert uses
the new meter classes with the status-alert color always paired with an
icon + text label ("⚠ Under-optimized trip"), never color alone; "Auto-
optimize" is now `st.button(..., type="primary")` (Streamlit's native
primary styling, themed via config.toml) while "See cars to add" stays
secondary — satisfies "primary action" without custom CSS hacking
Streamlit's button internals. Every truck "max" label now reads
**"historical reference"**, not "capacity" or "max loading" alone — both
in the picker and the trip-history expander caption — so it can't be
mistaken for a certified physical limit (the FVL glossary itself only
calls ~10 a "general rule"). Mock car sections got a `Simulated inventory`
badge; the real-truck section got a `Real fleet data` badge — the
visual real-vs-mock distinction the brief asked for. The map now colors
the origin marker in `NAVY` (was a hardcoded near-black) and the
destination markers in the refined `ACCENT`, plus a one-line color legend
underneath. Table numeric columns switched from `font-family:monospace` to
`font-variant-numeric:tabular-nums` (same visual alignment, correct CSS
property per the dataviz mark spec instead of a full monospace face).

**Auto-optimize before/after summary** (`alert_ui.py`): `_run_autofill`
now also stores the real pre-optimization `lot_loading` value it was
called with (`before_loading`) alongside the graph's own output — no new
computation, just carrying forward a value that already existed in scope.
`_render_autofill_log` renders 3 real stat tiles (Loading before / Loading
after / Gap after) computed entirely from `check_loading`'s existing
formula and the graph's own `added` list — no new metric, no invented
number, per the brief's explicit "usando esclusivamente risultati
realmente calcolati" constraint.

**Chat tab** (`app.py`): each answer now renders inside
`st.container(border=True)` (matches the dispatcher's card language) and
the bar chart color was set to the same `#D6001C` accent instead of
Streamlit's default blue, so a chat answer visually belongs to the same
system as the dispatcher tab. Spinner copy changed from "Thinking..." to
"Analyzing the FVL dataset..." (tone, not logic).

**Skipped, on purpose**: the brief's non-graphics "Rigore" constraints
(don't invent KPIs, don't change formulas/thresholds/agent behavior) were
already satisfied by existing code and required no change — touched
nothing there. The brief also asked to polish "Features & Roadmap" into a
pitch view, but that tab was explicitly hidden by the user's own more
recent instruction earlier in this session — left hidden, not resurrected,
since a specific recent instruction outranks a generic pasted brief.

**Verified**: full `AppTest` run of the dispatcher flow end-to-end (compose
lot with real Marseille cars → assign a real truck → alert triggers →
Auto-optimize via LangGraph → before/after summary renders with real
numbers) — zero exceptions at every step; manual "See cars to add" flow
re-verified; chat methodology expander re-verified; header/logo/stepper
markup confirmed present (logo `<img>` tag, product name, demo tag, badges,
"historical reference" wording) by inspecting the rendered markdown
fragments AppTest exposes. A live-browser screenshot was attempted via
Playwright (as the brief asked, "se disponibile") but hung at the same
"fonts loaded" step documented earlier in this file as a known sandbox
limitation, unrelated to this app — not resolved, DOM-level verification
via AppTest was used instead, same substitute strategy as every other UI
change in this session. A human should still do one manual look at
http://localhost:8501 before presenting to judges/management.

## Standalone landing-hero mockup + dispatcher adopts its visual language

Separate, explicit request: recreate CEVA's real corporate-site hero
section (given a screenshot + detailed CSS/layout spec of the actual
cevalogistics.com homepage) as a polished mockup, then unify the
dispatcher app's own look with it.

- **`ceva_landing_hero.html`** (project root) — a standalone, self-contained
  HTML/CSS page (no Streamlit involvement) recreating the real CEVA site's
  hero: navy header, big reversed logo, condensed-bold "Archivo" headline
  type + "Public Sans" body (Google Fonts), full-bleed diagonal warehouse
  illustration (hand-built inline SVG, not a stock photo), two overlapping
  promo panels ("Rise in motion" / "Engineering winning solutions" — also
  original SVG illustration, not real people's photos, to avoid using an
  unlicensed likeness), a white overlapping utility card (tabs + search),
  and a small capability strip below so the page doesn't read as a bare
  banner fragment. **Not published as a claude.ai Artifact** — it closely
  imitates a real company's actual branded site, which the Artifact tool's
  own policy treats as content to build as a local file rather than a
  shareable link, so it stays local-only (the user can ask for a public
  link explicitly if still wanted).
- `assets/ceva_logo_reversed.svg` — a white+red variant of the real logo
  file, generated by recoloring the file's own `#1d2546` fills to white
  (`#ff0000` untouched) — needed because the source-of-truth logo file
  only ships a navy-on-light variant, which is invisible on a navy header;
  same shapes, standard light/dark logo adaptation, not a redrawn mark.
- **Bug found and fixed**: the hero page first referenced the logo via
  `<img src="assets/...">` — a relative path that breaks depending on how
  a standalone file is opened (this is a remote/port-forwarded dev
  environment, not a local machine, so a raw `file://` path doesn't
  resolve the way it would locally). Fixed by inlining the logo's SVG
  markup directly into the page — zero local file dependencies left
  besides the Google Fonts CDN call.
- **Serving fix**: rather than a separate ad-hoc port (tried
  `python3 -m http.server 8502` first — wrong instinct, a new port isn't
  auto-forwarded the way the already-proven `:8501` is), enabled
  Streamlit's built-in static file serving (`[server] enableStaticServing
  = true` in `.streamlit/config.toml`) and placed a copy at
  `static/ceva_landing_hero.html` — reachable at
  `http://localhost:8501/app/static/ceva_landing_hero.html`, same port as
  the app, no separate process to manage.
- **Recurring gotcha hit again this session**: a stray second
  `streamlit run app.py` (no explicit `--server.port`, so it auto-fell
  back to 8502) was running with stale pre-redesign code — the user was
  briefly looking at that leftover instance's Network URL and seeing no
  changes. Killed it; only the one `--server.port 8501` instance should
  ever be running. Same "kill all, relaunch one clean instance" pattern
  documented earlier in this file — evidently still happening because the
  user also runs `make agent` themselves in their own terminal sometimes,
  independent of the instance this session manages.
- **Dispatcher app then explicitly asked to adopt the hero's visual
  language** (chosen over a header-only hybrid, and over keeping the
  previous subdued "enterprise dashboard" look): `theme.py`'s
  `inject_base_css()` now also loads Archivo from Google Fonts;
  `.ceva-header` is a full-bleed navy band (negative-margin bleed past
  Streamlit's block-container gutter) with the bigger reversed logo;
  `LOGO_PATH` switched to the reversed SVG accordingly; all headings
  (`h1-h3`) and tab labels (`[data-testid="stTab"] p` — confirmed via
  Playwright DOM inspection to be the real element, not a `<button
  role="tab">` as first guessed) render in Archivo 800-weight uppercase;
  every rectangular surface (`.ceva-card`, `.ceva-badge`, `.ceva-empty`,
  `.ceva-meter-*`, Streamlit's own buttons and bordered containers via
  `[data-testid="stBaseButton-primary/secondary"]` and
  `[data-testid="stVerticalBlockBorderWrapper"]`) had `border-radius`
  zeroed — matches the original hero spec's "sharp rectangular blocks, no
  rounded corners" instruction, applied consistently, not just in the
  header. Small circular status affordances (step-flow dots) were kept
  round on purpose — they're iconography, not panels.
- Verified via Playwright DOM inspection (not screenshot — still hits the
  same sandbox "fonts loaded" hang documented earlier): header background
  computed as `rgb(29,37,70)` (`#1D2546`, correct), logo renders at the
  set 42px height, header spans ~99% of viewport width (full-bleed), tab
  labels compute to `Archivo, sans-serif` / `800` / `uppercase`. Full
  dispatcher flow (compose lot → assign truck → alert → Auto-optimize)
  re-verified via `AppTest` after the theme changes: zero exceptions.

## How to continue

1. If cross-analysis with problems 4/5 is wanted for pitch narrative, load
   the S&P energy-mix and SDES files into `data/` too — not required for the
   core pitch.
2. Possible next steps: explain the 46% target-before-departure anomaly if
   time allows; investigate why only ~39% of trips have valid distance data;
   build the pitch deck around the confirmed problem-1 numbers.

## Style constraints (from the project's CLAUDE.md)

Minimal code, no premature abstractions, no error handling for impossible
scenarios, surgical changes. Don't add features not requested during the
hackathon: time goes to analysis, not infrastructure.
