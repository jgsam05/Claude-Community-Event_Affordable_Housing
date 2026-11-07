"""End-to-end tests on the synthetic fixture world (no network)."""
import os

os.environ["PARCEL_ENGINE_MODE"] = "fixture"

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from parcel_engine import api, arcgis, pipeline, registry, scoring, tax_default, validation
from parcel_engine.joins import HANDLERS
from parcel_engine.sources import FixtureSources

LEVELS = {"High", "Medium", "Low", "Insufficient"}


@pytest.fixture(scope="module")
def fcs():
    return {z: pipeline.build_zip(z, FixtureSources(), write=False) for z in ["92618", "92620", "92705"]}


def props(fc):
    return [f["properties"] for f in fc["features"]]


# ---------- ZIP selection ----------
def test_cross_city_zip_tags_every_jurisdiction(fcs):
    m = fcs["92705"]["metadata"]
    assert set(m["jurisdictions"]) == {"Santa Ana", "Tustin", "Unincorporated"}
    assert m["crosses_city_lines"] is True
    assert sum(m["jurisdictions"].values()) == m["parcel_count"] == len(fcs["92705"]["features"])
    assert any(p["straddles_city_line"] for p in props(fcs["92705"]))


def test_parcels_belong_to_one_zip(fcs):
    apns = [p["apn"] for z in fcs for p in props(fcs[z])]
    assert len(apns) == len(set(apns))


def test_zip_errors():
    c = TestClient(api.app)
    assert c.get("/zip/9261").status_code == 400
    assert c.get("/zip/99999").status_code == 404   # not a ZCTA
    r = c.get("/zip/10001")                         # ZCTA outside OC
    assert r.status_code == 404 and "not an Orange County ZIP" in r.json()["detail"]


# ---------- geometry ----------
def test_geometry_signals(fcs):
    for p in props(fcs["92618"]):
        assert p["lot_sqft"] > 0 and p["buildable_sqft"] < p["lot_sqft"]
        assert 0 <= p["building_coverage"] <= 1
        assert p["vacant"] == (p["building_sqft"] < 50)
        assert p["frontage_method"] == "centerline_buffer" and p["frontage_ft"] > 0
    assert any(p["vacant"] for p in props(fcs["92618"]))


# ---------- scoring / confidence ----------
def test_level_thresholds():
    assert [scoring.level_for(n) for n in (10, 9, 8.5, 7, 6.5, 5, 4.5, 0)] == \
        ["High", "High", "Medium", "Medium", "Low", "Low", "Insufficient", "Insufficient"]


def test_every_feature_has_scores_and_reasons(fcs):
    for z, fc in fcs.items():
        for p in props(fc):
            assert p["level"] in LEVELS and p["signals_total"] == 10
            assert p["sig"] == 10 - len(p["missing"])
            if p["level"] == "Insufficient":
                assert p["opp"] is None and p["development_potential"] is None
            else:
                assert 0 <= p["opp"] <= 100
                for k in ("opp_reason", "dev_reason", "risk_reason"):
                    assert p[k] and p[k].split(":")[0] in {"High", "Medium", "Low", "High risk", "Moderate risk", "Low risk"}
                assert p["reasons"] and all(r["dir"] in ("up", "down") and r["text"].endswith(".") for r in p["reasons"])


def test_thin_data_lowers_confidence(fcs):
    lv = fcs["92620"]["metadata"]["level_counts"]
    assert lv["High"] == 0 and lv["Low"] > 0
    assert all("Year built" in p["missing"] or p["vacant"] for p in props(fcs["92620"]))


def test_sb4_faith_based_capped_low(fcs):
    faith = [p for p in props(fcs["92618"]) if p["faith_based"]]
    assert faith and all(p["level"] == "Low" and p["confidence_cap"] for p in faith)


def test_risk_reduces_opportunity(fcs):
    for p in props(fcs["92705"]):
        if p["opp"] is not None and p["feasibility_risk"]:
            assert p["opp"] < p["development_potential"]
    flood = [p for p in props(fcs["92705"]) if p["flood_sfha"]]
    assert flood and all("Flood" in p["risk_reason"] for p in flood if p["risk_reason"])


def test_missing_datasets_make_insufficient():
    omit = {"ocgis_building_footprints", "scag_land_use", "scag_he_sites", "scag_hqta", "octa_gtfs",
            "metrolink_gtfs", "lodes_wac", "tcac_opportunity", "acs5", "fema_nfhl"}
    fc = pipeline.build_zip("92618", FixtureSources(omit=omit), write=False)
    ps = props(fc)
    assert all(p["level"] == "Insufficient" and p["opp"] is None for p in ps)
    assert all("Building coverage" in p["missing"] for p in ps)


# ---------- API ----------
def test_api_geojson_shape():
    c = TestClient(api.app)
    fc = c.get("/zip/92705").json()
    assert fc["type"] == "FeatureCollection" and fc["features"]
    f = fc["features"][0]
    assert f["geometry"]["type"] in ("Polygon", "MultiPolygon")
    lon, lat = f["geometry"]["coordinates"][0][0][:2] if f["geometry"]["type"] == "Polygon" \
        else f["geometry"]["coordinates"][0][0][0][:2]
    assert -119 < lon < -116 and 32 < lat < 35   # WGS84, not state plane feet
    ranks = [x["properties"]["rank"] for x in fc["features"] if x["properties"]["rank"]]
    assert ranks == sorted(ranks)
    assert fc["metadata"]["signals"] == scoring.SIGNALS


# ---------- registry ----------
def test_registry_complete():
    ids = [d["id"] for d in registry.DATASETS]
    assert len(ids) == len(set(ids))
    for d in registry.DATASETS:
        for k in ("url", "license", "refresh_date", "access"):
            assert d.get(k), (d["id"], k)
        if d.get("join"):
            assert d["join"]["type"] in HANDLERS
    assert isinstance(registry.phase1_gaps(), list)
    assert TestClient(api.app).get("/registry").json()["datasets"]


# ---------- describe_layer (recorded OCGIS field list, 2026-11-07) ----------
def test_describe_layer_on_recorded_ocgis_fields(monkeypatch):
    fields = [{"name": n, "type": t, "alias": n} for n, t in [
        ("OBJECTID", "esriFieldTypeOID"), ("SITE_ADDRESS", "esriFieldTypeString"),
        ("ASSESSMENT_NO", "esriFieldTypeString"), ("YEAR_BUILT", "esriFieldTypeString"),
        ("NBR_BEDROOMS", "esriFieldTypeSmallInteger")]]
    monkeypatch.setattr(arcgis, "layer_info", lambda url: {"name": "Parcels", "fields": fields})
    rep = arcgis.describe_layer("x", fill_rates=False)["conditional"]
    assert rep["year_built"]["present"] and rep["year_built"]["fields"] == ["YEAR_BUILT"]
    assert not rep["use_code"]["present"]
    assert not rep["assessed_values"]["present"]      # ASSESSMENT_NO is the APN, not a value
    assert not rep["owner_name"]["present"]


# ---------- tax-defaulted PDFs ----------
def test_tax_pdf_parse(tmp_path):
    from reportlab.pdfgen import canvas
    pdf = tmp_path / "auction.pdf"
    c = canvas.Canvas(str(pdf))
    c.drawString(72, 720, "Item 101  APN 072-478-23  Min bid $12,000")
    c.drawString(72, 700, "Item 102  APN 935 - 123 - 04  Call 714-834-3411")
    c.drawString(72, 680, "Item 103  APN 072-478-23 (duplicate)")
    c.save()
    out = tmp_path / "apns.csv"
    res = tax_default.parse_folder(tmp_path, out)
    got = pd.read_csv(out, dtype=str)["apn"].tolist()
    assert got == ["072-478-23", "935-123-04"] and res["apns"] == 2


# ---------- validation ----------
def test_validation_lift(fcs):
    df = pd.DataFrame(props(fcs["92618"]))
    df["apn_norm"] = df["apn"].str.replace("-", "").str.zfill(8)
    top = df.nlargest(20, "opp")["apn_norm"]
    res = validation.validate(df, pd.DataFrame({"apn_norm": top, "units": 1}))
    assert res["status"] == "ok" and res["lift_top_decile"] > 1 and res["auc"] > 0.8
    assert validation.validate(df, None)["status"] == "not_run"


def test_catalog_covers_every_dataset(tmp_path):
    from parcel_engine import catalog
    md, csvp = catalog.write(tmp_path / "D.md", tmp_path / "d.csv")
    text = md.read_text()
    assert all(f"### {d['id'].replace('_', '-')}" in text for d in registry.DATASETS)
    assert len(pd.read_csv(csvp)) == len(registry.DATASETS)


def test_no_third_party_mirrors():
    """Non-county data must come from its publisher, not the OCGIS copies used in v0.1."""
    for d in registry.DATASETS:
        assert d["authority"] in {"original", "compiler", "community", "consortium"}, d["id"]
        if "County of Orange" not in d["publisher"]:
            assert "ocgis.com" not in d["url"], d["id"]
    community = {d["id"] for d in registry.DATASETS if d["authority"] == "community"}
    assert community == {"osm_worship", "osm_grocery"}
    assert registry.BY_ID["osm_worship"].get("low_confidence")
