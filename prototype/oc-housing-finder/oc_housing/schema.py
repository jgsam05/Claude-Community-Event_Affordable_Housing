"""Shared data model. Every field that can be missing is Optional: None means
UNKNOWN, never "no". Scoring treats unknown as a confidence gap, not a zero."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

LandUse = Literal[
    "vacant",
    "surface_parking",
    "commercial_1story",
    "commercial_other",
    "single_family",
    "multifamily",
    "mobile_home_park",
    "industrial",
    "public",
    "institutional_faith",
    "other",
]

OwnerType = Literal["public", "corporate", "individual", "nonprofit", "faith", "unknown"]

OpportunityLevel = Literal["highest", "high", "moderate", "low", "very_low"]

ZoneCategory = Literal[
    "residential_low",
    "residential_multi",
    "commercial",
    "mixed_use",
    "industrial",
    "public",
    "other",
]


class Parcel(BaseModel):
    parcel_id: str
    apn: Optional[str] = None
    address: Optional[str] = None
    zip_code: str
    city: Optional[str] = None  # jurisdiction, set by spatial join (never trust ZIP)
    community: Optional[str] = None  # unincorporated community name, e.g. Rossmoor
    lat: float
    lon: float
    geometry: dict  # GeoJSON geometry, EPSG:4326

    lot_sqft: Optional[float] = None
    land_use: Optional[LandUse] = None
    year_built: Optional[int] = None
    building_sqft: Optional[float] = None
    land_value: Optional[float] = None
    improvement_value: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_year: Optional[int] = None
    owner_type: OwnerType = "unknown"  # type only, never owner names

    zoning_code: Optional[str] = None
    stack_units: Optional[int] = None  # >1 = condo/shared-lot stack collapsed into this site

    # Distress
    tax_default: Optional[bool] = None
    code_violations: Optional[int] = None
    vacant_registry: Optional[bool] = None

    # Legal / location signals
    housing_element_site: Optional[bool] = None
    transit_distance_m: Optional[float] = None
    opportunity_level: Optional[OpportunityLevel] = None

    # Constraints (True = constraint present)
    coastal_zone: Optional[bool] = None
    fire_hazard: Optional[bool] = None
    flood_zone: Optional[bool] = None
    airport_zone: Optional[bool] = None
    contamination: Optional[bool] = None
    historic: Optional[bool] = None
    mobile_home: Optional[bool] = None

    is_synthetic: bool = False


class ZoneRule(BaseModel):
    city: str
    zone_code: str
    description: str = ""
    category: ZoneCategory = "other"
    max_density_du_ac: Optional[float] = None
    max_height_ft: Optional[float] = None
    min_lot_sqft: Optional[float] = None
    parking_per_unit: Optional[float] = None
    source_url: str = ""
    retrieved: str = ""
    is_sample: bool = False


class PathwayEstimate(BaseModel):
    name: str
    units: Optional[int] = None  # None = cannot be computed from available data
    status: Literal["applies", "does_not_apply", "unknown"]
    note: str = ""


class UnitEstimate(BaseModel):
    base_units: Optional[int] = None
    best_units: Optional[int] = None
    best_pathway: Optional[str] = None
    pathways: list[PathwayEstimate] = Field(default_factory=list)
    laws_verified: bool = False
    disclaimer: str = (
        "Screening-level estimate only. Not legal, zoning, or investment advice; "
        "verify with the city and a qualified professional."
    )


class Component(BaseModel):
    name: str
    score: Optional[float] = None  # 0..1, None = unknown
    weight: float
    explanation: str


class ParcelScore(BaseModel):
    parcel_id: str
    result_type: Literal["development", "preservation_watch"]
    potential: float  # 0..100
    risk: float  # 0..100, higher = worse
    overall: float  # 0..100
    confidence: float  # 0..1
    risk_confidence: float  # 0..1
    components: list[Component]
    risk_components: list[Component]
    units: UnitEstimate
    land_cost_per_unit: Optional[float] = None
    price_basis: Optional[str] = None
    zoning_status: Literal["ingested", "sample", "not_ingested", "code_not_in_table"]
    caveats: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    reason: str = ""  # plain-language summary of why it scored this way
