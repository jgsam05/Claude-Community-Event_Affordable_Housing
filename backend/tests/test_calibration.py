"""Calibration: scores must not be inflated by a mislabeled tier, double counting or missing evidence."""
import os

os.environ["PARCEL_ENGINE_MODE"] = "fixture"

import pandas as pd
import pytest

from parcel_engine import pipeline, scoring
from parcel_engine.sources import FixtureSources


@pytest.mark.parametrize("category,expected", [
    ("Highest Resource", 1.0), ("High Resource", 1.0), ("High", 1.0),
    ("Moderate Resource", 0.5), ("Moderate Resource (Rapidly Changing)", 0.5),
    ("Low Resource", 0.0),
    ("High Segregation & Poverty", 0.0),   # contains "high" but is the lowest tier
    ("High Segregation and Poverty", 0.0), (None, 0.0),
])
def test_opportunity_area_tiers(category, expected):
    assert scoring._opportunity_value(category) == expected


def test_discount_pulls_above_median_scores_toward_the_median_by_missing_evidence():
    df = pd.DataFrame({"opp": [20.0, 40.0, 90.0, 90.0, None], "evidence": [10, 10, 9, 5, 4],
                       "development_potential": [20, 40, 90, 90, None], "feasibility_risk": [0, 0, 0, 0, None],
                       "opp_reason": ["", "", "", "", ""]})
    out = scoring._discount_for_missing_evidence(df)
    median = 40.0 if False else float(df["opp"].dropna().median())
    assert out.loc[0, "opp"] == 20 and out.loc[1, "opp"] == 40          # at or below the median: untouched
    assert out.loc[2, "opp"] == round(median + (90 - median) * 0.9)      # 9 of 10 keeps 90% of the gap
    assert out.loc[3, "opp"] == round(median + (90 - median) * 0.5)      # 5 of 10 keeps half
    assert out.loc[3, "opp"] < out.loc[2, "opp"] < 90
    assert "Discounted from 90" in out.loc[2, "opp_reason"]
    assert pd.isna(out.loc[4, "opp"])


def test_full_evidence_is_not_discounted_and_nothing_is_raised():
    df = pd.DataFrame({"opp": [10.0, 50.0, 80.0], "evidence": [10, 10, 10], "development_potential": [10, 50, 80],
                       "feasibility_risk": [0, 0, 0], "opp_reason": ["", "", ""]})
    assert scoring._discount_for_missing_evidence(df)["opp"].tolist() == [10, 50, 80]


def test_pathway_bonuses_do_not_double_count_transit_and_land_use():
    assert "commercial_pathway" not in scoring.BONUS_POINTS and "parking_reform" not in scoring.BONUS_POINTS


@pytest.fixture(scope="module")
def thin_and_full():
    full = pipeline.build_zip("92618", FixtureSources(), write=False)
    thin = pipeline.build_zip("92618", FixtureSources(omit={"nrhp", "dtsc_envirostor", "geotracker", "coastal_zone"}), write=False)
    return full, thin


def test_each_parcel_lists_the_risk_layers_that_were_not_checked(thin_and_full):
    full, thin = thin_and_full
    for f in thin["features"]:
        p = f["properties"]
        assert {"contamination", "historic properties", "coastal zone"} <= set(p["risk_unchecked"])
        if p["feasibility_risk"] is not None:
            assert "Risk is a minimum" in p["risk_reason"]


def test_opportunity_never_exceeds_its_raw_score(thin_and_full):
    for fc in thin_and_full:
        for f in fc["features"]:
            p = f["properties"]
            if p["opp"] is not None:
                assert p["opp"] <= p["opp_raw"] and p["evidence"] > 0
