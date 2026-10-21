"""W4-02 q12-6: MG-W402-001 reaches the S5 Overview through a persisted `NO_LEGACY_EVIDENCE` cutover basis.

The W4-02 installer imports the Site with no legacy documents and records that explicit basis with the import; the
Overview route accepts it in place of the S2 Evidence comparison. Every other import (here a KOBO-style MINIGRID
import that a real legacy YAML document declares, so it has no basis and no passing comparison) keeps the 409, and the
installer records no basis when a legacy document declares MG-W402-001 (B-L2). Served through `create_app`.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    import test_s1_bindings_postgres as s1
    from test_s4_schedule_tick_postgres import import_site
    from test_w402_authored_v4_postgres import INSTALLED, install

    from assetops_backend.sites.adapters.import_files import legacy_documents, read_import_source
    from assetops_backend.sites.w402_demo import FIXTURE_PATH, MG_W402_SITE_CODE, install_mg_w402_site


def import_legacy_declared(store, tmp_path, code: str):
    """A MINIGRID import of `code` that a real legacy YAML document declares: the document is written to a legacy
    store root, read back by the production `legacy_documents` reader and passed to the import (same path)."""
    root = tmp_path / "legacy-sites"
    root.mkdir()
    path = root / f"{code.lower()}.yaml"
    path.write_text(s1.KOBO_SOURCE.read_text(encoding="utf-8").replace("site_id: KOBO-001", f"site_id: {code}"),
                    encoding="utf-8")
    documents = legacy_documents((root,))
    assert [d.site_code for d in documents] == [code]
    result = s1.import_site(store, tenant_slug="demo", configured_tenant_slug="demo",
                            source=read_import_source(str(path)), legacy_documents=documents, clock=s1.Clock(s1.NOW))
    return result.site


def _client(monkeypatch) -> TestClient:
    from assetops_backend import main

    monkeypatch.setenv("DATABASE_URL", URL)
    return TestClient(main.create_app())


def test_installer_records_the_empty_legacy_basis_and_the_overview_serves(store, engine, monkeypatch,  # noqa: F811
                                                                         tmp_path) -> None:
    installed = install(store)
    tenant_id, site_id = installed.result.site.tenant_id, installed.result.site.id
    assert store.no_legacy_evidence_basis(tenant_id, site_id) is True
    install(store)  # idempotent rerun: still exactly one basis row for the same import
    with engine.connect() as c:
        rows = c.execute(text("SELECT basis, site_import_id FROM site_cutover_basis WHERE site_id = :s"),
                         {"s": site_id}).all()
        imported = c.execute(text("SELECT id FROM site_import WHERE site_id = :s"), {"s": site_id}).scalar_one()
    assert [(r.basis, r.site_import_id) for r in rows] == [("NO_LEGACY_EVIDENCE", imported)]

    legacy = import_legacy_declared(store, tmp_path, "KOBO-912")  # legacy-declared: no basis, no passing comparison
    assert legacy.site_type == "MINIGRID"
    assert store.no_legacy_evidence_basis(legacy.tenant_id, legacy.id) is False

    with _client(monkeypatch) as client:
        for day in ("2026-10-06", "2026-10-12"):
            response = client.get(f"/api/sites/MG-W402-001/overview?date={day}")
            assert response.status_code == 200, response.text
        refused = client.get("/api/sites/KOBO-912/overview?date=2026-10-06")
        assert refused.status_code == 409, refused.text
        assert refused.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
        # UTC-day parsing is unchanged behind the basis.
        assert client.get("/api/sites/MG-W402-001/overview?date=2026-13-40").status_code == 422


def test_installer_records_no_basis_when_a_legacy_document_declares_the_site(store, engine, monkeypatch) -> None:  # noqa: F811
    """B-L2: the installer's basis is guarded. Real legacy documents read from the fixture's own store root declare
    MG-W402-001 at the import's path, so the import succeeds but no cutover basis is written and the Overview keeps
    the 409 instead of inferring the basis."""
    documents = legacy_documents((Path(FIXTURE_PATH).parent,))
    assert MG_W402_SITE_CODE in [d.site_code for d in documents]
    installed = install_mg_w402_site(store, tenant_slug="demo", clock=s1.Clock(INSTALLED), legacy_documents=documents)
    tenant_id, site_id = installed.result.site.tenant_id, installed.result.site.id
    assert store.no_legacy_evidence_basis(tenant_id, site_id) is False
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM site_cutover_basis WHERE site_id = :s"),
                         {"s": site_id}).scalar_one() == 0
    with _client(monkeypatch) as client:
        refused = client.get("/api/sites/MG-W402-001/overview?date=2026-10-06")
        assert refused.status_code == 409, refused.text
        assert refused.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"


def test_a_basis_for_another_import_digest_no_longer_matches(store, engine) -> None:  # noqa: F811
    installed = install(store)
    tenant_id, site_id = installed.result.site.tenant_id, installed.result.site.id
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("UPDATE site_cutover_basis SET source_sha256 = :sha WHERE site_id = :s"),
                  {"sha": "0" * 64, "s": site_id})
    assert store.no_legacy_evidence_basis(tenant_id, site_id) is False


def test_a_basis_needs_the_import_record(store) -> None:  # noqa: F811
    legacy = import_site(store, "KOBO-913").site
    store.record_no_legacy_evidence_basis(legacy.tenant_id, legacy.id, now=legacy.created_at)
    assert store.no_legacy_evidence_basis(legacy.tenant_id, legacy.id) is True  # explicit write only
    with pytest.raises(ValueError):
        store.record_no_legacy_evidence_basis(legacy.tenant_id, replace(legacy, id=legacy.tenant_id).id,
                                              now=legacy.created_at)
