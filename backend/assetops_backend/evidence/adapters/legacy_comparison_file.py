"""Immutable legacy comparison reports (S2-02 phase 3a, item 5; Q14 default).

Each run of the explicit comparison writes one new JSON report under the
evidence store root, `migration/<site_code_key>/<compared_at>-<report_id>.json`,
created exclusively and never overwritten. The newest report for a Site decides
the Evidence cutover. Nothing else is written here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from assetops_backend.evidence.adapters.json_evidence_store import EVIDENCE_STORE_ROOT
from assetops_backend.evidence.ports import EvidenceStoreUnavailable


def _key(site_code: str) -> str:
    return site_code.strip().lower()


class ComparisonReportFiles:
    def __init__(self, root: Path | None = None) -> None:
        self._root = (EVIDENCE_STORE_ROOT / "migration") if root is None else Path(root)

    def write(self, report: dict) -> Path:
        stamp = report["compared_at"].replace(":", "").replace("-", "").replace(".", "")
        folder = self._root / _key(report["site_id"])
        path = folder / f"{stamp}-{report['report_id']}.json"
        folder.mkdir(parents=True, exist_ok=True)
        text = json.dumps(report, sort_keys=True, indent=2) + "\n"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        return path

    def latest(self, site_code: str) -> dict | None:
        folder = self._root / _key(site_code)
        if not folder.is_dir():
            return None
        found = sorted(folder.glob("*.json"))
        if not found:
            return None
        try:
            report = json.loads(found[-1].read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise EvidenceStoreUnavailable(f"the comparison report {found[-1].name} is unreadable") from error
        return report if isinstance(report, dict) else None
