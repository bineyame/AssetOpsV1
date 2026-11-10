"""FX-COLD-LINKED (build sheet OWN-GAPS, DS-1f ruling D-E5.8): the Cold composer resolves a visit- or Action-linked
Finding that the selected (latest) assessment leaves out, as EV does (addendum 3 (d)). Fake ports, no database; the
Postgres check is `test_fx_cold_linked_postgres.py`."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from test_out_b3_cold_ev import C, F118, HI, LO, MR5, T, Fake, cold_ports, contributor

from assetops_backend.site_outcomes import cold
from assetops_backend.site_outcomes.board import assemble

REPEATED = "REPEATED_MAINTENANCE_NO_RESULT"
E1 = dict(MR5, case_id="e1", code="MR-001", occurred_at=T(9, 0, 2))
E2 = dict(MR5, case_id="e2", code="MR-002", occurred_at=T(9, 0, 12))
#: a later clean assessment: the next day's window, whose selection holds no Finding
CLEAN_LO, CLEAN_HI = LO + timedelta(days=1), HI + timedelta(days=1)


def run(finding):
    calls: list[str] = []

    def single(fid, lo, hi):
        calls.append(fid)
        return finding(fid)

    ports = cold_ports(Fake(cold_findings={"items": [], "next_cursor": None}))
    work = lambda kind, lo, hi, cur: {"rows": [E1, E2, MR5] if kind == "maintenance" else [], "next_cursor": None}
    ports = replace(ports, work=work, finding=single)
    comp = cold.compose(ports, site_code=C, lo=CLEAN_LO, hi=CLEAN_HI, site_timezone="Africa/Nairobi")
    return comp, {r["category"]: r for r in assemble(comp.facts)}, calls


def test_later_clean_assessment_keeps_the_linked_start_failure_and_its_repeat_warning() -> None:
    comp, rows, calls = run(lambda fid: F118 if fid == "f118" else None)
    assert calls == ["f118"]  # the visits and DA1 link f118; the clean selection lacks it, so it is read by id
    (w,) = [w for w in comp.facts.warnings if w.kind == REPEATED]
    assert w.count == 3 and w.fault_name == "automatic start failure"
    assert any(r["kind"] == "FINDING" and r["id"] == "f118" for r in w.evidence_refs), w.evidence_refs
    assert w.seen.endswith("; the automatic start failure is still open")
    cost = rows[cold.COST]
    assert cost["state"] == "NEEDS_ATTENTION" and cost["lead_outcome"]["key"] == "CC-3"
    assert contributor(cost, "maintenance_effectiveness")["text"] != cold.NO_REPEAT
    assert comp.failed == ()
    # the resolved Finding is outside the clean window: Protect does not claim a start failure in it
    assert rows[cold.PROTECT]["subline"] == cold.PROTECT_SUBLINE


def test_refused_single_read_unsettles_cc3_and_names_the_finding_source() -> None:
    def refuse(fid):
        raise PermissionError("refused")
    comp, rows, _ = run(refuse)
    assert "cold_findings" in comp.failed and comp.read_state == "PARTIAL"
    assert comp.facts.settled["CC-3"] is False
    assert not [w for w in comp.facts.warnings if w.kind == REPEATED]


def test_single_read_none_drops_nothing_else() -> None:
    comp, rows, calls = run(lambda fid: None)
    assert calls == ["f118"] and comp.failed == ()
    assert not [w for w in comp.facts.warnings if w.kind == REPEATED]
    assert contributor(rows[cold.COST], "maintenance_effectiveness")["text"] == cold.NO_REPEAT
