# Implementer confirmation: parallel telemetry and commercial lanes (2026-10-27)

Reviewed `.agent/parallel-feasibility-2026-10-27.md` against code (read-only greps).

## Verdict: AGREE-WITH-CHANGES

The write-set claims hold. Two lanes, one validation queue, is workable. Changes below are small.

## Checked and confirmed
- Single migration writer: head is `backend/migrations/versions/0035_w5_ev_work.py`; no telemetry migration.
- TEL-05 move: `tools/checks/dependency-direction.ps1:233-240` scans `backend` with `-IncludeTests` for `assetops_gateway`, so a backend test importing the gateway or field fails. `host/tests` is the right home. Precedent: `host/tests/test_s6_verification_publication.py` already uses a database and `gateway_process`.
- `host/conftest.py` (module docstring) makes host tests import without installing `host`, matching "host and field are not installed".
- `backend/tests` fixtures are already read from host tests (`host/tests/test_cold_lab_execution.py:45`), so TEL-05 can reach `pg_harness` and the Kobo basis the same way.

## Missed or under-specified items
1. `tools/checks/module-roots.ps1:15-30` lists required directories (`gateway`, `gateway/assetops_gateway`, ...) and `requiredFiles` below it. TEL-01 must add `field`, `field/assetops_field` and its `pyproject.toml` here. The doc lists the file but not that the lane must add required-root entries, not just forbid-rules.
2. `dependency-direction.ps1:476` excludes `host/tests/*` from the host-imports-pack scan, but the host-side gateway check (~l.225-231) counts `hostChannelImports`. A new TEL-05 under `host/tests` that imports `assetops_field` needs an explicit allow rule for `host/tests` in the D4 check, or the new "no field in host product" rule will flag it. State that the field-forbid scopes to `host/` non-tests.
3. Heavy-lite: TEL-04/06a start a real gateway process; `host/tests/gateway_process.py` ports are not named in the doc. Reserve fixed ports (5020, TLS) in TEL-00 and check the commercial dev server (5173/8000) does not use them.
4. `pg_harness.py:72` names databases `<stem>_pt<run>_<tag>_test`; fine. But a telemetry host-side Postgres test and a commercial backend run share one container, so two heavy runs at once still contend on connections. The queue rule covers this.

## Practicality
- Review load: the 6-review grouping is fine. TEL-01 merges first and the shared check edit is small; commercial R1 will need a `main` merge.
- One shared venv: if the coordinator installs `pymodbus` mid-sprint, a commercial full suite is unaffected, but a stale `PYTHONPATH` in a reused terminal is the real risk. Add the PYTHONPATH line to each lane's first task file, not just this doc.
- 29 Oct TEL-05 deadline with one implementer is tight; TEL-06a is correctly the first slip.
