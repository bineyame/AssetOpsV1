"""W3-01 commit 1: the shared public `source_provenance` DTO over PostgreSQL.

`.agent/W3-01-build-spec.md` "Shared provenance DTO resolution", "Review closure" B8/B10 and "Review closure 2"
D2/D6; `D-2026-10-20-shared-provenance-dto` and its amendments. Every vector is a real stored binding (authored
P01/P02, one and two registered runs, unbound uploads) or a missing, foreign-Site, foreign-tenant or broken link
(built inside a rolled-back transaction, as `test_s405_resolver_postgres.py` does). Each asserts the public keys,
`state == classification`, the full cited ID set (never a subset), the in-scope `source_ids`, the canonical
reasons, `detail` equal to `SourceProvenanceResolver.resolve` on the same set, and the selection digest recomputed
independently here. The empty vector pins the build spec's literal W20 digest. Requires
ASSETOPS_TEST_DATABASE_URL (see backend/TESTING.md).
"""

from __future__ import annotations

import hashlib
import json
import os
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


@pytest.fixture(autouse=True)
def _release_connections():
    yield
    import gc

    gc.collect()


if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import Kit, converted_enabled
    from test_s2_registered_basis import request as run_request
    from test_s2_registered_basis_postgres import service as run_setup
    from test_s405_publication_postgres import P02
    from test_s405_resolver_postgres import authored, simulated, upload

    from assetops_backend.evidence import source_provenance as sp
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.public_provenance import PublicProvenance
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore

# The build spec's W20 injected empty-citation factory (Review closure 2): tenant, Site and the five selected IDs
# (Action, selected event, origin Finding revision, basis assessment, Foundation revision) with no citation.
_F = "10000000-0000-4000-8000-000000000"
W20_TENANT, W20_SITE = _F + "001", _F + "011"
W20_SELECTED = [_F + "201", _F + "202", _F + "102", _F + "203", _F + "204"]
W20_DIGEST = "sha256:ed86298acb47897962bf2baa31e72a852723b994b43134f3eab8546742fe3e85"

PUBLIC_KEYS = ["basis_sha256", "classification", "detail", "evidence_ids", "reasons", "source_ids", "state"]


@pytest.fixture()
def kit(store, engine):  # noqa: F811
    _, outcome = converted_enabled(store, engine)
    return Kit(engine, outcome.published.changed.id)


def digest(tenant, site, selected, accepted) -> str:
    """Independent recomputation of the decision's selection digest."""
    doc = {"version": "source-provenance-basis/1", "tenant_id": str(tenant), "site_id": str(site),
           "selected_revision_ids": sorted({str(s) for s in selected}),
           "accepted_evidence_ids": sorted({str(a) for a in accepted})}
    return "sha256:" + hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sources_in_scope(engine, tenant, site, ids) -> list[str]:  # noqa: F811
    with engine.connect() as c:
        return sorted({str(s).lower() for s in c.execute(text(
            "SELECT DISTINCT source_id FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[])) AND source_id IS NOT NULL"),
            {"t": tenant, "s": site, "ids": list(ids)}).scalars()})


def check(dto, resolved, *, tenant, site, selected, cited, sources) -> None:
    """The shared assertions every vector makes."""
    assert sorted(dto) == PUBLIC_KEYS
    assert dto["classification"] == dto["state"] == resolved["state"]
    assert dto["evidence_ids"] == sorted(set(cited))  # the full cited set, missing/foreign IDs kept
    assert dto["source_ids"] == sources
    assert dto["basis_sha256"] == digest(tenant, site, selected, cited)
    assert dto["reasons"] == dto["detail"]["reasons"]
    codes = [r["code"] for r in dto["reasons"]]
    assert codes == sorted(codes)
    assert sorted(map(json.dumps, dto["reasons"])) == sorted(map(json.dumps, (
        {**r, "accepted_evidence_ids": sorted(r["accepted_evidence_ids"])} for r in resolved["reasons"])))
    nine = ("state", "reasons", "accepted_evidence_ids", "problematic_accepted_evidence_ids", "publication_ids",
            "source_classes", "fixtures", "runs", "evidence")
    assert list(dto["detail"]) == list(nine)
    assert {k: v for k, v in dto["detail"].items() if k != "reasons"} == {k: resolved[k] for k in nine[:1] + nine[2:]}


def codes_of(dto) -> list[str]:
    return [r["code"] for r in dto["reasons"]]


def test_empty_foreign_broken_and_mixed_precedence(kit, store, engine, tmp_path) -> None:  # noqa: F811
    ledger = PostgresEvidenceLedger(URL)
    public, resolver = PublicProvenance(ledger), sp.SourceProvenanceResolver(ledger)
    tenant, site = kit.principal.tenant_id, kit.principal.site_id
    selected = [str(uuid4())]

    def vector(ids, *, t=tenant, s=site, sel=selected):
        dto = public.cited_set(t, s, ids, sel)
        check(dto, resolver.resolve(t, s, ids), tenant=t, site=s, selected=sel, cited=ids,
              sources=sources_in_scope(engine, t, s, ids))
        return dto

    # Empty citation set: UNKNOWN, non-null digest; the build spec's literal W20 digest.
    empty = public.cited_set(W20_TENANT, W20_SITE, [], W20_SELECTED)
    assert empty["basis_sha256"] == W20_DIGEST
    assert {k: empty[k] for k in PUBLIC_KEYS if k != "detail"} == {
        "classification": "UNKNOWN", "state": "UNKNOWN", "source_ids": [], "evidence_ids": [],
        "basis_sha256": W20_DIGEST, "reasons": [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]}
    assert public.cited_set(W20_TENANT, W20_SITE, [], [])["basis_sha256"] is None  # no selection only

    # Positive authored set, then missing ID precedence over MIXED.
    _, auth = authored(kit, kit.seal(kit.pv(1)))
    plain = upload(kit, kit.seal(kit.pv(2, first=3)))
    positive = vector(auth)
    assert positive["classification"] == sp.AUTHORED_DEMONSTRATION and positive["reasons"] == []
    assert positive["source_ids"]  # non-vacuous: the in-scope set really names a source
    missing = str(uuid4())
    m = vector(auth + plain + [missing])
    assert m["classification"] == sp.UNKNOWN and codes_of(m) == [sp.EVIDENCE_NOT_FOUND]
    assert missing in m["evidence_ids"] and m["source_ids"] == positive["source_ids"]
    unbound = vector(plain)
    assert unbound["classification"] == sp.UNKNOWN and codes_of(unbound) == [sp.NO_POSITIVE_BINDING]

    # Foreign Site of the same tenant and a foreign tenant: UNKNOWN, IDs kept, no foreign source disclosed.
    other_site = uuid4()
    foreign = vector(auth, s=other_site)
    assert codes_of(foreign) == [sp.FOREIGN_SITE_EVIDENCE] and foreign["source_ids"] == []
    assert foreign["evidence_ids"] == sorted(auth)
    other_tenant = vector(auth, t=uuid4())
    assert codes_of(other_tenant) == [sp.EVIDENCE_NOT_FOUND] and other_tenant["source_ids"] == []

    # MIXED: two authored fixture versions; one and two registered runs; crossed classes plus bound and unbound.
    _, p02 = authored(kit, kit.seal(kit.pv(1, first=5)), fixture=P02)
    fixtures = vector(auth + p02)
    assert fixtures["classification"] == sp.MIXED and codes_of(fixtures) == [sp.AUTHORED_FIXTURE_VERSION_CONFLICT]
    listed = fixtures["reasons"][0]["fixtures"]
    assert listed == sorted(listed, key=lambda f: (f["fixture_id"], f["fixture_version"])) and len(listed) == 2
    runs = run_setup(store, YamlRunStore(tmp_path / "runs"))
    first, second = runs.create_draft_run(run_request()), runs.create_draft_run(run_request())
    _, one = simulated(kit, first, [kit.seal(kit.pv(1, first=10))])
    assert vector(one)["classification"] == sp.REGISTERED_SIMULATION
    _, two = simulated(kit, second, [kit.seal(kit.pv(1, first=12))])
    both = vector(one + two)
    assert both["classification"] == sp.MIXED and codes_of(both) == [sp.MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS]
    assert both["reasons"][0]["run_ids"] == sorted([first.run_id, second.run_id])
    crossed = vector(one + auth + plain)
    assert crossed["classification"] == sp.MIXED
    assert codes_of(crossed) == [sp.BOUND_AND_UNBOUND, sp.CROSSED_SOURCE_CLASSES]
    assert crossed["reasons"][1]["source_classes"] == sorted([sp.AUTHORED_DEMONSTRATION, sp.REGISTERED_SIMULATION])

    # Broken link: precedence over MIXED, read on the rolled-back connection (the real adapter SQL).
    lost_body = kit.seal(kit.pv(1, first=20))
    lost = upload(kit, lost_body)
    with engine.connect() as c:
        tx = c.begin()
        try:
            for name in ("batch_publication_link_batch_fk", "batch_publication_link_publication_fk",
                         "batch_publication_link_publication_unique"):
                c.execute(text(f"ALTER TABLE batch_publication_link DROP CONSTRAINT {name}"))
            p = c.execute(text("SELECT gateway_id, source_id FROM evidence_publication WHERE tenant_id = :t "
                               "AND site_id = :s LIMIT 1"), {"t": tenant, "s": site}).one()
            batch = c.execute(text("SELECT batch_id FROM accepted_evidence WHERE id = :e"), {"e": lost[0]}).scalar_one()
            doc = json.loads(lost_body)
            c.execute(text(
                "INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, "
                "source_id, external_batch_id, payload_sha256, linked_at) VALUES (:b, :p, :t, :s, :g, :src, :eb, "
                ":sha, now())"), {"b": batch, "p": uuid4(), "t": tenant, "s": site, "g": p[0], "src": p[1],
                                  "eb": doc["batch_id"], "sha": doc["payload_sha256"]})
            reads = PostgresEvidenceLedger(URL)
            reads._run = lambda work, write=False: work(c)
            ids = auth + p02 + lost
            broken = PublicProvenance(reads).cited_set(tenant, site, ids, selected)
            resolved = sp.SourceProvenanceResolver(reads).resolve(tenant, site, ids)
        finally:
            tx.rollback()
    check(broken, resolved, tenant=tenant, site=site, selected=selected, cited=ids,
          sources=sources_in_scope(engine, tenant, site, ids))
    assert broken["classification"] == sp.UNKNOWN and codes_of(broken) == [sp.BROKEN_PUBLICATION_LINK]
    assert broken["reasons"][0]["details"] == [{"accepted_evidence_id": lost[0], "detail": sp.PUBLICATION_NOT_FOUND}]
    assert broken["source_ids"]  # in-scope rows still name their source even when the set is UNKNOWN


def test_persisted_ev_class_disagreement_unknown(kit, store, engine, tmp_path) -> None:  # noqa: F811
    """Run 1 ruling 4: positive/positive disagreement, a null persisted class and resolver UNKNOWN against a
    persisted positive class each give UNKNOWN with every resolver reason kept beside SOURCE_CLASS_MISMATCH (full
    cited IDs, the stored class), and `detail` equal to the final state/reasons with the other seven resolver keys."""
    ledger = PostgresEvidenceLedger(URL)
    public, resolver = PublicProvenance(ledger), sp.SourceProvenanceResolver(ledger)
    tenant, site = kit.principal.tenant_id, kit.principal.site_id
    selected = [str(uuid4()), str(uuid4())]  # pure adapter vectors; the public EV mapping is ruling 7's test
    _, auth = authored(kit, kit.seal(kit.pv(1)))
    plain = upload(kit, kit.seal(kit.pv(2, first=3)))
    runs = run_setup(store, YamlRunStore(tmp_path / "runs"))
    _, sim = simulated(kit, runs.create_draft_run(run_request()), [kit.seal(kit.pv(1, first=10))])

    def mismatch(ids, persisted, resolved_state):
        dto = public.ev_selected(tenant, site, ids, selected, persisted)
        resolved = resolver.resolve(tenant, site, ids)
        assert resolved["state"] == resolved_state  # non-vacuous: the resolver really says this
        assert sorted(dto) == PUBLIC_KEYS
        assert dto["classification"] == dto["state"] == sp.UNKNOWN
        assert dto["evidence_ids"] == sorted(set(ids))
        assert dto["source_ids"] == sources_in_scope(engine, tenant, site, ids)
        assert dto["basis_sha256"] == digest(tenant, site, selected, ids)
        added = {"code": "SOURCE_CLASS_MISMATCH", "accepted_evidence_ids": sorted(set(ids)),
                 "persisted_class": persisted}
        assert added in dto["reasons"]
        kept = [r for r in dto["reasons"] if r != added]
        assert sorted(map(json.dumps, kept)) == sorted(map(json.dumps, (
            {**r, "accepted_evidence_ids": sorted(r["accepted_evidence_ids"])} for r in resolved["reasons"])))
        codes = codes_of(dto)
        assert codes == sorted(codes)
        assert dto["detail"]["state"] == sp.UNKNOWN and dto["detail"]["reasons"] == dto["reasons"]
        seven = ("accepted_evidence_ids", "problematic_accepted_evidence_ids", "publication_ids", "source_classes",
                 "fixtures", "runs", "evidence")
        assert {k: dto["detail"][k] for k in seven} == {k: resolved[k] for k in seven}
        return dto

    # Positive/positive disagreement: resolver AUTHORED, stored REGISTERED (and the reverse).
    assert codes_of(mismatch(auth, sp.REGISTERED_SIMULATION, sp.AUTHORED_DEMONSTRATION)) == ["SOURCE_CLASS_MISMATCH"]
    mismatch(sim, sp.AUTHORED_DEMONSTRATION, sp.REGISTERED_SIMULATION)
    # A null persisted class on a selected row is a mismatch.
    mismatch(auth, None, sp.AUTHORED_DEMONSTRATION)
    # Resolver UNKNOWN against a persisted positive class: both reasons coexist.
    both = mismatch(plain, sp.AUTHORED_DEMONSTRATION, sp.UNKNOWN)
    assert codes_of(both) == [sp.NO_POSITIVE_BINDING, "SOURCE_CLASS_MISMATCH"]

    # Agreement adds nothing; no selected row means no comparison; the estate projection drops `detail`.
    agree = public.ev_selected(tenant, site, auth, selected, sp.AUTHORED_DEMONSTRATION)
    assert agree == public.cited_set(tenant, site, auth, selected)
    unselected = public.ev_selected(tenant, site, auth, [], sp.REGISTERED_SIMULATION)
    assert unselected["classification"] == sp.AUTHORED_DEMONSTRATION and unselected["basis_sha256"] is None
    estate = public.ev_selected(tenant, site, plain, selected, sp.AUTHORED_DEMONSTRATION, detail=False)
    assert sorted(estate) == [k for k in PUBLIC_KEYS if k != "detail"]

    # The same adapter on one caller connection (the cold/EV snapshot path) gives the identical DTO.
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.evidence.public_provenance import LinkRowsReads

    with engine.connect() as c:
        on_c = PublicProvenance(LinkRowsReads(lambda t, s, ids: link_rows_on(c, t, s, ids)))
        assert on_c.ev_selected(tenant, site, plain, selected, sp.AUTHORED_DEMONSTRATION) == both


def test_w1_revision_selection_sets_and_estate_projection(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    """Run 1 rulings 2 and 6 on a real W1 Finding and consequence: the default selected sets are
    `{finding_revision.id}` and `{consequence_revision.id, finding_revision.id}` over their exact cited sets, the W1
    top-level resolver fields stay, and the estate projection is exactly the six public keys."""
    from test_s405_publication_postgres import P01
    from test_s405_resolver_postgres import power_site

    from assetops_backend.evidence.public_provenance import (
        consequence_row_selection,
        estate_projection,
        finding_row_selection,
    )

    s, rev, cid = power_site(store, engine, capsys, monkeypatch, lambda d, t: P01)
    try:
        ledger = PostgresEvidenceLedger(URL)
        public, resolver = PublicProvenance(ledger), sp.SourceProvenanceResolver(ledger)
        with engine.connect() as conn:
            cited = sorted(str(x) for x in conn.execute(text(
                "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r"),
                {"r": rev["id"]}).scalars())
            power = sorted(str(x) for x in conn.execute(text(
                "SELECT evidence_id FROM financial_consequence_power_interval WHERE consequence_revision_id = :c"),
                {"c": cid}).scalars())
        assert cited and power
        f = public.finding_revision(s.tenant, s.site, rev["id"])
        assert f["basis_sha256"] == digest(s.tenant, s.site, [rev["id"]], cited)
        assert finding_row_selection(rev["id"]) == [str(rev["id"]).lower()]
        raw_f = resolver.finding_revision(s.tenant, s.site, rev["id"])
        assert {k: f[k] for k in raw_f if k != "reasons"} == {k: v for k, v in raw_f.items() if k != "reasons"}
        assert f["classification"] == f["state"] == sp.AUTHORED_DEMONSTRATION and f["evidence_ids"] == cited

        c = public.consequence_revision(s.tenant, s.site, cid)
        assert c["basis_sha256"] == digest(s.tenant, s.site, [cid, rev["id"]], set(cited) | set(power))
        assert consequence_row_selection(cid, rev["id"]) == sorted([str(cid).lower(), str(rev["id"]).lower()])
        raw_c = resolver.consequence_revision(s.tenant, s.site, cid)
        assert {k: c[k] for k in raw_c if k != "reasons"} == {k: v for k, v in raw_c.items() if k != "reasons"}
        assert c["evidence_ids"] == sorted(set(cited) | set(power))
        # An explicit ruling-2 set (e.g. a cold/EV Finding row) replaces the W1 default.
        other = [rev["id"], uuid4()]
        assert public.finding_revision(s.tenant, s.site, rev["id"], other)["basis_sha256"] == digest(
            s.tenant, s.site, other, cited)

        estate = estate_projection(f)
        assert sorted(estate) == ["basis_sha256", "classification", "evidence_ids", "reasons", "source_ids", "state"]
        assert estate == {k: f[k] for k in estate}
    finally:
        s.prices.dispose()
        s.store.dispose()


def test_pending_dual_blocks() -> None:
    """Run 1 ruling 5: the three sibling blocks and the compatibility alias."""
    from assetops_backend.evidence.public_provenance import dual_blocks

    sel = {"classification": "AUTHORED_DEMONSTRATION", "basis_sha256": "sha256:" + "a" * 64}
    pend = {"classification": "MIXED", "basis_sha256": None}
    assert dual_blocks(sel, None) == {"source_provenance": sel, "selected_source_provenance": sel,
                                      "pending_source_provenance": None}
    both = dual_blocks(sel, pend)
    assert both["source_provenance"] == both["pending_source_provenance"] == pend
    assert both["selected_source_provenance"] == sel  # the selected row is never relabelled
    assert dual_blocks(None, pend) == {"source_provenance": pend, "selected_source_provenance": None,
                                       "pending_source_provenance": pend}
    with pytest.raises(ValueError):
        dual_blocks(sel, {**pend, "basis_sha256": sel["basis_sha256"]})  # never the prior digest on pending
    with pytest.raises(ValueError):
        dual_blocks(None, None)  # unruled; see .agent/W3-01-pending-rulings.md
