"""Build a REAL-data parcel file for one Orange County ZIP from free public services.

    python -m oc_housing.etl.real_zip 92701

Sources (see config/datasets.yaml): OC Public Works legal lots (geometry, APN, ZIP,
assessed values) joined SPATIALLY to SCAG 2024 land use, zoning, and Housing Element
sites. Spatial join, not APN join: in a pilot on 92701 an APN join matched only ~15-25%
of lots (condo stacks and parent/child parcels carry different APNs); a point-in-polygon
join matched every lot tested.

Output: data/parcels_in/real_<zip>.geojson plus data/parcels_in/real_<zip>.report.json.
Load with:  python -m oc_housing.build --parcels data/parcels_in/real_<zip>.geojson \
                --mapping config/parcel_mapping_real.yaml
Owner mailing addresses are never copied.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx
from shapely import STRtree
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
OC = "https://ocgis.com/arcpub/rest/services/LegalLotsAttributeOpenData/FeatureServer/0/query"
SCAG = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/{}/MapServer/0/query"
CLIENT = httpx.Client(timeout=180, follow_redirects=True, headers={"User-Agent": "oc-housing-finder/0.2"})
MIN_LOT_SQFT = 500  # drop slivers / right-of-way fragments

# SCAG LU24 code -> our LandUse. Unlisted codes map to None (unknown), never guessed.
# Dictionary: data/raw/scag_landuse_description.txt
def map_lu(code: str | None) -> str | None:
    if not code:
        return None
    c = str(code)
    if c in ("3000", "3100", "3300", "1900"):
        return "vacant"
    if c == "1247":
        return "surface_parking"        # public parking facilities
    if c.startswith("1130") or c in ("1131", "1132"):
        return "mobile_home_park"
    if c.startswith("111") or c == "1150":
        return "single_family"
    if c.startswith("112") or c in ("1100", "1140"):
        return "multifamily"
    if c in ("1220", "1222", "1223", "1230", "1210", "1211", "1500", "1610", "1620", "1600"):
        return "commercial_1story"      # refined later with building footprints
    if c.startswith("12") and c not in ("1245",):
        return "public" if c in ("1240", "1241", "1242", "1243", "1246", "1260", "1261", "1262", "1263", "1264", "1265", "1266") else "commercial_other"
    if c == "1245":
        return "institutional_faith"
    if c.startswith("13"):
        return "industrial"
    return "other"


def _page(url: str, params: dict, max_pages: int = 60) -> list[dict]:
    out, offset = [], 0
    for _ in range(max_pages):
        r = CLIENT.get(url, params={**params, "resultOffset": offset, "resultRecordCount": 1000}).json()
        if "error" in r:
            raise RuntimeError(str(r["error"])[:200])
        feats = r.get("features", [])
        out += feats
        if not r.get("exceededTransferLimit") and len(feats) < 1000:
            break
        offset += len(feats)
    return out


def _num(v):
    try:
        return float(str(v).replace(",", "")) if str(v).strip() not in ("", "None") else None
    except ValueError:
        return None


def _scag_layer(name: str, bbox: tuple, fields: str) -> tuple[list, STRtree, list[dict]]:
    env = ",".join(map(str, bbox))
    feats = _page(SCAG.format(name), {"f": "geojson", "geometry": env, "geometryType": "esriGeometryEnvelope",
                                      "inSR": 4326, "outSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                                      "outFields": fields, "where": "1=1"})
    feats = [f for f in feats if f.get("geometry")]
    geoms = [shape(f["geometry"]) for f in feats]
    return geoms, STRtree(geoms), [f["properties"] for f in feats]


def _lookup(tree, geoms, props, pt):
    hits = [i for i in tree.query(pt) if geoms[i].contains(pt)]
    if not hits:
        return None
    # stacked polygons (condos) overlap; take the largest-area record, deterministic
    return props[max(hits, key=lambda i: (geoms[i].area, i))]


def build(zip_code: str, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or ROOT / "data" / "parcels_in"
    out_dir.mkdir(parents=True, exist_ok=True)
    lots = _page(OC, {"f": "geojson", "where": f"SiteZip5='{zip_code}'", "outSR": 4326,
                      "outFields": "AssessmentNo,SiteAddress,SiteCityState,SiteZip5,LandVal,ImprovedVal,LotType,Shape__Area"})
    if not lots:
        raise SystemExit(f"No OC parcels for ZIP {zip_code}. Not an OC ZIP, or the layer has none.")
    shapes = [shape(f["geometry"]) for f in lots if f.get("geometry")]
    minx, miny = min(s.bounds[0] for s in shapes), min(s.bounds[1] for s in shapes)
    maxx, maxy = max(s.bounds[2] for s in shapes), max(s.bounds[3] for s in shapes)
    bbox = (minx - 0.001, miny - 0.001, maxx + 0.001, maxy + 0.001)
    lu = _scag_layer("Existinglanduse_poly_OR", bbox, "APN24,LU24,CITY")
    zn = _scag_layer("Zoning_poly_OR", bbox, "APN24,ZN24_CITY,ZN24_SCAG,CITY")
    gp = _scag_layer("GeneralPlan_poly_OR", bbox, "APN24,GP24_CITY,DEN_MAX,DEN_AVG")
    he = _scag_layer("HousingElementSite_poly_scag", bbox, "APN24,Jurisdiction,Low_Income_HE_Capacity,Total_HE_Capacity")

    feats, rep = [], {"zip": zip_code, "lots_fetched": len(lots), "dropped_no_geometry": 0, "dropped_tiny": 0,
                      "with_land_use": 0, "with_zoning": 0, "with_gp": 0, "he_site": 0,
                      "blank_land_val": 0, "unmapped_lu_codes": {}, "scag_cities": {}}
    for f in lots:
        if not f.get("geometry"):
            rep["dropped_no_geometry"] += 1
            continue
        g = shape(f["geometry"])
        p = f["properties"]
        area = p.get("Shape__Area") or 0
        if area < MIN_LOT_SQFT:
            rep["dropped_tiny"] += 1
            continue
        pt = g.representative_point()
        l, z, gpr, h = _lookup(lu[1], lu[0], lu[2], pt), _lookup(zn[1], zn[0], zn[2], pt), \
            _lookup(gp[1], gp[0], gp[2], pt), _lookup(he[1], he[0], he[2], pt)
        code = l.get("LU24") if l else None
        use = map_lu(code)
        if l:
            rep["with_land_use"] += 1
            if code and use == "other":
                rep["unmapped_lu_codes"][code] = rep["unmapped_lu_codes"].get(code, 0) + 1
        if z:
            rep["with_zoning"] += 1
            rep["scag_cities"][z.get("CITY")] = rep["scag_cities"].get(z.get("CITY"), 0) + 1
        if gpr:
            rep["with_gp"] += 1
        if h:
            rep["he_site"] += 1
        lv, iv = _num(p.get("LandVal")), _num(p.get("ImprovedVal"))
        if lv is None:
            rep["blank_land_val"] += 1
        apn = re.sub(r"\D", "", p.get("AssessmentNo") or "")
        feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {
            "apn": apn or None, "address": p.get("SiteAddress"), "zip": zip_code,
            "lot_sqft": round(area), "land_use": use, "scag_lu24": code,
            "zoning_code": (z or {}).get("ZN24_CITY") or None,
            "scag_city": (z or l or {}).get("CITY"),
            "gp_density_max": (gpr or {}).get("DEN_MAX"),
            "land_value": lv, "improvement_value": iv,
            "housing_element_site": True if h else None,
            "he_low_income_capacity": (h or {}).get("Low_Income_HE_Capacity"),
        }})
    rep["parcels_written"] = len(feats)
    rep["join_rates"] = {k: round(rep[k] / max(len(feats), 1), 3) for k in ("with_land_use", "with_zoning", "with_gp")}
    (out_dir / f"real_{zip_code}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    (out_dir / f"real_{zip_code}.report.json").write_text(json.dumps(rep, indent=1))
    return rep


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1]), indent=1))
