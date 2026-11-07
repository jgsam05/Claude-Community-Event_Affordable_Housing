"""Live-mode loaders, exercised offline with local files and mocked HTTP."""
import io
import zipfile

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from parcel_engine import arcgis, registry, sources
from parcel_engine.sources import LiveSources


@pytest.fixture
def raw(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "RAW", tmp_path / "raw")
    monkeypatch.setattr(sources, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(registry, "STATE_FILE", tmp_path / "state.json")
    (tmp_path / "raw").mkdir()
    return tmp_path / "raw"


AREA = box(-117.80, 33.65, -117.70, 33.72)  # Irvine-ish, EPSG:4326


def test_missing_file_is_not_ingested(raw):
    s = LiveSources()
    assert s.get("dtsc_envirostor", AREA) is None and s.status["dtsc_envirostor"] == "not_ingested"


def test_latlon_csv_and_ingest_stamp(raw):
    pd.DataFrame({"ID": ["1", "2"], "LATITUDE": ["33.68", "40.0"], "LONGITUDE": ["-117.75", "-120"]}) \
        .to_csv(raw / "envirostor_sites.csv", index=False)
    g = LiveSources().get("dtsc_envirostor", AREA)
    assert len(g) == 1 and g.crs.to_epsg() == 2230
    assert registry.records()[[r["id"] for r in registry.records()].index("dtsc_envirostor")]["ingest_date"]


def test_gtfs_zip(raw):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("stops.txt", "stop_id,stop_lat,stop_lon\n1,33.69,-117.76\n2,33.70,-117.74\n")
    (raw / "octa_gtfs.zip").write_bytes(buf.getvalue())
    assert len(LiveSources().get("octa_gtfs", AREA)) == 2


def test_vector_file_clipped(raw):
    gpd.GeoDataFrame({"HAZ": [1, 2]}, geometry=[box(-117.76, 33.68, -117.75, 33.69), box(-110, 30, -109, 31)],
                     crs=4326).to_file(raw / "scag_hqta.gpkg")
    assert len(LiveSources().get("scag_hqta", AREA)) == 1


def test_acs_api_parse(raw, monkeypatch):
    rows = [["B19013_001E", "B25070_001E", "B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E",
             "state", "county", "tract"],
            ["95000", "100", "10", "5", "5", "20", "06", "059", "052410"],
            ["-666666666", "0", "0", "0", "0", "0", "06", "059", "099999"]]

    class R:
        def raise_for_status(self): pass
        def json(self): return rows
    monkeypatch.setattr(sources.requests, "get", lambda *a, **k: R())
    df = LiveSources().get("acs5")
    assert df.loc[0, "tract_geoid"] == "06059052410" and df.loc[0, "rent_burden_share"] == 0.4
    assert pd.isna(df.loc[1, "median_hh_income"]) and pd.isna(df.loc[1, "rent_burden_share"])


def test_lodes_tract_sum(raw):
    pd.DataFrame({"w_geocode": ["060590524101001", "060590524101002", "060370001001000"], "C000": [10, 5, 99]}) \
        .to_csv(raw / "ca_wac_S000_JT00_2022.csv.gz", index=False, compression="gzip")
    df = LiveSources().get("lodes_wac")
    assert df.to_dict("records") == [{"tract_geoid": "06059052410", "tract_jobs": 15}]


def test_arcgis_query_pages_by_object_id(monkeypatch):
    calls = []

    def fake(url, params, method="GET", retries=3):
        calls.append(params)
        if params.get("returnIdsOnly"):
            return {"objectIds": [1, 2, 3]}
        ids = params["objectIds"].split(",")
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"OBJECTID": int(i)},
             "geometry": {"type": "Point", "coordinates": [-117.75, 33.68]}} for i in ids]}
    monkeypatch.setattr(arcgis, "_get", fake)
    g = arcgis.query("http://x/0", geometry=AREA, chunk=2)
    assert len(g) == 3 and g.crs.to_epsg() == 2230
    assert '"rings"' in calls[0]["geometry"] and calls[0]["inSR"] == "4326"
    assert len(calls) == 3  # ids + 2 pages


def test_publisher_zip_with_shapefile(raw, tmp_path):
    shp_dir = tmp_path / "shp"
    shp_dir.mkdir()
    gpd.GeoDataFrame({"FHSZ_Description": ["Very High"]}, geometry=[box(-117.76, 33.68, -117.75, 33.69)],
                     crs=4326).to_file(shp_dir / "fhsz.shp")
    with zipfile.ZipFile(raw / "fhsz_lra_2025.zip", "w") as z:
        for f in shp_dir.iterdir():
            z.write(f, f"fhsz/{f.name}")
    g = LiveSources().get("calfire_fhsz_lra", AREA)
    assert len(g) == 1 and "FHSZ_Descr" in g.columns   # shapefile truncates to 10 chars
