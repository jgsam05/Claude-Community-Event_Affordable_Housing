from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..schema import ZoneRule

CSV_COLUMNS = [
    "city",
    "zone_code",
    "description",
    "category",
    "max_density_du_ac",
    "max_height_ft",
    "min_lot_sqft",
    "parking_per_unit",
    "source_url",
    "retrieved",
    "is_sample",
]


def _num(value: str) -> Optional[float]:
    value = (value or "").strip()
    if value == "":
        return None
    return float(value)


class ZoningAdapter(ABC):
    """One jurisdiction's zoning rules in the common schema."""

    city: str

    @abstractmethod
    def rules(self) -> dict[str, ZoneRule]:
        ...

    def lookup(self, zone_code: Optional[str]) -> Optional[ZoneRule]:
        if not zone_code:
            return None
        return self.rules().get(zone_code.strip().upper())

    @property
    def is_sample(self) -> bool:
        return any(r.is_sample for r in self.rules().values())


class CsvZoningAdapter(ZoningAdapter):
    """Rules loaded from rows of a CSV that all belong to one city.

    This is the fastest way to add a city: copy the rules from the city's
    municipal code into data/zoning/<city>.csv (see _TEMPLATE.csv). Fill
    source_url and retrieved so every number is traceable.
    """

    def __init__(self, city: str, rows: list[dict]):
        self.city = city
        self._rules: dict[str, ZoneRule] = {}
        for row in rows:
            rule = ZoneRule(
                city=city,
                zone_code=row["zone_code"].strip().upper(),
                description=row.get("description", ""),
                category=(row.get("category") or "other").strip(),
                max_density_du_ac=_num(row.get("max_density_du_ac", "")),
                max_height_ft=_num(row.get("max_height_ft", "")),
                min_lot_sqft=_num(row.get("min_lot_sqft", "")),
                parking_per_unit=_num(row.get("parking_per_unit", "")),
                source_url=row.get("source_url", ""),
                retrieved=row.get("retrieved", ""),
                is_sample=(row.get("is_sample", "").strip().lower() in ("1", "true", "yes")),
            )
            self._rules[rule.zone_code] = rule

    def rules(self) -> dict[str, ZoneRule]:
        return self._rules


def load_adapters(zoning_dir: Path) -> dict[str, ZoningAdapter]:
    """Load every data/zoning/*.csv (files starting with '_' are templates)."""
    by_city: dict[str, list[dict]] = {}
    if not zoning_dir.exists():
        return {}
    for path in sorted(zoning_dir.glob("*.csv")):
        if path.name.startswith("_"):
            continue
        with path.open(newline="") as fh:
            for row in csv.DictReader(fh):
                city = (row.get("city") or "").strip()
                if not city or not (row.get("zone_code") or "").strip():
                    continue
                by_city.setdefault(city, []).append(row)
    return {city: CsvZoningAdapter(city, rows) for city, rows in by_city.items()}
