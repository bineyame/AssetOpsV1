"""W4-03 final review L2/L3 and uF 5 without a database: the Alternative command instant is read after the Finding
lock, and the single retry after a write race returns the exact prior body, refuses a changed key, and maps an
exhausted retry (or a race in a scenario correction) to 503 `DECISION_STORE_UNAVAILABLE`, never an uncaught 500."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from assetops_backend.mini_decisions import alternatives as alt
from assetops_backend.mini_decisions import scenarios as scn
from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal, DecisionRefused
from assetops_backend.mini_decisions.store import MiniDecisionWriteRefused
from assetops_backend.work import model as work

PRINCIPAL_ID = "service:w403-fixture"
ATTESTATION = "service=w403-fixture;job=final-review;rule=w403/1"
T, S = uuid4(), uuid4()
WHO = DecisionPrincipal("SERVICE", PRINCIPAL_ID, T, S, GRANT_PREFIX + PRINCIPAL_ID)
FINDING, FREV = str(uuid4()), str(uuid4())
AT = datetime(2026, 10, 9, tzinfo=timezone.utc)


def alt_body(key: str = "w403-race-0001", reason: str = "Not established.") -> dict[str, Any]:
    return {"schema_version": "mini-alternative-command-1", "idempotency_key": key,
            "actor": {"kind": "SERVICE", "id": PRINCIPAL_ID, "attestation": ATTESTATION},
            "finding_revision_id": FREV, "alternative_key": "POLICY", "supersedes_revision_id": None,
            "explanation": "A policy may explain the run.", "evidence_summary": "The policy record.",
            "cited_accepted_evidence_ids": [], "missing_evidence_reason": "No counterfactual record.",
            "disposition": "PLAUSIBLE", "reason": reason}


class FakeStore:
    """`races` transactions raise the store's write refusal (an insert IntegrityError); later ones run `write`."""

    def __init__(self, races: int, prior_sha: str | None = None) -> None:
        self.races, self.prior_sha, self.calls = races, prior_sha, []

    @contextmanager
    def transaction(self):
        if self.races:
            self.races -= 1
            raise MiniDecisionWriteRefused("duplicate key value violates unique constraint")
        yield object()

    def db_now(self, c):
        self.calls.append("now")
        return AT

    def finding_root(self, c, tenant_id, site_id, root, lock=False):
        self.calls.append("lock" if lock else "read")
        return {"id": root, "domain": "mini_grid"}

    def alternative_revisions(self, c, tenant_id, site_id, root):
        if self.prior_sha is None:
            return []
        return [{"id": uuid4(), "idempotency_key": "w403-race-0001", "payload_sha256": self.prior_sha,
                 "finding_revision_id": FREV, "alternative_key": "POLICY", "version_no": 1,
                 "supersedes_revision_id": None, "created_at": AT}]

    def finding_revisions(self, c, tenant_id, site_id, root):
        return []

    def lock_scenario(self, c, tenant_id, site_id, root_id):
        raise AssertionError("not reached: every transaction races")


def sha_of(body: dict[str, Any]) -> str:
    return work.command_sha256({"site_id": str(S), "route": alt.ROUTE, "root_id": FINDING}, alt.parse_command(body))


def test_l2_command_instant_is_read_after_the_finding_lock() -> None:
    store = FakeStore(races=0)
    with pytest.raises(DecisionRefused) as refused:
        alt.AlternativeService(store, None).create(T, S, WHO, FINDING, alt_body())  # type: ignore[arg-type]
    assert refused.value.code == "DECISION_LINK_SCOPE_INVALID"  # no such revision in the fake
    assert store.calls == ["lock", "now"]


def test_u_f5_single_retry_exact_body_changed_key_and_exhausted() -> None:
    body = alt_body()
    # A same-key race: the retry rechecks the key in a new transaction and answers the exact prior 200 body.
    status, out = alt.AlternativeService(FakeStore(1, sha_of(body)), None).create(  # type: ignore[arg-type]
        T, S, WHO, FINDING, body)
    assert status == 200 and out["schema_version"] == "mini-alternative-write-1" and out["finding_id"] == FINDING
    # The racing row carried different content under the key: 409, not a second write.
    with pytest.raises(DecisionRefused) as changed:
        alt.AlternativeService(FakeStore(1, sha_of(alt_body(reason="Other."))), None).create(  # type: ignore[arg-type]
            T, S, WHO, FINDING, body)
    assert (changed.value.status, changed.value.code) == (409, "DECISION_DUPLICATE_KEY")
    # A second race after the single retry is 503, never the store's raw refusal.
    with pytest.raises(DecisionRefused) as exhausted:
        alt.AlternativeService(FakeStore(2), None).create(T, S, WHO, FINDING, body)  # type: ignore[arg-type]
    assert (exhausted.value.status, exhausted.value.code) == (503, "DECISION_STORE_UNAVAILABLE")


def test_l3_scenario_correction_race_is_503() -> None:
    correction = {"schema_version": "mini-scenario-command-1", "idempotency_key": "w403-race-fix1",
                  "actor": {"kind": "SERVICE", "id": PRINCIPAL_ID, "attestation": ATTESTATION},
                  "name": "Tariff", "kind": "TARIFF_ONLY",
                  "assumptions": [{"key": "tariff_per_kwh", "value": "0.3", "unit": "USD/kWh", "source": "Authored"}],
                  "pinned_selection": [], "narrative": "Tariff only.", "supersedes_revision_id": str(uuid4()),
                  "correction_reason": "Fix."}
    service = scn.ScenarioService(FakeStore(1), None)  # type: ignore[arg-type]
    with pytest.raises(DecisionRefused) as raced:
        service.correct(T, S, WHO, str(uuid4()), correction)
    assert (raced.value.status, raced.value.code) == (503, "DECISION_STORE_UNAVAILABLE")
