"""Load a user-supplied parcel file and map it into the Parcel schema.

The OC Assessor does not publish attributed parcel data (use code, year built,
values) as a free download; it comes from vendors such as ParcelQuest or Regrid,
or from a county records request. Export it as GeoJSON (EPSG:4326), set the
column names in config/parcel_mapping.yaml, and run:

    python -m oc_housing.build --parcels data/parcels_in/my_export.geojson
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import yaml
from shapely.geometry import shape

from ..schema import Parcel

ROOT = Path(__file__).resolve().parents[2]


def _num(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int(v: Any) -> Optional[int]:
    n = _num(v)
    return int(n) if n is not None else None


def _bool(v: Any) -> Optional[bool]:
    if v is None or v == "":
        return None
    if isinstance(v, str):
        return v.strip().lower() in ("1", "y", "yes", "true", "t")
    return bool(v)


def load_mapping(path: Path | None = None) -> dict:
    return yaml.safe_load((path or ROOT / "config" / "parcel_mapping.yaml").read_text())


def load_parcels(geojson_path: Path, mapping: dict) -> tuple[list[Parcel], dict]:
    """Returns (parcels, report). Rows that cannot be mapped are counted, not hidden."""
    data = json.loads(geojson_path.read_text())
    cols: dict = mapping["columns"]
    use_map: dict = {str(k): v for k, v in (mapping.get("use_codes") or {}).items()}
    owner_map: dict = {str(k): v for k, v in (mapping.get("owner_types") or {}).items()}

    def get(props: dict, key: str):
        col = cols.get(key)
        return props.get(col) if col else None

    parcels, skipped, unmapped_use = [], 0, set()
    for i, feat in enumerate(data["features"]):
        props = feat.get("properties") or {}
        geom = feat.get("geometry")
        zip_code = str(get(props, "zip_code") or "").strip()[:5]
        if not geom or not zip_code:
            skipped += 1
            continue
        centroid = shape(geom).centroid
        raw_use = get(props, "use_code")
        land_use = use_map.get(str(raw_use)) if raw_use is not None else None
        if raw_use is not None and land_use is None:
            unmapped_use.add(str(raw_use))
        apn = get(props, "apn")
        parcels.append(Parcel(
            parcel_id=str(apn or f"row-{i}"),
            apn=str(apn) if apn else None,
            address=get(props, "address"),
            zip_code=zip_code,
            lat=centroid.y, lon=centroid.x, geometry=geom,
            lot_sqft=_num(get(props, "lot_sqft")),
            land_use=land_use,
            year_built=_int(get(props, "year_built")),
            building_sqft=_num(get(props, "building_sqft")),
            land_value=_num(get(props, "land_value")),
            improvement_value=_num(get(props, "improvement_value")),
            last_sale_price=_num(get(props, "last_sale_price")),
            last_sale_year=_int(get(props, "last_sale_year")),
            owner_type=owner_map.get(str(get(props, "owner_type")), "unknown"),
            zoning_code=(str(get(props, "zoning_code")).strip().upper()
                         if get(props, "zoning_code") else None),
            stack_units=_int(get(props, "stack_units")),
            housing_element_site=_bool(get(props, "housing_element_site")),
            tax_default=_bool(get(props, "tax_default")),
            code_violations=_int(get(props, "code_violations")),
        ))
    report = {
        "rows_in": len(data["features"]),
        "parcels_loaded": len(parcels),
        "skipped_no_geometry_or_zip": skipped,
        "unmapped_use_codes": sorted(unmapped_use),
    }
    return parcels, report
