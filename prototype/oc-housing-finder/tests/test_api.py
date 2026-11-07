import csv
import io

import pytest
from fastapi.testclient import TestClient

from oc_housing.api import app, store


@pytest.fixture(scope="module")
def client():
    if not store.parcels:
        pytest.skip("No processed data; run `python -m oc_housing.build` first")
    return TestClient(app)


def test_health_reports_synthetic_and_unverified(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["parcels"] > 0
    assert h["laws_verified"] is False
    assert "not legal" in h["disclaimer"].lower()


def test_zip_lookup_returns_ranked_geojson(client):
    r = client.get("/api/zip/92701").json()
    scores = [f["properties"]["overall"] for f in r["features"]]
    assert scores == sorted(scores, reverse=True)
    assert r["features"][0]["geometry"]["type"] == "Polygon"
    assert r["summary"]["total_in_zip"] == len(scores)


def test_malformed_zip_is_400(client):
    assert client.get("/api/zip/abc").status_code == 400
    assert client.get("/api/zip/9270").status_code == 400


def test_unloaded_zip_is_404_and_lists_loaded_zips(client):
    r = client.get("/api/zip/93001")
    assert r.status_code == 404
    body = r.json()
    assert "No parcel data" in body["message"] and body["loaded_zips"]


def test_multi_city_zip_is_split_by_jurisdiction(client):
    cities = client.get("/api/zip/92627").json()["summary"]["cities"]
    assert len(cities) >= 2  # one ZIP spans two cities; each uses its own rules


def test_filters_apply(client):
    allr = client.get("/api/zip/92701").json()["features"]
    hi = client.get("/api/zip/92701?min_score=60").json()["features"]
    assert len(hi) < len(allr) and all(f["properties"]["overall"] >= 60 for f in hi)
    conf = client.get("/api/zip/92701?min_confidence=0.9").json()["features"]
    assert all(f["properties"]["confidence"] >= 0.9 for f in conf)
    city = client.get("/api/zip/92627?city=Newport%20Beach").json()["features"]
    assert city and all(f["properties"]["city"] == "Newport Beach" for f in city)


def test_csv_export_has_no_owner_identity(client):
    text = client.get("/api/zip/92701/export.csv?min_score=40").text
    rows = list(csv.DictReader(io.StringIO(text)))
    assert rows
    assert not any("owner" in k.lower() for k in rows[0])  # type/name never exported
    assert all(r["is_synthetic"] == "True" for r in rows)


def test_geojson_export_carries_disclaimer(client):
    r = client.get("/api/zip/92701/export.geojson")
    assert r.status_code == 200 and "not legal" in r.json()["disclaimer"].lower()


def test_gap_report_lists_zoning_status_by_city(client):
    g = client.get("/api/zip/92627/gaps").json()
    assert "zoning_status_by_jurisdiction" in g and g["unknown_field_counts"]
    assert "mobile_home" not in g["unknown_field_counts"]


def test_parcel_detail_has_component_breakdown(client):
    pid = client.get("/api/zip/92701").json()["features"][0]["id"]
    d = client.get(f"/api/parcel/{pid}").json()
    assert d["score"]["components"] and d["score"]["risk_components"]
    assert "geometry" not in d["parcel"]
    assert client.get("/api/parcel/NOPE").status_code == 404


def test_coverage_lists_every_city_plus_unincorporated(client):
    cov = client.get("/api/coverage").json()
    names = [c["jurisdiction"] for c in cov]
    assert len(cov) == 35 and "Unincorporated Orange County" in names  # 34 cities + county
    assert {c["zoning"] for c in cov} <= {"none", "sample", "ingested"}


def test_every_parcel_has_plain_language_reason(client):
    for f in client.get("/api/zip/92701").json()["features"][:25]:
        assert len(f["properties"]["reason"]) > 40


def test_datasets_registry_documents_source_license_refresh(client):
    d = client.get("/api/datasets").json()
    assert d["datasets"] and d["rejected"]
    for ds in d["datasets"]:
        assert ds["status"] and ("license" in ds or ds["status"] in ("candidate", "unverified"))
        if ds["status"].startswith("verified"):
            assert "license" in ds and ("refresh" in ds or "rows" in ds or "rows_orange" in ds)
