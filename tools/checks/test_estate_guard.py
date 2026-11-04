"""W3-01 commit 2 (q5 ruling 3, c2 r1 q11-A 2): self-tests for the read-only estate guard integration.

Each test copies the guard inputs (`tools/`, `backend/assetops_backend/`, `config/`, `contracts/`) into a private
temporary directory, edits the copy, and runs the configuration-persistence seam (rules 1-8) there; the tracked
workspace is never written. `tools/check-all.ps1` runs this file as a required step.

    python -m pytest tools/checks/test_estate_guard.py

- `test_pg_reader_import_allowed`: the real `$pgReaders` module (`estate/adapters/postgres_estate_read.py`) imports
  the driver and reads, and the seam passes; the same driver import in an unlisted adapter module is refused.
- `test_pg_reader_write_rejected`: the same reader with one INSERT fails rule 8's single-writer refusal.
- `test_domain_driver_import_rejected`: a driver import in the estate package above `adapters/` fails rule 2, which
  only applies because `estate` is a `$domains` entry.
W3-02 adds its own reader path to `$pgReaders` with its own reviewed file and guard test.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NL = chr(10)
ROOT = Path(__file__).resolve().parents[2]
ESTATE = "backend/assetops_backend/estate"
READER = f"{ESTATE}/adapters/postgres_estate_read.py"
UNLISTED = f"{ESTATE}/adapters/_guard_probe_unlisted_read.py"
ABOVE_ADAPTERS = f"{ESTATE}/_guard_probe_driver.py"
GUARD_INPUTS = ("tools", "backend/assetops_backend", "backend/migrations", "config", "contracts", ".gitignore")

READER_SELECT = (
    '"""Guard probe: a read-only estate adapter."""\n\n'
    "from sqlalchemy import text\n\n"
    '_PROBE = text("SELECT id FROM action WHERE tenant_id = :t")\n'
)
READER_INSERT = '\n_PROBE_WRITE = text("INSERT INTO action (id, tenant_id) VALUES (:i, :t)")\n'
DOMAIN_DRIVER = '"""Guard probe: storage technology above the estate adapter layer."""\n\nimport sqlalchemy\n'


def run_seam(cwd: Path) -> subprocess.CompletedProcess[str]:
    script = ('$ErrorActionPreference = "Stop"; . (Join-Path $PWD "tools/checks/_common.ps1"); '
              '. (Join-Path $PWD "tools/checks/configuration-persistence.ps1"); '
              '$f = @(Invoke-ConfigurationPersistenceCheck); '
              'if ($f.Count -gt 0) { $f | ForEach-Object { Write-Output "- $_" }; exit 1 }; Write-Output "passed"')
    env = dict(os.environ, ASSETOPS_GUARD_PYTHON=sys.executable)
    return subprocess.run(["powershell", "-NoProfile", "-Command", script],
                          cwd=cwd, capture_output=True, text=True, env=env)


def isolated_copy(edit) -> subprocess.CompletedProcess[str]:
    """Run the seam over a temporary copy of the guard inputs after `edit(copy_root)`."""
    with tempfile.TemporaryDirectory(prefix="estate-guard-") as tmp:
        copy = Path(tmp)
        for name in GUARD_INPUTS:
            source = ROOT / name
            if source.is_file():
                shutil.copy2(source, copy / name)
            elif source.exists():
                shutil.copytree(source, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        edit(copy)
        return run_seam(copy)


def with_probe(path: str, body: str) -> subprocess.CompletedProcess[str]:
    def edit(copy: Path) -> None:
        file = copy / path
        assert not file.exists(), f"{path} exists in the copy"
        file.write_text(body, encoding="utf-8")
    return isolated_copy(edit)


def failures(out: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in out.stdout.splitlines() if line.startswith("- ")]


def test_pg_reader_import_allowed() -> None:
    out = isolated_copy(lambda copy: None)  # the real reader, unmodified, imports the driver and reads
    assert out.returncode == 0, NL.join(failures(out)) or out.stderr
    real = (ROOT / READER).read_text(encoding="utf-8")
    assert "from sqlalchemy" in real or "import sqlalchemy" in real
    refused = with_probe(UNLISTED, READER_SELECT)  # the allowance is the listed path, not the adapter layer
    assert refused.returncode == 1 and any(
        "Database driver imported outside" in line and UNLISTED in line for line in failures(refused)), refused.stdout


def test_pg_reader_write_rejected() -> None:
    def edit(copy: Path) -> None:
        file = copy / READER
        file.write_text(file.read_text(encoding="utf-8") + READER_INSERT, encoding="utf-8")
    out = isolated_copy(edit)
    found = failures(out)
    assert out.returncode == 1
    assert any(f"A second product database writer in {READER}:" in line for line in found), found
    assert not any("Database driver imported outside" in line and READER in line for line in found), found


def test_domain_driver_import_rejected() -> None:
    out = with_probe(ABOVE_ADAPTERS, DOMAIN_DRIVER)
    found = failures(out)
    assert out.returncode == 1
    assert any(f"Storage technology above the adapter layer in {ABOVE_ADAPTERS}:" in line for line in found), found
    assert any(f"Database driver imported outside" in line and ABOVE_ADAPTERS in line for line in found), found


# W5-02a K1b (ruling A5/B3): the read-only domain Action index adapter is a listed `$pgReaders` module - its driver
# import is admitted, and one INSERT in it still fails rule 8's single-writer refusal.
DOMAIN_READER = "backend/assetops_backend/work/adapters/postgres_domain_action_index.py"
DOMAIN_READER_INSERT = '\n_PROBE_WRITE = text("INSERT INTO domain_action (id, tenant_id) VALUES (:i, :t)")\n'


def test_domain_action_index_reader_allowed_and_write_rejected() -> None:
    real = (ROOT / DOMAIN_READER).read_text(encoding="utf-8")
    assert "from sqlalchemy" in real

    def edit(copy: Path) -> None:
        file = copy / DOMAIN_READER
        file.write_text(file.read_text(encoding="utf-8") + DOMAIN_READER_INSERT, encoding="utf-8")
    out = isolated_copy(edit)
    found = failures(out)
    assert out.returncode == 1
    assert any(f"A second product database writer in {DOMAIN_READER}:" in line for line in found), found
    assert not any("Database driver imported outside" in line and DOMAIN_READER in line for line in found), found


# OUT-E E3: the trial cost-check store is a `$pgWriters` entry and the sole, INSERT-only writer of
# `trial_cost_comparison_revision`. The probes prove the rule fails without the registration, without the owner
# INSERT (anti-vacuity), with an UPDATE in the writer and with a write from another module.
TRIAL_WRITER = "backend/assetops_backend/financials/adapters/postgres_trial_comparison_store.py"
TRIAL_GUARD = "tools/checks/configuration-persistence.ps1"
TRIAL_INSERT = "INSERT INTO trial_cost_comparison_revision ("
TRIAL_FOREIGN = "backend/assetops_backend/financials/adapters/_guard_probe_trial_write.py"


def _replace(copy: Path, path: str, old: str, new: str) -> None:
    file = copy / path
    text = file.read_text(encoding="utf-8")
    assert text.count(old) == 1, (path, old)
    file.write_text(text.replace(old, new), encoding="utf-8")


def test_trial_comparison_writer_registered() -> None:
    real = (ROOT / TRIAL_WRITER).read_text(encoding="utf-8")
    assert TRIAL_INSERT in real and "from sqlalchemy" in real
    assert isolated_copy(lambda copy: None).returncode == 0
    out = isolated_copy(lambda copy: _replace(copy, TRIAL_GUARD, ", $trialComparisonWriter)", ")"))
    found = failures(out)
    assert out.returncode == 1
    assert any("Database driver imported outside" in line and TRIAL_WRITER in line for line in found), found


def test_trial_comparison_insert_only_and_not_vacuous() -> None:
    out = isolated_copy(lambda copy: _replace(copy, TRIAL_WRITER, TRIAL_INSERT,
                                              "INSERT INTO trial_cost_comparison_probe ("))
    found = failures(out)
    assert out.returncode == 1
    assert any("found no INSERT INTO trial_cost_comparison_revision" in line for line in found), found

    def update(copy: Path) -> None:
        file = copy / TRIAL_WRITER
        file.write_text(file.read_text(encoding="utf-8") + '\n_PROBE = text("UPDATE trial_cost_comparison_revision '
                        'SET state = :s WHERE id = :i")\n', encoding="utf-8")
    found = failures(isolated_copy(update))
    assert any("trial cost-check store never updates" in line or "insert-only" in line for line in found), found


def test_trial_comparison_foreign_write_rejected() -> None:
    body = ('"""Guard probe: a second writer of the cost-check table."""\n\nfrom sqlalchemy import text\n\n'
            '_PROBE = text("INSERT INTO trial_cost_comparison_revision (id) VALUES (:i)")\n')
    found = failures(with_probe(TRIAL_FOREIGN, body))
    assert any(TRIAL_FOREIGN in line for line in found), found


THREAD_WRITER = "backend/assetops_backend/chain/adapters/postgres_thread_store.py"
THREAD_READER = "backend/assetops_backend/chain/adapters/postgres_thread_sources.py"
THREAD_INSERT = "INSERT INTO finding_thread_event ("


def test_thread_writer_insert_only_and_not_vacuous() -> None:
    """CH-2 §8: the thread store keeps one owner INSERT per thread table and never updates."""
    real = (ROOT / THREAD_WRITER).read_text(encoding="utf-8")
    assert THREAD_INSERT in real and "from sqlalchemy" in real
    found = failures(isolated_copy(lambda copy: _replace(copy, THREAD_WRITER, THREAD_INSERT,
                                                         "INSERT INTO finding_thread_probe (")))
    assert any("found no INSERT INTO finding_thread_event" in line for line in found), found

    def update(copy: Path) -> None:
        file = copy / THREAD_WRITER
        file.write_text(file.read_text(encoding="utf-8") + '\n_PROBE = text("UPDATE finding_thread '
                        'SET subject_ref = :s WHERE id = :i")\n', encoding="utf-8")
    found = failures(isolated_copy(update))
    assert any("thread store never updates" in line or "insert-only" in line for line in found), found


def test_thread_sources_reader_write_rejected() -> None:
    """CH-2 §8: the thread source reader is a `$pgReaders` module; a write in it is refused."""
    def edit(copy: Path) -> None:
        file = copy / THREAD_READER
        file.write_text(file.read_text(encoding="utf-8") +
                        '\n_PROBE_WRITE = text("INSERT INTO finding_thread (id) VALUES (:i)")\n', encoding="utf-8")
    found = failures(isolated_copy(edit))
    assert any(THREAD_READER in line for line in found), found
    assert not any("Database driver imported outside" in line and THREAD_READER in line for line in found), found


SNAPSHOT_WRITER = "backend/assetops_backend/chain/adapters/postgres_snapshot_store.py"
SNAPSHOT_INSERT = "INSERT INTO site_day_snapshot ("


def test_snapshot_writer_insert_only_and_not_vacuous() -> None:
    """CH-1a §7 (CH-2 review Low): the day-snapshot store keeps its owner INSERT and never deletes."""
    real = (ROOT / SNAPSHOT_WRITER).read_text(encoding="utf-8")
    assert SNAPSHOT_INSERT in real and "from sqlalchemy" in real
    found = failures(isolated_copy(lambda copy: _replace(copy, SNAPSHOT_WRITER, SNAPSHOT_INSERT,
                                                         "INSERT INTO site_day_snapshot_probe (")))
    assert any("found no INSERT INTO site_day_snapshot" in line for line in found), found

    def delete(copy: Path) -> None:
        file = copy / SNAPSHOT_WRITER
        file.write_text(file.read_text(encoding="utf-8") +
                        '\n_PROBE = text("DELETE FROM site_day_snapshot WHERE tenant_id = :t")\n', encoding="utf-8")
    found = failures(isolated_copy(delete))
    assert any("day-snapshot store never updates" in line or "insert-only" in line for line in found), found


EVENT_WRITER = "backend/assetops_backend/chain/adapters/postgres_event_store.py"
EVENT_MIGRATION = "backend/migrations/versions/0044_chain_events.py"
EVENT_CONSUMED = "INSERT INTO event_consumption ("
EVENT_DONE = "AND marked_at = :at"
EVENT_ARBITER = "ON CONFLICT (source, idempotency_key) DO NOTHING;"


def _append(copy: Path, path: str, body: str) -> None:
    file = copy / path
    file.write_text(file.read_text(encoding="utf-8") + body, encoding="utf-8")


def test_event_store_statements_declared_and_not_vacuous() -> None:
    """CH-1b §7: the event store runs only its four declared statements, and each is present."""
    real = (ROOT / EVENT_WRITER).read_text(encoding="utf-8")
    assert EVENT_CONSUMED in real and EVENT_DONE in real and "from sqlalchemy" in real
    found = failures(isolated_copy(lambda copy: _replace(copy, EVENT_WRITER, EVENT_CONSUMED,
                                                         "INSERT INTO event_consumption_probe (")))
    assert any("found no event_consumption insert statement" in line for line in found), found
    # The compare-and-delete must compare marked_at: a plain DELETE of the queue row is refused.
    found = failures(isolated_copy(lambda copy: _replace(copy, EVENT_WRITER, EVENT_DONE, "")))
    assert any("event store runs only its four declared statements" in line for line in found), found
    assert any("found no snapshot_dirty compare-and-delete statement" in line for line in found), found
    # event_consumption is insert-only; a non-backfill outbox INSERT from Python is refused.
    found = failures(isolated_copy(lambda copy: _append(copy, EVENT_WRITER,
        '\n_PROBE = text("UPDATE event_consumption SET processed_at = now() WHERE event_id = :e")\n'
        '_PROBE_2 = text("INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, '
        "subject, idempotency_key) VALUES ('reading.accepted', 1, :o, 'x', :t, :s, '{}', :k) "
        'ON CONFLICT (source, idempotency_key) DO NOTHING")\n')))
    refused = [line for line in found if "event store runs only its four declared statements" in line]
    assert any("UPDATE event_consumption" in line for line in refused), found
    assert any("reading.accepted" in line for line in refused), found


EVENT_PAGE_ACCEPT = (
    '\n_PROBE = text("INSERT INTO event_consumption (consumer, event_id) VALUES (:c_0, :e_0), (:c_1, :e_1)")\n'
    '_PROBE_2 = text("INSERT INTO snapshot_dirty (tenant_id, site_id, local_day, measure, first_event_id) "\n'
    '                "VALUES (:t_0, :s_0, :d_0, :m_0, :e_0), (:t_1, :s_1, :d_1, :m_1, :e_1) "\n'
    '                "ON CONFLICT (tenant_id, site_id, local_day, measure) DO UPDATE SET marked_at = clock_timestamp()")\n')
EVENT_PAGE_REJECT = (
    '\n_PROBE = text("INSERT INTO event_consumption (consumer, event_id) SELECT :c, unnest(CAST(:ids AS uuid[]))")\n'
    '_PROBE_2 = text("INSERT INTO event_consumption (consumer, event_id) VALUES (:c, unnest(:ids))")\n'
    '_PROBE_3 = text("INSERT INTO snapshot_dirty (tenant_id, site_id, local_day, measure, first_event_id) "\n'
    '                "SELECT tenant_id, site_id, local_day, measure, first_event_id FROM snapshot_dirty_probe "\n'
    '                "ON CONFLICT (tenant_id, site_id, local_day, measure) DO UPDATE SET marked_at = clock_timestamp()")\n'
    '_PROBE_4 = text("INSERT INTO snapshot_dirty (tenant_id, site_id, local_day, measure, first_event_id) "\n'
    '                "VALUES (:t_0, :s_0, :d_0, :m_0, :e_0), (:t_1, :s_1, :d_1, :m_1, :e_1) "\n'
    '                "ON CONFLICT (tenant_id, site_id, local_day) DO UPDATE SET marked_at = clock_timestamp()")\n')


def test_event_page_writes_accept_multi_row_values_only() -> None:
    """CH1b-R2 note 3: the page write's multi-row VALUES list is accepted for the consumption insert and the mark
    upsert; a SELECT, an unnest or another ON CONFLICT arbiter is refused."""
    accepted = isolated_copy(lambda copy: _append(copy, EVENT_WRITER, EVENT_PAGE_ACCEPT))
    assert accepted.returncode == 0 and "passed" in accepted.stdout, failures(accepted) or accepted.stdout
    found = failures(isolated_copy(lambda copy: _append(copy, EVENT_WRITER, EVENT_PAGE_REJECT)))
    refused = [line for line in found if "event store runs only its four declared statements" in line]
    assert any("SELECT :c, unnest" in line for line in refused), found
    assert any("VALUES (:c, unnest(:ids))" in line for line in refused), found
    assert any("FROM snapshot_dirty_probe" in line for line in refused), found
    assert any("ON CONFLICT (tenant_id, site_id, local_day) DO UPDATE" in line for line in refused), found


def test_event_tables_foreign_write_rejected() -> None:
    """CH-1b §7: another registered writer may not write an event table; the outbox is trigger-written."""
    found = failures(isolated_copy(lambda copy: _append(copy, SNAPSHOT_WRITER,
        '\n_PROBE = text("INSERT INTO event_outbox (type) VALUES (:t)")\n'
        '_PROBE_2 = text("DELETE FROM snapshot_dirty WHERE tenant_id = :t")\n')))
    assert any("event outbox is written only by the migration 0044 triggers" in line for line in found), found
    assert any("writes event table 'snapshot_dirty'" in line for line in found), found


def test_event_migration_arbiter_and_not_vacuous() -> None:
    """CH-1b §7: the 0044 producers keep the DO NOTHING arbiter; removing every producer INSERT is vacuous."""
    real = (ROOT / EVENT_MIGRATION).read_text(encoding="utf-8")
    assert real.count(EVENT_ARBITER) == 1
    found = failures(isolated_copy(lambda copy: _replace(copy, EVENT_MIGRATION, EVENT_ARBITER,
                                                         "ON CONFLICT (source, idempotency_key) DO UPDATE SET payload = '{}';")))
    assert any("keeps exactly the ON CONFLICT (source, idempotency_key) DO NOTHING arbiter" in line for line in found), found
    assert any("runs no ON CONFLICT DO UPDATE" in line for line in found), found
    found = failures(isolated_copy(lambda copy: _replace(copy, EVENT_MIGRATION, '"INSERT INTO event_outbox (',
                                                         '"INSERT INTO event_outbox_probe (')))
    assert any("found no INSERT INTO event_outbox in" in line for line in found), found
