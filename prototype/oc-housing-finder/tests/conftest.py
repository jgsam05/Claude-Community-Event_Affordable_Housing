import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oc_housing.schema import Parcel, ZoneRule  # noqa: E402
from oc_housing.scoring import load_yaml  # noqa: E402
from oc_housing.zoning.base import CsvZoningAdapter  # noqa: E402

SQ = {"type": "Polygon", "coordinates": [[[-117.9, 33.7], [-117.899, 33.7],
                                         [-117.899, 33.701], [-117.9, 33.701], [-117.9, 33.7]]]}


def make_parcel(**kw) -> Parcel:
    base = dict(parcel_id="T1", zip_code="92701", city="Testville", lat=33.7005,
                lon=-117.8995, geometry=SQ)
    base.update(kw)
    return Parcel(**base)


def make_adapter(city="Testville", rows=None) -> CsvZoningAdapter:
    rows = rows or [
        dict(zone_code="R1", category="residential_low", max_density_du_ac="6"),
        dict(zone_code="R3", category="residential_multi", max_density_du_ac="30"),
        dict(zone_code="C1", category="commercial", max_density_du_ac="0"),
    ]
    return CsvZoningAdapter(city, rows)


@pytest.fixture
def parcel_factory():
    return make_parcel


@pytest.fixture
def adapters():
    return {"Testville": make_adapter()}


@pytest.fixture
def scoring_cfg():
    return load_yaml("scoring.yaml")


@pytest.fixture
def laws_cfg():
    return load_yaml("laws.yaml")
