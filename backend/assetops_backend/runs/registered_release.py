"""S4-05b phase 1: register a registered run's sealed batches as `REGISTERED_SIMULATION` before the release.

`tasks/S4-05-stored-demo-provenance.md` contract items 1-2 and the S4-05a carry N-L1: the
`run_attestation(run, stage)` + `register_run` call lives here, in a non-route module the Lab host composes
beside `release_registered`, never in `simulator_lab_api.py` or any `*_api.py` (rule 8 refuses designation
names in HTTP modules). The release itself is the gateway's: it uploads with its own credential, so a batch
that is not published first would be admitted with an unknown source.

Only public run identity reaches the publication (the run ID and its server-computed identity digest, plus
the gateway's exact sealed bytes); no private scenario truth crosses. A batch the gateway already moved past
`STAGED` was released earlier, so it is skipped (an identical retry of a release changes nothing); any
refusal raises `LabControlRefused("SOURCE_PUBLICATION_REFUSED")` and nothing is released.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from assetops_contracts.lab_projection import LabControlRefused

from assetops_backend.evidence.publication import PublicationLedger, PublicationRefused, register_run
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.source_publication import run_attestation

SOURCE_PUBLICATION_REFUSED = "SOURCE_PUBLICATION_REFUSED"


@dataclass(frozen=True)
class _UnreleasedStage:
    """The Stage view narrowed to the batches still `STAGED` (not yet released), read by attribute."""

    run_id: str
    status: str
    envelopes: tuple
    batches: tuple


class RegisteredRunPublisher:
    """Publishes a completed registered run's not-yet-released sealed batches before the gateway release."""

    def __init__(self, ledger: Callable[[], PublicationLedger]) -> None:
        self._ledger = ledger

    def publish(self, run: SimulationRun, stage: Any) -> tuple[str, ...]:
        """The publication IDs recorded (or identically re-read) for every still-`STAGED` batch of `run`."""
        pending = tuple(b for b in getattr(stage, "batches", ()) if getattr(b, "state", "STAGED") == "STAGED")
        if not pending:
            return ()
        view = _UnreleasedStage(run_id=str(getattr(stage, "run_id", "")), status=str(getattr(stage, "status", "")),
                                envelopes=tuple(getattr(stage, "envelopes", ())), batches=pending)
        try:
            registered = register_run(self._ledger(), run_attestation(run, view))
        except PublicationRefused as error:
            raise LabControlRefused(SOURCE_PUBLICATION_REFUSED, run.run_id, f"{error.kind}: {error.detail}") from None
        except Exception as error:  # noqa: BLE001 - an unreachable ledger publishes nothing, so nothing is released
            raise LabControlRefused(SOURCE_PUBLICATION_REFUSED, run.run_id,
                                    f"LEDGER_UNAVAILABLE: {type(error).__name__}") from None
        return tuple(str(r.publication_id) for r in registered)


def publisher_for(database_url: str | None) -> RegisteredRunPublisher:
    """The composed publisher. Without a database every release is refused (fail closed), never unpublished."""
    def ledger() -> PublicationLedger:
        if not database_url:
            raise PublicationRefused("LEDGER_UNAVAILABLE", "no product database is configured")
        from assetops_backend.evidence.composition import build_evidence_ledger

        return build_evidence_ledger(database_url)

    return RegisteredRunPublisher(ledger)


__all__ = ["RegisteredRunPublisher", "SOURCE_PUBLICATION_REFUSED", "publisher_for"]
