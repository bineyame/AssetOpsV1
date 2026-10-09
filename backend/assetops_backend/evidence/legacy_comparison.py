"""The explicit legacy evidence replay comparison (S2-02 phase 3a, item 5).

Before an imported Site's Evidence routes read the central Postgres ledger, an
operator runs `python -m assetops_backend.evidence_migration run` for it. That
compares the Site's historical file-backed evidence (accepted records,
rejections, conflicts and batch counts in the legacy JSON store) with a dry-run
replay of every stored envelope through the legacy V1 parser, and with the
ledger's accepted envelope for the same message ID where one exists. It writes
nothing to Postgres and nothing under the legacy stores; its only output is one
immutable comparison report (`adapters/legacy_comparison_file.py`).

Outcomes:
  PASSED      no exception; `empty_set` states whether the file store held any
              legacy evidence for the Site at all (an empty-set comparison is
              recorded as such, never as a replayed match).
  EXCEPTIONS  only configuration exceptions (a legacy channel that no binding
              revision of the imported Site registers). Recorded, not guessed;
              the cutover stays closed.
  FAILED      a replay parse failure, digest/message mismatch, a count mismatch
              or a ledger digest that differs from the legacy envelope.

`permits_cutover` is the one predicate the Evidence routes ask. The S3 hand-off
fixtures (file-saved `dispatch` claims and the ledger's recompute jobs) ride in
the report verbatim, without any analytic claim.

Freshness (Q14, Architect batch answers 3). A report binds the tenant UUID, the
Site UUID, the active environment (`environment_identity`: the product
database's host, port and name, never its credentials) and a deterministic
`legacy_inventory` fingerprint of the Site's legacy input: its file-store
batches, records, rejections and conflicts and every committed artifact filed
for the Site, the zero inventory included. `permits_cutover` is given the
inventory recomputed from the current input on every read; a changed inventory,
another environment or tenant, or an unreadable store keeps the cutover closed
until a fresh comparison. An old PASSED report never authorizes a changed store.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from assetops_backend.evidence.models import SiteEvidence
from assetops_contracts.committed_artifact import envelope_content_digest
from assetops_contracts.source_envelope import EnvelopeRejected, parse_canonical_envelope_json

#: Version 2 adds the environment and legacy-inventory binding (Q14); a version-1
#: report (no fingerprint) no longer opens the cutover.
REPORT_SCHEMA = {"id": "assetops.evidence-legacy-comparison", "version": 2}
REPLAY_PARSER = "source-envelope V1 (parse_canonical_envelope_json), dry run"
FAILING_KINDS = frozenset({
    "REPLAY_PARSE_FAILED", "MESSAGE_ID_MISMATCH", "DIGEST_MISMATCH", "COUNT_MISMATCH", "LEDGER_DIGEST_MISMATCH",
})
REPRESENTATIVES = 3


def _counts(legacy: SiteEvidence) -> dict:
    return {
        "batches": len(legacy.batches),
        "accepted_records": len(legacy.records),
        "rejections": len(legacy.rejections),
        "conflicts": len(legacy.conflicts),
        "batch_totals": {
            "accepted": sum(b.accepted for b in legacy.batches),
            "duplicates": sum(b.duplicates for b in legacy.batches),
            "rejected": sum(b.rejected for b in legacy.batches),
            "conflicts": sum(b.conflicts for b in legacy.batches),
        },
    }


def environment_identity(database_url: str | None) -> str | None:
    """The active environment a report is scoped to: the product database's
    driver family, host, port and database name. Credentials are dropped."""
    if not database_url:
        return None
    parts = urlsplit(database_url)
    if not parts.hostname or not parts.path.strip("/"):
        return None
    family = parts.scheme.split("+", 1)[0]
    return f"{family}://{parts.hostname.lower()}:{parts.port or 5432}/{parts.path.strip('/')}"


def legacy_inventory(legacy: SiteEvidence, committed_artifacts: Sequence[tuple[str, str]]) -> dict:
    """The deterministic fingerprint of a Site's legacy input (Q14).

    `committed_artifacts` is `(run_id, sha256 of the stored artifact bytes)` for
    every committed artifact filed for the Site. The zero inventory has a digest
    too, so evidence that appears after an empty-set comparison changes it."""
    document = {
        "batches": [asdict(b) for b in legacy.batches],
        "records": [asdict(r) for r in legacy.records],
        "rejections": [asdict(r) for r in legacy.rejections],
        "conflicts": [asdict(c) for c in legacy.conflicts],
        "committed_artifacts": sorted([run_id, digest] for run_id, digest in committed_artifacts),
    }
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return {
        "digest": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "batches": len(legacy.batches),
        "accepted_records": len(legacy.records),
        "rejections": len(legacy.rejections),
        "conflicts": len(legacy.conflicts),
        "committed_artifacts": len(committed_artifacts),
    }


def compare(
    *,
    site_code: str,
    tenant_id: UUID,
    site_id: UUID,
    legacy: SiteEvidence,
    ledger_digests: Mapping[str, str],
    bound_channels: Iterable[tuple[str, str]],
    legacy_dispatch_claims: list[dict],
    recompute_jobs: list[dict],
    compared_at: str,
    committed_artifacts: Sequence[tuple[str, str]],
    environment: str,
) -> dict[str, Any]:
    """Build the comparison report. Pure: every input is already read."""
    exceptions: list[dict] = []
    replayed: list[dict] = []
    bound = set(bound_channels)
    for record in legacy.records:
        result = {"message_id": record.message_id, "batch_id": record.batch_id,
                  "source_time": record.source_time, "digest": record.content_digest, "replay": "MATCHED"}
        try:
            envelope = parse_canonical_envelope_json(record.envelope_text)
        except EnvelopeRejected as error:
            result["replay"] = "PARSE_FAILED"
            exceptions.append({"kind": "REPLAY_PARSE_FAILED", "message_id": record.message_id,
                               "detail": f"{error.kind} at {error.field}: {error.detail}"})
        else:
            if envelope.message_id != record.message_id:
                result["replay"] = "MESSAGE_ID_MISMATCH"
                exceptions.append({"kind": "MESSAGE_ID_MISMATCH", "message_id": record.message_id,
                                   "detail": f"the replayed envelope names {envelope.message_id}"})
        digest = envelope_content_digest(record.envelope_text)
        if digest != record.content_digest:
            result["replay"] = "DIGEST_MISMATCH"
            exceptions.append({"kind": "DIGEST_MISMATCH", "message_id": record.message_id,
                               "detail": f"stored {record.content_digest}, replayed {digest}"})
        stored = ledger_digests.get(record.message_id)
        result["ledger"] = "ABSENT" if stored is None else ("SAME" if stored == digest else "DIFFERENT")
        if stored is not None and stored != digest:
            exceptions.append({"kind": "LEDGER_DIGEST_MISMATCH", "message_id": record.message_id,
                               "detail": f"ledger {stored}, legacy {digest}"})
        if (record.device_id, record.signal_id) not in bound:
            exceptions.append({"kind": "CONFIGURATION_UNMAPPED", "message_id": record.message_id,
                               "detail": f"{record.device_id}/{record.signal_id} is not registered by any binding "
                                         "revision of the imported Site; no current mapping is guessed"})
        replayed.append(result)
    counts = _counts(legacy)
    totals = counts["batch_totals"]
    if totals["accepted"] != counts["accepted_records"]:
        exceptions.append({"kind": "COUNT_MISMATCH", "message_id": None,
                           "detail": f"batches accepted {totals['accepted']}, records stored "
                                     f"{counts['accepted_records']}"})
    if totals["rejected"] != counts["rejections"]:
        exceptions.append({"kind": "COUNT_MISMATCH", "message_id": None,
                           "detail": f"batches rejected {totals['rejected']}, rejections stored "
                                     f"{counts['rejections']}"})
    empty = not (legacy.records or legacy.rejections or legacy.conflicts or legacy.batches)
    if any(e["kind"] in FAILING_KINDS for e in exceptions):
        outcome = "FAILED"
    elif exceptions:
        outcome = "EXCEPTIONS"
    else:
        outcome = "PASSED"
    if empty:
        statement = (f"Empty-set comparison: the legacy file store holds no evidence for {site_code}, so "
                     "nothing was replayed and no record is claimed to match.")
    else:
        statement = (f"Replayed {len(replayed)} legacy record(s) through the V1 parser: "
                     f"{sum(1 for r in replayed if r['replay'] == 'MATCHED')} matched; "
                     f"{len(exceptions)} exception(s).")
    representative = replayed[:REPRESENTATIVES] + replayed[REPRESENTATIVES:][-REPRESENTATIVES:]
    return {
        "schema": dict(REPORT_SCHEMA),
        "report_id": str(uuid4()),
        "site_id": site_code,
        "site_uuid": str(site_id),
        "tenant_id": str(tenant_id),
        "environment": environment,
        "legacy_inventory": legacy_inventory(legacy, committed_artifacts),
        "compared_at": compared_at,
        "outcome": outcome,
        "empty_set": empty,
        "statement": statement,
        "legacy": {"store": "LEGACY_FILE", **counts},
        "replay": {"parser": REPLAY_PARSER, "replayed": len(replayed),
                   "matched": sum(1 for r in replayed if r["replay"] == "MATCHED"),
                   "in_ledger": sum(1 for r in replayed if r["ledger"] != "ABSENT")},
        "representative_records": representative,
        "exceptions": exceptions,
        "s3_fixtures": {
            "statement": "Hand-off fixtures for the S3 dispatch comparison; no analytic result is claimed here.",
            "legacy_dispatch_claims": legacy_dispatch_claims,
            "recompute_jobs": recompute_jobs,
        },
        "writes": "None to Postgres; the legacy evidence, run, Stage and commit stores are left untouched.",
    }


def permits_cutover(
    report: Mapping[str, Any] | None,
    site_code: str,
    site_id: UUID,
    *,
    tenant_id: UUID,
    environment: str | None,
    inventory: Mapping[str, Any] | None,
) -> tuple[bool, str]:
    """Whether the newest comparison record lets the Site's Evidence read the ledger.

    `inventory` is `legacy_inventory` recomputed from the CURRENT legacy input
    (None when it could not be read, which closes the gate)."""
    if report is None:
        return False, ("No legacy comparison record exists; run "
                       "`python -m assetops_backend.evidence_migration run` for the Site.")
    if report.get("schema") != REPORT_SCHEMA or report.get("site_uuid") != str(site_id):
        return False, "The newest comparison record is for another schema or Site; run a fresh comparison."
    if report.get("tenant_id") != str(tenant_id):
        return False, "The newest comparison record is for another tenant."
    if environment is None or report.get("environment") != environment:
        return False, "The newest comparison record was made in another environment; run a fresh comparison here."
    if report.get("outcome") != "PASSED":
        return False, f"The newest comparison record is {report.get('outcome')}, not PASSED."
    if report.get("empty_set") is not False and not (
        report.get("empty_set") is True and str(report.get("statement", "")).startswith("Empty-set comparison")
    ):
        return False, "The comparison record does not state whether it compared an empty set."
    if inventory is None:
        return False, "The Site's legacy input could not be read, so the comparison cannot be confirmed current."
    recorded = report.get("legacy_inventory")
    if not isinstance(recorded, Mapping) or recorded.get("digest") != inventory.get("digest"):
        return False, ("The Site's legacy input has changed since the newest comparison (inventory "
                       f"{inventory.get('digest')}); run a fresh comparison.")
    if report.get("empty_set") is True and any(
            inventory.get(k) for k in ("batches", "accepted_records", "rejections", "conflicts")):
        return False, "The empty-set comparison no longer matches a legacy store that now holds evidence."
    return True, ""
