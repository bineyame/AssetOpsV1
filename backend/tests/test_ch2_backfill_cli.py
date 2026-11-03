"""CH-2 L4: the backfill CLI refuses the protected databases and a dry run writes nothing (fake reader and store)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from assetops_backend.chain import backfill


class FakeReader:
    def __init__(self, db: str) -> None:
        self.db, self.tenant = db, uuid4()
        self.calls: list[str] = []

    def database_name(self): return self.db
    def tenant_id(self, slug): self.calls.append("tenant_id"); return self.tenant
    def site_ids(self, tenant_id, code=None): self.calls.append("site_ids"); return [(uuid4(), "X")]
    def sources(self, tenant_id, site_id=None, after=None): self.calls.append("sources"); return []
    def opportunity_labels(self, tenant_id): self.calls.append("labels"); return {}
    def all_actions(self, tenant_id, site_id=None): self.calls.append("all_actions"); return []
    def unlinked_actions(self, tenant_id, site_id=None): self.calls.append("unlinked"); return []


class TrippedStore:
    def __getattr__(self, name):
        raise AssertionError(f"the store was touched: {name}")


@pytest.fixture(autouse=True)
def _url(monkeypatch):
    monkeypatch.setattr(backfill, "database_url", lambda: "postgresql://x/y")


@pytest.mark.parametrize("db", ["assetops_polish_full_test", "assetops_demo3_full_test"])
def test_protected_databases_are_refused_before_any_read_or_write(db, capsys):
    reader = FakeReader(db)
    assert backfill.main(["--steps", "b,c"], reader=reader, store=TrippedStore()) == 2
    assert reader.calls == [] and "read-only" in capsys.readouterr().err


def test_dry_run_on_a_protected_database_reads_and_never_touches_the_store(capsys):
    reader = FakeReader("assetops_polish_full_test")
    assert backfill.main(["--dry-run", "--steps", "a,b,c,d,e"], reader=reader, store=TrippedStore()) == 0
    out = capsys.readouterr().out
    assert "sources" in reader.calls and '"dry_run": true' in out
    assert '"step": "d"' in out and '"step": "e"' in out and '"step": "a"' in out and "skipped" in out


def test_a_non_protected_database_writes_through_the_store():
    class Store(TrippedStore):
        def __getattr__(self, name):
            raise RuntimeError("write attempted")
    with pytest.raises((RuntimeError, AttributeError, TypeError)):
        backfill.main(["--steps", "b"], reader=_with_source(FakeReader("assetops_scratch_test")), store=Store())


def _with_source(reader):
    from datetime import datetime, timezone
    from assetops_backend.chain.threads import Source
    s = Source(uuid4(), uuid4(), "UTC", uuid4(), None, "M", "ASSET", "a", "M@1", None, "ACTIVE", None, None,
               datetime(2026, 1, 1, tzinfo=timezone.utc), uuid4())
    reader.sources = lambda *a, **k: [s]
    return reader


def test_step_a_calls_build_range_for_each_site_from_first_evidence_to_today():
    from datetime import datetime, timezone
    from types import SimpleNamespace

    first = datetime(2026, 10, 1, 5, 0, tzinfo=timezone.utc)
    calls = []

    class Inputs:
        def site(self, tenant_id, code): return SimpleNamespace(site_id=uuid4(), timezone="UTC")
        def first_evidence_time(self, tenant_id, site_id): return first

    class Builder:
        def build_range(self, tenant_id, site, from_day, to_day, *rest):
            calls.append((from_day, to_day))
            return [SimpleNamespace(written=True), SimpleNamespace(written=False)]

    services = SimpleNamespace(inputs=Inputs(), builder=Builder(), dispose=lambda: None)
    reader = FakeReader("assetops_scratch_test")
    out = backfill._step_a(reader, reader.tenant, None, "postgresql://x/y", False, services)
    assert calls and calls[0][0].isoformat() == "2026-10-01" and out["written"] == 1 and out["sites"][0]["considered"] == 2
