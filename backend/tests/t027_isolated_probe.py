"""Rebuild accepted evidence from artifact texts alone (T027 AC15).

`build(root, artifact_dir)` ingests every committed artifact in `artifact_dir`
into an empty evidence store under `root` and returns the read-model payloads.
Run as a script (`python -I`, a working directory outside the repository, with
an import blocker for the simulator and host modules) it prints those payloads
and the blocked modules found loaded, so the test can show the rebuild needs no
simulator, host or execution composition. Phase 2 extends `build` to the
Overview read model (`overview`), so the same isolated test proves AC15 for it;
T028 adds the analytics read models (declaration, dispatch, Findings).
"""

from __future__ import annotations

import importlib.abc
import json
import sys
from pathlib import Path

BLOCKED = (
    "assetops_simulator", "host", "lab_execution", "source_stages", "kobo", "lab_app",
    "fixtures",
)


class _Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BLOCKED:
            raise ImportError(f"blocked: {name}")
        return None


def build(root: Path, artifact_dir: Path, site) -> dict:
    from fastapi.testclient import TestClient

    from assetops_backend.config import FeatureFlags
    from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
    from assetops_backend.main import create_app
    from assetops_contracts.committed_artifact import ingestion_batch, parse_artifact_text
    from run_fixtures import FakeSites

    app = create_app(
        FeatureFlags(simulator_lab_enabled=False),
        site_repository=FakeSites((site,)),
        evidence_store=JsonEvidenceStore(root / "evidence"),
        clock=lambda: "2030-01-01T00:00:00Z",
    )
    for path in sorted(artifact_dir.glob("*.json")):
        app.state.ingestion.ingest(
            ingestion_batch(parse_artifact_text(path.read_text(encoding="utf-8")))
        )
    client = TestClient(app)
    base = f"/api/sites/{site.site_id}/evidence"
    records = client.get(f"{base}/records", params={"limit": 1000}).json()
    return {
        "evidence": client.get(base).json(),
        "overview": client.get(f"/api/sites/{site.site_id}/overview").json(),
        # T028 AC14: the analytics read models rebuild with the same blockers.
        "analytics": client.get(f"/api/sites/{site.site_id}/analytics").json(),
        "dispatch": client.get(f"/api/sites/{site.site_id}/dispatch").json(),
        "findings": client.get(f"/api/sites/{site.site_id}/findings").json(),
        "records": records,
        "details": [client.get(f"{base}/records/{r['message_id']}").json()
                    for r in records["records"]],
        "rejections": client.get(f"{base}/rejections").json(),
        "lab_status": client.get("/api/simulator-lab/runs").status_code,
    }


def leaked() -> list[str]:
    return sorted(m for m in sys.modules if m.split(".")[0] in BLOCKED)


if __name__ == "__main__":
    tests_dir, root, artifact_dir = (Path(arg) for arg in sys.argv[1:4])
    sys.path.insert(0, str(tests_dir))
    sys.meta_path.insert(0, _Blocker())
    from test_t027_ingestion import a_site

    payload = build(root, artifact_dir, a_site())
    print(json.dumps({"payload": payload, "leaked": leaked()}))
