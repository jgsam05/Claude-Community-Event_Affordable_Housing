"""Extract APNs from OC Treasurer-Tax Collector tax-defaulted / auction PDFs.

Kept separate from the joins because PDF layout changes between lists. Output
is data/cache/tax_defaulted_apns.csv with one row per APN and where it was found,
which the `oc_tax_defaulted` registry join reads as a low-confidence flag.

Usage: python -m parcel_engine.cli parse-tax-pdfs [folder]
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pdfplumber

from . import registry
from .sources import CACHE, RAW, norm_apn

# OC APNs print as 123-456-78 (book-page-parcel). Allow spaces and stray OCR gaps,
# and the 9-digit form some lists use (123-456-789) when it leads with a 0.
APN_RE = re.compile(r"(?<!\d)(\d{3})\s?-\s?(\d{3})\s?-\s?(\d{2,3})(?!\d)")


def extract_apns_from_text(text: str) -> list[str]:
    out = []
    for a, b, c in APN_RE.findall(text):
        if len(c) == 3:
            if not c.startswith("0"):
                continue  # 3-digit tail that isn't zero-padded is usually a phone/case number
            c = c[1:]
        out.append(f"{a}-{b}-{c}")
    return out


def parse_folder(folder: Path | None = None, out_path: Path | None = None) -> dict:
    folder = folder or RAW / registry.BY_ID["oc_tax_defaulted"]["local_file"]
    out_path = out_path or CACHE / "tax_defaulted_apns.csv"
    rows, seen, problems = [], set(), []
    pdfs = sorted(Path(folder).glob("*.pdf"))
    for pdf in pdfs:
        try:
            with pdfplumber.open(pdf) as doc:
                for i, page in enumerate(doc.pages, start=1):
                    text = page.extract_text() or ""
                    if not text.strip():
                        problems.append(f"{pdf.name} p{i}: no text layer (scanned? needs OCR)")
                        continue
                    for apn in extract_apns_from_text(text):
                        key = norm_apn(apn)
                        if key in seen:
                            continue
                        seen.add(key)
                        rows.append({"apn": apn, "apn_norm": key, "source_pdf": pdf.name, "page": i})
        except Exception as e:
            problems.append(f"{pdf.name}: {e}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["apn", "apn_norm", "source_pdf", "page"])
        w.writeheader()
        w.writerows(rows)
    if pdfs:
        registry.stamp_ingest("oc_tax_defaulted", extra={"method": "pdfplumber", "pdfs": [p.name for p in pdfs],
                                                         "apns": len(rows)})
    return {"pdfs": len(pdfs), "apns": len(rows), "problems": problems, "output": str(out_path)}
