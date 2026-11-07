from oc_housing.scoring import score_parcel


def score(p, adapters, scoring_cfg, laws_cfg):
    return score_parcel(p, adapters, scoring_cfg, laws_cfg)


def test_vacant_multifamily_lot_scores_high(parcel_factory, adapters, scoring_cfg, laws_cfg):
    p = parcel_factory(land_use="vacant", lot_sqft=30000, zoning_code="R3", owner_type="public",
                       transit_distance_m=300, opportunity_level="high", building_sqft=0,
                       tax_default=True)
    s = score(p, adapters, scoring_cfg, laws_cfg)
    assert s.potential > 75
    assert s.units.best_units and s.units.best_units > 20
    assert s.result_type == "development"


def test_unknown_data_lowers_confidence_not_score(parcel_factory, adapters, scoring_cfg, laws_cfg):
    full = parcel_factory(land_use="vacant", lot_sqft=30000, zoning_code="R3", owner_type="public",
                          transit_distance_m=300, opportunity_level="high", tax_default=False)
    sparse = parcel_factory(land_use="vacant", lot_sqft=30000, zoning_code="R3")
    a = score(full, adapters, scoring_cfg, laws_cfg)
    b = score(sparse, adapters, scoring_cfg, laws_cfg)
    assert b.confidence < a.confidence
    # Unknown components are excluded from the average, never counted as zero.
    unknown = [c for c in b.components if c.score is None]
    assert unknown and all(c.score is None for c in unknown)
    assert b.potential > 50


def test_known_nonresidential_zoning_scores_zero_upside_not_unknown(
        parcel_factory, adapters, scoring_cfg, laws_cfg):
    # Regression: a vacant lot in a zone allowing no housing used to rank #1
    # because its legal upside was treated as unknown instead of zero.
    p = parcel_factory(land_use="vacant", lot_sqft=8000, zoning_code="C1")
    s = score(p, adapters, scoring_cfg, laws_cfg)
    legal = next(c for c in s.components if c.name == "legal_upside")
    assert s.units.best_units == 0
    assert legal.score == 0.0


def test_unknown_zoning_is_not_guessed(parcel_factory, scoring_cfg, laws_cfg):
    p = parcel_factory(land_use="vacant", lot_sqft=30000, zoning_code="R3", city="Costa Mesa")
    s = score(p, {}, scoring_cfg, laws_cfg)  # no adapters at all
    assert s.zoning_status == "not_ingested"
    assert s.units.base_units is None
    assert any("not yet ingested" in g for g in s.data_gaps)


def test_zone_code_missing_from_table_is_flagged(parcel_factory, adapters, scoring_cfg, laws_cfg):
    p = parcel_factory(land_use="vacant", lot_sqft=30000, zoning_code="ZZZ")
    s = score(p, adapters, scoring_cfg, laws_cfg)
    assert s.zoning_status == "code_not_in_table"


def test_adu_only_does_not_get_uplift_bonus_when_zoning_unknown(
        parcel_factory, scoring_cfg, laws_cfg):
    p = parcel_factory(land_use="single_family", lot_sqft=6000, city="Nowhere")
    s = score(p, {}, scoring_cfg, laws_cfg)
    legal = next(c for c in s.components if c.name == "legal_upside")
    assert s.units.best_pathway == "adu"
    assert legal.score < 0.1  # size-only, no uplift term


def test_risk_flags_add_risk_and_unknown_does_not(parcel_factory, adapters, scoring_cfg, laws_cfg):
    clean = score(parcel_factory(land_use="vacant", lot_sqft=20000, coastal_zone=False,
                                 fire_hazard=False), adapters, scoring_cfg, laws_cfg)
    risky = score(parcel_factory(land_use="vacant", lot_sqft=20000, coastal_zone=True,
                                 fire_hazard=True), adapters, scoring_cfg, laws_cfg)
    unknown = score(parcel_factory(land_use="vacant", lot_sqft=20000), adapters,
                    scoring_cfg, laws_cfg)
    assert risky.risk > clean.risk == 0
    assert unknown.risk == 0 and unknown.risk_confidence < clean.risk_confidence
    assert risky.overall < clean.overall


def test_mobile_home_is_derived_not_reported_unknown(parcel_factory, adapters, scoring_cfg, laws_cfg):
    s = score(parcel_factory(land_use="single_family", lot_sqft=6000), adapters,
              scoring_cfg, laws_cfg)
    assert not any(g == "mobile_home: unknown" for g in s.data_gaps)


def test_mobile_home_park_is_preservation_watch(parcel_factory, adapters, scoring_cfg, laws_cfg):
    s = score(parcel_factory(land_use="mobile_home_park", lot_sqft=90000, zoning_code="R3"),
              adapters, scoring_cfg, laws_cfg)
    assert s.result_type == "preservation_watch"
    assert s.risk > 0  # flagged as a preserve-not-demolish constraint


def test_prop13_caveat_when_no_recent_sale(parcel_factory, adapters, scoring_cfg, laws_cfg):
    old = parcel_factory(land_use="commercial_1story", lot_sqft=20000, building_sqft=4000,
                         land_value=900000, improvement_value=200000, last_sale_year=1995)
    s = score(old, adapters, scoring_cfg, laws_cfg)
    under = next(c for c in s.components if c.name == "underbuilt")
    assert "Prop 13" in under.explanation


def test_cost_per_unit_prefers_recent_sale(parcel_factory, adapters, scoring_cfg, laws_cfg):
    p = parcel_factory(land_use="vacant", lot_sqft=43560, zoning_code="R3", land_value=100_000,
                       last_sale_price=3_000_000, last_sale_year=2025)
    s = score(p, adapters, scoring_cfg, laws_cfg)
    assert "recent sale" in s.price_basis
    assert s.land_cost_per_unit == round(3_000_000 / s.units.best_units)


def test_synthetic_and_unverified_laws_are_caveated(parcel_factory, adapters, scoring_cfg, laws_cfg):
    s = score(parcel_factory(land_use="vacant", lot_sqft=9000, is_synthetic=True),
              adapters, scoring_cfg, laws_cfg)
    text = " ".join(s.caveats)
    assert "SYNTHETIC" in text and "unverified" in text
