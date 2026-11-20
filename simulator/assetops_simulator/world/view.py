"""The view of a manifest the generator may read (spec §4.2; strategy Appendix F row 1).

Built by allowlist: a key is copied only if it is named below, so nothing else in a
manifest (expectations, checks, findings, bridges, observations, incidents) can
reach the generator. Absent keys are omitted, never written as null. A binary float
becomes its `repr` text, an int stays an int, a str stays a str; any other type is
refused. Applying the view to a view returns it unchanged.
"""

from __future__ import annotations

import math
from typing import Any

from .canonical import canonical_bytes, sha256_hex

TOP_KEYS = ("manifest_version", "as_of", "accounting_period", "currency", "timezone_default", "history", "tenants")
TENANT_KEYS = ("tenant", "vertical", "prices", "energy_model", "capacity_crates_per_room", "sites")
SITE_KEYS = ("site", "code", "physical", "tariff", "period")
PERIOD_KEYS = ("plan", "actual", "coverage")


def _value(item: Any, path: str) -> Any:
    if isinstance(item, bool):
        raise ValueError(f"VIEW_TYPE {path}")
    if isinstance(item, int):
        return item
    if isinstance(item, float):
        if not math.isfinite(item):
            raise ValueError(f"VIEW_TYPE {path}")
        return repr(item)
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        out = {}
        for key, sub in item.items():
            if not isinstance(key, str):
                raise ValueError(f"VIEW_TYPE {path}.{key!r}")
            out[key] = _value(sub, f"{path}.{key}")
        return out
    if isinstance(item, list):
        return [_value(sub, f"{path}[{i}]") for i, sub in enumerate(item)]
    raise ValueError(f"VIEW_TYPE {path}")


def _pick(source: dict, keys: tuple[str, ...], path: str, nested: dict) -> dict:
    out = {}
    for key in keys:
        if key not in source:
            continue
        sub_path = f"{path}.{key}" if path else key
        if key in nested:
            out[key] = nested[key](source[key], sub_path)
        else:
            out[key] = _value(source[key], sub_path)
    return out


def _period(period: Any, path: str) -> dict:
    if not isinstance(period, dict):
        raise ValueError(f"VIEW_TYPE {path}")
    return _pick(period, PERIOD_KEYS, path, {})


def _site(site: Any, path: str) -> dict:
    if not isinstance(site, dict):
        raise ValueError(f"VIEW_TYPE {path}")
    return _pick(site, SITE_KEYS, path, {"period": _period})


def _sites(sites: Any, path: str) -> list:
    if not isinstance(sites, list):
        raise ValueError(f"VIEW_TYPE {path}")
    return [_site(s, f"{path}[{i}]") for i, s in enumerate(sites)]


def _tenant(tenant: Any, path: str) -> dict:
    if not isinstance(tenant, dict):
        raise ValueError(f"VIEW_TYPE {path}")
    return _pick(tenant, TENANT_KEYS, path, {"sites": _sites})


def _tenants(tenants: Any, path: str) -> list:
    if not isinstance(tenants, list):
        raise ValueError(f"VIEW_TYPE {path}")
    return [_tenant(t, f"{path}[{i}]") for i, t in enumerate(tenants)]


class ManifestView(dict):
    """A manifest reduced to the allowlisted keys. A plain dict, so it digests as one."""

    @classmethod
    def from_document(cls, doc: dict) -> "ManifestView":
        if not isinstance(doc, dict):
            raise ValueError("VIEW_TYPE $")
        return cls(_pick(doc, TOP_KEYS, "", {"tenants": _tenants}))


def view_digest(view: dict) -> str:
    return sha256_hex(canonical_bytes(view))
