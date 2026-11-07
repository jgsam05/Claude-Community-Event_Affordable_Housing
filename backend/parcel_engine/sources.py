"""Data access. `get(id, area)` returns data for a registry dataset clipped to an
area, or None when the dataset is not available (its signals then count as
missing). Two implementations: LiveSources (real endpoints and files) and
FixtureSources (synthetic data for tests and offline demos).
"""
from __future__ import annotations

import io
import logging
import zipfile
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import box

from . import arcgis, registry
from .config import WORK_CRS

log = logging.getLogger(__name__)
RAW = registry.DATA_DIR / "raw"
CACHE = registry.DATA_DIR / "cache"
OC_STATE, OC_COUNTY = "06", "059"


def pick(df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
    """First candidate column present in df (case-insensitive)."""
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    if required:
        raise KeyError(f"none of {candidates} in columns {list(df.columns)[:30]}")
    return None


def norm_apn(v) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    digits = "".join(ch for ch in str(v) if ch.isdigit())
    return digits.zfill(8) if digits else None


class Sources:
    mode = "base"

    def __init__(self):
        self.status: dict[str, str] = {}

    def get(self, dataset_id: str, area_4326=None):
        raise NotImplementedError

    def available(self, dataset_id: str) -> bool:
        return self.status.get(dataset_id) == "loaded"


class LiveSources(Sources):
    mode = "live"

    def get(self, dataset_id, area_4326=None, cache_key: str | None = None):
        spec = registry.BY_ID[dataset_id]
        try:
            data = self._load(spec, area_4326, cache_key)
        except FileNotFoundError:
            self.status[dataset_id] = "not_ingested"
            return None
        except Exception as e:  # a broken source should not take down the ZIP
            log.warning("dataset %s failed: %s", dataset_id, e)
            self.status[dataset_id] = f"error: {e}"
            return None
        self.status[dataset_id] = "loaded"
        return data

    # ----- loaders -----
    def _load(self, spec, area, cache_key):
        access = spec["access"]
        if access == "arcgis_rest":
            cached = CACHE / f"{spec['id']}_{cache_key}.parquet" if cache_key else None
            if cached and cached.exists():
                return gpd.read_parquet(cached)
            where = (spec.get("join") or {}).get("where", "1=1")
            gdf = arcgis.query(spec["url"], where=where, geometry=area)
            if cached is not None:
                cached.parent.mkdir(parents=True, exist_ok=True)
                gdf.to_parquet(cached)
            registry.stamp_ingest(spec["id"], extra={"method": "arcgis_rest query"})
            return gdf
        if access == "census_api":
            return self._acs()
        if access == "pdf_dir":
            path = CACHE / "tax_defaulted_apns.csv"
            if not path.exists():
                raise FileNotFoundError(path)
            return pd.read_csv(path, dtype=str)
        path = RAW / spec["local_file"]
        if not path.exists():
            raise FileNotFoundError(path)
        registry.stamp_ingest(spec["id"], datetime.fromtimestamp(path.stat().st_mtime).date().isoformat(),
                              extra={"method": f"local file {path.name}"})
        if spec["id"] == "lodes_wac":
            return self._lodes(path)
        return self._read_file(spec, path, area)

    def _read_file(self, spec, path: Path, area):
        join = spec.get("join") or {}
        suffix = "".join(path.suffixes).lower()
        if join.get("gtfs") or (suffix.endswith(".zip") and "gtfs" in path.name):
            with zipfile.ZipFile(path) as z:
                df = pd.read_csv(io.BytesIO(z.read("stops.txt")))
            return _points(df, "stop_lat", "stop_lon", area)
        if suffix.endswith(".csv") or suffix.endswith(".txt") or suffix.endswith(".csv.gz"):
            sep = "\t" if suffix.endswith(".txt") else ","
            df = pd.read_csv(path, sep=sep, dtype=str, low_memory=False)
            if "lat" in join:
                return _points(df, pick(df, join["lat"]), pick(df, join["lon"]), area)
            return df
        gdf = gpd.read_parquet(path) if suffix.endswith(".parquet") else gpd.read_file(path)
        gdf = gdf.to_crs(WORK_CRS)
        if area is not None:
            clip = gpd.GeoSeries([area], crs=4326).to_crs(WORK_CRS).iloc[0].envelope
            gdf = gdf[gdf.intersects(clip)]
        return gdf

    def _acs(self):
        path = CACHE / "acs5_oc_tracts.csv"
        if path.exists():
            return pd.read_csv(path, dtype={"tract_geoid": str})
        spec = registry.BY_ID["acs5"]
        vars_ = ["B19013_001E", "B25070_001E", "B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E"]
        r = requests.get(spec["url"], params={"get": ",".join(vars_), "for": "tract:*",
                                              "in": f"state:{OC_STATE} county:{OC_COUNTY}"}, timeout=60)
        r.raise_for_status()
        rows = r.json()
        df = pd.DataFrame(rows[1:], columns=rows[0])
        for v in vars_:
            df[v] = pd.to_numeric(df[v], errors="coerce")
        df.loc[df["B19013_001E"] < 0, "B19013_001E"] = None  # Census null sentinel
        burdened = df[["B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E"]].sum(axis=1)
        out = pd.DataFrame({
            "tract_geoid": df["state"] + df["county"] + df["tract"],
            "median_hh_income": df["B19013_001E"],
            "rent_burden_share": (burdened / df["B25070_001E"]).where(df["B25070_001E"] > 0),
        })
        path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(path, index=False)
        registry.stamp_ingest("acs5", extra={"method": "Census API", "vintage_url": spec["url"]})
        return out

    def _lodes(self, path: Path):
        df = pd.read_csv(path, dtype={"w_geocode": str}, usecols=["w_geocode", "C000"])
        df = df[df["w_geocode"].str.startswith(OC_STATE + OC_COUNTY)]
        df["tract_geoid"] = df["w_geocode"].str[:11]
        return df.groupby("tract_geoid", as_index=False)["C000"].sum().rename(columns={"C000": "tract_jobs"})


def _points(df, lat_col, lon_col, area):
    df = df.copy()
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col])
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs=4326)
    if area is not None:
        minx, miny, maxx, maxy = area.bounds
        pad = 0.05  # ~3 miles: nearest-distance joins need context outside the ZIP
        gdf = gdf[gdf.intersects(box(minx - pad, miny - pad, maxx + pad, maxy + pad))]
    return gdf.to_crs(WORK_CRS)


class FixtureSources(Sources):
    """Synthetic world from fixtures.py. Never real county data."""
    mode = "fixture"

    def __init__(self, omit: set[str] | None = None):
        super().__init__()
        from . import fixtures
        self.world = fixtures.world()
        self.omit = omit or set()

    def get(self, dataset_id, area_4326=None, cache_key=None):
        if dataset_id in self.omit or dataset_id not in self.world:
            self.status[dataset_id] = "not_ingested"
            return None
        self.status[dataset_id] = "loaded"
        data = self.world[dataset_id]
        if isinstance(data, gpd.GeoDataFrame) and area_4326 is not None and dataset_id != "census_zcta":
            env = gpd.GeoSeries([area_4326], crs=4326).to_crs(WORK_CRS).iloc[0].buffer(15000).envelope
            data = data[data.intersects(env)]
        return data.copy()


def make_sources() -> Sources:
    from .config import MODE
    return FixtureSources() if MODE == "fixture" else LiveSources()

