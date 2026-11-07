"""Runtime configuration. Override with environment variables."""
import os

# Working CRS for all measurements: NAD83 / California zone VI (US ft), same as OCGIS.
WORK_CRS = "EPSG:2230"
OUT_CRS = "EPSG:4326"

# "live" queries real sources; "fixture" uses synthetic data (tests, offline demos).
MODE = os.environ.get("PARCEL_ENGINE_MODE", "live")

# Phase 1 sample ZIPs. 92705 crosses Santa Ana, Tustin and unincorporated North Tustin.
SAMPLE_ZIPS = ["92618", "92620", "92705"]
CROSS_CITY_SAMPLE = "92705"

# Footprint source: ocgis_building_footprints (REST) or overture_buildings (file).
FOOTPRINT_SOURCE = os.environ.get("FOOTPRINT_SOURCE", "ocgis_building_footprints")

# A ZCTA counts as an OC ZIP if at least this share of its area falls inside the county.
MIN_OC_SHARE = 0.05

# Geometry parameters (feet).
SETBACK_FT = 10.0            # uniform inward buffer for rough buildable area
FRONTAGE_BUFFER_FT = 60.0    # parcel edge within this distance of a centerline counts as frontage
MIN_FOOTPRINT_SQFT = 50.0    # ignore slivers when deciding a parcel is vacant

SCORING_VERSION = "0.1.0"
