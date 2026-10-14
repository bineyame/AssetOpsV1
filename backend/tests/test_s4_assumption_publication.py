"""S4-02a phase 1: pure publication planning and the human write route's refusals (no database).

Packet `tasks/S4-02a-site-assumptions.md` item 2. The PostgreSQL behaviour (series lock, server instant,
retry, concurrency, triggers) is in `test_s4_assumptions_postgres.py`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.financial_api import build_financial_assumption_router
from assetops_backend.financials.assumptions import (
    Current,
    NewAssignment,
    Publication,
    PublicationRefused,
    parse_value,
    plan_assignments,
    validate,
)

BACKEND = Path(__file__).resolve().parents[1]


def _t(month: int, year: int = 2026) -> datetime:
    return datetime(year, month, 1, tzinfo=timezone.utc)


NOW = datetime(2026, 10, 13, 12, tzinfo=timezone.utc)
A, B = uuid4(), uuid4()


def refused(work) -> PublicationRefused:
    with pytest.raises(PublicationRefused) as caught:
        work()
    return caught.value


class TestPlan:
    def test_initial_on_empty_series_and_into_a_gap(self) -> None:
        assert plan_assignments("INITIAL", _t(1), None, NOW, []).insert == (NewAssignment(None, _t(1), None),)
        cur = [Current(A, A, _t(1), _t(3))]
        assert plan_assignments("INITIAL", _t(3), _t(5), NOW, cur).close == ()

    def test_initial_overlapping_current_is_409(self) -> None:
        error = refused(lambda: plan_assignments("INITIAL", _t(2), None, NOW, [Current(A, A, _t(1), None)]))
        assert (error.status, error.code) == (409, "INITIAL_OVERLAPS_CURRENT")

    def test_succession_truncates_the_open_ended_assignment(self) -> None:
        plan = plan_assignments("SUCCESSION", _t(1, 2027), None, NOW, [Current(A, A, _t(1), None)])
        assert plan.close == (A,)
        assert plan.insert == (NewAssignment(A, _t(1), _t(1, 2027)), NewAssignment(None, _t(1, 2027), None))

    def test_succession_negatives_are_409(self) -> None:
        open_v1 = [Current(A, A, _t(1), None)]
        assert refused(lambda: plan_assignments("SUCCESSION", _t(9), None, NOW, open_v1)).code == "SUCCESSION_NOT_FUTURE"
        two = [Current(A, A, _t(1), _t(1, 2027)), Current(B, B, _t(1, 2027), None)]
        error = refused(lambda: plan_assignments("SUCCESSION", _t(11), None, NOW, two))
        assert (error.status, error.code) == (409, "SUCCESSION_OVERLAP_NOT_PERMITTED")
        bounded = [Current(A, A, _t(1), _t(1, 2028))]
        assert refused(lambda: plan_assignments("SUCCESSION", _t(1, 2027), None, NOW, bounded)).code == \
            "SUCCESSION_OVERLAP_NOT_PERMITTED"
        assert refused(lambda: plan_assignments("SUCCESSION", _t(1, 2027), None, NOW, [])).code == \
            "SUCCESSION_NOTHING_TO_SUCCEED"

    def test_middle_correction_keeps_both_remainders_on_the_old_revision(self) -> None:
        cur = [Current(A, A, _t(1), _t(1, 2027)), Current(B, B, _t(1, 2027), None)]
        plan = plan_assignments("CORRECTION", _t(6), _t(7), NOW, cur)
        assert plan.close == (A,)
        assert plan.insert == (NewAssignment(A, _t(1), _t(6)), NewAssignment(A, _t(7), _t(1, 2027)),
                               NewAssignment(None, _t(6), _t(7)))

    def test_correction_spanning_two_assignments(self) -> None:
        cur = [Current(A, A, _t(1), _t(5)), Current(B, B, _t(5), None)]
        plan = plan_assignments("CORRECTION", _t(4), _t(6), NOW, cur)
        assert set(plan.close) == {A, B}
        assert plan.insert == (NewAssignment(A, _t(1), _t(4)), NewAssignment(B, _t(6), None),
                               NewAssignment(None, _t(4), _t(6)))

    def test_correction_negatives(self) -> None:
        assert refused(lambda: plan_assignments("CORRECTION", _t(1, 2027), None, NOW,
                                                [Current(A, A, _t(1), None)])).code == "CORRECTION_NOT_BACKDATED_OR_BOUNDED"
        assert refused(lambda: plan_assignments("CORRECTION", _t(2), _t(3), NOW, [])).code == \
            "CORRECTION_NOTHING_TO_CORRECT"


def publication(**overrides) -> Publication:
    base = dict(assumption_key="diesel_price_per_litre", currency="USD", value=Decimal("1.25"),
                basis="AUTHORED_ESTIMATE", source_reference="test", valid_from=_t(1), valid_to=None,
                change_kind="INITIAL", correction_reason=None, expected_prior_revision_id=None,
                idempotency_key="k", channel="SYSTEM_CLI")
    return Publication(**{**base, **overrides})


class TestValidation:
    @pytest.mark.parametrize("overrides,code", [
        ({"change_kind": "CORRECTION"}, "CORRECTION_REASON_REQUIRED"),
        ({"change_kind": "CORRECTION", "correction_reason": "  "}, "CORRECTION_REASON_REQUIRED"),
        ({"value": Decimal("-0.01")}, "VALUE_NEGATIVE"),
        ({"value": Decimal("NaN")}, "VALUE_NOT_FINITE"),
        ({"value": Decimal("Infinity")}, "VALUE_NOT_FINITE"),
        ({"value": 1.25}, "VALUE_NOT_FINITE"),
        ({"basis": "SCENARIO"}, "BASIS_NOT_OPERATIONAL"),
        ({"currency": "usd"}, "CURRENCY_NOT_ISO"),
        ({"assumption_key": "maintenance_rate"}, "UNKNOWN_ASSUMPTION_KEY"),
        ({"valid_from": datetime(2026, 1, 1)}, "VALIDITY_NOT_ZONED"),
        ({"valid_to": _t(1)}, "VALIDITY_EMPTY"),
        ({"source_reference": " "}, "SOURCE_REQUIRED"),
        ({"channel": "HUMAN_API"}, "CHANNEL_NOT_SYSTEM"),
        ({"correction_reason": "why"}, "REASON_ONLY_FOR_CORRECTION"),
    ])
    def test_invalid_publication_is_422(self, overrides, code) -> None:
        error = refused(lambda: validate(publication(**overrides)))
        assert (error.status, error.code) == (422, code)

    def test_value_is_an_authored_decimal_string(self) -> None:
        assert str(parse_value("1.250")) == "1.250"
        assert refused(lambda: parse_value(1.25)).code == "VALUE_NOT_AUTHORED_DECIMAL"
        assert refused(lambda: parse_value("one")).code == "VALUE_NOT_DECIMAL"


SITE = ("KOBO-001", uuid4(), uuid4())


def client(access=None, known=True) -> TestClient:
    app = FastAPI()
    scope = (lambda code: SITE if known and code == "KOBO-001" else None)
    app.include_router(build_financial_assumption_router(scope) if access is None
                       else build_financial_assumption_router(scope, access=access))
    return TestClient(app)


ROUTE = "/api/sites/KOBO-001/financial-assumptions"
CLEAN = {"value": "1.30", "currency": "USD"}


class TestHumanWriteRouteHasNoSuccessPath:
    def test_default_access_is_401_before_anything_else(self) -> None:
        for body in (CLEAN, {"author_id": str(uuid4())}, {"actor": "me"}):
            response = client().post(ROUTE, json=body)
            assert response.status_code == 401
            assert response.json()["detail"]["code"] == "UNAUTHENTICATED"
        assert client().post("/api/sites/NOPE/financial-assumptions", json=CLEAN).status_code == 401

    @pytest.mark.parametrize("refusal", [None, 403, 404])
    def test_body_actor_or_author_is_422_before_403_404(self, refusal) -> None:
        for body in ({"author_id": "x"}, {"actor_kind": "SYSTEM"}, {"price": {"Author": "x"}},
                     {"authorization_basis": "mine"}):
            response = client(lambda r, s: refusal).post(ROUTE, json=body)
            assert response.status_code == 422, body
            assert response.json()["detail"]["code"] == "CLIENT_ACTOR_FORBIDDEN"

    def test_scope_refusals_from_the_injected_seam(self) -> None:
        assert client(lambda r, s: 403).post(ROUTE, json=CLEAN).json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
        assert client(lambda r, s: 404).post(ROUTE, json=CLEAN).status_code == 404
        assert client(lambda r, s: None, known=False).post(ROUTE, json=CLEAN).status_code == 404

    def test_an_admitted_request_without_a_verified_human_is_still_401(self) -> None:
        response = client(lambda r, s: None).post(ROUTE, json=CLEAN)
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "HUMAN_PRINCIPAL_REQUIRED"

    def test_the_route_never_uses_development_access(self) -> None:
        source = (BACKEND / "assetops_backend" / "financial_api.py").read_text(encoding="utf-8")
        code = source.split('"""', 2)[2]  # everything after the module docstring
        assert "development_access" not in code and "finding_api" not in code

    def test_the_product_app_refuses_the_write(self, monkeypatch) -> None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from assetops_backend.main import create_app
        response = TestClient(create_app()).post(ROUTE, json=CLEAN)
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "UNAUTHENTICATED"
