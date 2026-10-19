"""W2-05b EV replay read (`.agent/W2-05b-build-spec.md` commit 5 and q4 "Final commit 4-5" item 2).

The cold replay (`cold_replay.py`) mirrored for the closed EV pair. `EvReplayService.replay` reads one explicitly
selected, persisted EV run and the public transport that its
`REGISTERED_SIMULATION` publications carried into the S2 ledger: publication IDs ordered by
`(recorded_at, id)`, linked Batch V2 external IDs, per-batch counts recomputed from dispositions, accepted IDs
and a digest over every disposition's public envelope. It issues no SQL itself: the injected reader is the
evidence ledger's SELECT-only `ev_replay_*` methods, which share one REPEATABLE READ, READ ONLY snapshot. No private trajectory, forcing, report payload or run
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
from assetops_backend.runs.profiles import EV_CHARGER_MODEL, EV_PUBLICATION_PROFILE
from assetops_backend.scenarios.ev_parsing import EV_OBSERVATION_PROFILE
from assetops_backend.sites.identity import site_id_key
from assetops_contracts.ingestion_batch_v2 import BatchRejected, parse_canonical_batch_v2_text
from assetops_contracts.source_envelope import canonical_json

DECISIONS = ("ACCEPTED", "DUPLICATE", "REJECTED", "CONFLICT")


class EvReplayUnavailable(Exception):
    """503 `EV_REPLAY_UNAVAILABLE`: a store read failed, or what was read cannot be a completed replay."""


class EvRunNotFound(Exception):
    """404 `RUN_NOT_FOUND`: no persisted EV run of this tenant Site has this ID."""


class EvReplayReader(Protocol):
    def ev_replay_rows(self, tenant_id: UUID, site_id: UUID, run_id: str) -> dict: ...

    def ev_replay_run_referenced(self, tenant_id: UUID, site_id: UUID, run_id: str) -> bool: ...


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _profile(profile_id: str, version: int) -> dict[str, Any]:
    return {"profile_id": profile_id, "profile_version": version}


class EvReplayService:
    def __init__(self, reader: EvReplayReader, runs: SimulationRunRepository) -> None:
        self._reader = reader
        self._runs = runs

    def replay(self, tenant_id: UUID, site_id: UUID, site_code: str, run_id: str) -> dict[str, Any]:
        run = self._run(tenant_id, site_id, run_id)
        profile, scenario_digest = self._ev_identity(run, tenant_id, site_id, site_code)
        try:
            rows = self._reader.ev_replay_rows(tenant_id, site_id, run_id)
        except LedgerUnavailable as error:
            raise EvReplayUnavailable(str(error)) from error
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
                    raise EvReplayUnavailable(f"batch {external_id} ordinal {row['ordinal']} has decision {decision!r}")
                counts[decision.lower()] += 1
                referenced = row["accepted_evidence_id"] if decision in ("ACCEPTED", "DUPLICATE") else None
                if decision in ("ACCEPTED", "DUPLICATE") and referenced is None:
                    raise EvReplayUnavailable(f"batch {external_id} ordinal {row['ordinal']} names no evidence")
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
                referenced = self._reader.ev_replay_run_referenced(tenant_id, site_id, run_id)
            except LedgerUnavailable as error:
                raise EvReplayUnavailable(str(error)) from error
            if referenced:
                raise EvReplayUnavailable(f"a publication names run {run_id}, which is not persisted") from missing
            raise EvRunNotFound(run_id) from missing
        except (RunConfigurationInvalid, RunStoreUnavailable) as error:
            raise EvReplayUnavailable(str(error)) from error

    @staticmethod
    def _ev_identity(run: SimulationRun, tenant_id: UUID, site_id: UUID,
                       site_code: str) -> tuple[dict[str, Any], str]:
        identity = run.deterministic_identity
        basis = run.registered_basis
        if (basis is None or basis.tenant_id != str(tenant_id) or basis.site_record_id != str(site_id)
                or site_id_key(identity.site.site_id) != site_id_key(site_code)):
            raise EvRunNotFound(run.run_id)  # another tenant/Site's run, or no registered basis
        frozen = identity.profiles
        pair = ((frozen.model_profile_id, frozen.model_profile_version),
                (frozen.publication_profile_id, frozen.publication_profile_version))
        ev_pair = ((EV_CHARGER_MODEL.model_profile_id, EV_CHARGER_MODEL.model_profile_version),
                     (EV_PUBLICATION_PROFILE.publication_profile_id,
                      EV_PUBLICATION_PROFILE.publication_profile_version))
        if pair != ev_pair:
            raise EvRunNotFound(run.run_id)  # not an EV run
        observation_id, _, observation_version = EV_OBSERVATION_PROFILE.rpartition("/")
        if ((frozen.observation_profile_id, frozen.observation_profile_version)
                != (observation_id, int(observation_version)) or not identity.scenario.scenario_sha256):
            raise EvReplayUnavailable(f"run {run.run_id} has the EV pair without its frozen observation identity")
        return ({
            "model_profile": _profile(frozen.model_profile_id, frozen.model_profile_version),
            "publication_profile": _profile(frozen.publication_profile_id, frozen.publication_profile_version),
            "observation_profile": _profile(frozen.observation_profile_id, frozen.observation_profile_version),
        }, identity.scenario.scenario_sha256)

    @staticmethod
    def _linked_batch(publication: dict, tenant_id: UUID, site_id: UUID) -> str:
        if publication["b_id"] is None:
            raise EvReplayUnavailable(f"publication {publication['publication_id']} links a batch that is absent")
        if ((publication["b_tenant"], publication["b_site"]) != (str(tenant_id), str(site_id))
                or (publication["b_ext"], publication["b_sha"]) != (publication["p_ext"], publication["p_sha"])):
            raise EvReplayUnavailable(f"publication {publication['publication_id']} and its batch disagree")
        if publication["b_status"] != "COMPLETED":
            raise EvReplayUnavailable(f"batch {publication['b_ext']} is {publication['b_status']}, not completed")
        return publication["b_ext"]

    @staticmethod
    def _envelopes(publication: dict, dispositions: list[dict]) -> tuple[str, ...]:
        external_id = publication["b_ext"]
        try:
            batch = parse_canonical_batch_v2_text(publication["b_text"])
        except BatchRejected as error:
            raise EvReplayUnavailable(f"batch {external_id} text is not canonical Batch V2: {error}") from error
        if (batch.batch_id, batch.payload_sha256) != (external_id, publication["b_sha"]):
            raise EvReplayUnavailable(f"batch {external_id} text does not match its commitment")
        total = publication["b_total"]
        if len(batch.envelopes) != total or [d["ordinal"] for d in dispositions] != list(range(total)):
            raise EvReplayUnavailable(f"batch {external_id} dispositions are incomplete")
        return batch.envelopes
