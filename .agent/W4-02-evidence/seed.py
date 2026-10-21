"""Seed w402r_test for the W4-02 unit-7 captures: a fresh migrated DB, MG-W402-001 installed by the W4-02 installer,
an MG-W402-001 gateway credential issued by the provisioning CLI, both authored variants of
`backend/conversions/w4-mini-depth-cases-v1.json` posted as public Batch V2 content to `POST /api/ingestion/batches`
(TLS boundary, registered credential), the mini worker drained, and the replay record (accepted IDs + selection seqs,
no credential) written to `replay.json`.
q12-8: before each gateway upload, the exact sealed Batch V2 is published with the existing server-side authored-publication
command (`assetops_backend.publish_source`, fixture `assetops.w4-mini-depth-cases` v1, Site MG-W402-001); a refused
publication stops the seed. Batch body digests and publication IDs go into the replay record (no credential). This is the harness of `test_w402_replay_selection_postgres.py`, run once
against the private DB; the UI then reads only through uvicorn + vite.
Usage (repo root, PYTHONPATH as in the brief): python .agent/W4-02-evidence/seed.py"""
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/w402r_test"
os.environ["ASSETOPS_TEST_DATABASE_URL"] = URL
for k in ("ASSETOPS_TEST_RUN_ID", "ASSETOPS_TEST_DATABASE_BASE_URL"):
    os.environ.pop(k, None)
sys.path.insert(0, str(ROOT / "backend" / "tests"))
import pg_harness  # noqa: E402

pg_harness.fresh_database()
from sqlalchemy import create_engine  # noqa: E402

engine = create_engine(URL)
pg_harness.assert_at_head(engine)
from test_w402_authored_v4_postgres import cases, install, snapshot  # noqa: E402
from test_w402_replay_selection_postgres import ZONE, _client, _issue  # noqa: E402

from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore  # noqa: E402
from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess  # noqa: E402
from assetops_backend.mini_depth.store import PostgresMiniDepthStore  # noqa: E402
from assetops_backend.mini_depth.worker import MiniDepthWorker  # noqa: E402
from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore  # noqa: E402

store = PostgresFoundationStore(URL)
installed = install(store)
tenant_id, site_id = installed.result.site.tenant_id, installed.result.site.id
access = PostgresGatewayAccess(URL)
with tempfile.TemporaryDirectory() as tmp:
    token = _issue(engine, access, Path(tmp), site_id)
doc, sha = snapshot(engine, installed.binding_set.id)
spec = cases.load_spec()
client = _client(access)
os.environ["DATABASE_URL"] = URL
from assetops_backend import publish_source  # noqa: E402

accepted = {}
publications = []
for variant in spec["variants"]:
    batches = cases.build_batches(spec, doc, sha, variant["variant"])
    for b in batches:
        with tempfile.TemporaryDirectory() as tmp:
            batch_file = Path(tmp) / "batch.json"
            batch_file.write_text(b.body, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = publish_source.main(["--site", "MG-W402-001", "--fixture-id", "assetops.w4-mini-depth-cases",
                                            "--fixture-version", "1", "--batch-file", str(batch_file)])
        if code != 0:
            raise SystemExit(f"publication refused (exit {code}) for {variant['variant']} {b.source_id}; seed stopped")
        found = re.search(r"publication ([0-9a-f-]{36})", out.getvalue())
        publications.append({"variant": variant["variant"], "source_id": b.source_id, "count": b.count,
                             "batch_body_sha256": hashlib.sha256(b.body.encode("utf-8")).hexdigest(),
                             "publication_id": found.group(1) if found else None})
        r = client.post("/api/ingestion/batches", content=b.body,
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        assert r.status_code == 200, r.text
    with engine.connect() as c:
        accepted[variant["variant"]] = cases.accepted_ids(c, str(site_id), cases.message_ids(batches))
mini = PostgresMiniDepthStore(engine)
outcomes = MiniDepthWorker(PostgresAssessmentStore(URL), mini).run_pending(500, tenant_id, site_id)
assert outcomes and all(o.status == "DONE" for o in outcomes)
identity = {"binding_set_revision_id": str(installed.binding_set.id), "role_set": "minigrid-roles-4", "snapshot_sha256": sha}
record = cases.replay_record(spec, identity, doc, accepted)
record["publications"] = publications
record["selections"] = cases.selection_record(mini.site_selections(tenant_id, site_id), ZONE)
assert token not in json.dumps(record)
(Path(__file__).parent / "replay.json").write_text(json.dumps(record, indent=1, default=str), encoding="utf-8")
print("site", site_id, "accepted", {k: len(v) for k, v in accepted.items()}, "selections", len(record["selections"]),
      "jobs", len(outcomes))
