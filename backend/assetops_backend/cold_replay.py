"""W2-02 cold replay read (`.agent/W2-02-build-spec.md` "Commit (4) exact contract").

`ColdReplayService.replay` reads one explicitly selected, persisted cold run and the public transport that its
`REGISTERED_SIMULATION` publications carried into the S2 ledger: publication IDs ordered by
`(recorded_at, id)`, linked Batch V2 external IDs, per-batch counts recomputed from dispositions, accepted IDs
and a digest over every disposition's public envelope. It issues no SQL itself: the injected reader is the
evidence ledger's SELECT-only `cold_replay_*` methods. No private trajectory, forcing, report payload or run
truth is read or returned; the run profile comes only from the frozen persisted run, never from publications.
"""

from __future__ import annotations

import hashlib
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunNotFound,
    RunStoreUnavailable,
    SimulationRunRepository,
)
from assetops_backend.runs.profiles import COLD_PUBLICATION_PROFILE, COLD_THERMAL_MODEL
from assetops_backend.scenarios.cold_parsing import COLD_OBSERVATION_PROFILE
from assetops_backend.sites.identity import site_id_key
from assetops_contracts.ingestion_batch_v2 import BatchRejected, parse_canonical_batch_v2_text
from assetops_contracts.source_envelope import canonical_json

DECISIONS = ("ACCEPTED", "DUPLICATE", "REJECTED", "CONFLICT")


class ColdReplayUnavailable(Exception):
    """503 `COLD_REPLAY_UNAVAILABLE`: a store read failed, or what was read cannot be a completed replay."""


class ColdRunNotFound(Exception):
    """404 `RUN_NOT_FOUND`: no persisted cold run of this tenant Site has this ID."""


class ColdReplayReader(Protocol):
    def cold_replay_rows(self, tenant_id: UUID, site_id: UUID, run_id: str) -> dict: ...

    def cold_replay_run_referenced(self, tenant_id: UUID, site_id: UUID, run_id: str) -> bool: ...


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _profile(profile_id: str, version: int) -> dict[str, Any]:
    return {"profile_id": profile_id, "profile_version": version}


class ColdReplayService:
    def __init__(self, reader: ColdReplayReader, runs: SimulationRunRepository) -> None:
        self._reader = reader
        self._runs = runs

    def replay(self, tenant_id: UUID, site_id: UUID, site_code: str, run_id: str) -> dict[str, Any]:
        run = self._run(tenant_id, site_id, run_id)
        profile, scenario_digest = self._cold_identity(run, tenant_id, site_id, site_code)
        try:
            rows = self._reader.cold_replay_rows(tenant_id, site_id, run_id)
        except LedgerUnavailable as error:
            raise ColdReplayUnavailable(str(error)) from error
        by_batch: dict[str, list[dict]] = {}
        for row in rows["dispositions"]:
            by_batch.setdefault(row["batch_id"], []).append(row)
        publication_ids: list[str] = []
        batch_ids: list[str] = []
        receipts: list[dict[str, Any]] = []
        accepted: list[str] = []
        digest_input: list[list[Any]] = []
        for publication in rows["publications"]:
            publication_ids.append(publication["publication_id"])
            if publication["l_batch"] is None:
                continue  # a valid pending release: its ID, no batch, receipt or accepted ID
            external_id = self._linked_batch(publication, tenant_id, site_id)
            dispositions = by_batch.get(publication["b_id"], [])
            envelopes = self._envelopes(publication, dispositions)
            counts = {"accepted": 0, "duplicate": 0, "rejected": 0, "conflict": 0}
            for row, envelope in zip(dispositions, envelopes):
                decision = row["decision"]
                if decision not in DECISIONS:
                    raise ColdReplayUnavailable(f"batch {external_id} ordinal {row['ordinal']} has decision {decision!r}")
                counts[decision.lower()] += 1
                referenced = row["accepted_evidence_id"] if decision in ("ACCEPTED", "DUPLICATE") else None
                if decision in ("ACCEPTED", "DUPLICATE") and referenced is None:
                    raise ColdReplayUnavailable(f"batch {external_id} ordinal {row['ordinal']} names no evidence")
                if decision == "ACCEPTED":
                    accepted.append(referenced)
                digest_input.append([external_id, row["ordinal"], _sha256(envelope), decision, referenced])
            batch_ids.append(external_id)
            receipts.append({"batch_id": external_id, **counts})
        return {
            "publication_id": publication_ids[-1] if publication_ids else None,
            "publication_ids": publication_ids,
            "run_profile": profile,
            "scenario_digest": scenario_digest,
            "batch_ids": batch_ids,
            "receipts": receipts,
            "accepted_record_ids": accepted,
            "public_digest": _sha256(canonical_json(digest_input)),
        }

    def _run(self, tenant_id: UUID, site_id: UUID, run_id: str) -> SimulationRun:
        try:
            return self._runs.get_run(run_id)
        except RunNotFound as missing:
            try:
                referenced = self._reader.cold_replay_run_referenced(tenant_id, site_id, run_id)
            except LedgerUnavailable as error:
                raise ColdReplayUnavailable(str(error)) from error
            if referenced:
                raise ColdReplayUnavailable(f"a publication names run {run_id}, which is not persisted") from missing
            raise ColdRunNotFound(run_id) from missing
        except (RunConfigurationInvalid, RunStoreUnavailable) as error:
            raise ColdReplayUnavailable(str(error)) from error

    @staticmethod
    def _cold_identity(run: SimulationRun, tenant_id: UUID, site_id: UUID,
                       site_code: str) -> tuple[dict[str, Any], str]:
        identity = run.deterministic_identity
        basis = run.registered_basis
        if (basis is None or basis.tenant_id != str(tenant_id) or basis.site_record_id != str(site_id)
                or site_id_key(identity.site.site_id) != site_id_key(site_code)):
            raise ColdRunNotFound(run.run_id)  # another tenant/Site's run, or no registered basis
        frozen = identity.profiles
        pair = ((frozen.model_profile_id, frozen.model_profile_version),
                (frozen.publication_profile_id, frozen.publication_profile_version))
        cold_pair = ((COLD_THERMAL_MODEL.model_profile_id, COLD_THERMAL_MODEL.model_profile_version),
                     (COLD_PUBLICATION_PROFILE.publication_profile_id,
                      COLD_PUBLICATION_PROFILE.publication_profile_version))
        if pair != cold_pair:
            raise ColdRunNotFound(run.run_id)  # not a cold run
        observation_id, _, observation_version = COLD_OBSERVATION_PROFILE.rpartition("/")
        if ((frozen.observation_profile_id, frozen.observation_profile_version)
                != (observation_id, int(observation_version)) or not identity.scenario.scenario_sha256):
            raise ColdReplayUnavailable(f"run {run.run_id} has the cold pair without its frozen observation identity")
        return ({
            "model_profile": _profile(frozen.model_profile_id, frozen.model_profile_version),
            "publication_profile": _profile(frozen.publication_profile_id, frozen.publication_profile_version),
            "observation_profile": _profile(frozen.observation_profile_id, frozen.observation_profile_version),
        }, identity.scenario.scenario_sha256)

    @staticmethod
    def _linked_batch(publication: dict, tenant_id: UUID, site_id: UUID) -> str:
        if publication["b_id"] is None:
            raise ColdReplayUnavailable(f"publication {publication['publication_id']} links a batch that is absent")
        if ((publication["b_tenant"], publication["b_site"]) != (str(tenant_id), str(site_id))
                or (publication["b_ext"], publication["b_sha"]) != (publication["p_ext"], publication["p_sha"])):
            raise ColdReplayUnavailable(f"publication {publication['publication_id']} and its batch disagree")
        if publication["b_status"] != "COMPLETED":
            raise ColdReplayUnavailable(f"batch {publication['b_ext']} is {publication['b_status']}, not completed")
        return publication["b_ext"]

    @staticmethod
    def _envelopes(publication: dict, dispositions: list[dict]) -> tuple[str, ...]:
        external_id = publication["b_ext"]
        try:
            batch = parse_canonical_batch_v2_text(publication["b_text"])
        except BatchRejected as error:
            raise ColdReplayUnavailable(f"batch {external_id} text is not canonical Batch V2: {error}") from error
        if (batch.batch_id, batch.payload_sha256) != (external_id, publication["b_sha"]):
            raise ColdReplayUnavailable(f"batch {external_id} text does not match its commitment")
        total = publication["b_total"]
        if len(batch.envelopes) != total or [d["ordinal"] for d in dispositions] != list(range(total)):
            raise ColdReplayUnavailable(f"batch {external_id} dispositions are incomplete")
        return batch.envelopes
