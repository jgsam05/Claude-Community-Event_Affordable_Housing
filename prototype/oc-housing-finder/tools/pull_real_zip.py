"""Pull REAL parcels for one ZIP and attach SCAG zoning / land use / general-plan density.

  python tools/pull_real_zip.py 92701 [--out data/parcels_in]

Sources (see config/datasets.yaml):
  parcels   OC Public Works LegalLotsAttributeOpenData (filter SiteZip5)
  zoning    SCAG Zoning_poly_OR        (ZN24_CITY = the city's own zone code)
  landuse   SCAG Existinglanduse_poly_OR (LU24)
  gp        SCAG GeneralPlan_poly_OR   (GP24_CITY, DEN_MAX, FAR_MAX)
  he        SCAG HousingElementSite_poly_scag (city-listed Housing Element sites)
Join key: 8-digit APN (OC AssessmentNo without dashes == SCAG APN24).
Owner mailing address is deliberately NOT kept.
"""
import argparse, json, re, sys, time
from pathlib import Path
import httpx

OC = "https://ocgis.com/arcpub/rest/services/LegalLotsAttributeOpenData/FeatureServer/0"
S = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/"
SCAG = {
    "zoning": (S + "Zoning_poly_OR/MapServer/0", "CITY,APN24,ZN24_CITY,ZN24_SCAG,ACRES"),
    "landuse": (S + "Existinglanduse_poly_OR/MapServer/0", "APN24,LU24,LU24_2ND"),
    "gp": (S + "GeneralPlan_poly_OR/MapServer/0", "APN24,GP24_CITY,DEN_MAX,DEN_AVG,FAR_MAX"),
    "he": (S + "HousingElementSite_poly_scag/MapServer/0", "APN24,Low_Income_HE_Capacity,Total_HE_Capacity"),
}
c = httpx.Client(timeout=120, follow_redirects=True, headers={"User-Agent": "oc-housing-finder/0.1"})


def q(url, **p):
    p.setdefault("f", "json")
    for attempt in range(3):
        r = c.get(url + "/query", params=p)
        j = r.json()
        if "error" not in j:
            return j
        time.sleep(2)
    raise RuntimeError(j["error"])


def pull_parcels(zip_code):
    feats, off = [], 0
    while True:
        j = q(OC, where=f"SiteZip5='{zip_code}'", outFields="AssessmentNo,SiteAddress,SiteCityState,LandVal,ImprovedVal,AssdAmt,LotType,Shape__Area",
              outSR=4326, returnGeometry="true", f="geojson", resultOffset=off, resultRecordCount=1000, orderByFields="OBJECTID")
        batch = j.get("features", [])
        feats += batch
        if len(batch) < 1000 and not j.get("exceededTransferLimit"):
            break
        off += len(batch)
    return feats


def apn8(s):
    d = re.sub(r"\D", "", s or "")
    return d if len(d) == 8 else None


def pull_scag(name, apns):
    url, fields = SCAG[name]
    out = {}
    apns = sorted(apns)
    for i in range(0, len(apns), 150):
        chunk = ",".join(f"'{a}'" for a in apns[i:i + 150])
        j = q(url, where=f"COUNTY='Orange' AND APN24 IN ({chunk})" if name != "he" else f"APN24 IN ({chunk})",
              outFields=fields, returnGeometry="false")
        for f in j.get("features", []):
            a = f["attributes"]
            out.setdefault(a["APN24"], []).append(a)   # keep all rows; STACK rows are condos/stacked parcels
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zip")
    ap.add_argument("--out", default="data/parcels_in")
    a = ap.parse_args()
    feats = pull_parcels(a.zip)
    keep, no_apn = [], 0
    for f in feats:
        p = f["properties"]
        k = apn8(p.get("AssessmentNo"))
        if not k or not f.get("geometry"):
            no_apn += 1
            continue
        p["apn8"] = k
        keep.append(f)
    apns = {f["properties"]["apn8"] for f in keep}
    layers = {n: pull_scag(n, apns) for n in SCAG}
    rep = {"zip": a.zip, "oc_rows": len(feats), "dropped_no_apn_or_geometry": no_apn, "unique_apn": len(apns)}
    for n, d in layers.items():
        rep[f"{n}_matched_apns"] = len(d)
    for f in keep:
        p, k = f["properties"], f["properties"]["apn8"]
        z, lu, gp, he = (layers[n].get(k) for n in ("zoning", "landuse", "gp", "he"))
        p["city_scag"] = z[0]["CITY"] if z else None
        p["zoning_code"] = z[0]["ZN24_CITY"] if z else None
        p["scag_zone"] = z[0]["ZN24_SCAG"] if z else None
        p["lu24"] = lu[0]["LU24"] if lu else None
        p["gp_code"] = gp[0]["GP24_CITY"] if gp else None
        p["gp_den_max"] = gp[0]["DEN_MAX"] if gp else None
        p["gp_far_max"] = gp[0]["FAR_MAX"] if gp else None
        p["he_site"] = bool(he)
        p["he_low_income_cap"] = he[0]["Low_Income_HE_Capacity"] if he else None
        p["stacked"] = bool(z and len(z) > 1)
        p["zip"] = a.zip
    rep["he_sites_in_zip"] = sum(1 for f in keep if f["properties"]["he_site"])
    rep["cities_scag"] = sorted({f["properties"]["city_scag"] for f in keep if f["properties"]["city_scag"]})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"real_{a.zip}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": keep}))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    sys.exit(main())
