"""Validate scores against APR Table A2 (building permits by APN).

Question asked: do parcels that actually got housing permits score higher than
the rest of their ZIP? Reports base rate, hit rate in the top decile, lift, and
a rank-based AUC. A2 includes ADUs and single-unit permits, so this is a weak
check of "where housing gets built", not of affordable feasibility.
"""
from __future__ import annotations

import pandas as pd

from . import registry
from .sources import RAW, norm_apn, pick

A2_APN = ["APN", "apn", "PRIOR_APN"]
A2_UNITS = ["NO_BUILDING_PERMITS", "BP_TOTAL_UNITS", "TOT_BP_UNITS", "UNITS"]


def load_a2(path=None) -> pd.DataFrame | None:
    path = path or RAW / registry.BY_ID["apr_table_a2"]["local_file"]
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype=str, low_memory=False)
    apn = pick(df, A2_APN)
    units = pick(df, A2_UNITS, required=False)
    out = pd.DataFrame({"apn_norm": df[apn].map(norm_apn)})
    out["units"] = pd.to_numeric(df[units], errors="coerce").fillna(1) if units else 1
    out = out.dropna(subset=["apn_norm"]).groupby("apn_norm", as_index=False)["units"].sum()
    return out[out["units"] > 0]


def validate(scored: pd.DataFrame, a2: pd.DataFrame | None) -> dict:
    if a2 is None:
        return {"status": "not_run", "reason": "APR Table A2 not ingested (data/raw/apr_table_a2.csv)"}
    s = scored[scored["opp"].notna()].copy()
    if s.empty:
        return {"status": "not_run", "reason": "no scored parcels"}
    s["permitted"] = s["apn_norm"].isin(set(a2["apn_norm"]))
    n_pos = int(s["permitted"].sum())
    base = n_pos / len(s)
    top = s.nlargest(max(1, len(s) // 10), "opp")
    top_rate = float(top["permitted"].mean())
    auc = None
    if 0 < n_pos < len(s):
        ranks = s["opp"].rank(method="average")
        auc = float((ranks[s["permitted"]].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * (len(s) - n_pos)))
    return {
        "status": "ok", "scored_parcels": int(len(s)), "permitted_parcels": n_pos,
        "base_rate": round(base, 4), "top_decile_rate": round(top_rate, 4),
        "lift_top_decile": round(top_rate / base, 2) if base else None,
        "auc": None if auc is None else round(auc, 3),
        "interpretation": ("AUC 0.5 = scores no better than random at finding permitted parcels; "
                           "lift > 1 = permits concentrate in the top decile."),
        "permitted_examples": s[s["permitted"]].nlargest(10, "opp")[["apn", "address", "opp", "level"]]
        .to_dict(orient="records"),
    }
