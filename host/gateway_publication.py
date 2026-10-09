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
    GatewaySealRefusal,
    RegisteredStageView,
    registered_stage_status,
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
    return [text for _, _, text in keyed_reports(run_id, snapshot_sha256, observations, interval_minutes)]


def keyed_reports(
    run_id: str, snapshot_sha256: str, observations: Iterable[DeviceObservation], interval_minutes: int
) -> list[tuple[DeviceObservation, str, str]]:
    """Each public report with the observation it came from and its admission key."""
    seen: dict[tuple[str, str, str], int] = {}
    texts: list[tuple[DeviceObservation, str, str]] = []
    for observation in observations:
        slot = (observation.device_id, observation.signal_id, observation.source_sample_time)
        ordinal = seen.get(slot, 0)
        seen[slot] = ordinal + 1
        key = report_key(run_id, snapshot_sha256, *slot, ordinal)
        report = report_from_observation(observation, interval_minutes=interval_minutes, report_key=key)
        if report is not None:
            texts.append((observation, key, device_report_text(report)))
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
        self._activate(basis)
        try:
            texts = report_texts(run_id, basis.snapshot_sha256, observations, interval_minutes)
        except EnvelopeRejected as rejected:
            raise PublicationRefused("REPORT_NOT_ADAPTABLE", str(rejected)) from rejected
        return self._sealed(self._admit(run_id, basis, texts, "admit"))

    def publish_at_run_clock(self, run_id: str, basis, texts: Sequence[str], instant: str) -> list[dict]:
        """S2-01c: advance the run's gateway clock to `instant`, admit, seal.

        `D-2026-10-09-s2-simulated-publication-clock`. The caller passes only
        reports already due at `instant`; the gateway stamps `published_at`
        from its persisted run clock at first admission and answers a replay
        with its first identity, unchanged. Returns the per-report admissions
        in order, so the Lab can record which delayed report became which
        envelope. Sealing runs even when nothing new was admitted, which is
        the retry of an earlier failed seal."""
        self._activate(basis)
        self._link.call("advance_publication_clock", {"lab_run_ref": run_id, "instant": instant})
        admissions = self._admit(run_id, basis, list(texts), "admit_at_run_clock")
        self._sealed(admissions)
        return admissions

    def _activate(self, basis) -> None:
        identity = self._link.call("identity")
        if identity["tenant_id"] != basis.tenant_id or identity["site_id"] != basis.site_record_id:
            raise PublicationRefused(
                "WRONG_SITE",
                f"the gateway is provisioned for Site {identity['site_id']}, not this run's {basis.site_record_id}",
            )
        self._link.call(
            "activate", {"snapshot_text": basis.snapshot_canonical, "claimed": claimed_references(basis)}
        )

    def _admit(self, run_id: str, basis, texts: list[str], op: str) -> list[dict]:
        admissions: list[dict] = []
        for start in range(0, len(texts), ADMISSION_CHUNK):
            try:
                answer = self._link.call(
                    op,
                    {
                        "snapshot_sha256": basis.snapshot_sha256,
                        "lab_run_ref": run_id,
                        "reports": texts[start : start + ADMISSION_CHUNK],
                    },
                )
            except GatewayRequestRefused as refused:
                if refused.kind == "DISK_PRESSURE_STOP":
                    # S2-01c AC3: acquisition refused before any sequence; what
                    # was admitted and sealed before is retained untouched.
                    raise PublicationRefused("DISK_PRESSURE_STOP", refused.detail) from refused
                raise
            admissions.extend(answer["admissions"])
        return admissions

    def _sealed(self, admissions: list[dict]) -> PublicationResult:
        counts = {"ADMITTED": 0, "ALREADY_ADMITTED": 0, "HELD": 0}
        for admission in admissions:
            counts[admission["outcome"]] += 1
        try:
            batch_ids = self._link.call("seal")["batch_ids"]
        except GatewayRequestRefused as refused:
            # Admission is already committed: the ledger keeps the unbatched
            # envelopes and a durable seal refusal the Stage read reports.
            raise PublicationRefused(
                "SEAL_REFUSED", f"the reports were admitted but not all could be sealed: {refused}"
            ) from refused
        return PublicationResult(
            counts["ADMITTED"], counts["ALREADY_ADMITTED"], counts["HELD"], tuple(batch_ids)
        )

    def diagnostics(self) -> dict:
        """S2-01c: the gateway's local diagnostic read, or an explicit unavailable state.

        A gateway that cannot be reached is `GATEWAY_UNAVAILABLE` with its
        reason, never a healthy zero queue. Local only: no central receipt."""
        try:
            document = self._link.call("diagnostics")
        except (GatewayUnavailable, GatewayRequestRefused) as failure:
            return {"status": "GATEWAY_UNAVAILABLE", "detail": str(failure), "diagnostics": None}
        return {"status": "AVAILABLE", "detail": None, "diagnostics": document}

    def inject_fault(self, fault: str, value) -> dict:
        """S2-01c fault fixture (SIMULATED gateways only); raises on refusal."""
        return self._link.call("inject_fault", {"fault": fault, "value": value})

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
        seal_refusals = tuple(GatewaySealRefusal(**r) for r in document.get("seal_refusals", ()))
        status = registered_stage_status(envelopes, holds, seal_refusals)
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
            seal_refusals=seal_refusals,
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
