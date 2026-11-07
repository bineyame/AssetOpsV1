"""DD1b1-R Q6, Q7 L0: the prepare-only refusal, the unset statement text, and the objectives instant. No database."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from assetops_backend.objectives.adapters import postgres_objective_store as objective_store
from assetops_backend.objectives.adapters.postgres_objective_store import PostgresObjectiveStore, _insert_statement
from assetops_backend.prepare_clock import PrepareClockRefused, require_prepare_database

import demo_combined


def url(database: str) -> str:
    return f"postgresql+psycopg://u:p@127.0.0.1:1/{database}"


@pytest.mark.parametrize("database", ["assetops_polish_x", "assetops_polish_full_test", "foo_test",
                                      "assetops_demo3_main_test"])
def test_prepare_databases_pass(database: str) -> None:
    require_prepare_database(url(database))


@pytest.mark.parametrize("database", ["assetops", "assetops_polish", "assetops_demo3_x", "assetops_test_x"])
def test_other_databases_refuse_by_name(database: str) -> None:
    with pytest.raises(PrepareClockRefused, match=f"PREPARE_CLOCK_REFUSED.*{database}"):
        require_prepare_database(url(database))


@pytest.mark.parametrize("missing", [None, "", "postgresql+psycopg://u:p@127.0.0.1:1"])
def test_no_database_refuses(missing: str | None) -> None:
    with pytest.raises(PrepareClockRefused):
        require_prepare_database(missing)


def test_a_refused_construction_opens_no_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_engine(*_a, **_k):
        raise AssertionError("a refused construction must not build an engine")

    monkeypatch.setattr(objective_store, "create_engine", no_engine)
    with pytest.raises(PrepareClockRefused):
        PostgresObjectiveStore(url("assetops"), test_recorded_clock_override=lambda: datetime.now(timezone.utc))


def test_unset_store_is_not_checked_and_its_statement_is_the_server_clock() -> None:
    assert PostgresObjectiveStore(url("assetops")).test_recorded_clock_override is None
    statement = _insert_statement()
    assert "clock_timestamp(), :min_days)" in statement and ":recorded_at" not in statement
    assert ":recorded_at, :min_days)" in _insert_statement(":recorded_at")


def _story(first_start: str) -> dict:
    return {"ev": {"install_at": "2026-10-10T06:30:00Z"},
            "days": [{"site": "ev", "day": "2026-10-20", "start": "2026-10-20T08:00:00Z"},
                     {"site": "kobo", "day": "x", "start": first_start},
                     {"site": "kobo", "day": "missing", "start": None}]}


def test_objectives_instant_is_ev_install_plus_the_tariff_offset() -> None:
    instant = demo_combined.objectives_instant(_story("2026-10-11T03:00:00Z"))
    assert instant == datetime(2026, 10, 10, 7, 0, tzinfo=timezone.utc)


def test_objectives_instant_stops_when_a_built_day_is_earlier() -> None:
    with pytest.raises(SystemExit, match="OBJECTIVES_INSTANT_CONFLICT.*kobo"):
        demo_combined.objectives_instant(_story("2026-10-10T03:00:00Z"))
