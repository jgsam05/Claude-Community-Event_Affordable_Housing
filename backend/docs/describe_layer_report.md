# describe_layer: OCGIS parcel layer

**Layer:** `https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0`
**Checked:** 2026-11-07, from the layer's REST metadata and a 2-record `outFields=*` query.
**Service:** "Orange County Parcels", copyright "OC Survey, Geospatial Services". Polygon, WKID 102646 (EPSG:2230, US ft). maxRecordCount 1000. Query formats JSON, geoJSON, PBF. No `editingInfo.lastEditDate`, so the layer publishes no refresh date.

## Fields

| Field | Type | Alias |
|---|---|---|
| OBJECTID | OID | OBJECTID |
| SITE_ADDRESS | String(102) | Address |
| ASSESSMENT_NO | String(22) | APN (format `072-478-23`) |
| YEAR_BUILT | String(4) | 99!YearBuilt |
| NBR_BEDROOMS | SmallInteger | NBR_BEDROOMS |

## Conditional signals: decision

| Signal | Field needed | Present? | Decision |
|---|---|---|---|
| Land use code (parking, single-story retail, strip malls) | Use code | **No** | Use SCAG parcel land use (`scag_land_use`). If that file isn't ingested, the signal counts as missing. |
| Building age | Year built | **Yes** (`YEAR_BUILT`) | Kept. Both sampled records had it empty, so expect a low fill rate. Empty values count as missing (vacant parcels excepted). |
| Improvement-to-land ratio | Assessed values | **No** | Removed. |
| Owner type | Owner name | **No** | Public ownership only, from APR Table H, SLA notices and DGS state land. |
| Land cost per unit | Assessed land value | **No** | Unit-count estimate only (not built in Phase 1). |
| Airport compatibility zones | OC ALUC GIS layer | Not checked | Not ingested. Remove unless a GIS layer turns up. |
| Zoning for cities without adapters | SCAG zoning | n/a | Not ingested. Front end already says "Zoning isn't included yet." |

`ASSESSMENT_NO` is the APN, not an assessed value. `describe_layer()` excludes `*_NO` fields from the value match for this reason, and a test pins it.

## Still to measure on a networked machine

```
python -m parcel_engine.cli describe-layer
```

This re-reads the fields and adds a `fill_rate` for `YEAR_BUILT` (non-empty count ÷ total). If the fill rate is very low (under ~20%), consider dropping Year built from the 10 confidence signals. Otherwise it will push most parcels down one level.
