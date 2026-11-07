"""State-law pathways: each status, exclusions, and datasets that are not loaded."""
from parcel_engine import pathways

ALL = lambda ids: (lambda k: k in ids)
LOADED = {"hcd_sb35", "osm_worship", "hcd_sla_notices", "hcd_compliance", "scag_he_sites", "hud_lihtc"}


def run(row, loaded=LOADED):
    return pathways.analyze(row.get, ALL(loaded))


def by_id(paths):
    return {p["id"]: p for p in paths}


def test_sb35_likely_when_subject_and_no_exclusion():
    paths, _ = run({"jurisdiction": "Tustin", "sb35_status": "Subject to SB 35 (10% affordability)", "lot_sqft": 9000})
    p = by_id(paths)["sb35"]
    assert p["status"] == "likely" and "10%" in p["why"]


def test_sb35_blocked_by_flood_zone():
    paths, _ = run({"jurisdiction": "Tustin", "sb35_status": "Subject to SB 35 (10% affordability)", "flood_sfha": True})
    assert by_id(paths)["sb35"]["status"] == "blocked"


def test_sb35_omitted_when_exempt():
    paths, _ = run({"sb35_status": "Exempt"})
    assert "sb35" not in by_id(paths)


def test_unloaded_datasets_are_listed_not_silent():
    paths, unchecked = run({"lot_sqft": 5000}, loaded=set())
    ids = {u["id"] for u in unchecked}
    assert {"sb35", "sb4", "sla", "builders_remedy", "he", "preservation"} <= ids
    assert all(u["needs"] for u in unchecked)
    assert "sb35" not in by_id(paths)


def test_commercial_land_use_is_possible_and_blocked_by_hazard():
    paths, _ = run({"land_use_code": "1210"})
    assert by_id(paths)["commercial"]["status"] == "possible"
    paths, _ = run({"land_use_code": "1210", "fault_zone": True})
    assert by_id(paths)["commercial"]["status"] == "blocked"
    paths, _ = run({"land_use_code": "1110"})  # single-family residential
    assert "commercial" not in by_id(paths)


def test_parking_reform_near_transit_and_density_bonus_for_any_lot():
    paths, _ = run({"in_hqta": True, "lot_sqft": 4000})
    got = by_id(paths)
    assert got["parking"]["status"] == "likely" and got["density"]["status"] == "applies"
    paths, _ = run({"in_hqta": False, "lot_sqft": 4000})
    assert "parking" not in by_id(paths)


def test_surplus_land_statuses():
    paths, _ = run({"sla_notice": True})
    assert by_id(paths)["sla"]["status"] == "applies"
    paths, _ = run({"public_surplus": True})
    assert by_id(paths)["sla"]["status"] == "likely"


def test_faith_based_and_housing_element_and_builders_remedy():
    paths, _ = run({"faith_based": True, "he_rezone": True, "jurisdiction": "Tustin", "he_status": "Out of compliance"})
    got = by_id(paths)
    assert got["sb4"]["status"] == "possible" and got["he"]["status"] == "applies" and got["builders_remedy"]["status"] == "likely"
    assert "rezone" in got["he"]["why"]


def test_preservation_near_tax_credit_housing():
    paths, _ = run({"dist_lihtc_ft": 0})
    assert by_id(paths)["preservation"]["status"] == "possible"
    paths, _ = run({"dist_lihtc_ft": 900})
    assert "preservation" not in by_id(paths)


def test_every_entry_explains_itself():
    paths, _ = run({"jurisdiction": "Tustin", "sb35_status": "Subject to SB 35 (10% affordability)", "land_use_code": "1220",
                    "in_hqta": True, "lot_sqft": 8000, "he_site": True, "faith_based": True})
    for p in paths:
        assert p["status"] in {"applies", "likely", "possible", "blocked"}
        assert p["law"] and p["name"] and p["why"] and p["basis"] and p["caveat"]
