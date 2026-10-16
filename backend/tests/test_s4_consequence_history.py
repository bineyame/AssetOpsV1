"""S4-08 Site consequence history: service and route over an in-memory store (no database).

Classification at a cutoff (incl. a skewed application-clock FindingRevision and the same-instant boundary),
recorded-amount dispositions, cursor fence/scope refusals, equal-timestamp paging, the zero state, route order
and scope refusals. The real snapshot, fence under interleaving and joins are in the `_postgres` file.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.consequence_history_api import build_consequence_history_router
from assetops_backend.financial_read_api import build_financial_read_router
from assetops_backend.financials import consequence_history as ch

UTC = timezone.utc
T0 = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
TENANT, SITE = uuid4(), uuid4()
POSITIVE = {"state": "AUTHORED_DEMONSTRATION"}


def at(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


class Store:
    """The adapter's contract over lists: cutoff filter, fence over all in-scope rows, keyset page."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.frs: list[dict] = []
        self.links: dict = {}
        self.calls: list = []
        self.fail = False

    def fr(self, finding: UUID, no: int, created: datetime, title: str = "Generator ran") -> UUID:
        rid = uuid4()
        self.frs.append({"id": rid, "finding_id": finding, "revision_no": no, "created_at": created, "title": title,
                         "episode_start": at(-600), "episode_end": at(-500)})
        return rid

    def add(self, finding: UUID, fr: UUID, no: int, recorded: datetime, state: str = "PRICED",
            price: UUID | None = None, tech: str = "a", rid: UUID | None = None, link: bool = True) -> UUID:
        cid = rid or uuid4()
        prior = next((r["id"] for r in reversed(self.rows) if r["finding_revision_id"] == fr), None)
        priced = state == "PRICED"
        price = price or (uuid4() if priced else None)
        self.rows.append({
            "id": cid, "finding_id": finding, "finding_revision_id": fr, "revision_no": no,
            "prior_consequence_revision_id": prior, "recorded_at": recorded, "window_start": at(-600),
            "window_end": at(-500), "state": state, "quantity_state": "AVAILABLE", "quantity_reason": None,
            "quantity_unit": "L", "quantity_high": Decimal("12.65"), "price_reason": None if priced else "NO_PRICE",
            "price_revision_id": price, "price_value": Decimal("1.25") if priced else None,
            "price_currency": "USD" if priced else None, "currency": "USD" if priced else None,
            "amount_low": Decimal(0) if priced else None, "amount_high": Decimal("15.8125") if priced else None,
            "technical_input_sha256": tech})
        if priced and link:
            self.links[cid] = [{"consequence_revision_id": cid, "assumption_revision_id": price,
                                "assignment_id": uuid4(), "role": "PRICE", "a_tenant_id": TENANT, "a_site_id": SITE,
                                "a_revision_id": price, "valid_from": at(-9999), "valid_to": None,
                                "recorded_from": at(-9999), "recorded_to": at(30)}]
        return cid

    def site_history(self, tenant_id, site_id, cutoff, after, limit):
        if self.fail:
            raise RuntimeError("store down")
        self.calls.append((cutoff, after, limit))
        cut = cutoff or at(10_000)
        scoped = [r for r in self.rows if r["recorded_at"] <= cut]
        key = lambda r: (r["recorded_at"], r["id"])  # noqa: E731
        ordered = sorted(scoped, key=key, reverse=True)
        top = max(scoped, key=key, default=None)
        page = [r for r in ordered if after is None or key(r) < (after[0], after[1])][:limit + 1]
        fids = {r["finding_id"] for r in page}
        frs = []
        for fr in self.frs:
            if fr["finding_id"] in fids:
                mine = [r for r in scoped if r["finding_revision_id"] == fr["id"]]
                best = max(mine, key=key, default=None)
                frs.append({**fr, "latest_consequence_id": None if best is None else best["id"]})
        return {"cutoff": cut, "fence": {"count": len(scoped), "max_recorded_at": None if top is None
                                         else top["recorded_at"], "max_id": None if top is None else str(top["id"])},
                "page": page, "finding_revisions": frs, "links": self.links,
                "priors": {r["id"]: r for r in self.rows}}


class Provenance:
    def __init__(self, state="AUTHORED_DEMONSTRATION"):
        self.state, self.by = state, {}

    def consequence_revision(self, tenant_id, site_id, cid):
        return {"state": self.by.get(cid, self.state), "finding_revision_id": uuid4()}


def read(store, cutoff=None, limit=25, after=None, source_open=True, provenance=None):
    svc = ch.ConsequenceHistoryService(store, provenance=provenance or Provenance())
    req = ch.parse_request(None if cutoff is None else ch.instant(cutoff), after, str(limit))
    return svc.read(TENANT, SITE, "KOBO-001", req, source_open=source_open, source_reason="closed",
                    access_basis="dev")


def states(body):
    return {r["consequence_revision_id"]: r["at_cutoff"] for r in body["rows"]}


class TestClassification:
    def test_latest_finding_revision_demotes_older_chain_heads(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        c1 = s.add(f, r1, 1, at(1))
        c2 = s.add(f, r1, 2, at(2), tech="a")
        r2 = s.fr(f, 2, at(3))
        c3 = s.add(f, r2, 1, at(4))
        assert states(read(s, at(2))) == {str(c1): "HISTORICAL_AT_CUTOFF", str(c2): "CURRENT_AT_CUTOFF"}
        # At the instant r2 exists without a consequence: no row of the Finding is current.
        assert set(states(read(s, at(3))).values()) == {"HISTORICAL_AT_CUTOFF"}
        assert states(read(s, at(4)))[str(c3)] == "CURRENT_AT_CUTOFF"
        assert states(read(s, at(4)))[str(c2)] == "HISTORICAL_AT_CUTOFF"

    def test_cutoff_immediately_before_at_and_after_each_recorded_timestamp(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        c1 = s.add(f, r1, 1, at(1))
        c2 = s.add(f, r1, 2, at(2))
        eps = timedelta(microseconds=1)
        assert read(s, at(1) - eps)["rows"] == []
        assert states(read(s, at(1))) == {str(c1): "CURRENT_AT_CUTOFF"}
        assert states(read(s, at(2) - eps)) == {str(c1): "CURRENT_AT_CUTOFF"}
        assert states(read(s, at(2))) == {str(c1): "HISTORICAL_AT_CUTOFF", str(c2): "CURRENT_AT_CUTOFF"}
        assert states(read(s, at(2) + eps)) == states(read(s, at(2)))

    def test_skewed_created_at_later_than_consequence_still_qualifies(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        c1 = s.add(f, r1, 1, at(1))
        r2 = s.fr(f, 2, at(9))  # application clock ahead of the database clock
        c2 = s.add(f, r2, 1, at(5))
        assert states(read(s, at(5))) == {str(c1): "HISTORICAL_AT_CUTOFF", str(c2): "CURRENT_AT_CUTOFF"}
        assert states(read(s, at(4))) == {str(c1): "CURRENT_AT_CUTOFF"}

    def test_same_instant_boundary_for_created_at_and_recorded_at(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        c1 = s.add(f, r1, 1, at(1))
        s.fr(f, 2, at(2))  # created exactly at the cutoff: qualifies, has no consequence
        assert states(read(s, at(2))) == {str(c1): "HISTORICAL_AT_CUTOFF"}
        assert states(read(s, at(2) - timedelta(microseconds=1))) == {str(c1): "CURRENT_AT_CUTOFF"}


class TestMoney:
    def test_no_current_amount_at_any_cutoff_even_when_every_gate_passes(self):
        s, f = Store(), uuid4()
        s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        for body in (read(s), read(s, at(1))):
            assert body["current_amount_shown"] is False
            row = body["rows"][0]
            assert row["at_cutoff"] == "CURRENT_AT_CUTOFF"
            assert row["recorded_amount"] == {"disposition": "SHOWN", "label": ch.RECORDED_LABEL,
                                              "amount": {"low": "0.00", "high": "15.82", "currency": "USD"},
                                              "is_current_amount": False}
        assert read(s)["cutoff"]["selected_by"] == "SERVER_DEFAULT"

    def test_closed_source_hides_even_a_recorded_amount_and_keeps_the_row(self):
        s, f = Store(), uuid4()
        s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        body = read(s, at(1), source_open=False)
        assert body["source_gate"] == {"open": False, "reason": "closed"}
        assert [r["recorded_amount"]["disposition"] for r in body["rows"]] == ["SOURCE_CLOSED"]
        assert body["rows"][0]["recorded_amount"]["amount"] is None

    @pytest.mark.parametrize("state", ["MIXED", "UNKNOWN"])
    def test_mixed_or_unknown_source_withholds_the_amount(self, state):
        s, f = Store(), uuid4()
        s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        row = read(s, at(1), provenance=Provenance(state))["rows"][0]
        assert row["recorded_amount"]["disposition"] == "MIXED_OR_UNKNOWN_SOURCE"
        assert row["recorded_amount"]["amount"] is None and row["source_provenance"]["state"] == state

    def test_unresolvable_provenance_is_unknown_and_withheld(self):
        s, f = Store(), uuid4()
        s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        svc = ch.ConsequenceHistoryService(s, provenance=None)
        body = svc.read(TENANT, SITE, "K", ch.parse_request(None, None, None), source_open=True, source_reason=None,
                        access_basis="dev")
        assert body["rows"][0]["recorded_amount"]["disposition"] == "MIXED_OR_UNKNOWN_SOURCE"

    def test_unpriced_version_is_listed_with_typed_missing_price_never_zero(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        s.add(f, r1, 1, at(1), state="UNPRICED")
        s.add(f, r1, 2, at(2), tech="a")
        rows = read(s, at(2))["rows"]
        unpriced = rows[1]
        assert unpriced["price"]["state"] == "NO_PRICE_LINK" and unpriced["price"]["price_revision_id"] is None
        assert unpriced["recorded_amount"] == {"disposition": "UNPRICED", "label": None, "amount": None,
                                               "is_current_amount": False}
        assert rows[0]["change_from_prior"] == "PRICE_ONLY"

    def test_broken_or_foreign_price_link_is_typed_never_substituted(self):
        s, f = Store(), uuid4()
        cid = s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        s.links[cid][0]["a_site_id"] = uuid4()
        row = read(s, at(1))["rows"][0]
        assert row["price"]["state"] == "LINEAGE_INCONSISTENT"
        assert row["recorded_amount"]["disposition"] == "LINEAGE_INCONSISTENT"
        s.links[cid] = []
        assert read(s, at(1))["rows"][0]["price"]["state"] == "LINEAGE_INCONSISTENT"

    def test_assignment_recorded_close_after_the_cutoff_is_not_shown(self):
        s, f = Store(), uuid4()
        s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        assert read(s, at(1))["rows"][0]["price"]["assignments"][0]["recorded"]["to"] is None
        assert read(s, at(40))["rows"][0]["price"]["assignments"][0]["recorded"]["to"] == ch.instant(at(30))


class TestPaging:
    def test_equal_timestamps_page_without_duplicate_or_skip(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        ids = {str(s.add(f, r1, i + 1, at(1))) for i in range(5)}
        seen, after = [], None
        while True:
            body = read(s, at(1), limit=2, after=after)
            seen += [r["consequence_revision_id"] for r in body["rows"]]
            after = body["next_cursor"]
            if after is None:
                break
        assert len(seen) == 5 and set(seen) == ids
        assert seen == sorted(seen, reverse=True)

    def test_final_page_has_no_cursor_and_empty_set_says_so(self):
        s = Store()
        body = read(s, at(1))
        assert body["rows"] == [] and body["next_cursor"] is None and body["zero_statement"]

    def test_late_row_stamped_before_the_cutoff_refuses_the_next_page(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        for i in range(3):
            s.add(f, r1, i + 1, at(i + 1))
        first = read(s, at(10), limit=2)
        s.add(f, r1, 4, at(0.5))  # a late commit stamped before the cutoff
        with pytest.raises(ch.HistoryBasisChanged) as refused:
            read(s, at(10), limit=2, after=first["next_cursor"])
        assert refused.value.detail["reason"] == "FENCE_CHANGED" and refused.value.detail["rows"] is None
        assert refused.value.status == 409

    def test_row_stamped_after_the_cutoff_stays_excluded_and_keeps_the_fence(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        for i in range(3):
            s.add(f, r1, i + 1, at(i + 1))
        first = read(s, at(10), limit=2)
        s.add(f, r1, 4, at(11))
        second = read(s, at(10), limit=2, after=first["next_cursor"])
        assert len(second["rows"]) == 1 and second["next_cursor"] is None

    def test_cursor_scope_is_bound(self):
        s, f = Store(), uuid4()
        r1 = s.fr(f, 1, at(0))
        for i in range(3):
            s.add(f, r1, i + 1, at(i + 1))
        cursor = read(s, at(10), limit=2)["next_cursor"]
        with pytest.raises(ch.HistoryBasisChanged) as refused:
            read(s, at(9), limit=2, after=cursor)
        assert refused.value.detail["changed_fields"] == ["recorded_at"]
        with pytest.raises(ch.HistoryBasisChanged):
            read(s, at(10), limit=3, after=cursor)

    @pytest.mark.parametrize("bad", ["x", "eyJ2IjoxfQ", "!!!"])
    def test_tampered_cursor_is_400(self, bad):
        with pytest.raises(ch.InvalidHistoryCursor) as refused:
            ch.parse_request("2026-10-10T09:00:00Z", bad, None)
        assert refused.value.status == 400

    def test_cutoff_must_be_zoned_and_a_cursor_needs_its_cutoff(self):
        with pytest.raises(ch.InvalidHistoryRequest):
            ch.parse_request("2026-10-10T09:00:00", None, None)
        with pytest.raises(ch.InvalidHistoryRequest):
            ch.parse_request(None, ch.encode_cursor({"v": 1}), None)
        with pytest.raises(ch.InvalidHistoryRequest):
            ch.parse_request(None, None, "101")


def app(store, *, found=True, gate=lambda c, t, s: (True, "")):
    a = FastAPI()
    scope = (lambda code: (code, TENANT, SITE) if found and code == "KOBO-001" else None)
    a.include_router(build_consequence_history_router(
        ch.ConsequenceHistoryService(store, provenance=Provenance()), scope, (RuntimeError,), gate=gate))
    a.include_router(build_financial_read_router(None, scope))
    return TestClient(a)


class TestRoute:
    def test_route_is_not_taken_for_a_price_revision_and_returns_the_exact_cutoff(self):
        s, f = Store(), uuid4()
        s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        cut = "2026-10-10T09:01:00.123456+00:00"
        body = app(s).get("/api/sites/KOBO-001/financial-assumptions/consequences",
                          params={"recorded_at": cut}).json()
        assert body["cutoff"]["recorded_at"] == cut and body["current_amount_shown"] is False
        assert body["links"]["api_prices_at_cutoff"].endswith("recorded_at=2026-10-10T09%3A01%3A00.123456%2B00%3A00")

    def test_scope_refusals_happen_before_lookup(self):
        s = Store()
        r = app(s, found=False).get("/api/sites/OTHER/financial-assumptions/consequences")
        assert r.status_code == 404 and s.calls == []
        r = app(s).get("/api/sites/KOBO-001/financial-assumptions/consequences", params={"after": "zz",
                                                                                         "recorded_at": "2026-10-10T09:00:00Z"})
        assert r.status_code == 400 and r.json()["detail"]["rows"] is None and s.calls == []
        r = app(s).get("/api/sites/KOBO-001/financial-assumptions/consequences",
                       params={"recorded_at": "2026-10-10T09:00:00"})
        assert r.status_code == 422 and r.json()["detail"]["code"] == "INSTANT_NOT_ZONED"

    def test_store_failure_is_unavailable_not_empty(self):
        s = Store()
        s.fail = True
        r = app(s).get("/api/sites/KOBO-001/financial-assumptions/consequences")
        assert r.status_code == 503 and r.json()["detail"]["code"] == "CONSEQUENCE_HISTORY_UNAVAILABLE"

    def test_closed_gate_lists_rows_without_amounts(self):
        s, f = Store(), uuid4()
        s.add(f, s.fr(f, 1, at(0)), 1, at(1))
        body = app(s, gate=lambda c, t, x: (False, "closed")).get(
            "/api/sites/KOBO-001/financial-assumptions/consequences").json()
        assert len(body["rows"]) == 1 and body["rows"][0]["recorded_amount"]["disposition"] == "SOURCE_CLOSED"
