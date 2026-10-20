"""W2-07 commit 2: the pure EV gross tariff scenario and the EV money worker's refusal path (no database).

`.agent/W2-07-build-spec.md` q1 R5/R6 precedence and composition tables, q3 R8 (pending is a retryable FAILED
attempt, never a stored revision) and C1-C5. The Postgres replay vectors and the named R8 settlement regression are
in `test_w207_ev_money_postgres.py`.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from assetops_backend.financials import ev_money as em
from assetops_backend.financials.ev_recompute import ERROR_PENDING, EvConsequenceWorker

T0 = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(hours=1)
SIM = "REGISTERED_SIMULATION"
C1, C2 = "c1" + "0" * 34, "c2" + "0" * 34
TARIFF = em.TariffAssignment("t1", Decimal("0.27775"), "KES", em.TARIFF_UNIT, T0, T1, T1 + timedelta(days=14))


def at(minute: int) -> datetime:
    return T0 + timedelta(minutes=minute)


def session(rid: str, state: str = "COMPLETED", kwh: str | None = "10.000", unknown: int | None = 0):
    return em.SessionHead(rid, rid[0] * 64, state, None if kwh is None else Decimal(kwh), unknown)


def meter(rid: str, eid: str, a: int, b: int, kwh: str, connector: str = C1, use: str = "SUPPORT",
          reason: str | None = None) -> em.MeterInterval:
    return em.MeterInterval(rid, connector, eid, eid[0] * 64, at(a), at(b), Decimal(kwh), use, reason)


def basis(sessions, intervals, tariffs=(TARIFF,), gate=SIM, stored=SIM) -> em.EvMoneyBasis:
    return em.EvMoneyBasis("tenant", "site", T0, T1, at(65), "assessment", stored, gate, tuple(sessions),
                           tuple(intervals), tuple(tariffs))


A = session("a" * 36)
B_INCOMPLETE = session("b" * 36, "INCOMPLETE", "5.000", 300)
A_ROWS = [meter(A.revision_id, "e1", 0, 10, "5.000"), meter(A.revision_id, "e2", 10, 20, "5.000")]
B_ROWS = [meter(B_INCOMPLETE.revision_id, "e3", 30, 40, "5.000", C2)]


def test_exact_selected_session_basis_and_support_eligibility() -> None:
    # One complete session priced exactly; quantity and amount are exact Decimals, no rounding.
    one = em.derive(basis([A], A_ROWS))
    assert (one.state, one.reason, one.quantity_kwh, one.amount, one.currency) == (
        "ESTIMATED", "ELIGIBLE_COMPLETE_INTERVALS", Decimal("10.000"), Decimal("2.77750000"), "KES")
    assert str(one.amount) == "2.77750000" and one.tariff_revision_id == "t1" and one.tariff_value == Decimal("0.27775")
    assert one.sessions == ((A.revision_id, Decimal("10.000")),) and one.evidence_ids == ("e1", "e2")
    assert one.overlap_group == "ev:" + em.sha256_canonical(["tenant", "site", em.iso(T0), em.iso(T1), "t1"])

    # C1/C2: the technical hash rows are every selected session's SUPPORT interval (sorted, deduplicated) with the
    # run cutoff; R6 eligible + incomplete prices only the eligible subset and links only it.
    mixed = em.derive(basis([A, B_INCOMPLETE], A_ROWS + B_ROWS))
    assert (mixed.state, mixed.quantity_kwh, mixed.amount) == ("ESTIMATED", Decimal("10.000"), Decimal("2.77750000"))
    assert mixed.sessions == one.sessions and mixed.evidence_ids == ("e1", "e2")
    rows = em.technical_rows(basis([A, B_INCOMPLETE], A_ROWS + B_ROWS))
    assert [r[2] for r in rows] == ["e1", "e2", "e3"] and rows[0][1] == A.basis_sha256
    assert mixed.technical_input_sha256 == em.sha256_canonical([em.iso(T0), em.iso(T1), em.iso(at(65)), rows])
    assert mixed.technical_input_sha256 != one.technical_input_sha256  # the excluded partial ID stays in the hash
    assert mixed.basis_sha256 == em.sha256_canonical([mixed.technical_input_sha256, "t1", Decimal("0.27775"), "KES",
                                                      SIM, SIM, ["assessment"], "ev-gross-tariff/1"])

    # R5: incomplete only -> UNPRICED/INCOMPLETE_ENERGY even with no tariff; quantity, amount, currency null.
    for tariffs in ((TARIFF,), ()):
        k = em.derive(basis([B_INCOMPLETE], B_ROWS, tariffs))
        assert (k.state, k.reason, k.quantity_kwh, k.amount, k.currency, k.sessions, k.evidence_ids) == (
            "UNPRICED", "INCOMPLETE_ENERGY", None, None, None, (), ())
    # A missing-meter COMPLETED head (uncovered seconds) is not eligible either.
    gap = session("c" * 36, "COMPLETED", "25.000", 300)
    assert em.derive(basis([gap], [meter(gap.revision_id, "e9", 0, 50, "25.000")])).reason == "INCOMPLETE_ENERGY"

    # R6 eligible + incomplete with no tariff / with a gap: eligible kWh retained, unpriced.
    k = em.derive(basis([A, B_INCOMPLETE], A_ROWS + B_ROWS, ()))
    assert (k.state, k.reason, k.quantity_kwh, k.amount, k.currency) == (
        "UNPRICED", "TARIFF_MISSING", Decimal("10.000"), None, None)
    short = em.TariffAssignment("t1", Decimal("0.27775"), "KES", em.TARIFF_UNIT, T0, at(15), T1)
    assert em.derive(basis([A], A_ROWS, (short,))).reason == "PRICE_GAP_OR_CHANGE"  # e2 crosses valid_to
    # C3: no assignment covering any eligible interval is TARIFF_MISSING even if a Site tariff exists elsewhere.
    later = em.TariffAssignment("t9", Decimal("0.27775"), "KES", em.TARIFF_UNIT, at(30), T1, T1)
    assert em.derive(basis([A], A_ROWS, (later,))).reason == "TARIFF_MISSING"

    # R6 eligible + contradictory session, duplicate accepted interval ID, overlapping intervals: WITHHELD, no subset.
    bad = session("d" * 36, "CONTRADICTORY", None, None)
    for case in (basis([A, bad], A_ROWS), basis([A, session("e" * 36)], A_ROWS + [meter("e" * 36, "e1", 0, 10, "5.000")]),
                 basis([A], A_ROWS + [meter(A.revision_id, "e7", 5, 15, "1.000")]),
                 basis([A], A_ROWS + [meter(A.revision_id, "e8", 20, 25, "1.000", use="EXCLUDED",
                                            reason="METER_OVERLAP")])):
        k = em.derive(case)
        assert (k.state, k.reason, k.quantity_kwh, k.amount, k.currency, k.sessions, k.evidence_ids) == (
            "WITHHELD", "CONTRADICTORY_EVIDENCE", None, None, None, (), ())

    # R6 two eligible sessions with disjoint intervals: one union under one revision; two revisions -> gap.
    c = session("f" * 36)
    c_rows = [meter(c.revision_id, "e5", 30, 40, "4.000", C2), meter(c.revision_id, "e6", 40, 50, "6.000", C2)]
    union = em.derive(basis([A, c], A_ROWS + c_rows))
    assert (union.state, union.quantity_kwh, union.amount) == ("ESTIMATED", Decimal("20.000"), Decimal("5.55500000"))
    assert union.evidence_ids == ("e1", "e2", "e5", "e6") and len(union.sessions) == 2
    first = em.TariffAssignment("t1", Decimal("0.27775"), "KES", em.TARIFF_UNIT, T0, at(30), T1)
    second = em.TariffAssignment("t2", Decimal("0.27775"), "KES", em.TARIFF_UNIT, at(30), T1, T1)
    k = em.derive(basis([A, c], A_ROWS + c_rows, (first, second)))
    assert (k.state, k.reason, k.quantity_kwh, k.amount) == ("UNPRICED", "PRICE_GAP_OR_CHANGE", Decimal("20.000"), None)
    usd = em.TariffAssignment("t2", Decimal("0.27775"), "USD", em.TARIFF_UNIT, at(30), T1, T1)
    assert em.derive(basis([A, c], A_ROWS + c_rows, (first, usd))).reason == "PRICE_GAP_OR_CHANGE"

    # A witnessed full-coverage zero delta is a legitimate numeric zero; no session is no consequence.
    z = session("9" * 36, kwh="0.000")
    zero = em.derive(basis([z], [meter(z.revision_id, "e0", 0, 10, "0.000")]))
    assert (zero.state, zero.quantity_kwh, zero.amount) == ("ESTIMATED", Decimal("0.000"), Decimal("0E-8"))
    assert em.derive(basis([], [])) is None


class FakeUnit:
    def __init__(self, store) -> None:
        self.store = store

    def work(self):
        return {"id": self.store.work_id, "succeeded": self.store.succeeded, "window_start": T0, "window_end": T1}

    def pending(self, work) -> bool:
        return self.store.pending

    def basis(self, work):
        return self.store.basis

    def append(self, consequence):
        self.store.appended.append(consequence)
        return uuid4(), False

    def succeed(self) -> int:
        self.store.succeeded = True
        return 1


class FakeStore:
    def __init__(self, pending: bool, basis_value) -> None:
        self.work_id, self.pending, self.basis, self.succeeded = uuid4(), pending, basis_value, False
        self.appended, self.failures = [], []

    @contextmanager
    def ev_unit(self, tenant_id, site_id, work_id):
        yield FakeUnit(self)

    def ev_record_failure(self, tenant_id, site_id, work_id, error_code) -> int:
        self.failures.append(error_code)
        return len(self.failures)

    def ev_pending_work(self, tenant_id, site_id):
        return [] if self.succeeded else [{"id": self.work_id}]


def test_pending_historical_and_unassessable_source_withhold_current_amount() -> None:
    # R8: an overlapping unsettled W2-06 job wins over every quantity/tariff row: a FAILED PENDING_RECOMPUTE attempt,
    # no consequence (not a stored WITHHELD/PENDING_RECOMPUTE revision), and the work stays selectable.
    store = FakeStore(True, basis([A], A_ROWS))
    out = EvConsequenceWorker(store).process_one(uuid4(), uuid4(), store.work_id)
    assert (out.succeeded, out.error_code, out.attempt_no, store.appended, store.failures) == (
        False, ERROR_PENDING, 1, [], ["PENDING_RECOMPUTE"])
    assert ERROR_PENDING == "PENDING_RECOMPUTE"
    # Once settled the same work succeeds with the exact estimate.
    store.pending = False
    out = EvConsequenceWorker(store).process_one(uuid4(), uuid4(), store.work_id)
    assert out.succeeded and [k.amount for k in store.appended] == [Decimal("2.77750000")]

    # A source gate wins over contradiction, incompleteness and tariff rows (C5): non-assessable class or a mismatch
    # with the selected stored class is WITHHELD/SOURCE_GATE with null amount/currency/quantity.
    for gate, stored in (("MIXED", "MIXED"), ("UNKNOWN", SIM), ("AUTHORED_DEMONSTRATION", SIM)):
        for sessions, rows in (([A], A_ROWS), ([A, session("d" * 36, "CONTRADICTORY", None, None)], A_ROWS),
                               ([B_INCOMPLETE], B_ROWS)):
            k = em.derive(basis(sessions, rows, gate=gate, stored=stored))
            assert (k.state, k.reason, k.source_gate, k.quantity_kwh, k.amount, k.currency) == (
                "WITHHELD", "SOURCE_GATE", gate, None, None, None)

    # No exact selection, or a selection with no qualifying session, is no consequence and a successful empty item.
    for value in (None, basis([], [])):
        store = FakeStore(False, value)
        out = EvConsequenceWorker(store).process_one(uuid4(), uuid4(), store.work_id)
        assert out.succeeded and out.consequence_revision_id is None and store.appended == []

    # Historical and stale states are read guards only: derive never emits them.
    assert not {"HISTORICAL_CURRENT_CLAIM", "STALE_BASIS", "PENDING_RECOMPUTE"} & {
        v for k, v in vars(em).items() if k.isupper() and isinstance(v, str) and k not in ("ERROR_PENDING",)}
