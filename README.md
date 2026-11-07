# Claude-Community-Event_Affordable_Housing

> **Goal:** Build a web tool where a user enters an Orange County, CA ZIP code and gets a ranked, mapped list of parcels that are strong screening candidates for affordable housing development or preservation, using only free, public datasets.
>
> **Candidates come from:** vacant or lightly built parcels (building footprint coverage), Housing Element sites and rezone sites, publicly owned and surplus land, faith-based parcels, tax-defaulted parcels, and existing subsidized housing with expiring affordability (preservation).
>
> **Each parcel is scored on:** development potential (lot size, buildable area, coverage, Housing Element status, state-law pathways), location quality (transit, jobs, schools, grocery, opportunity area, CalEnviroScreen, ACS rent burden), and feasibility risk (flood, fire, seismic, coastal, oil wells, contamination, historic). Every score shows its components, sources, and a confidence level.

Every doc, screen and script in this repo should trace back to this goal.

UCI × SoCal Affordable Housing. Form a team, pick a lane, and build a working prototype with Claude by 2:30.

## OCA

OCA is a free screening tool: enter an Orange County, CA ZIP code and get a ranked, mapped list of parcels that are strong candidates for affordable housing development, redevelopment or preservation, using only free public datasets. Each parcel shows an Opportunity Score built from two separate scores, Development Potential and Feasibility Risk, with a confidence level and a plain-language reason for every score.

OCA points people to where to look first. It does not confirm zoning, ownership, price or buildability.

## Run it

```
cd backend && pip install -r requirements.txt
uvicorn parcel_engine.api:app --port 8000
# in another terminal:
cd parcel-screener-prototype && python -m http.server 8001
# open http://localhost:8001/?api=http://localhost:8000#/zip/92705
```

Without `?api=` the front end runs on built-in sample data, labeled as such.

## Repo map

- `parcel-screener-prototype/`: the OCA front end (ZIP search, ranked cards, map, score report, how-to-use page). Opens with `?api=` to use the backend.
- `backend/`: data pipeline, scoring engine and API (see `backend/README.md` and `backend/docs/scoring.md`).
- `docs/DATASETS.md`: every input dataset with source, license and refresh date ([CSV](docs/datasets.csv)).
- `docs/data-pipeline-task.md`: data pipeline and API task spec.
- `design/DESIGN.md`: OCA design principles and style guide (name, logo, color, type, layout, voice, scores, video). Start here before changing any screen.
- `design/oca-canvas/`: brand, UI designs, score report, how-to-use page and demo video storyboard. All parcels and scores there are illustrative sample data.
- `design/video/`: 30-second demo video source and render script.
