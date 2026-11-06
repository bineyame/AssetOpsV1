"""DD-1a1 (DD1a1-R5 "probe first", L2, own `*_test` DB): one sequence epoch per Site-day stream on the registered
demo Kobo Site, through the real gateway process and the ordinary S2 batch ingestion.

The Site is made the way the demo prepare makes it (`tools/demo_combined_kobo.py` `build`). Each run of one local day
reopens that day's one gateway state (`_publish_and_accept(gateway_dir=...)`), so the epoch's sequence continues
across separately sealed runs; a complement keeps only the source times no story run (and no later complement) sends.

- Day A (2026-10-20): the mill story run (03:00-15:00Z) first, then `night-early` (D-1 21:00-03:00Z) received after
  it with later sequences but earlier source times, then its rest of day `kobo-rest-mill` (15:00-21:00Z) (DD1a2-R Q7
  withdrew the `steady-afternoon` file this probe used; this is the full-day shape the calendar keeps).
- Day B (2026-10-21), a `late` day: `night-early` received at its own end + 1 h plus the late offset (2 d 00:30), then
  the `normal` story run at D+2d 12:30.

Every delivery is COMPLETED with no duplicate, rejection or conflict (asserted in `_publish_and_accept`). The test then
reads `accepted_evidence`: one epoch per source per day, each source time once per stream, and the sequence of each
stream continuous from 1 in admission order.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
MANIFEST = json.loads((ROOT / "backend" / "conversions" / "d-verification-window-v3.json").read_text(encoding="utf-8"))
IMPORT_AT = datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)
INSTALL_AT = IMPORT_AT + timedelta(hours=1)
KNOWN_AT = "2026-10-08T00:00:00Z"
Z = "%Y-%m-%dT%H:%M:%SZ"

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


def _t(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _keep(lo: datetime, hi: datetime, owned: list[tuple[datetime, datetime]]):
    """[lo, hi) minus every story run's closed [start, end]."""
    return lambda s: lo <= _t(s) < hi and not any(a <= _t(s) <= b for a, b in owned)


def test_one_epoch_per_site_day_is_accepted(tmp_path):
    import pg_harness
    import test_s1_bindings_postgres as pgb
    import test_s6_verification_publication as pub
    import test_s6_verification_replay as rp
    from sqlalchemy import create_engine, text

    import demo_combined_kobo as dk
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    pg_harness.fresh_database()
    store = PostgresFoundationStore(URL)
    engine = create_engine(URL)
    seal_before = pub.SEAL_ONCE
    pub.SEAL_ONCE = True
    try:
        result = pgb.imported(store, when=IMPORT_AT)
        pgb.convert(store, pgb.BindingService(store, pgb.Clock(INSTALL_AT)), result.tenant, result.site, pgb.FIXTURE)
        dk.configure_at(store, result, INSTALL_AT)
        with engine.begin() as c:
            c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
            c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})

        def run(epoch, scenario, start, end, received, keep=None):
            M = copy.deepcopy(MANIFEST)
            M["scenario"] = {"scenario_id": scenario, "scenario_version": 1}
            spec = {"start": start, "end": end, "seed": MANIFEST["runs"]["baseline"]["seed"], "sequence_epoch": epoch,
                    "foundation_known_at": KNOWN_AT, "received_at": received}
            drafted, _ = rp._draft(store, spec, M)
            out = rp._publish_and_accept(tmp_path / f"{epoch}-{start[:13]}", drafted, epoch, rp._at(received),
                                         gateway_dir=tmp_path / f"gw-{epoch}", keep=keep)
            print(epoch, scenario, start, end, "received", received, out, flush=True)
            return out

        a3, a15, a21 = _t("2026-10-20T03:00:00Z"), _t("2026-10-20T15:00:00Z"), _t("2026-10-20T21:00:00Z")
        story_a = [(a3, a15)]
        run("probe-a", "kobo-mill-midday", "2026-10-20T03:00:00Z", "2026-10-20T15:00:00Z",
            "2026-10-20T16:00:00Z")
        run("probe-a", "kobo-night-early", "2026-10-19T21:00:00Z", "2026-10-20T03:00:00Z", "2026-10-20T17:00:00Z",
            _keep(_t("2026-10-19T21:00:00Z"), a3, story_a))
        run("probe-a", "kobo-rest-mill", "2026-10-20T15:00:00Z", "2026-10-20T21:00:00Z",
            "2026-10-20T22:00:00Z", _keep(a15, a21, story_a))
        b3, b11 = _t("2026-10-21T03:00:00Z"), _t("2026-10-21T11:00:00Z")
        run("probe-b", "kobo-night-early", "2026-10-20T21:00:00Z", "2026-10-21T03:00:00Z", "2026-10-23T04:30:00Z",
            _keep(_t("2026-10-20T21:00:00Z"), b3, [(b3, b11)]))
        run("probe-b", "kobo-s3-dispatch-necessary-run", "2026-10-21T03:00:00Z", "2026-10-21T11:00:00Z",
            "2026-10-23T12:30:00Z")

        with engine.connect() as c:
            epochs = c.execute(text(
                "SELECT source_id::text, count(DISTINCT sequence_epoch) FROM accepted_evidence "
                "GROUP BY source_id, ((source_time AT TIME ZONE 'UTC') + interval '3 hours')::date")).fetchall()
            twice = c.execute(text(
                "SELECT source_id::text, sequence_epoch, device_id, signal_id, source_time, count(*) "
                "FROM accepted_evidence GROUP BY 1, 2, 3, 4, 5 HAVING count(*) > 1")).fetchall()
            edges = c.execute(text(
                "SELECT source_time, count(*) FROM accepted_evidence WHERE sequence_epoch = 'probe-a' AND "
                "source_time IN ('2026-10-20T03:00:00Z', '2026-10-20T15:00:00Z', '2026-10-20T21:00:00Z') "
                "GROUP BY 1 ORDER BY 1")).fetchall()
            gaps = c.execute(text(
                "SELECT source_id::text, sequence_epoch, min(sequence), max(sequence), count(*) "
                "FROM accepted_evidence GROUP BY 1, 2")).fetchall()
            bounds = c.execute(text(
                "SELECT sequence_epoch, min(source_time), max(source_time), count(*) FROM accepted_evidence "
                "GROUP BY 1 ORDER BY 1")).fetchall()
        print("streams", [tuple(map(str, r)) for r in bounds])
        print("sequence per stream", sorted({(r[1], r[2], r[3], r[4]) for r in gaps}))
        assert {r[1] for r in epochs} == {1}, epochs
        assert twice == [], twice[:5]
        assert all(r[2] == 1 and r[3] == r[4] for r in gaps), gaps
        assert [r[0] for r in bounds] == ["probe-a", "probe-b"]
        # the story run's edge instants are sent once (by the story), and 21:00 belongs to the next day
        print("edges", [(str(r[0]), r[1]) for r in edges])
        assert len(edges) == 2 and edges[0][1] == edges[1][1] > 0, edges
    finally:
        pub.SEAL_ONCE = seal_before  # DD-1a1 review M2: the default per-group seal stays the default for later tests
        pg_harness.dispose(store)
        engine.dispose()


def test_default_seal_path_is_restored_after_the_probe():
    """DD-1a1 review M2: seal-once is off by default (D-2026-10-09); the probe above switches it on only for itself, so
    the S6 publication and replay tests keep exercising the default per-group seal when run after it."""
    import test_s6_verification_publication as pub

    assert pub.SEAL_ONCE is False
