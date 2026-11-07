"""OC city / unincorporated boundaries and the parcel -> jurisdiction join.

Source (verified reachable): OC GIS "OCCityBoundaries" FeatureService, layer 8.
ZIP codes do NOT line up with city limits, so every parcel is joined to a
jurisdiction spatially, and that jurisdiction's rules are the ones that apply.

How the layer is interpreted is documented (and configurable) in
config/jurisdictions.yaml. Key points: empty rows are dropped, census
communities such as Rossmoor and the 'Supervisory District N' polygons are
unincorporated and follow county rules, and anything matching no polygon is
left as None rather than guessed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import httpx
import yaml
from shapely.geometry import Point, shape
from shapely.strtree import STRtree
from shapely.validation import make_valid

BOUNDARY_URL = (
    "https://services.arcgis.com/UXmFoWC7yDHcDN5Q/ArcGIS/rest/services/"
    "OCCityBoundaries/FeatureServer/8/query"
)
ROOT = Path(__file__).resolve().parents[2]


def fetch_boundaries(dest: Path, force: bool = False) -> dict:
    """Download boundaries as GeoJSON (WGS84) and cache to `dest`."""
    if dest.exists() and not force:
        return json.loads(dest.read_text())
    params = {
        "where": "1=1",
        "outFields": "NAME,PlaceType,GEOID",
        "outSR": "4326",
        "f": "geojson",
        "resultRecordCount": "2000",
    }
    resp = httpx.get(BOUNDARY_URL, params=params, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    if "features" not in data or not data["features"]:
        raise RuntimeError(f"Boundary service returned no features: {str(data)[:200]}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data))
    return data


def load_jurisdiction_config() -> dict:
    return yaml.safe_load((ROOT / "config" / "jurisdictions.yaml").read_text())


@dataclass(frozen=True)
class Jurisdiction:
    name: str                      # a city name, or the unincorporated label
    kind: str                      # 'city' | 'unincorporated'
    community: Optional[str] = None  # e.g. 'Rossmoor' when unincorporated


class JurisdictionIndex:
    """Point-in-polygon lookup over the boundary features."""

    def __init__(self, geojson: dict, cfg: Optional[dict] = None):
        cfg = cfg or load_jurisdiction_config()
        self._label = cfg["unincorporated_label"]
        communities = set(cfg.get("unincorporated_communities") or [])

        self._geoms: list = []
        self._juris: list[Jurisdiction] = []
        self.dropped_empty = 0
        for feat in geojson["features"]:
            props = feat.get("properties") or {}
            name = props.get("NAME")
            if not name or not feat.get("geometry"):
                self.dropped_empty += 1
                continue
            geom = shape(feat["geometry"])
            if not geom.is_valid:
                geom = make_valid(geom)
            if name in communities:
                j = Jurisdiction(self._label, "unincorporated", community=name)
            elif props.get("PlaceType") == "Unincorporated":
                j = Jurisdiction(self._label, "unincorporated")
            else:
                j = Jurisdiction(name, "city")
            self._geoms.append(geom)
            self._juris.append(j)
        self._tree = STRtree(self._geoms)
        self.expected_cities = cfg.get("expected_incorporated_cities")

    @property
    def cities(self) -> list[str]:
        return sorted({j.name for j in self._juris if j.kind == "city"})

    def lookup(self, lat: float, lon: float) -> Optional[Jurisdiction]:
        hits = [int(i) for i in self._tree.query(Point(lon, lat), predicate="intersects")]
        if not hits:
            return None
        hits.sort(key=lambda i: self._geoms[i].area)  # most specific if overlapping
        return self._juris[hits[0]]

    def assign(self, parcels: Iterable) -> int:
        """Set parcel.city (+ community) for each parcel; returns matches."""
        matched = 0
        for p in parcels:
            j = self.lookup(p.lat, p.lon)
            p.city = j.name if j else None
            p.community = j.community if j else None
            matched += j is not None
        return matched
