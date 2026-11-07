from oc_housing.laws import estimate_units


def path(est, name):
    return next(p for p in est.pathways if p.name == name)


def test_base_zoning_math(parcel_factory, adapters, laws_cfg):
    # 1 acre at 30 du/ac -> 30 units
    p = parcel_factory(land_use="vacant", lot_sqft=43560)
    est = estimate_units(p, adapters["Testville"].lookup("R3"), laws_cfg)
    assert est.base_units == 30
    # density bonus: +50% -> 45
    assert path(est, "density_bonus").units == 45
    assert est.best_units == 45 and est.best_pathway == "density_bonus"


def test_density_bonus_needs_min_base_units(parcel_factory, adapters, laws_cfg):
    p = parcel_factory(land_use="vacant", lot_sqft=5000)  # ~0.11 ac * 30 = 3 units
    est = estimate_units(p, adapters["Testville"].lookup("R3"), laws_cfg)
    assert est.base_units == 3
    assert path(est, "density_bonus").status == "does_not_apply"


def test_sb9_thresholds(parcel_factory, adapters, laws_cfg):
    r1 = adapters["Testville"].lookup("R1")
    big = estimate_units(parcel_factory(land_use="single_family", lot_sqft=5000), r1, laws_cfg)
    mid = estimate_units(parcel_factory(land_use="single_family", lot_sqft=3000), r1, laws_cfg)
    small = estimate_units(parcel_factory(land_use="single_family", lot_sqft=2000), r1, laws_cfg)
    assert path(big, "sb9").units == 4
    assert path(mid, "sb9").units == 2
    assert path(small, "sb9").units == 0


def test_ab2011_only_on_commercial_and_big_enough(parcel_factory, adapters, laws_cfg):
    c1 = adapters["Testville"].lookup("C1")
    ok = estimate_units(parcel_factory(land_use="surface_parking", lot_sqft=43560), c1, laws_cfg)
    tiny = estimate_units(parcel_factory(land_use="surface_parking", lot_sqft=5000), c1, laws_cfg)
    assert path(ok, "ab2011").units == 30
    assert path(tiny, "ab2011").status == "does_not_apply"


def test_zero_best_units_when_zoning_known_and_nothing_applies(parcel_factory, adapters, laws_cfg):
    est = estimate_units(parcel_factory(land_use="vacant", lot_sqft=5000),
                         adapters["Testville"].lookup("C1"), laws_cfg)
    assert est.best_units == 0 and est.best_pathway is None


def test_no_rule_means_unknown_not_zero(parcel_factory, laws_cfg):
    est = estimate_units(parcel_factory(land_use="vacant", lot_sqft=30000), None, laws_cfg)
    assert est.base_units is None and est.best_units is None
    assert path(est, "base_zoning").status == "unknown"


def test_laws_unverified_flag_propagates(parcel_factory, adapters, laws_cfg):
    est = estimate_units(parcel_factory(land_use="vacant", lot_sqft=30000),
                         adapters["Testville"].lookup("R3"), laws_cfg)
    assert est.laws_verified is False  # ships unverified until a human reviews it
    assert "not legal" in est.disclaimer.lower()
