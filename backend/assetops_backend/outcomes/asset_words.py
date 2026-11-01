"""POLISH §3 asset labels (PA-2b, Addendum 6 Q4): the one plain asset word map behind every work `asset_label`.

A label is the plain type word; the stored `asset_code` is appended only when the Site has more than one non-retired
asset of that type. A generator is "Backup generator" on a cold-chain Site and "Generator" on mini-grid and EV Sites.
An unmapped type reads as its capitalised type word ("POWER_CONVERSION_SYSTEM" -> "Power conversion system").
"""
from __future__ import annotations

COLDCHAIN = "COLDCHAIN"
#: §3 map. The EV foundation stores connectors as EV_CONNECTOR and chargers as EV_CHARGER, so both read as the plain
#: word ("Connector", "Charger") rather than the capitalised fallback ("Ev connector").
ASSET_WORDS = {"COMPRESSOR": "Compressor", "BATTERY": "Battery", "GENERATOR": "Generator", "CONNECTOR": "Connector",
               "EV_CONNECTOR": "Connector", "EV_CHARGER": "Charger"}
COLD_GENERATOR = "Backup generator"


def asset_word(asset_type: str | None, site_type: str | None) -> str | None:
    """The plain type word of one stored asset type on a Site of `site_type`; None without a type."""
    if not asset_type:
        return None
    if asset_type == "GENERATOR" and site_type == COLDCHAIN:
        return COLD_GENERATOR
    return ASSET_WORDS.get(asset_type) or asset_type.replace("_", " ").strip().capitalize()


def asset_label(asset_code: str | None, asset_type: str | None, site_type: str | None,
                same_type_count: int | None) -> str | None:
    """The visible label of a work row's asset: None when the row names no asset."""
    if asset_code is None:
        return None
    word = asset_word(asset_type, site_type) or asset_code
    return f"{word} {asset_code}" if (same_type_count or 0) > 1 and word != asset_code else word
