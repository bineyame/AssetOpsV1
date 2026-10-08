"""Registered-run publication through the separate durable gateway (S2-01b).

For a run set up from a registered Site, the gateway's SQLite outbox replaces the
file-backed Stage as the publication authority. This module is the Lab host's
side of `D-2026-10-08-s2-local-gateway-snapshot-transfer`:

- it reaches the gateway only through `assetops_gateway.ipc.GatewayLink`, the
  authenticated local channel - never the ledger or service directly;
- it hands over the run's already frozen canonical snapshot bytes and the
  references `RegisteredBasis` froze with them, and nothing it re-derives;
- it adapts each public `DeviceObservation` with the contract adapter
  `report_from_observation`, so only `assetops.simulated-device-report` text
  crosses the process boundary: no kernel, world, oracle, scenario or run
  cause, and the run ID only as the gateway's local provenance reference;
- a deterministic `report_key` per observation makes the host's whole-series
  replay land on the identity the gateway already admitted.

Any failure is raised, never papered over: the caller records it and the Stage
stays pending. There is no YAML or file-backed fallback for a registered run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, Sequence

from assetops_contracts.gateway_report import device_report_text, report_from_observation
from assetops_contracts.gateway_stage import (
    REGISTERED_STAGE_STATEMENTS,
    GatewayBatch,
    GatewayEnvelope,
    GatewayHold,
    RegisteredStageView,
)
from assetops_contracts.observation import DeviceObservation
from assetops_contracts.source_envelope import EnvelopeRejected
from assetops_gateway.ipc import GatewayLink, GatewayRequestRefused, GatewayUnavailable

#: The gateway's per-request admission bound (`service.MAX_ADMISSION_CHUNK`).
ADMISSION_CHUNK = 1024


class PublicationRefused(RuntimeError):
    """The host refused to publish, before or after reaching the gateway."""

    def __init__(self, kind: str, detail: str) -> None:
        self.kind, self.detail = kind, detail
        super().__init__(f"{kind}: {detail}")


@dataclass(frozen=True)
class PublicationResult:
    admitted: int
    already_admitted: int
    held: int
    batch_ids: tuple[str, ...]


def report_key(run_id: str, snapshot_sha256: str, device_id: str, signal_id: str, source_time: str, ordinal: int) -> str:
    """One observation's local admission identity.

    Deterministic, so a replayed series of the same run is ALREADY_ADMITTED;
    the ordinal separates genuinely repeated samples at one source time. Opaque,
    so the run ID never appears in a report as readable text."""
    material = "\x1f".join((run_id, snapshot_sha256, device_id, signal_id, source_time, str(ordinal)))
    return "lab-" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def report_texts(
    run_id: str, snapshot_sha256: str, observations: Iterable[DeviceObservation], interval_minutes: int
) -> list[str]:
    """The public reports for a series; dropped/suppressed observations make none."""
    seen: dict[tuple[str, str, str], int] = {}
    texts: list[str] = []
    for observation in observations:
        slot = (observation.device_id, observation.signal_id, observation.source_sample_time)
        ordinal = seen.get(slot, 0)
        seen[slot] = ordinal + 1
        report = report_from_observation(
            observation,
            interval_minutes=interval_minutes,
            report_key=report_key(run_id, snapshot_sha256, *slot, ordinal),
        )
        if report is not None:
            texts.append(device_report_text(report))
    return texts


def claimed_references(basis) -> dict[str, object]:
    """What `RegisteredBasis` froze with the snapshot bytes; checked by the gateway."""
    return {
        "snapshot_sha256": basis.snapshot_sha256,
        "foundation_revision_id": basis.foundation_revision_id,
        "foundation_version": basis.foundation_version,
        "binding_set_id": basis.binding_set_id,
        "binding_set_revision_id": basis.binding_set_revision_id,
        "binding_set_version": basis.binding_set_version,
    }


class RegisteredGatewayPublisher:
    def __init__(self, link: GatewayLink) -> None:
        self._link = link

    def publish(
        self,
        run_id: str,
        basis,
        observations: Sequence[DeviceObservation],
        *,
        interval_minutes: int,
    ) -> PublicationResult:
        """Activate the frozen basis, admit the series, seal. Raises on any refusal."""
        identity = self._link.call("identity")
        if identity["tenant_id"] != basis.tenant_id or identity["site_id"] != basis.site_record_id:
            raise PublicationRefused(
                "WRONG_SITE",
                f"the gateway is provisioned for Site {identity['site_id']}, not this run's {basis.site_record_id}",
            )
        self._link.call(
            "activate", {"snapshot_text": basis.snapshot_canonical, "claimed": claimed_references(basis)}
        )
        try:
            texts = report_texts(run_id, basis.snapshot_sha256, observations, interval_minutes)
        except EnvelopeRejected as rejected:
            raise PublicationRefused("REPORT_NOT_ADAPTABLE", str(rejected)) from rejected
        counts = {"ADMITTED": 0, "ALREADY_ADMITTED": 0, "HELD": 0}
        for start in range(0, len(texts), ADMISSION_CHUNK):
            answer = self._link.call(
                "admit",
                {
                    "snapshot_sha256": basis.snapshot_sha256,
                    "lab_run_ref": run_id,
                    "reports": texts[start : start + ADMISSION_CHUNK],
                },
            )
            for admission in answer["admissions"]:
                counts[admission["outcome"]] += 1
        batch_ids = self._link.call("seal")["batch_ids"]
        return PublicationResult(
            counts["ADMITTED"], counts["ALREADY_ADMITTED"], counts["HELD"], tuple(batch_ids)
        )

    def stage(
        self, run_id: str, basis, *, execution_status: str, notes: Sequence[str] = ()
    ) -> RegisteredStageView:
        """The run's Stage, read back from the gateway ledger."""
        try:
            identity = self._link.call("identity")
            document = self._link.call("run_stage", {"lab_run_ref": run_id})
        except (GatewayUnavailable, GatewayRequestRefused) as failure:
            return unavailable_stage(run_id, basis, execution_status, str(failure), notes)
        envelopes = tuple(GatewayEnvelope(**e) for e in document["envelopes"])
        holds = tuple(GatewayHold(**h) for h in document["holds"])
        status = "STAGED" if envelopes or holds else "NOT_STAGED"
        return RegisteredStageView(
            run_id=run_id,
            status=status,
            statement=REGISTERED_STAGE_STATEMENTS[status],
            execution_status=execution_status,
            snapshot_sha256=basis.snapshot_sha256,
            site_id=identity["site_id"],
            gateway_id=identity["gateway_id"],
            sequence_epoch=document["sequence_epoch"],
            envelopes=envelopes,
            batches=tuple(
                GatewayBatch(**{**b, "message_ids": tuple(b["message_ids"])}) for b in document["batches"]
            ),
            holds=holds,
            queue_depth_by_state=dict(document["queue_depth_by_state"]),
            publication_notes=tuple(notes),
        )


def unavailable_stage(
    run_id: str, basis, execution_status: str, detail: str, notes: Sequence[str] = ()
) -> RegisteredStageView:
    return RegisteredStageView(
        run_id=run_id,
        status="GATEWAY_UNAVAILABLE",
        statement=REGISTERED_STAGE_STATEMENTS["GATEWAY_UNAVAILABLE"],
        execution_status=execution_status,
        snapshot_sha256=basis.snapshot_sha256,
        site_id=None,
        gateway_id=None,
        sequence_epoch=None,
        envelopes=(),
        batches=(),
        holds=(),
        queue_depth_by_state={},
        unavailable_detail=detail,
        publication_notes=tuple(notes),
    )
