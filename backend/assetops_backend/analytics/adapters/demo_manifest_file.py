"""Demo-manifest fault-fixture annotations (S3-01 phase 3; Architect F4/Q4).

The `s3-dispatch-cases-v1` manifest is environment-local demo provenance. It
never fills an analytic input. A read may attach a separate, attributed note
when a run's exact accepted evidence IDs match a case the manifest labels as a
fault fixture. Nothing is inferred from an epoch name, and the note is never
presented as a central attestation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

STATEMENT = ("Labelled fault fixture in the demo manifest, matched by exact accepted evidence IDs. This is a "
             "demo-manifest annotation, not a central attestation: central evidence carries no fixture marker, and "
             "the gateway, source, sequence epoch, batch and accepted IDs shown are the recorded provenance.")


GATEWAY_STATEMENT = ("The demo manifest records these exact accepted evidence IDs as a Lab run sealed by the "
                     "registered gateway and delivered over its credential (the ordinary path). The central "
                     "ledger's own provenance - gateway, source, sequence epoch, batch - is shown beside it.")


class DemoManifestAnnotations:
    def __init__(self, path: str | None) -> None:
        self.path = Path(path) if path else None

    def _load(self) -> tuple[dict[str, Any], str] | None:
        if self.path is None or not self.path.is_file():
            return None
        raw = self.path.read_bytes()
        return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()

    def annotate(self, evidence_ids: set[str]) -> list[dict[str, Any]]:
        loaded = self._load()
        if loaded is None:
            return []
        manifest, digest = loaded
        out = []
        for case in manifest.get("cases", []):
            matched = sorted(evidence_ids & set(case.get("evidence_ids", [])))
            if matched and case.get("gateway_sealed") and not case.get("fault_fixture"):
                # Opt-in (S4-01 Q6/Q15): the producer's ordinary registered-gateway case, named as such.
                out.append({
                    "kind": "DEMO_MANIFEST_GATEWAY_CASE", "label": "ordinary registered gateway path in demo manifest",
                    "statement": GATEWAY_STATEMENT, "case_id": case.get("case_id"), "case_label": case.get("label"),
                    "manifest_epochs": case.get("epochs", []), "matched_evidence_ids": matched,
                    "source": {"manifest": manifest.get("label"), "path": str(self.path), "sha256": digest},
                })
                continue
            if not case.get("fault_fixture"):
                continue
            if matched:
                out.append({
                    "kind": "DEMO_MANIFEST_FAULT_FIXTURE", "label": "labelled fault fixture in demo manifest",
                    "statement": STATEMENT, "case_id": case.get("case_id"), "case_label": case.get("label"),
                    "manifest_epochs": case.get("epochs", []), "matched_evidence_ids": matched,
                    "source": {"manifest": manifest.get("label"),
                               "path": str(self.path), "sha256": digest},
                })
        return out
