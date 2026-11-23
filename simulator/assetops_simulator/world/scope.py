"""Scope inputs, scope digests and seeds (spec §4.3; R11).

A scope is one tenant, Site and month. Its digest covers exactly what its rules can
read, so a change re-seeds only the scopes it reaches. Prices and tariffs are not
inputs: no rule reads them.
"""

from __future__ import annotations

from fractions import Fraction

from . import GENERATOR
from .canonical import canonical_bytes, sha256_hex

GLOBAL_KEYS = ("months", "anchor_period", "seasons", "day_classes", "families", "money_leaves")
SIDES = ("plan", "actual")

#: D-DD.102: per rule word, the `physical` keys it reads. A rule word absent from the table reads none, so a kit
#: correction (a data sheet, an import limit) re-seeds no scope whose rules do not read it.
PHYSICAL_READS: dict[str, tuple[str, ...]] = {"fleet_kwh": ("buses", "kwh_per_bus_night"), "fleet_nights": ("buses",)}

#: D-DD.164: per vertical and side, the `period` keys whose value `M` writes from a run. They leave the scope digest
#: (a seed never covers a value written back from the run it seeds) and stay readable as values. Side `"period"`
#: names a key of `period` itself. A key not listed stays in the digest.
RUN_WRITTEN: dict[str, dict[str, tuple[str, ...]]] = {
    "MINI_GRID": {
        # D-DD.131's restated October fuel leaves and the identities computed from them
        "actual": ("diesel_l", "necessary_l", "candidate_l", "diesel_cost", "contribution", "variance"),
        # D-DD.170's run-rate fuel budget and its dependent plan figures
        "plan": ("diesel_l", "necessary_l", "candidate_l", "unexplained_l", "diesel_cost", "contribution", "variance"),
        # the blocks D-DD.131 restates
        "period": ("fuel_balance", "bridge", "findings_expected"),
    },
    # the meter's October kWh (D-DD.144)
    "COLD_CHAIN": {"actual": ("kwh",)},
    # D-DD.20's metered EV leaves, with D-DD.158's two hour windows
    "EV_DEPOT": {"actual": ("peak_kwh", "offpeak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw")},
}


def history_global(history: dict) -> dict:
    """The history's global inputs a scope reads. `seasons` is restricted to the history's months plus the anchor
    (D-DD.90): a season declared for a later month of the readings span is read by no history rule."""
    out = {key: history[key] for key in GLOBAL_KEYS}
    read = set(history["months"]) | {history["anchor_period"]}
    out["seasons"] = {month: season for month, season in history["seasons"].items() if month in read}
    return out


def scope_key(tenant: str, site: str, month: str) -> str:
    return f"{tenant}/{site}/{month}"


def merged_rules(history: dict, vertical: str, tenant: str, site: str) -> dict | None:
    """The vertical's table merged by side with the Site's override (the override wins
    and may add keys). None when the vertical has no table."""
    table = history.get("rules", {}).get(vertical)
    if table is None:
        return None
    override = history.get("sites", {}).get(f"{tenant}/{site}", {})
    merged = {}
    for side in SIDES:
        rules = dict(table.get(side, {}))
        rules.update(override.get(side, {}))
        merged[side] = rules
    return merged


def physical_read(site_doc: dict, rules: dict) -> dict:
    """The part of the Site's `physical` block that the scope's rules read (D-DD.102): the words are the first
    whitespace token of every string rule on both sides; `{}` when the Site has no block."""
    physical = site_doc.get("physical")
    if not isinstance(physical, dict):
        return {}
    keys: set[str] = set()
    for side in SIDES:
        for rule in rules.get(side, {}).values():
            if isinstance(rule, str) and rule.split():
                keys.update(PHYSICAL_READS.get(rule.split()[0], ()))
    return {k: physical[k] for k in sorted(keys) if k in physical}


def period_input(site_doc: dict, vertical: str) -> dict:
    """`period` with exactly the vertical's `RUN_WRITTEN` keys removed (D-DD.164); a missing key is skipped."""
    table = RUN_WRITTEN.get(vertical, {})
    out = {}
    for name, value in site_doc["period"].items():
        if name in table.get("period", ()):
            continue
        if isinstance(value, dict) and name in table:
            value = {k: v for k, v in value.items() if k not in table[name]}
        out[name] = value
    return out


def scope_input(view: dict, tenant_doc: dict, site_doc: dict, month: str, rules: dict) -> dict:
    history = view["history"]
    tenant = {"tenant": tenant_doc["tenant"], "vertical": tenant_doc["vertical"]}
    for optional in ("energy_model", "capacity_crates_per_room"):
        if optional in tenant_doc:
            tenant[optional] = tenant_doc[optional]
    site = {"site": site_doc["site"], "code": site_doc["code"], "period": period_input(site_doc, tenant_doc["vertical"])}
    physical = physical_read(site_doc, rules)
    if physical:
        site["physical"] = physical
    return {
        "generator": GENERATOR,
        "month": month,
        "history_global": history_global(history),
        "rules": rules,
        "tenant": tenant,
        "site": site,
    }


def scope_digest(inputs: dict) -> str:
    return sha256_hex(canonical_bytes(inputs))


def seed(digest: str, key: str, stream: str) -> str:
    return sha256_hex(f"{digest}|{key}|{stream}".encode("utf-8"))


def unit_interval(h: str) -> Fraction:
    """A seed's first 32 bits as a value in [-1, 1], in thousandths."""
    return Fraction(int(h[:8], 16) % 2001 - 1000, 1000)
