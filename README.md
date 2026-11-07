# Claude-Community-Event_Affordable_Housing
UCI × SoCal Affordable Housing. Form a team, pick a lane, and build a working prototype with Claude by 2:30.

## OCA

OCA is a free screening tool: enter an Orange County, CA ZIP code and get a ranked, mapped list of parcels that are strong candidates for affordable housing development, redevelopment or preservation, using only free public datasets. Each parcel shows an Opportunity Score built from two separate scores, Development Potential and Feasibility Risk, with a confidence level and a plain-language reason for every score.

OCA points people to where to look first. It does not confirm zoning, ownership, price or buildability.

## Run it

Needs Python 3.11+ and git. No Node or build step.

**1. Clone and install**

```
git clone https://github.com/jgsam05/Claude-Community-Event_Affordable_Housing
cd Claude-Community-Event_Affordable_Housing/backend
pip install -r requirements.txt
```

**2. Start the backend** (terminal 1, from `backend/`)

```
uvicorn parcel_engine.api:app --port 8000
```

This is live mode: it queries county and state data over the network, so the first load of a ZIP can be slow. For an offline demo with synthetic parcels, set the mode first:

```
# macOS / Linux / Git Bash
PARCEL_ENGINE_MODE=fixture uvicorn parcel_engine.api:app --port 8000
# Windows PowerShell
$env:PARCEL_ENGINE_MODE="fixture"; uvicorn parcel_engine.api:app --port 8000
```

Check it with http://localhost:8000/health (it reports `live` or `fixture`).

**3. Start the website** (terminal 2, from the repo root)

```
cd parcel-screener-prototype
python -m http.server 8001
```

**4. Open it**

http://localhost:8001/?api=http://localhost:8000#/zip/92705

Sample ZIPs: `92618` and `92620` (Irvine) and `92705` (crosses Santa Ana, Tustin and North Tustin). Without `?api=` the front end runs on built-in sample data, labeled as such.

**Which ZIP codes work**

- Fixture mode (offline demo): only `92618`, `92620` and `92705`.
- Live mode: any Orange County ZIP. A valid OC ZIP has at least 5% of its area inside OC cities or unincorporated land. Anything else returns 404, and a ZIP that is not 5 digits returns 400. Only the three sample ZIPs have been designed around; other OC ZIPs are untested.
- Front end without `?api=`: built-in sample data only.

| Sample ZIP | Why |
|---|---|
| `92618` | Irvine, the normal case |
| `92620` | Irvine, thin data (warning banner, many Insufficient parcels) |
| `92705` | Crosses city lines: Santa Ana, Tustin and North Tustin |

**Tests:** `cd backend && PARCEL_ENGINE_MODE=fixture python -m pytest -q`

**Data:** live scoring uses datasets in `backend/data/raw/`. A missing dataset does not break anything: its signals count as missing and lower confidence. `docs/DATASETS.md` lists every source and download link; `backend/README.md` explains which are automatic and which are manual.

**Troubleshooting**

- `address already in use`: another server holds port 8000 or 8001. Stop it or pick another port, and change `?api=` to match.
- Page shows sample data: the URL is missing `?api=http://localhost:8000`, or the backend is not running.

## Repo map

- `parcel-screener-prototype/`: the OCA front end (ZIP search, ranked cards, map, score report, how-to-use page). Opens with `?api=` to use the backend.
- `backend/`: data pipeline, scoring engine and API (see `backend/README.md` and `backend/docs/scoring.md`).
- `docs/DATASETS.md`: every input dataset with source, license and refresh date ([CSV](docs/datasets.csv)).
- `docs/data-pipeline-task.md`: data pipeline and API task spec.
- `design/DESIGN.md`: OCA design principles and style guide (name, logo, color, type, layout, voice, scores, video). Start here before changing any screen.
- `design/oca-canvas/`: brand, UI designs, score report, how-to-use page and demo video storyboard. All parcels and scores there are illustrative sample data.
- `design/video/`: 30-second demo video source and render script.
