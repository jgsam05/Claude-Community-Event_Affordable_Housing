# Parcel Screener — clickable prototype

Front-end prototype for screening parcels by ZIP code. Each parcel shows an **opportunity score (0–100)** and a **confidence level** (High, Medium, Low, Insufficient) that says how much data the score stands on.

By default all data is generated sample data. To use the backend in `../backend`, start the API and open the page with `?api=`:

```
cd ../backend && uvicorn parcel_engine.api:app --port 8000
# then: http://localhost:8001/?api=http://localhost:8000#/zip/92705   (serve this folder on 8001)
```

Or set `window.PARCEL_API = 'http://localhost:8000'` before `app.js` loads. With an API set, coverage, signals and the data date come from the backend, and the map draws each parcel's real bounding box.

## Run it

No build step, no dependencies.

- Open `index.html` in a browser, or
- From this folder: `python3 -m http.server 8000`, then go to http://localhost:8000, or
- Turn on GitHub Pages for the repo and point it at this folder.

## What to try

| Try | What you'll see |
|---|---|
| `92618` | Normal results: map + list, click any parcel for details |
| `92620` | Thin-data ZIP: banner, lots of Insufficient parcels |
| `10001` | ZIP outside coverage |
| `9261` | Inline validation error |
| Hide every confidence level | Empty-filter state |

Toggle **Color map by** to switch the map between Confidence and Opportunity. `Esc` closes the detail panel.

## Design decisions front end should keep

- **Confidence is a level, not a percentage.** Rules: High 9–10 of 10 signals, Medium 7–8, Low 5–6, Insufficient 0–4. These thresholds are placeholders until back end tests them on real ZIPs.
- **Insufficient parcels show no opportunity score.** They read "Not scored."
- **One variable per map fill.** Confidence uses a blue lightness scale; opportunity uses an orange scale. In Opportunity mode, Low-confidence parcels collapse to 2 muted colors so a weak score can't look strong.
- **The 1px parcel stroke is required.** The light blue fill is only ~1.6:1 against the map background; the stroke carries the contrast.
- **The list is the accessible version of the map.** Every score, level and reason exists there as text.
- **Reason strings follow one template:** `[Signal] [value] — [comparison to ZIP].` Missing data always states the effect: `Year built unavailable — not scored.`

## Placeholders to fill

In `app.js`, top of file: `COVERED_ZIPS`, `COVERAGE_LABEL`, `DATA_AS_OF`, `THIN_DATA_THRESHOLD`. Basemap provider is `[PROVIDER]` in the map attribution.

## Not built

- Real basemap and real parcel geometry (the map is a stylized grid)
- Zoom (buttons are placeholders)
- Full sources page
