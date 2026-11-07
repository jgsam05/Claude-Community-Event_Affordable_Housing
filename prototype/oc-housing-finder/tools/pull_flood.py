"""Download OC flood polygons (FEMA NFHL via OC Public Works) clipped to the loaded parcels' bbox.
  data/overlays/flood_sfha.geojson   sfha_tf='T'  (1% annual chance, special flood hazard area)
  data/overlays/flood_clear.geojson  fld_zone='X' (mapped, minimal/0.2% hazard)
'AREA NOT INCLUDED' (not mapped) is NOT downloaded: those parcels stay UNKNOWN."""
import json, sys, httpx
from pathlib import Path
from shapely.geometry import shape
ROOT = Path(__file__).resolve().parents[1]
U = "https://services.arcgis.com/UXmFoWC7yDHcDN5Q/arcgis/rest/services/OC_Flood_Hazard_Areas_Polygons/FeatureServer/7/query"
c = httpx.Client(timeout=120)
fs = json.load(open(ROOT / "data/parcels_in/real_sites.geojson"))["features"]
xs, ys = [], []
for f in fs[::20]:
    b = shape(f["geometry"]).bounds; xs += [b[0], b[2]]; ys += [b[1], b[3]]
env = f"{min(xs)-.005},{min(ys)-.005},{max(xs)+.005},{max(ys)+.005}"
(ROOT / "data/overlays").mkdir(exist_ok=True)
for name, where in [("flood_sfha", "sfha_tf='T'"), ("flood_clear", "fld_zone='X'")]:
    feats, off = [], 0
    while True:
        r = c.get(U, params={"where": where, "geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                             "spatialRel": "esriSpatialRelIntersects", "outFields": "fld_zone,sfha_tf", "outSR": 4326,
                             "f": "geojson", "resultOffset": off, "resultRecordCount": 2000, "orderByFields": "OBJECTID"}).json()
        b = r.get("features", []); feats += b
        if len(b) < 2000 and not r.get("exceededTransferLimit"): break
        off += len(b)
    (ROOT / f"data/overlays/{name}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    print(name, len(feats))
