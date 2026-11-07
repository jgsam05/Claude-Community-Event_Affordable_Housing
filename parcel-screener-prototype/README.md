# OCA front end

The OCA site screener: enter an Orange County ZIP code and get a ranked, mapped list of parcels worth a closer look for affordable housing. Look and copy follow `../design/DESIGN.md`.

No build step, no dependencies.

## Run it

With the backend (real scores):

```
cd ../backend && uvicorn parcel_engine.api:app --port 8000
# in this folder:
python -m http.server 8001
# open http://localhost:8001/?api=http://localhost:8000#/zip/92705
```

Set `PARCEL_ENGINE_MODE=fixture` on the backend to run on synthetic test data without network. You can also set `window.PARCEL_API` before `app.js` loads instead of `?api=`.

Without `?api=`, the page runs on generated sample data for 92618, 92620 and 92705, scored with the same formula and labeled "Sample data" everywhere.

## Real map

When the backend (or a saved snapshot) provides parcel polygons, the map is a live Leaflet map over the Esri Light Gray basemap, with the real county parcels drawn at their true coordinates and colored in the OCA palette (opportunity: orange tint, yellow, blue, green, low to high; Low-confidence parcels stay muted). Zoom and drag work; clicking a parcel or a numbered pin selects the site. Without polygons (sample mode) it falls back to the schematic map.

- Leaflet is vendored in `vendor/leaflet/` (BSD-2), so the map code has no CDN dependency.
- `data/92701.geojson` is a saved copy of the backend's `/zip/92701` output (5,312 real Santa Ana parcels, built from county records on 2026-11-07), so the page shows a real ZIP with no backend running: open `http://localhost:8001/#/zip/92701`. Any `data/<zip>.geojson` works the same way.
- Tiles: Esri World Light Gray (free with attribution, shown on the map). Swap `TILE_BASE` and `TILE_LABELS` in `app.js` to change providers. Carto's free tiles now require an API key.

## Screens

| Route | Screen |
|---|---|
| `#/` | Home: ZIP search, "What OCA does", the three scores |
| `#/zip/92705` | Results: site-type filters, confidence filter, sort, cards or data table, map, selected site with Development potential, Feasibility risk and Confidence tiles, CSV export |
| `#/zip/92705/<apn>/report` | Parcel score report: every input, its value, public source and confidence; print or save as PDF |
| `#/how` | How to use OCA: audience, five steps, reading scores, six kinds of sites, limits, glossary |
| `#/methods` | Sources & methods: formula, weights, confidence rules, datasets, what's excluded |

## Things to try

| Try | What you'll see |
|---|---|
| `92705` | Crosses city lines (Santa Ana, Tustin, unincorporated) |
| `92620` (sample mode) | Thin data: banner, many "Not scored" parcels |
| `10001` | ZIP outside coverage |
| Hide every confidence level | Empty-filter state |

`Esc` closes the selected site.

## Design decisions to keep

- **The front end shows the backend's scores; it never recomputes them.** The sample generator uses the same formula only so sample mode looks realistic.
- **Insufficient parcels show no score.** They read "Not scored".
- **Status is never color alone.** Confidence is always a word ("High confidence"); pins carry a rank number.
- **One variable per map fill.** Opportunity uses a blue lightness scale; Low-confidence parcels collapse to 2 muted greys so a weak score can't look strong. Confidence uses green / yellow / orange tint, which also differ in lightness.
- **The list is the accessible version of the map.** Every score, level and reason exists there as text, and every map pin is a labeled button.
- **Reason strings come from the backend** and follow `[Signal] [value] — [comparison to ZIP].` Missing data always states the effect: `Year built unavailable — not scored.`

## Not built yet

- Zoning
- Street-level search (the map opens fitted to the ZIP; use zoom and drag from there)
- Zoning
