"""Generic polygon overlays: hazard zones, zoning polygons, Housing Element sites.

Each overlay is a GeoJSON polygon layer in EPSG:4326 dropped into data/overlays/
and declared in config/overlays.yaml. A parcel is matched by its centroid.

  mode: flag   -> sets parcel.<field> = True when inside, False when outside
                  (only use for layers that cover the WHOLE county, otherwise
                  "outside" would wrongly mean "checked and clear")
  mode: flag_inside_only -> sets True when inside, leaves None (unknown) outside
  mode: clear_inside -> sets False when inside AND still unknown (apply AFTER the True layer)
  mode: value  -> copies feature property `attribute` into parcel.<field>
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import yaml
from shapely.geometry import Point, shape
from shapely.strtree import STRtree


def apply_overlay(parcels: Iterable, geojson: dict, field: str, mode: str,
                  attribute: str | None = None) -> int:
    geoms, props = [], []
    for feat in geojson["features"]:
        if feat.get("geometry"):
            geoms.append(shape(feat["geometry"]))
            props.append(feat.get("properties") or {})
    if not geoms:
        return 0
    tree = STRtree(geoms)
    touched = 0
    for p in parcels:
        hits = tree.query(Point(p.lon, p.lat), predicate="intersects")
        if len(hits):
            if mode in ("flag", "flag_inside_only"):
                setattr(p, field, True)
            elif mode == "clear_inside":   # mapped-and-clear area: False only if nothing set it True
                if getattr(p, field) is None:
                    setattr(p, field, False)
            elif mode == "value":
                setattr(p, field, props[int(hits[0])].get(attribute))
            touched += 1
        elif mode == "flag":
            setattr(p, field, False)
    return touched


def apply_configured_overlays(parcels: list, root: Path, cfg_name: str = "overlays.yaml") -> dict[str, int]:
    cfg_path = root / "config" / cfg_name
    if not cfg_path.exists():
        return {}
    cfg = yaml.safe_load(cfg_path.read_text()) or {}
    report: dict[str, int] = {}
    for item in cfg.get("overlays", []) or []:
        path = root / "data" / "overlays" / item["file"]
        if not path.exists():
            report[item["file"]] = -1  # declared but file missing
            continue
        geo = json.loads(path.read_text())
        report[item["file"]] = apply_overlay(
            parcels, geo, item["field"], item["mode"], item.get("attribute"))
    return report
