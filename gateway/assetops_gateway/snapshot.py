"""Verify a frozen registered acquisition snapshot before the gateway uses it.

The gateway receives S1's `assetops.acquisition-snapshot/1` canonical bytes (as
frozen by S2-01a on a registered Lab Draft) and the revision references the
host claims for them. It checks, without trusting either input:

- SHA-256 of the exact UTF-8 bytes equals the claimed hash (byte integrity);
- the schema is one this gateway reads, and the text is already canonical;
- internal consistency: exact keys, `bindings_sha256` recomputed over the rows,
  every row's gateway and source inside the snapshot's own lists, unique
  `(device_id, signal_id)`, a supported conversion;
- the snapshot sits inside this gateway's independently provisioned scope:
  tenant, Site, gateway, `SIMULATED` mode and permitted sources;
- the claimed revision references equal the snapshot's own.

The hash proves byte integrity, not publisher authority: the authenticated local
host is the issuer (`D-2026-10-08-s2-local-gateway-snapshot-transfer`), and that
authentication belongs to the transport, not this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field as _field
from datetime import datetime, timezone
from typing import Any

ACQUISITION_SNAPSHOT_SCHEMA_V1 = "assetops.acquisition-snapshot/1"
SUPPORTED_SNAPSHOT_SCHEMAS = frozenset({ACQUISITION_SNAPSHOT_SCHEMA_V1})
SUPPORTED_CONVERSIONS = frozenset({"IDENTITY", "ENUM", "IDENTITY_KWH"})
STATE_UNIT = "state"
#: W2-05b q3 Q17: `IDENTITY_KWH` is read only on EV connector energy, kWh to kWh, with no parameters.
IDENTITY_KWH = "IDENTITY_KWH"
IDENTITY_KWH_ROLE = "ev_connector_energy"
KWH_UNIT = "kWh"

_DIGEST = re.compile(r"[0-9a-f]{64}")
_REGISTERED_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z")


class SnapshotRefused(ValueError):
    def __init__(self, kind: str, field: str, detail: str) -> None:
        self.kind = kind
        self.field = field
        self.detail = detail
        super().__init__(f"{kind} at {field}: {detail}")


@dataclass(frozen=True)
class Provisioning:
    """This gateway's own identity, provisioned independently of any request."""

    tenant_id: str
    site_id: str
    gateway_id: str
    source_mode: str
    permitted_source_ids: frozenset[str]


@dataclass(frozen=True)
class ClaimedReferences:
    """What the host says the bytes are; checked against the bytes."""

    snapshot_sha256: str
    foundation_revision_id: str
    foundation_version: int
    binding_set_id: str
    binding_set_revision_id: str
    binding_set_version: int


@dataclass(frozen=True)
class Binding:
    binding_revision_id: str
    device_id: str
    signal_id: str
    source_id: str
    role: str
    source_unit: str
    canonical_unit: str
    conversion_kind: str
    enum_map: tuple[tuple[str, str], ...]
    #: W2-02: the row's five v4 mapping keys exactly as the snapshot states them, or None for a v3 row.
    v4_metadata: dict[str, Any] | None = _field(default=None, compare=False, hash=False)


@dataclass(frozen=True)
class VerifiedSnapshot:
    snapshot_sha256: str
    snapshot_text: str
    schema: str
    tenant_id: str
    site_id: str
    gateway_id: str
    foundation_revision_id: str
    foundation_version: int
    foundation_valid_from: str
    foundation_valid_to: str | None
    binding_set_id: str
    binding_set_revision_id: str
    binding_set_version: int
    binding_valid_from: str
    binding_valid_to: str | None
    source_ids: tuple[str, ...]
    bindings: tuple[Binding, ...]

    def binding_for(self, device_id: str, signal_id: str) -> Binding | None:
        for binding in self.bindings:
            if binding.device_id == device_id and binding.signal_id == signal_id:
                return binding
        return None

    def valid_at(self, instant: datetime) -> bool:
        """Inside both the Foundation and binding half-open valid periods."""
        for start, end in (
            (self.foundation_valid_from, self.foundation_valid_to),
            (self.binding_valid_from, self.binding_valid_to),
        ):
            if instant < registered_instant(start):
                return False
            if end is not None and instant >= registered_instant(end):
                return False
        return True


def registered_instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _canonical(document: Any) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _exact(value: object, keys: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SnapshotRefused("MALFORMED_SNAPSHOT", where, "an object is wanted")
    extra = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    if extra:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", f"{where}.{extra[0]}", "unknown field")
    if missing:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", f"{where}.{missing[0]}", "missing field")
    return value


def _text(value: object, where: str) -> str:
    if type(value) is not str or not value:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", where, "non-empty text is wanted")
    return value


def _instant(value: object, where: str, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if type(value) is not str or not _REGISTERED_INSTANT.fullmatch(value):
        raise SnapshotRefused("MALFORMED_SNAPSHOT", where, f"{value!r} is not a UTC instant")
    return value


def _int(value: object, where: str) -> int:
    if type(value) is not int or value < 1:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", where, "a positive whole number is wanted")
    return value


_BINDING_KEYS = {
    "binding_revision_id",
    "device_id",
    "signal_id",
    "source_id",
    "gateway_id",
    "asset_id",
    "role",
    "source_unit",
    "canonical_unit",
    "conversion",
}
#: W2-00 ruling 4: optional v4 mapping metadata on a binding row. A v3 row carries none of them; a v4 row
#: carries all five. S2 checks their values against the closed channel table.
_V4_BINDING_KEYS = {
    "allowed_record_kinds",
    "allowed_outcomes",
    "requires_correlation",
    "requires_session",
    "allowed_units",
}


def _v4_metadata(raw: dict[str, Any], where: str) -> None:
    present = _V4_BINDING_KEYS & set(raw)
    if not present:
        return
    if present != _V4_BINDING_KEYS:
        missing = sorted(_V4_BINDING_KEYS - present)[0]
        raise SnapshotRefused("MALFORMED_SNAPSHOT", f"{where}.{missing}", "v4 mapping metadata states all five keys")
    for key in ("allowed_record_kinds", "allowed_units"):
        value = raw[key]
        if type(value) is not list or not all(type(v) is str and v for v in value):
            raise SnapshotRefused("MALFORMED_SNAPSHOT", f"{where}.{key}", "a list of non-empty text is wanted")
    outcomes = raw["allowed_outcomes"]
    if not isinstance(outcomes, dict) or not all(
            type(v) is list and all(type(o) is str and o for o in v) for v in outcomes.values()):
        raise SnapshotRefused("MALFORMED_SNAPSHOT", f"{where}.allowed_outcomes",
                              "a record kind to outcome-list object is wanted")
    for key in ("requires_correlation", "requires_session"):
        if type(raw[key]) is not bool:
            raise SnapshotRefused("MALFORMED_SNAPSHOT", f"{where}.{key}", "a boolean is wanted")


def verify_snapshot(
    snapshot_text: object,
    claimed: ClaimedReferences,
    provisioning: Provisioning,
) -> VerifiedSnapshot:
    if type(snapshot_text) is not str:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", "snapshot", "snapshot bytes are UTF-8 text")
    if not _DIGEST.fullmatch(claimed.snapshot_sha256):
        raise SnapshotRefused("HASH_MISMATCH", "snapshot_sha256", "not a SHA-256 hex digest")
    actual = hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()
    if actual != claimed.snapshot_sha256:
        raise SnapshotRefused("HASH_MISMATCH", "snapshot_sha256", "the bytes do not hash to the claimed digest")
    try:
        document = json.loads(snapshot_text, parse_float=lambda t: (_ for _ in ()).throw(ValueError(t)))
    except ValueError as error:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", "snapshot", f"not JSON without floats: {error}") from error
    if not isinstance(document, dict):
        raise SnapshotRefused("MALFORMED_SNAPSHOT", "snapshot", "an object is wanted")
    schema = document.get("schema")
    if schema not in SUPPORTED_SNAPSHOT_SCHEMAS:
        raise SnapshotRefused("SCHEMA_UNSUPPORTED", "schema", f"{schema!r} is not a schema this gateway reads")
    if _canonical(document) != snapshot_text:
        raise SnapshotRefused("NOT_CANONICAL", "snapshot", "the bytes are not their own canonical text")
    top = _exact(
        document,
        {"schema", "tenant_id", "site", "gateway", "foundation", "mapping", "sources", "bindings"},
        "snapshot",
    )
    site = _exact(top["site"], {"site_id", "site_code"}, "site")
    gateway = _exact(top["gateway"], {"gateway_id", "gateway_external_id", "mode"}, "gateway")
    foundation = _exact(
        top["foundation"], {"revision_id", "version", "valid_from", "valid_to", "content_sha256"}, "foundation"
    )
    mapping = _exact(
        top["mapping"],
        {"binding_set_id", "binding_set_revision_id", "version", "role_set", "valid_from", "valid_to", "bindings_sha256"},
        "mapping",
    )
    tenant_id = _text(top["tenant_id"], "tenant_id")
    site_id = _text(site["site_id"], "site.site_id")
    gateway_id = _text(gateway["gateway_id"], "gateway.gateway_id")

    # Provisioned scope: independent of the request.
    for field, got, want in (
        ("tenant_id", tenant_id, provisioning.tenant_id),
        ("site.site_id", site_id, provisioning.site_id),
        ("gateway.gateway_id", gateway_id, provisioning.gateway_id),
        ("gateway.mode", gateway["mode"], provisioning.source_mode),
    ):
        if got != want:
            raise SnapshotRefused("OUT_OF_SCOPE", field, f"{got!r} is not this gateway's provisioned {want!r}")
    if provisioning.source_mode != "SIMULATED":
        raise SnapshotRefused("OUT_OF_SCOPE", "gateway.mode", "this gateway activates SIMULATED snapshots only")

    if not isinstance(top["sources"], list) or not top["sources"]:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", "sources", "a non-empty list is wanted")
    source_ids: list[str] = []
    for index, source in enumerate(top["sources"]):
        row = _exact(source, {"source_id", "source_external_id"}, f"sources[{index}]")
        source_ids.append(_text(row["source_id"], f"sources[{index}].source_id"))
    for source_id in source_ids:
        if source_id not in provisioning.permitted_source_ids:
            raise SnapshotRefused("OUT_OF_SCOPE", "sources", f"source {source_id} is not permitted on this gateway")

    if not isinstance(top["bindings"], list) or not top["bindings"]:
        raise SnapshotRefused("MALFORMED_SNAPSHOT", "bindings", "a non-empty list is wanted")
    bindings: list[Binding] = []
    content_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(top["bindings"]):
        where = f"bindings[{index}]"
        row = _exact(raw, _BINDING_KEYS | (_V4_BINDING_KEYS & set(raw) if isinstance(raw, dict) else set()), where)
        _v4_metadata(row, where)
        if row["gateway_id"] != gateway_id:
            raise SnapshotRefused("INCONSISTENT_SNAPSHOT", f"{where}.gateway_id", "not the snapshot's gateway")
        if row["source_id"] not in source_ids:
            raise SnapshotRefused("INCONSISTENT_SNAPSHOT", f"{where}.source_id", "not in the snapshot's sources")
        pair = (_text(row["device_id"], f"{where}.device_id"), _text(row["signal_id"], f"{where}.signal_id"))
        if pair in seen:
            raise SnapshotRefused("INCONSISTENT_SNAPSHOT", where, f"{pair} is bound twice")
        seen.add(pair)
        conversion = _exact(row["conversion"], {"kind", "parameters"}, f"{where}.conversion")
        kind = conversion["kind"]
        if kind not in SUPPORTED_CONVERSIONS:
            raise SnapshotRefused("UNSUPPORTED_CONVERSION", f"{where}.conversion.kind", f"{kind!r}")
        params = conversion["parameters"]
        enum_map: tuple[tuple[str, str], ...] = ()
        if kind == "IDENTITY":
            if params != {} or row["source_unit"] != row["canonical_unit"]:
                raise SnapshotRefused("UNSUPPORTED_CONVERSION", f"{where}.conversion", "IDENTITY keeps the unit")
        elif kind == IDENTITY_KWH:
            if (params != {} or row["role"] != IDENTITY_KWH_ROLE
                    or row["source_unit"] != KWH_UNIT or row["canonical_unit"] != KWH_UNIT):
                raise SnapshotRefused(
                    "UNSUPPORTED_CONVERSION", f"{where}.conversion",
                    "IDENTITY_KWH applies only to ev_connector_energy, kWh to kWh, with no parameters",
                )
        else:
            mapped = _exact(params, {"map"}, f"{where}.conversion.parameters")["map"]
            if not isinstance(mapped, dict) or not mapped or row["canonical_unit"] != STATE_UNIT:
                raise SnapshotRefused("UNSUPPORTED_CONVERSION", f"{where}.conversion", "ENUM maps labels to states")
            enum_map = tuple(sorted((str(k), str(v)) for k, v in mapped.items()))
        bindings.append(
            Binding(
                binding_revision_id=_text(row["binding_revision_id"], f"{where}.binding_revision_id"),
                device_id=pair[0],
                signal_id=pair[1],
                source_id=row["source_id"],
                role=_text(row["role"], f"{where}.role"),
                source_unit=_text(row["source_unit"], f"{where}.source_unit"),
                canonical_unit=_text(row["canonical_unit"], f"{where}.canonical_unit"),
                conversion_kind=kind,
                enum_map=enum_map,
                v4_metadata={k: row[k] for k in sorted(_V4_BINDING_KEYS)} if _V4_BINDING_KEYS & set(row) else None,
            )
        )
        content_rows.append({k: v for k, v in row.items() if k != "binding_revision_id"})
    if sorted(set(b.source_id for b in bindings)) != sorted(source_ids):
        raise SnapshotRefused("INCONSISTENT_SNAPSHOT", "sources", "sources are exactly the ones bindings use")
    content_rows.sort(key=lambda r: (r["device_id"], r["signal_id"]))
    recomputed = hashlib.sha256(
        _canonical({"role_set": mapping["role_set"], "bindings": content_rows}).encode("utf-8")
    ).hexdigest()
    if recomputed != mapping["bindings_sha256"]:
        raise SnapshotRefused("INCONSISTENT_SNAPSHOT", "mapping.bindings_sha256", "does not match the rows")

    verified = VerifiedSnapshot(
        snapshot_sha256=actual,
        snapshot_text=snapshot_text,
        schema=schema,
        tenant_id=tenant_id,
        site_id=site_id,
        gateway_id=gateway_id,
        foundation_revision_id=_text(foundation["revision_id"], "foundation.revision_id"),
        foundation_version=_int(foundation["version"], "foundation.version"),
        foundation_valid_from=_instant(foundation["valid_from"], "foundation.valid_from"),  # type: ignore[arg-type]
        foundation_valid_to=_instant(foundation["valid_to"], "foundation.valid_to", optional=True),
        binding_set_id=_text(mapping["binding_set_id"], "mapping.binding_set_id"),
        binding_set_revision_id=_text(mapping["binding_set_revision_id"], "mapping.binding_set_revision_id"),
        binding_set_version=_int(mapping["version"], "mapping.version"),
        binding_valid_from=_instant(mapping["valid_from"], "mapping.valid_from"),  # type: ignore[arg-type]
        binding_valid_to=_instant(mapping["valid_to"], "mapping.valid_to", optional=True),
        source_ids=tuple(sorted(source_ids)),
        bindings=tuple(bindings),
    )
    for field, got, want in (
        ("foundation.revision_id", verified.foundation_revision_id, claimed.foundation_revision_id),
        ("foundation.version", verified.foundation_version, claimed.foundation_version),
        ("mapping.binding_set_id", verified.binding_set_id, claimed.binding_set_id),
        ("mapping.binding_set_revision_id", verified.binding_set_revision_id, claimed.binding_set_revision_id),
        ("mapping.version", verified.binding_set_version, claimed.binding_set_version),
    ):
        if got != want:
            raise SnapshotRefused("REFERENCE_MISMATCH", field, f"snapshot says {got!r}, claim says {want!r}")
    return verified
