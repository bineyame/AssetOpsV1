"""Assessment history as one JSON document per Site, written atomically.

Same shape of write as the evidence store: `<name>.partial`, then `os.replace`.
Derived from accepted evidence, but not disposable: it is the only record of
an earlier revision once evidence changes (AC13).
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from assetops_backend.analytics.models import (
    AssessmentHistory,
    AssessmentLineage,
    AssessmentRevision,
)
from assetops_backend.analytics.ports import AssessmentStoreUnavailable

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The writable assessment store, outside version control (`var/` is gitignored).
ASSESSMENT_STORE_ROOT = REPO_ROOT / "var" / "assessments"

DOCUMENT_SCHEMA = {"id": "assetops.site-assessments", "version": 1}


def _revision(row: dict[str, Any]) -> AssessmentRevision:
    return AssessmentRevision(**row)


def _lineage(row: dict[str, Any]) -> AssessmentLineage:
    return AssessmentLineage(**{**row, "revisions": tuple(_revision(r) for r in row["revisions"])})


class JsonAssessmentStore:
    def __init__(self, root: Path | None = None) -> None:
        self._root = ASSESSMENT_STORE_ROOT if root is None else Path(root)
        self._lock = threading.Lock()

    def _path(self, site_id: str) -> Path:
        return self._root / "sites" / f"{site_id}.json"

    def load_history(self, site_id: str) -> AssessmentHistory:
        path = self._path(site_id)
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return AssessmentHistory(site_id=site_id)
        except OSError as error:
            raise AssessmentStoreUnavailable(f"cannot read {path.name}: {error}") from error
        try:
            document = json.loads(text)
            if document.get("schema") != DOCUMENT_SCHEMA or document.get("site_id") != site_id:
                raise AssessmentStoreUnavailable(f"{path.name} is not a site assessment document")
            return AssessmentHistory(
                site_id=site_id,
                lineages=tuple(_lineage(row) for row in document["lineages"]),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise AssessmentStoreUnavailable(f"{path.name} cannot be read") from error

    def save_history(self, history: AssessmentHistory) -> None:
        document = {
            "schema": DOCUMENT_SCHEMA,
            "site_id": history.site_id,
            "lineages": [
                {
                    "assessment_id": l.assessment_id,
                    "site_id": l.site_id,
                    "analytic_id": l.analytic_id,
                    "finding_type": l.finding_type,
                    "active": l.active,
                    "retired_at": l.retired_at,
                    "revisions": [
                        {
                            "revision": r.revision,
                            "assessed_at": r.assessed_at,
                            "model_version": r.model_version,
                            "basis_digest": r.basis_digest,
                            "assessment": r.assessment,
                        }
                        for r in l.revisions
                    ],
                }
                for l in history.lineages
            ],
        }
        path = self._path(history.site_id)
        with self._lock:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                partial = path.with_name(path.name + ".partial")
                partial.write_text(
                    json.dumps(document, sort_keys=True, separators=(",", ":")), encoding="utf-8"
                )
                os.replace(partial, path)
            except OSError as error:
                raise AssessmentStoreUnavailable(f"cannot write {path.name}: {error}") from error
