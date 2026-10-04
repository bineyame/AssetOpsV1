"""The Site > Evidence read model: accepted content only (T027 D3, AC8, AC10, AC20).

Every payload here is computed from what ingestion persisted - accepted
records, rejections, conflicts, batch progress and the immutable registries -
and from the Site's configuration. It never reads a stage, a world, a
LabProjection, an observation, a private trace or a scenario expectation; the
dependency guard holds that by import.

Coverage (AC10) names the signals the mini-grid Overview metrics need
(`NEEDED_SIGNALS`, substrate data keyed by `site_type` that names signals and
nothing else) and the selected window. A needed signal with no accepted record
in the window is a `NOT_REPORTED` coverage gap with no value. UNAVAILABLE
records are counted as unavailable, never filled, and no sample is carried
forward into a time it was not reported at.

Overlap (AC9): distinct message ids at the same (device, signal, source_time)
are all kept; coverage counts them as `overlapping` and the inspector lists
each, with no summing and no last-write-wins.

Nothing here describes capability readiness or claim ceilings (AC20).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from assetops_backend.evidence.models import (
    NORMALIZATION,
    NORMALIZATION_STATEMENT,
    AcceptedRecord,
    BatchProgress,
    ConfigurationBasis,
    SiteEvidence,
)
from assetops_backend.evidence.ports import EvidenceStore, find_batch
from assetops_backend.sites.models import SiteRecord

#: Read-time plain reasons for a rejected record, by its stored kind
#: (D-2026-10-04-plain-language-analysis-views). The stored rejection, its kind
#: and its ingestion-time `detail` are unchanged and still served; this is the
#: sentence the product shows. An unfamiliar kind gets `REJECTION_UNAVAILABLE`,
#: never its code.
REJECTION_READINGS: dict[str, str] = {
    "NOT_AN_ENVELOPE": "The delivery was not in the agreed record format.",
    "NOT_A_BATCH": "The delivery was not in the agreed record format.",
    "MALFORMED_TEXT": "The record's text could not be read.",
    "NOT_CANONICAL": "The record was not written in the agreed exact form.",
    "UNKNOWN_FIELD": "The record contained an item the agreed format does not include.",
    "MISSING_FIELD": "The record left out a required item.",
    "WRONG_TYPE": "An item in the record had the wrong kind of value.",
    "SCHEMA_UNSUPPORTED": "The record used a format version AssetOps does not accept.",
    "INVALID_IDENTITY": "The record's source, device or signal name was not valid.",
    "INVALID_TIMING": "The record's times were not valid.",
    "INVALID_PAYLOAD": "The record's value was not valid.",
    "MAPPING_INCOMPATIBLE": (
        "The record did not match how records from this source are interpreted."
    ),
    "UNIT_INCOMPATIBLE": (
        "The record's unit did not match the unit configured for that signal."
    ),
    "SITE_MISMATCH": "The record named a different site.",
    "SITE_UNKNOWN": "The record named a site AssetOps does not know.",
    "SOURCE_MODE_MISMATCH": (
        "The record's origin (demonstration or live) did not match the site's."
    ),
    "SIGNAL_NOT_IN_CONFIGURATION": (
        "The record's signal is not part of this site's equipment details."
    ),
    "BEFORE_CONFIGURATION_EFFECTIVE": (
        "The record is older than the equipment details it would be read against."
    ),
    "CONFIGURATION_UNRESOLVED": (
        "The site's equipment details for the record's time could not be found."
    ),
    "MAPPING_CONFLICT": (
        "The delivery described its records' interpretation differently from before."
    ),
    "BATCH_ID_CONFLICT": (
        "A delivery reused an earlier delivery's reference with different content."
    ),
}
REJECTION_UNAVAILABLE = (
    "This record was not accepted. A plain description of the reason is not available."
)


def rejection_reading(kind: str) -> str:
    """The plain sentence for one stored rejection kind."""
    return REJECTION_READINGS.get(kind, REJECTION_UNAVAILABLE)


@dataclass(frozen=True)
class NeededSignal:
    device_id: str
    signal_id: str
    #: The Overview metric(s) that read this signal. Names only; no card state.
    needed_by: tuple[str, ...]


#: The signals each Site type's Overview domains read (task T027 phase 2 card
#: list), in the domain order the backend serves. Substrate data: it names
#: domains and signals and holds no card state. Which cards render, and in
#: which order, is the frontend presentation profile's
#: (`frontend/src/sites/presentationProfiles.json`); a test pins the two
#: domain lists equal (review N9), so the Overview and coverage cannot drift.
OVERVIEW_DOMAIN_SIGNALS: dict[str, tuple[tuple[str, tuple[tuple[str, str], ...]], ...]] = {
    "MINIGRID": (
        ("Service", (
            ("residential-meter", "active-power"),
            ("clinic-meter", "active-power"),
            ("mill-meter", "active-power"),
        )),
        ("Dispatch", (
            ("generator-controller", "status"),
            ("generator-controller", "ac-power"),
        )),
        ("Battery", (("battery-pcs-controller", "state-of-charge"),)),
        ("Fuel", (("fuel-level-sensor", "fuel-level"),)),
        ("Renewable", (("pv-inverter-controller", "ac-power"),)),
    ),
}


def _needed_signals(
    domains: tuple[tuple[str, tuple[tuple[str, str], ...]], ...],
) -> tuple[NeededSignal, ...]:
    by_key: dict[tuple[str, str], list[str]] = {}
    for domain, signals in domains:
        for key in signals:
            by_key.setdefault(key, []).append(domain)
    return tuple(NeededSignal(key[0], key[1], tuple(names)) for key, names in by_key.items())


#: The signals each Site type's Overview metrics read, derived from
#: `OVERVIEW_DOMAIN_SIGNALS` so coverage and the Overview share one list.
NEEDED_SIGNALS: dict[str, tuple[NeededSignal, ...]] = {
    site_type: _needed_signals(domains)
    for site_type, domains in OVERVIEW_DOMAIN_SIGNALS.items()
}

SOURCE_HEALTH_STATEMENT = (
    "Source and connector health describe data delivery and quality, never asset health."
)
COVERAGE_STATEMENT = (
    "Coverage counts accepted records in the window only. A gap is not filled, "
    "unavailable records are counted rather than given a value, and no sample is "
    "carried forward."
)
OVERLAP_STATEMENT = (
    "Distinct records at the same device, signal and source time are all kept "
    "and shown; none is summed with, or replaces, another."
)


def _seconds_between(earlier: str, later: str) -> int:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return int((datetime.strptime(later, fmt) - datetime.strptime(earlier, fmt)).total_seconds())


def _in_window(record: AcceptedRecord, start: str | None, end: str | None) -> bool:
    return (start is None or record.source_time >= start) and (
        end is None or record.source_time <= end
    )


def _overlap_keys(records: list[AcceptedRecord]) -> set[tuple[str, str, str]]:
    counts: dict[tuple[str, str, str], int] = {}
    for record in records:
        key = (record.device_id, record.signal_id, record.source_time)
        counts[key] = counts.get(key, 0) + 1
    return {key for key, count in counts.items() if count > 1}


def batch_payload(progress: BatchProgress) -> dict[str, Any]:
    return {
        "batch_id": progress.batch_id,
        "site_id": progress.site_id,
        "source_id": progress.source_id,
        "gateway_id": progress.gateway_id,
        "source_mode": progress.source_mode,
        "status": progress.status,
        "total": progress.total,
        "processed": progress.processed,
        "accepted": progress.accepted,
        "duplicates": progress.duplicates,
        "rejected": progress.rejected,
        "conflicts": progress.conflicts,
        "refusal": (
            None
            if progress.refusal_kind is None
            else {"kind": progress.refusal_kind, "detail": progress.refusal_detail}
        ),
        "started_at": progress.started_at,
        "completed_at": progress.completed_at,
        "window_start": progress.window_start,
        "window_end": progress.window_end,
    }


def _record_summary(record: AcceptedRecord, overlapping: bool) -> dict[str, Any]:
    return {
        "message_id": record.message_id,
        "source_id": record.source_id,
        "gateway_id": record.gateway_id,
        "device_id": record.device_id,
        "signal_id": record.signal_id,
        "family": record.family,
        "value": record.original_value,
        "unit": record.original_unit,
        "quality": record.quality,
        "source_time": record.source_time,
        "published_at": record.published_at,
        "received_at": record.received_at,
        "overlapping": overlapping,
    }


def default_window(evidence: SiteEvidence) -> tuple[str | None, str | None]:
    """The latest completed batch's accepted window, else all accepted records."""
    completed = [
        p for p in evidence.batches
        if p.status == "COMPLETED" and p.window_start is not None
    ]
    if completed:
        latest = max(completed, key=lambda p: (p.completed_at or "", p.batch_id))
        return latest.window_start, latest.window_end
    if evidence.records:
        times = [record.source_time for record in evidence.records]
        return min(times), max(times)
    return None, None


def in_window(record: AcceptedRecord, start: str | None, end: str | None) -> bool:
    return _in_window(record, start, end)


class EvidenceReadModel:
    def __init__(self, store: EvidenceStore) -> None:
        self._store = store

    def _default_window(self, evidence: SiteEvidence) -> tuple[str | None, str | None]:
        return default_window(evidence)

    def site_evidence(
        self,
        site: SiteRecord,
        window_start: str | None = None,
        window_end: str | None = None,
    ) -> dict[str, Any]:
        evidence = self._store.load_site(site.site_id)
        if window_start is None and window_end is None:
            window_start, window_end = self._default_window(evidence)
            window_basis = "LATEST_RELEASE"
        else:
            window_basis = "REQUESTED"
        in_window = [r for r in evidence.records if _in_window(r, window_start, window_end)]
        overlaps = _overlap_keys(in_window)
        return {
            "site_id": site.site_id,
            "window": {"start": window_start, "end": window_end, "basis": window_basis},
            "sources": self._sources(evidence, in_window),
            "source_health_statement": SOURCE_HEALTH_STATEMENT,
            "coverage": self._coverage(site, in_window, overlaps),
            "coverage_statement": COVERAGE_STATEMENT,
            "overlap_statement": OVERLAP_STATEMENT,
            "basis": self._basis(site, in_window),
            "rejection_count": len(evidence.rejections),
            "conflict_count": len(evidence.conflicts),
        }

    def _sources(self, evidence: SiteEvidence, in_window: list[AcceptedRecord]) -> list[dict[str, Any]]:
        keys = {(r.source_id, r.gateway_id) for r in evidence.records}
        keys |= {(p.source_id, p.gateway_id) for p in evidence.batches}
        rows = []
        for source_id, gateway_id in sorted(keys):
            mine = [r for r in evidence.records if (r.source_id, r.gateway_id) == (source_id, gateway_id)]
            batches = [p for p in evidence.batches if (p.source_id, p.gateway_id) == (source_id, gateway_id)]
            latest = max(mine, key=lambda r: (r.source_time, r.message_id)) if mine else None
            rows.append(
                {
                    "source_id": source_id,
                    "gateway_id": gateway_id,
                    "source_mode": (
                        latest.source_mode if latest else batches[-1].source_mode
                    ),
                    "accepted_total": len(mine),
                    "accepted_in_window": sum(
                        1 for r in in_window if (r.source_id, r.gateway_id) == (source_id, gateway_id)
                    ),
                    "duplicates": sum(p.duplicates for p in batches),
                    "rejected": sum(p.rejected for p in batches),
                    "conflicts": sum(p.conflicts for p in batches),
                    "last_source_time": latest.source_time if latest else None,
                    "last_published_at": max((r.published_at for r in mine), default=None),
                    "last_received_at": max((r.received_at for r in mine), default=None),
                    "batches": [
                        {
                            "batch_id": p.batch_id,
                            "status": p.status,
                            "processed": p.processed,
                            "total": p.total,
                        }
                        for p in batches
                    ],
                }
            )
        return rows

    def _coverage(
        self,
        site: SiteRecord,
        in_window: list[AcceptedRecord],
        overlaps: set[tuple[str, str, str]],
    ) -> list[dict[str, Any]]:
        needed = NEEDED_SIGNALS.get(site.site_type, ())
        needed_by = {(n.device_id, n.signal_id): list(n.needed_by) for n in needed}
        declared_units: dict[tuple[str, str], str] = {}
        for device in site.foundation.devices or ():
            for signal in device.signals:
                declared_units[(device.device_id, signal.signal_id)] = signal.unit
        grouped: dict[tuple[str, str], list[AcceptedRecord]] = {}
        for record in in_window:
            grouped.setdefault((record.device_id, record.signal_id), []).append(record)
        rows = []
        for key in sorted(set(grouped) | set(needed_by)):
            records = sorted(grouped.get(key, []), key=lambda r: (r.source_time, r.message_id))
            if not records:
                rows.append(
                    {
                        "device_id": key[0],
                        "signal_id": key[1],
                        "family": None,
                        "status": "NOT_REPORTED",
                        "unit": declared_units.get(key),
                        "records": 0,
                        "good": 0,
                        "unavailable": 0,
                        "overlapping": 0,
                        "first_source_time": None,
                        "last_source_time": None,
                        "longest_silence_seconds": None,
                        "needed_by": needed_by.get(key, []),
                    }
                )
                continue
            times = sorted({r.source_time for r in records})
            silence = max(
                (_seconds_between(a, b) for a, b in zip(times, times[1:])), default=None
            )
            rows.append(
                {
                    "device_id": key[0],
                    "signal_id": key[1],
                    "family": records[0].family,
                    "status": "REPORTED",
                    "unit": records[-1].original_unit,
                    "records": len(records),
                    "good": sum(1 for r in records if r.quality == "GOOD"),
                    "unavailable": sum(1 for r in records if r.quality == "UNAVAILABLE"),
                    "overlapping": sum(
                        1 for r in records if (r.device_id, r.signal_id, r.source_time) in overlaps
                    ),
                    "first_source_time": times[0],
                    "last_source_time": times[-1],
                    "longest_silence_seconds": silence,
                    "needed_by": needed_by.get(key, []),
                }
            )
        return rows

    def _basis(self, site: SiteRecord, in_window: list[AcceptedRecord]) -> dict[str, Any]:
        mappings = sorted({(r.mapping_set_id, r.mapping_version) for r in in_window})
        versions = sorted({r.foundation_version for r in in_window})
        configurations: list[dict[str, Any]] = []
        for version in versions:
            basis: ConfigurationBasis | None = self._store.get_configuration(site.site_id, version)
            configurations.append(
                {
                    "foundation_version": version,
                    "foundation_valid_from": None if basis is None else basis.foundation_valid_from,
                    "registered_at": None if basis is None else basis.registered_at,
                    "signal_count": None if basis is None else len(basis.signals),
                }
            )
        return {
            "mappings": [
                {"mapping_set_id": set_id, "mapping_version": version}
                for set_id, version in mappings
            ],
            "configurations": configurations,
            "current_foundation": {
                "foundation_version": site.foundation.version,
                "foundation_valid_from": site.foundation.valid_from,
            },
        }

    def records(
        self,
        site_id: str,
        *,
        device_id: str | None = None,
        signal_id: str | None = None,
        source_id: str | None = None,
        window_start: str | None = None,
        window_end: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        evidence = self._store.load_site(site_id)
        selected = [
            r for r in evidence.records
            if _in_window(r, window_start, window_end)
            and (device_id is None or r.device_id == device_id)
            and (signal_id is None or r.signal_id == signal_id)
            and (source_id is None or r.source_id == source_id)
        ]
        overlaps = _overlap_keys(
            [r for r in evidence.records if _in_window(r, window_start, window_end)]
        )
        selected.sort(key=lambda r: (r.source_time, r.message_id), reverse=True)
        return {
            "site_id": site_id,
            "total": len(selected),
            "limit": limit,
            "records": [
                _record_summary(r, (r.device_id, r.signal_id, r.source_time) in overlaps)
                for r in selected[:limit]
            ],
        }

    def record(self, site_id: str, message_id: str) -> dict[str, Any] | None:
        evidence = self._store.load_site(site_id)
        record = next((r for r in evidence.records if r.message_id == message_id), None)
        if record is None:
            return None
        basis = self._store.get_configuration(site_id, record.foundation_version)
        overlapping = sorted(
            r.message_id for r in evidence.records
            if (r.device_id, r.signal_id, r.source_time)
            == (record.device_id, record.signal_id, record.source_time)
            and r.message_id != record.message_id
        )
        return {
            "message_id": record.message_id,
            "site_id": record.site_id,
            "source_id": record.source_id,
            "gateway_id": record.gateway_id,
            "source_mode": record.source_mode,
            "device_id": record.device_id,
            "signal_id": record.signal_id,
            "family": record.family,
            "measurement": record.measurement,
            "mapping": {
                "mapping_set_id": record.mapping_set_id,
                "mapping_version": record.mapping_version,
            },
            "configuration": {
                "foundation_version": record.foundation_version,
                "foundation_valid_from": record.foundation_valid_from,
                "registered_at": None if basis is None else basis.registered_at,
            },
            "quality": record.quality,
            "unavailable_reason": record.unavailable_reason,
            "original": {"value": record.original_value, "unit": record.original_unit},
            "normalized": {"value": record.normalized_value, "unit": record.normalized_unit},
            "normalization": NORMALIZATION,
            "normalization_statement": NORMALIZATION_STATEMENT,
            "interval": (
                None
                if record.interval_start is None
                else {"start": record.interval_start, "end": record.interval_end}
            ),
            "record_detail": {name: value for name, value in record.record_detail},
            "source_time": record.source_time,
            "published_at": record.published_at,
            "received_at": record.received_at,
            "batch_id": record.batch_id,
            "content_digest": record.content_digest,
            "envelope_text": record.envelope_text,
            "overlapping_with": overlapping,
            "conflicts": [
                {
                    "batch_id": c.batch_id,
                    "original_digest": c.original_digest,
                    "conflicting_digest": c.conflicting_digest,
                    "received_at": c.received_at,
                }
                for c in evidence.conflicts
                if c.message_id == message_id
            ],
        }

    def batch(self, batch_id: str) -> dict[str, Any] | None:
        progress = find_batch(self._store, batch_id)
        return None if progress is None else batch_payload(progress)

    def rejections(self, site_id: str, batch_id: str | None = None) -> dict[str, Any]:
        evidence = self._store.load_site(site_id)
        rows = [r for r in evidence.rejections if batch_id is None or r.batch_id == batch_id]
        return {
            "site_id": site_id,
            "total": len(rows),
            "rejections": [
                {
                    "batch_id": r.batch_id,
                    "index": r.index,
                    "message_id": r.message_id,
                    "kind": r.kind,
                    "field": r.field,
                    "detail": r.detail,
                    "reason": rejection_reading(r.kind),
                    "received_at": r.received_at,
                    "content_digest": r.content_digest,
                }
                for r in rows
            ],
            "conflicts": [
                {
                    "message_id": c.message_id,
                    "batch_id": c.batch_id,
                    "original_digest": c.original_digest,
                    "conflicting_digest": c.conflicting_digest,
                    "received_at": c.received_at,
                }
                for c in evidence.conflicts
                if batch_id is None or c.batch_id == batch_id
            ],
        }
