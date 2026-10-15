"""S4-05a phase 1: the server-recorded run side of a `REGISTERED_SIMULATION` publication.

Builds the evidence package's neutral `RunAttestation` from two server-held reads: the run store's record of a
registered run, and the registered gateway's Stage read for that run (`LabExecutionPort.registered_stage`). The
run identity digest is computed here from the record's immutable identity (run ID, creation time, frozen
deterministic identity and registered basis), never taken from a client; only the ID and the digest leave this
module, so private scenario truth stays out of product evidence.

The Stage view is read by attribute so this module does not import the gated stage contract (dependency rule:
only the Lab surface and its port import it). S4-05b calls `run_attestation` from the registered-commit
release step, before any STAGED batch moves to READY.
"""

from __future__ import annotations

import hashlib
import json

from assetops_backend.evidence.publication import PublicationRefused, RunAttestation, StagedBatch
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.parsing import render_run_document

RUN_IDENTITY_DOMAIN = "assetops.registered-run-identity.v1"
_IDENTITY_KEYS = ("run_id", "created_at", "deterministic_identity", "registered_basis")


def run_identity_sha256(run: SimulationRun) -> str:
    """SHA-256 over the run's immutable identity, as canonical JSON (sorted keys, no whitespace)."""
    document = render_run_document(run)
    identity = {key: document.get(key) for key in _IDENTITY_KEYS}
    body = json.dumps([RUN_IDENTITY_DOMAIN, identity], sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def run_attestation(run: SimulationRun, stage: object) -> RunAttestation:
    """The attestation for one registered run; refuses a run with no registered basis."""
    basis = run.registered_basis
    if basis is None:
        raise PublicationRefused("RUN_NOT_REGISTERED", "only a run with a registered basis can be designated")
    envelopes = tuple(getattr(stage, "envelopes", ()))
    return RunAttestation(
        run_id=run.run_id,
        run_identity_sha256=run_identity_sha256(run),
        tenant_id=basis.tenant_id,
        site_id=basis.site_record_id,
        snapshot_sha256=basis.snapshot_sha256,
        stage_run_id=str(getattr(stage, "run_id", "")),
        stage_status=str(getattr(stage, "status", "")),
        run_message_ids=frozenset(e.message_id for e in envelopes),
        batches=tuple(
            StagedBatch(batch_id=b.batch_id, payload_text=b.payload_text, sha256=b.sha256,
                        message_ids=tuple(b.message_ids))
            for b in getattr(stage, "batches", ())
        ),
    )
