"""Command line: python -m parcel_engine.cli <command>

  describe-layer [url]     conditional-field report (run first)
  build ZIP [ZIP...]       score ZIPs and write data/scored/<zip>.geojson
  samples                  build the three Phase 1 sample ZIPs
  parse-tax-pdfs [folder]  extract APNs from OC Treasurer PDFs
  registry                 print registry and Phase 1 gaps
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import arcgis, pipeline, registry, tax_default
from .config import SAMPLE_ZIPS


def _summary(fc: dict) -> str:
    m = fc["metadata"]
    return (f"{m['zip']}: {m['parcel_count']} parcels, jurisdictions={m['jurisdictions']}, "
            f"levels={m['level_counts']}, scored={m['scored_count']}, validation={m['validation'].get('status')}")


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    cmd, args = argv[0], argv[1:]
    if cmd == "describe-layer":
        print(json.dumps(arcgis.describe_layer(args[0] if args else registry.BY_ID["ocgis_parcels"]["url"]), indent=2))
    elif cmd in ("build", "samples"):
        for z in (args if cmd == "build" else SAMPLE_ZIPS):
            print(_summary(pipeline.build_zip(z)))
    elif cmd == "parse-tax-pdfs":
        print(json.dumps(tax_default.parse_folder(Path(args[0]) if args else None), indent=2))
    elif cmd == "registry":
        print(json.dumps({"datasets": registry.records(), "phase1_gaps": registry.phase1_gaps()}, indent=2))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
