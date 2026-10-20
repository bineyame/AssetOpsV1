"""Seed w401h_test for the W4-01 commit-5 captures (q3-10): a fresh migrated DB, KOBO-001 imported by the real
importer (as the S2 walkthrough runs it, so the served Site document matches var/sites/kobo-001.yaml), then Site
work cases written through the W4 command service with the private SERVICE principal (`service:w401-fixture`, the
harness of `test_w401_work_service_postgres.py`) at real DB time. The UI reads them only through the normal Site GET
routes. Seven incidents (five-row paging), three requests (one completed with an activity record, one cancelled).
No Finding/Action link: F01's accepted evidence is received 2026-10-30 (after real DB time), so a cited link is
refused by the B7 acceptance cutoff (q2-4); pinned-link rendering is covered by jsdom."""
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

ROOT = r"C:\Users\assef\Bineyame\AssetOpsV1-review"
sys.path.insert(0, ROOT + r"\backend\tests")
import pg_harness  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from test_s4_finding_store_postgres import URL  # noqa: E402

pg_harness.fresh_database()
engine = create_engine(URL)
pg_harness.assert_at_head(engine)
subprocess.run([sys.executable, "-m", "assetops_backend.sites.import_kobo", "--source", "var/sites/kobo-001.yaml",
                "--tenant", "demo"], cwd=ROOT, env={**os.environ, "DATABASE_URL": URL}, check=True,
               capture_output=True)
with engine.connect() as c:
    tenant, site = c.execute(text("SELECT tenant_id, id FROM site WHERE site_code = 'KOBO-001'")).one()
from test_w401_work_service_postgres import Ctx, event, incident, record, request  # noqa: E402

ctx = Ctx(SimpleNamespace(tenant=tenant, site=site, engine=engine))
now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
z = lambda d: d.isoformat().replace("+00:00", "Z")  # noqa: E731
day = now.replace(hour=0, minute=0)
cases = [
    ("Generator did not start on grid loss", "Grid supply dropped; the automatic start request was sent and the generator stayed off for 9 minutes."),
    ("Battery output limit reached", "Battery discharge hit its configured limit during the evening peak; load shed on two feeders."),
    ("Inverter tripped on overtemperature", "Inverter 2 tripped and restarted after cooling; cause under review."),
    ("Witnessed start request failed", "Operator observed a failed start request; cause not established."),
    ("Feeder breaker opened", "Feeder B breaker opened without a recorded fault; reclosed by hand."),
    ("Solar output lower than forecast", "Midday PV output stayed below forecast on a clear day; soiling suspected, not confirmed."),
    ("Communication loss with gateway", "No readings for 40 minutes; gateway rebooted on site."),
]
made = []
for i, (title, narrative) in enumerate(cases):
    occurred = day - timedelta(days=1 + i % 6, hours=-(9 + i), minutes=-(7 * i))
    _, c = ctx.case(incident(f"w401h-inc-{i}", occurred_at=z(occurred), title=title, narrative=narrative))
    made.append(c)
ctx.event(made[1]["id"], event("ASSIGN", {"assignee": "maintenance-lead"}, "w401h-assign-1", occurred_at=z(now - timedelta(minutes=30))))
ctx.event(made[2]["id"], event("CLOSE", {"reason": "Breaker reclosed and held"}, "w401h-close-2", occurred_at=z(now - timedelta(minutes=25))))
_, r1 = ctx.case(request("w401h-req-1", occurred_at=z(now - timedelta(hours=3)), title="Inspect starter circuit",
                         narrative="Witnessed failure requires inspection.", incident_id=made[3]["id"]))
ctx.event(r1["id"], event("ASSIGN", {"assignee": "tech-1"}, "w401h-req-1-assign", occurred_at=z(now - timedelta(minutes=20))))
_, rec1 = ctx.record(r1["id"], record("w401h-rec-1", activity="Starter connection inspected and reseated",
                                    outcome_note="Start test not yet witnessed",
                                    occurred_at=z(now - timedelta(minutes=15))))
ctx.event(r1["id"], event("COMPLETE", {"maintenance_record_id": rec1["id"]}, "w401h-req-1-complete",
                          occurred_at=z(now - timedelta(minutes=12))))
_, r2 = ctx.case(request("w401h-req-2", occurred_at=z(now - timedelta(hours=2)), title="Clean PV array",
                         narrative="Suspected soiling on string 3."))
_, r3 = ctx.case(request("w401h-req-3", occurred_at=z(now - timedelta(hours=1)), title="Replace gateway power supply",
                         narrative="Gateway rebooted twice this week."))
ctx.event(r3["id"], event("CANCEL", {"reason": "Duplicate of an earlier request"}, "w401h-req-3-cancel", occurred_at=z(now - timedelta(minutes=10))))
print("seeded tenant", tenant, "site", site, "incidents", [c["code"] for c in made],
      "requests", r1["code"], r2["code"], r3["code"], "now", z(now))
ctx.close()
engine.dispose()
