"""S4-05a phase 2: the pure source provenance truth table (`evidence/source_provenance.py`).

`tasks/S4-05-stored-demo-provenance.md` shared contract item 3; `.agent/architect-S4-05-answers.md` Q2 and
Follow-up M1; N-L2 (several run IDs are MIXED). Real-Postgres proof of the same rows is in
`test_s405_resolver_postgres.py`; this file pins every per-ID broken detail and the reason precedence.
"""

from __future__ import annotations

from dataclasses import replace

from assetops_backend.evidence import source_provenance as sp

T, S, G, SRC = "t", "s", "g", "src"


def commitment(ext="b1", sha="a" * 64, gateway=G, source=SRC, site=S):
    return (T, site, gateway, source, ext, sha)


def bound(eid, *, pub=None, cls=sp.AUTHORED_DEMONSTRATION, fixture=("fx", "1"), run=("run-1", "d" * 64), ext=None):
    ext = ext or f"batch-{eid}"
    c = commitment(ext)
    authored = cls == sp.AUTHORED_DEMONSTRATION
    return sp.LinkRow(eid, True, False, batch_id=f"B{eid}", evidence_gateway_source=(G, SRC), batch=c,
                      link_publication_id=pub or f"P{eid}", link=c, publication=c, source_class=cls,
                      fixture_id=fixture[0] if authored else None, fixture_version=fixture[1] if authored else None,
                      run_id=None if authored else run[0], run_identity_sha256=None if authored else run[1])


def unbound(eid):
    return sp.LinkRow(eid, True, False, batch_id=f"B{eid}", evidence_gateway_source=(G, SRC),
                      batch=commitment(f"batch-{eid}"))


def run(*rows, ids=None):
    links = {r.requested_id: sp.link_of(r) for r in rows}
    return sp.classify(ids if ids is not None else [r.requested_id for r in rows], links)


def codes(result):
    return [r["code"] for r in result["reasons"]]


class TestPositiveClasses:
    def test_two_publications_of_one_fixture_version_are_authored_and_list_both(self) -> None:
        r = run(bound("1"), bound("2"))
        assert r["state"] == sp.AUTHORED_DEMONSTRATION and r["reasons"] == []
        assert r["publication_ids"] == ["P1", "P2"] and r["fixtures"] == [{"fixture_id": "fx", "fixture_version": "1"}]
        assert r["problematic_accepted_evidence_ids"] == []
        assert [e["status"] for e in r["evidence"]] == [sp.BOUND, sp.BOUND]

    def test_one_run_is_registered_simulation_with_its_run_and_publications(self) -> None:
        sim = sp.REGISTERED_SIMULATION
        r = run(bound("1", cls=sim), bound("2", cls=sim))
        assert r["state"] == sim and r["runs"] == [{"run_id": "run-1", "run_identity_sha256": "d" * 64}]
        assert r["publication_ids"] == ["P1", "P2"] and r["fixtures"] == []


class TestMixed:
    def test_differing_fixture_version_or_id(self) -> None:
        for other in (("fx", "2"), ("fy", "1")):
            r = run(bound("1"), bound("2", fixture=other))
            assert r["state"] == sp.MIXED and codes(r) == [sp.AUTHORED_FIXTURE_VERSION_CONFLICT]
            assert r["problematic_accepted_evidence_ids"] == ["1", "2"]

    def test_several_runs_are_mixed_until_a_compatible_basis_exists(self) -> None:
        sim = sp.REGISTERED_SIMULATION
        r = run(bound("1", cls=sim), bound("2", cls=sim, run=("run-2", "d" * 64)))
        assert r["state"] == sp.MIXED and codes(r) == [sp.MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS]
        assert r["reasons"][0]["run_ids"] == ["run-1", "run-2"]

    def test_one_run_id_with_two_identity_digests_conflicts(self) -> None:
        sim = sp.REGISTERED_SIMULATION
        r = run(bound("1", cls=sim), bound("2", cls=sim, run=("run-1", "e" * 64)))
        assert r["state"] == sp.MIXED and codes(r) == [sp.RUN_IDENTITY_CONFLICT]

    def test_crossed_classes_and_bound_with_unbound_report_every_reason(self) -> None:
        r = run(bound("1"), bound("2", cls=sp.REGISTERED_SIMULATION), unbound("3"))
        assert r["state"] == sp.MIXED
        assert codes(r) == [sp.BOUND_AND_UNBOUND, sp.CROSSED_SOURCE_CLASSES]
        assert r["reasons"][0]["accepted_evidence_ids"] == ["3"]
        assert r["problematic_accepted_evidence_ids"] == ["1", "2", "3"]
        assert r["source_classes"] == [sp.AUTHORED_DEMONSTRATION, sp.REGISTERED_SIMULATION]


class TestUnknown:
    def test_empty_set(self) -> None:
        r = run(ids=[])
        assert (r["state"], codes(r), r["evidence"]) == (sp.UNKNOWN, [sp.EMPTY_CITATION_SET], [])

    def test_no_positive_binding(self) -> None:
        r = run(unbound("1"), unbound("2"))
        assert r["state"] == sp.UNKNOWN and codes(r) == [sp.NO_POSITIVE_BINDING]
        assert r["problematic_accepted_evidence_ids"] == ["1", "2"] and r["publication_ids"] == []

    def test_missing_foreign_and_broken_take_precedence_over_mixed(self) -> None:
        missing = sp.LinkRow("m", False, False)
        foreign = sp.LinkRow("f", False, True)
        broken = replace(bound("x"), publication=None)
        mixed = [bound("1"), bound("2", cls=sp.REGISTERED_SIMULATION), unbound("3")]
        r = run(*mixed, missing, foreign, broken, ids=["1", "2", "3", "m", "f", "x", "absent"])
        assert r["state"] == sp.UNKNOWN
        assert codes(r) == [sp.EVIDENCE_NOT_FOUND, sp.FOREIGN_SITE_EVIDENCE, sp.BROKEN_PUBLICATION_LINK]
        assert r["reasons"][0]["accepted_evidence_ids"] == ["absent", "m"]
        assert r["reasons"][2]["details"] == [{"accepted_evidence_id": "x", "detail": sp.PUBLICATION_NOT_FOUND}]
        assert r["problematic_accepted_evidence_ids"] == ["absent", "f", "m", "x"]
        # The bound IDs are still reported per evidence, but the set is not MIXED.
        assert r["publication_ids"] == ["P1", "P2"]

    def test_every_broken_detail(self) -> None:
        good = bound("1")
        other = commitment("other-batch")
        cases = {
            sp.BATCH_NOT_FOUND: replace(good, batch=None),
            sp.EVIDENCE_BATCH_SCOPE_MISMATCH: replace(good, evidence_gateway_source=("g2", SRC)),
            sp.LINK_COMMITMENT_MISMATCH: replace(good, link=other, publication=other),
            sp.PUBLICATION_NOT_FOUND: replace(good, publication=None),
            sp.PUBLICATION_COMMITMENT_MISMATCH: replace(good, publication=commitment(sha="b" * 64)),
            sp.PUBLICATION_CLASS_INVALID: replace(good, run_id="run-1"),
        }
        for detail, row in cases.items():
            link = sp.link_of(row)
            assert (link.status, link.broken_detail) == (sp.BROKEN_LINK, detail), detail
            assert run(row)["state"] == sp.UNKNOWN
        assert sp.link_of(replace(good, link=commitment(site="s2"))).broken_detail == sp.LINK_COMMITMENT_MISMATCH
        assert sp.link_of(replace(good, source_class="REAL")).broken_detail == sp.PUBLICATION_CLASS_INVALID


class Reads:
    def __init__(self, rows, cited, power) -> None:
        self.rows, self.cited, self.power = {r.requested_id: r for r in rows}, cited, power

    def link_rows(self, tenant_id, site_id, ids):
        return [self.rows[i] for i in ids if i in self.rows]

    def finding_revision_evidence(self, tenant_id, site_id, finding_revision_id):
        return self.cited

    def consequence_inputs(self, tenant_id, site_id, consequence_revision_id):
        return None if self.cited is None else ("FR", self.cited, self.power)


class TestRevisionSets:
    def test_consequence_only_power_conflict_is_mixed_beside_an_authored_finding(self) -> None:
        resolver = sp.SourceProvenanceResolver(Reads([bound("1"), bound("2"), bound("p", fixture=("fx", "2"))],
                                                     ["1", "2"], ["2", "p"]))
        finding = resolver.finding_revision("t", "s", "FR")
        consequence = resolver.consequence_revision("t", "s", "C")
        assert finding["state"] == sp.AUTHORED_DEMONSTRATION and finding["cited_accepted_evidence_ids"] == ["1", "2"]
        assert consequence["state"] == sp.MIXED and consequence["finding_revision_state"] == sp.AUTHORED_DEMONSTRATION
        assert consequence["cited_accepted_evidence_ids"] == ["1", "2"]
        assert consequence["power_accepted_evidence_ids"] == ["2", "p"]
        assert consequence["accepted_evidence_ids"] == ["1", "2", "p"]
        assert codes(consequence) == [sp.AUTHORED_FIXTURE_VERSION_CONFLICT, sp.CONSEQUENCE_POWER_INPUT_CONFLICT]
        assert consequence["reasons"][1]["accepted_evidence_ids"] == ["p"]

    def test_absent_revision_is_none_never_a_fallback(self) -> None:
        resolver = sp.SourceProvenanceResolver(Reads([], None, []))
        assert resolver.finding_revision("t", "s", "FR") is None
        assert resolver.consequence_revision("t", "s", "C") is None
