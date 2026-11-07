"""Probe ArcGIS REST endpoints and report what is actually there.

Usage:  python tools/probe_arcgis.py URL [URL ...] [--out results.json]
Each URL may be a folder, a service, or a layer. For layers it reports name,
geometry type, key metadata (copyright/description/last edit), a field list, and
a live record count. Anything that needs a token or errors is reported as such,
never silently skipped. Re-run it any time to refresh the 'refresh date' column
of the dataset registry.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx

TIMEOUT = httpx.Timeout(40.0, connect=15.0)


def get_json(client: httpx.Client, url: str, params: dict | None = None):
    r = client.get(url, params=params, timeout=TIMEOUT, follow_redirects=True)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, None


def ms_to_date(ms):
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return None


def probe(url: str) -> dict:
    base = url.split("?")[0].rstrip("/")
    out: dict = {"url": base}
    try:
        with httpx.Client(headers={"User-Agent": "oc-housing-finder-probe/0.1"}) as c:
            status, j = get_json(c, base, {"f": "pjson"})
            out["http"] = status
            if j is None:
                out["status"] = f"not_json (HTTP {status})"
                return out
            if "error" in j:
                err = j["error"]
                out["status"] = f"error {err.get('code')}: {err.get('message') or err.get('details')}"
                out["needs_token"] = err.get("code") in (498, 499)
                return out
            if "services" in j or "folders" in j:  # folder listing
                out["status"] = "folder"
                out["folders"] = j.get("folders", [])
                out["services"] = [f"{s['name']} ({s['type']})" for s in j.get("services", [])]
                return out
            if "fields" not in j:  # service root
                out["status"] = "service"
                out["name"] = j.get("serviceDescription") or j.get("mapName") or j.get("name")
                out["layers"] = [(l["id"], l["name"]) for l in j.get("layers", [])]
                out["tables"] = [(t["id"], t["name"]) for t in j.get("tables", [])]
                out["copyright"] = (j.get("copyrightText") or "")[:300]
                return out
            out["status"] = "layer"
            out["name"] = j.get("name")
            out["geometry"] = j.get("geometryType")
            out["max_record_count"] = j.get("maxRecordCount")
            out["copyright"] = (j.get("copyrightText") or "")[:300]
            out["description"] = " ".join((j.get("description") or "").split())[:400]
            out["last_edit"] = ms_to_date((j.get("editingInfo") or {}).get("lastEditDate")) \
                or ms_to_date((j.get("editingInfo") or {}).get("dataLastEditDate"))
            out["fields"] = [f["name"] for f in j.get("fields", [])]
            out["supports_query"] = "Query" in (j.get("capabilities") or "")
            s2, cnt = get_json(c, base + "/query",
                               {"where": "1=1", "returnCountOnly": "true", "f": "json"})
            out["count"] = cnt.get("count") if cnt and "count" in cnt else \
                (f"count_error: {cnt.get('error', {}).get('message')}" if cnt else f"HTTP {s2}")
    except Exception as e:  # network errors are results too
        out["status"] = f"exception: {type(e).__name__}: {e}"[:200]
    return out


def main(argv):
    out_path = None
    if "--out" in argv:
        i = argv.index("--out")
        out_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(probe, argv))
    for r in results:
        print("=" * 100)
        print(r["url"])
        for k, v in r.items():
            if k == "url":
                continue
            if k == "fields":
                print(f"  fields ({len(v)}): {v[:45]}{' ...' if len(v) > 45 else ''}")
            else:
                print(f"  {k}: {v}")
    if out_path:
        with open(out_path, "w") as fh:
            json.dump(results, fh, indent=2, default=str)


if __name__ == "__main__":
    main(sys.argv[1:])
