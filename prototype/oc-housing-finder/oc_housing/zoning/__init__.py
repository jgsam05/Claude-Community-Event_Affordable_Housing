"""Per-city zoning adapters.

Orange County has no county-wide zoning layer: each of the 34 cities (and the
unincorporated areas) controls its own. An adapter turns one jurisdiction's
rules into the common ZoneRule schema. Cities without an adapter are scored on
non-zoning signals and flagged "zoning not ingested" - zoning is never guessed.
"""

from .base import ZoningAdapter, CsvZoningAdapter, load_adapters

__all__ = ["ZoningAdapter", "CsvZoningAdapter", "load_adapters"]
