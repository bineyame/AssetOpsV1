"""W5-03a E1a: persisted EV depth producers over W2-05b's registered `Chain` (test fixture only).

Every case runs the real registered path (Draft run, host stage, gateway upload, central ingestion, W2-06 worker) in
a private `*_test` database; nothing here imports private simulator truth into a product read. Window
`[2026-10-06T08:00Z, 09:00Z)`; `Chain.decision_clock()` is 09:00, then 09:05 after `advance_late()`.

- `settled(chain, case)`: `complete` (observed, historical), `missing-meter` (partial energy), `fault` /
  `interrupted` (faulted status), `late-record` (first cutoff of the pending case).
- `pending(chain)`: `late-record` settled at 09:00, then `advance_late()` with its recompute job left unrun.
- `status_gap(chain)`: `complete` with the five Connector c1 state reports in `[08:40, 08:45)` omitted from the
  registered series before publication (a gap five times the one-minute cadence), then assessed at the returned decision clock.
- `declared_empty(built)`: a test-scoped time-valid Foundation revision with `weekly: []` for every connector,
  selected by a new assessment of the same window.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from test_w205b_ev_replay_postgres import CASES, URL, Chain, chain  # noqa: F401

if URL:
    from sqlalchemy import text

    from assetops_contracts.source_envelope import canonical_json
    from test_w206_ev_store_postgres import run_worker, select_exact

LO = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
HI = datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)
QUERY = "from=2026-10-06T08:00:00Z&to=2026-10-06T09:00:00Z"
#: The saved first watermark a historical read passes as `known_at`.
HISTORICAL_KNOWN_AT = "2026-10-06T09:00:00.000000Z"
GAP_DEVICE, GAP_SIGNAL = "c1-connector-controller", "state"
GAP_FROM, GAP_TO = "2026-10-06T08:40:00Z", "2026-10-06T08:45:00Z"


def settled(chain, case: str = "complete") -> Chain:  # noqa: F811
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    select_exact(built, LO, HI)  # the exact selected `[08:00, 09:00)` window at the committed cutoff
    return built


def pending(chain) -> Chain:  # noqa: F811
    """`late-record`: assessed at 09:00, then the 09:05 late release leaves an unrun overlapping recompute job."""
    built = settled(chain, "late-record")
    built.advance_late()
    return built


def status_gap(chain) -> Chain:  # noqa: F811
    """`complete` with Connector c1's state reports in `[08:40, 08:45)` dropped from the registered public series
    before it is sealed and published (`lab_execution.ev_reports`), so they never reach the gateway."""
    import lab_execution

    original = lab_execution.ev_reports
    omitted: list[str] = []

    def omitting(*args, **kwargs):
        kept = []
        for report in original(*args, **kwargs):
            if (report.device_id == GAP_DEVICE and report.signal_id == GAP_SIGNAL
                    and GAP_FROM <= report.source_time < GAP_TO):
                omitted.append(report.source_time)
            else:
                kept.append(report)
        return tuple(kept)

    built = chain("complete")
    lab_execution.ev_reports = omitting
    try:
        built.start_release_upload()
    finally:
        lab_execution.ev_reports = original
    run_worker(built)
    select_exact(built, LO, HI)
    assert sorted(omitted) == [f"2026-10-06T08:4{m}:00Z" for m in range(5)], omitted
    return built


def declared_empty(built: Chain) -> str:
    """Supersede the selected Foundation with a time-valid copy whose connector schedules are all `weekly: []`,
    recorded before the committed watermark, then select a new assessment of the window over it. Returns the new
    revision ID (lowercase)."""
    with built.engine.connect() as c:
        orig = c.execute(text("SELECT * FROM foundation_revision WHERE site_id = :s AND superseded_at IS NULL "
                              "ORDER BY version DESC LIMIT 1"), {"s": built.site_id}).mappings().one()
        top = c.execute(text("SELECT max(version) FROM foundation_revision WHERE site_id = :s"),
                        {"s": built.site_id}).scalar_one()
        watermark = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                              {"s": built.site_id}).scalar_one()
    content = dict(orig["content"] if isinstance(orig["content"], dict) else json.loads(orig["content"]))
    content["connector_enable_schedules"] = [{**x, "weekly": []} for x in content["connector_enable_schedules"]]
    new_id = uuid4()
    with built.engine.begin() as c:
        at = c.execute(text("SELECT CAST(:r AS timestamptz) + interval '1 microsecond'"),
                       {"r": orig["recorded_at"]}).scalar_one()
        assert at <= watermark
        c.execute(text("UPDATE foundation_revision SET superseded_at = :at WHERE id = :orig"),
                  {"at": at, "orig": orig["id"]})
        c.execute(text(
            "INSERT INTO foundation_revision (id, tenant_id, site_id, version, valid_from, valid_to, recorded_at, "
            "superseded_at, schema_version, content, content_sha256, origin, derived_from_revision_id, change_note) "
            "VALUES (:id, :t, :s, :v, :vf, :vt, :at, NULL, :sv, CAST(:content AS jsonb), :sha, 'PUBLISH', :orig, "
            ":note)"),
            {"id": new_id, "t": orig["tenant_id"], "s": orig["site_id"], "v": top + 1, "vf": orig["valid_from"],
             "vt": orig["valid_to"], "at": at, "sv": orig["schema_version"], "content": json.dumps(content),
             "sha": hashlib.sha256(canonical_json(content).encode()).hexdigest(), "orig": orig["id"],
             "note": "W5-03a E1a test-scoped Foundation with empty weekly schedules"})
    select_exact(built, LO, HI)
    return str(new_id).lower()
