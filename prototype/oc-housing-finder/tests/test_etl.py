import json
from pathlib import Path

from oc_housing.etl.boundaries import JurisdictionIndex
from oc_housing.etl.overlays import apply_overlay
from oc_housing.etl.parcels import load_parcels
from oc_housing.zoning.base import load_adapters

from conftest import make_parcel


def square(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def feat(name, ptype, geom):
    return {"type": "Feature", "geometry": geom, "properties": {"NAME": name, "PlaceType": ptype}}


CFG = {"unincorporated_label": "Unincorporated Orange County",
       "unincorporated_communities": ["Rossmoor"], "expected_incorporated_cities": 2}


def build_index():
    gj = {"features": [
        feat("Alpha", "City", square(0, 0, 1, 1)),
        feat("Beta", "City", square(1, 0, 2, 1)),
        feat("Rossmoor", "City", square(2, 0, 3, 1)),                       # census community
        feat("Supervisory District 3", "Unincorporated", square(3, 0, 4, 1)),
        {"type": "Feature", "geometry": None, "properties": {"NAME": None}},  # empty row
    ]}
    return JurisdictionIndex(gj, CFG)


# ---- jurisdictions ---------------------------------------------------------
def test_city_lookup_and_zip_independence():
    idx = build_index()
    assert idx.lookup(0.5, 0.5).name == "Alpha"
    assert idx.lookup(0.5, 1.5).name == "Beta"  # two cities, however the ZIP is drawn


def test_communities_and_districts_resolve_to_unincorporated():
    idx = build_index()
    ross = idx.lookup(0.5, 2.5)
    assert ross.name == "Unincorporated Orange County" and ross.community == "Rossmoor"
    dist = idx.lookup(0.5, 3.5)
    assert dist.name == "Unincorporated Orange County" and dist.kind == "unincorporated"


def test_no_match_returns_none_and_empty_rows_dropped():
    idx = build_index()
    assert idx.lookup(50, 50) is None
    assert idx.dropped_empty == 1
    assert idx.cities == ["Alpha", "Beta"]  # communities/districts are not cities


def test_invalid_geometry_is_repaired():
    from shapely.geometry import shape

    # Self-intersecting bowtie: two triangular lobes meeting at (1, 1).
    bowtie = {"type": "Polygon", "coordinates": [[[0, 0], [2, 2], [2, 0], [0, 2], [0, 0]]]}
    assert not shape(bowtie).is_valid  # prove the repair path is actually exercised
    idx = JurisdictionIndex({"features": [feat("Bow", "City", bowtie)]}, CFG)
    assert idx.lookup(1.0, 0.2).name == "Bow"   # lat=1.0, lon=0.2: inside the left lobe
    assert idx.lookup(1.0, 1.8).name == "Bow"   # inside the right lobe
    assert idx.lookup(1.8, 1.0) is None         # in the gap between lobes


def test_assign_sets_city_on_parcels():
    idx = build_index()
    a, b = make_parcel(parcel_id="a", lat=0.5, lon=0.5), make_parcel(parcel_id="b", lat=9, lon=9)
    assert idx.assign([a, b]) == 1
    assert a.city == "Alpha" and b.city is None


# ---- overlays --------------------------------------------------------------
HAZARD = {"features": [feat("zone", None, square(0, 0, 1, 1))]}


def test_flag_mode_marks_outside_as_false():
    inside, outside = make_parcel(parcel_id="i", lat=0.5, lon=0.5), make_parcel(parcel_id="o", lat=5, lon=5)
    apply_overlay([inside, outside], HAZARD, "fire_hazard", "flag")
    assert inside.fire_hazard is True and outside.fire_hazard is False


def test_flag_inside_only_leaves_outside_unknown():
    inside, outside = make_parcel(parcel_id="i", lat=0.5, lon=0.5), make_parcel(parcel_id="o", lat=5, lon=5)
    apply_overlay([inside, outside], HAZARD, "housing_element_site", "flag_inside_only")
    assert inside.housing_element_site is True and outside.housing_element_site is None


def test_value_mode_copies_attribute():
    gj = {"features": [{"type": "Feature", "geometry": square(0, 0, 1, 1),
                        "properties": {"ZONE": "R3"}}]}
    p = make_parcel(lat=0.5, lon=0.5)
    apply_overlay([p], gj, "zoning_code", "value", attribute="ZONE")
    assert p.zoning_code == "R3"


# ---- parcel loader ---------------------------------------------------------
MAPPING = {
    "columns": {"apn": "APN", "zip_code": "ZIP", "lot_sqft": "LOT", "use_code": "USE",
                "owner_type": "OWN", "address": None},
    "use_codes": {"0100": "vacant", "1100": "single_family"},
    "owner_types": {"CHURCH": "faith"},
}


def test_loader_maps_columns_and_reports_problems(tmp_path: Path):
    gj = {"features": [
        {"geometry": square(0, 0, 1, 1), "properties":
            {"APN": "111", "ZIP": "92701-1234", "LOT": "9000", "USE": "0100", "OWN": "CHURCH"}},
        {"geometry": square(0, 0, 1, 1), "properties": {"APN": "222", "ZIP": "92701", "USE": "9999"}},
        {"geometry": None, "properties": {"APN": "333", "ZIP": "92701"}},       # no geometry
        {"geometry": square(0, 0, 1, 1), "properties": {"APN": "444", "ZIP": ""}},  # no zip
    ]}
    f = tmp_path / "in.geojson"
    f.write_text(json.dumps(gj))
    parcels, rep = load_parcels(f, MAPPING)
    assert rep["parcels_loaded"] == 2 and rep["skipped_no_geometry_or_zip"] == 2
    assert rep["unmapped_use_codes"] == ["9999"]  # reported, never guessed
    first = parcels[0]
    assert first.zip_code == "92701" and first.lot_sqft == 9000
    assert first.land_use == "vacant" and first.owner_type == "faith"
    assert parcels[1].land_use is None and parcels[1].lot_sqft is None  # unknown, not zero


# ---- zoning adapters -------------------------------------------------------
def test_adapters_skip_templates_and_group_by_city(tmp_path: Path):
    hdr = "city,zone_code,description,category,max_density_du_ac,max_height_ft,min_lot_sqft,parking_per_unit,source_url,retrieved,is_sample\n"
    (tmp_path / "_TEMPLATE.csv").write_text(hdr + "Skipped,X,,other,1,,,,,,\n")
    (tmp_path / "rules.csv").write_text(
        hdr + "Alpha,r3,multi,residential_multi,30,45,,1.5,http://x,2026-01-01,\n"
              "Beta,R1,single,residential_low,6,30,,2,,,\n")
    ad = load_adapters(tmp_path)
    assert set(ad) == {"Alpha", "Beta"}
    assert ad["Alpha"].lookup("R3").max_density_du_ac == 30  # case-insensitive
    assert ad["Alpha"].lookup("nope") is None
    assert not ad["Alpha"].is_sample
