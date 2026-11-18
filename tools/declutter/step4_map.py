"""Declutter step 4 (2026-11-18): where each file tracked under `.agent/` at BASE went.

One source for the move, split, archive-header, citation-rewrite and link-check scripts in
this folder, so a reviewer can re-run each of them against the same map.

Rules, in order (`old_location(path)` returns the new path):
1. KEEP: stays in `.agent/` (live coordination files, files code reads, the pending owner file).
2. SPECS: a build sheet or build spec listed in `specs/INDEX.md` -> `specs/<ID>/spec.md`
   (an over-cap sheet is then split into parts; `specs/<ID>/README.md` maps old lines to parts).
3. DECLUTTER: the live declutter spec, its packets and reviews -> `specs/DECLUTTER/<name>`.
4. `.agent/owner-*.md` -> `owner/<name>`.
5. Everything else -> `archive/agent-history/<path below .agent/>` with one header line.
"""
from __future__ import annotations

BASE = "bae760425"  # main a87224025 plus the owner note; the tree the moves start from
ARCHIVE = "archive/agent-history"

KEEP = {
    "coordinator-handoff.md": "tracked live coordination state (trimmed to one current block)",
    "lane-rules-vps-2026-11-12.md": "live lane rules on this machine (cited by .ai/NOW.md)",
    "architect-sequence-client-scope-2026-11-11.md": "live demo-sprint plan (cited by .ai/NOW.md)",
    "backlog-post-demo.md": "live post-demo backlog; the owner picks items after the demo",
    "page-load-architecture-review-2026-11-14.html": "owner decisions D1-D6 still pending",
    "convertion_potential.html": "owner-facing document on main (cited by .ai/NOW.md); its home is step 5",
    "decision-intelligence-mechanism-2026-11-14.html": "owner-facing document on main (cited by .ai/NOW.md); its home is step 5",
    "mock-departure-register.md": "read by tools/checks/mock-deviation-labels.mjs; RULES section 6 adds rows here",
    "W1-UX-combined-owner-walkthrough.md": "read by tools/checks/test_evidence_checks.mjs",
    "owner-walkthrough-notes-2026-11-01.md": "pending: uncommitted change in the main checkout; move after it is committed",
}

SPECS = {  # basename in .agent/ -> spec ID (folder under specs/), as in specs/INDEX.md
    "W2-02-build-spec.md": "W2-02",
    "W2-03-build-spec.md": "W2-03",
    "W2-04-build-spec.md": "W2-04",
    "W2-05a-build-spec.md": "W2-05a",
    "W2-05b-build-spec.md": "W2-05b",
    "W2-06-build-spec.md": "W2-06",
    "W2-07-build-spec.md": "W2-07",
    "W2-F-build-spec.md": "W2-F",
    "W3-01-build-spec.md": "W3-01",
    "W3-02-build-spec.md": "W3-02",
    "W3-03-build-spec.md": "W3-03",
    "W4-01-build-spec.md": "W4-01",
    "W4-02-build-spec.md": "W4-02",
    "W4-03-build-spec.md": "W4-03",
    "W5-01-build-spec.md": "W5-01",
    "W5-02-build-spec.md": "W5-02",
    "W5-03-build-spec.md": "W5-03",
    "W5-04-build-spec.md": "W5-04",
    "W5-F1-build-spec.md": "W5-F1",
    "W6-01-build-spec.md": "W6-01",
    "build-sheet-CH-0.md": "CH-0",
    "build-sheet-CH-1a.md": "CH-1a",
    "build-sheet-CH-1b.md": "CH-1b",
    "build-sheet-CH-2.md": "CH-2",
    "build-sheet-CH-3.md": "CH-3",
    "build-sheet-CH-4.md": "CH-4",
    "build-sheet-CH-5a.md": "CH-5a",
    "build-sheet-CH-5b.md": "CH-5b",
    "build-sheet-CH-5c.md": "CH-5c",
    "build-sheet-CH-5d.md": "CH-5d",
    "build-sheet-CH-6.md": "CH-6",
    "build-sheet-CH-9.md": "CH-9",
    "build-sheet-CH-9b.md": "CH-9b",
    "build-sheet-COV-PARTIAL.md": "COV-PARTIAL",
    "build-sheet-DD-1.md": "DD-1",
    "build-sheet-DEMO-COMBINED.md": "DEMO-COMBINED",
    "build-sheet-DEMO-SPARSE.md": "DEMO-SPARSE",
    "build-sheet-DIESEL-1.md": "DIESEL-1",
    "build-sheet-FIX-COLD-DRAIN.md": "FIX-COLD-DRAIN",
    "build-sheet-FUEL-1.md": "FUEL-1",
    "build-sheet-IDX-GAPS.md": "IDX-GAPS",
    "build-sheet-LINK-LINEAGE.md": "LINK-LINEAGE",
    "build-sheet-MD-0.md": "MD-0",
    "build-sheet-OUT-C.md": "OUT-C",
    "build-sheet-OUT-D.md": "OUT-D",
    "build-sheet-OUT-E.md": "OUT-E",
    "build-sheet-OUT-W.md": "OUT-W",
    "build-sheet-OWN-GAPS-2026-11-08.md": "OWN-GAPS",
    "build-sheet-POLISH.md": "POLISH",
    "build-sheet-SCN-kobo-reserve.md": "SCN",
    "build-sheet-TEST-drift.md": "TEST-drift",
    "build-sheet-WALK1.md": "WALK1",
    "build-spec-commercial-2026-10-27.md": "Lane-C",
    "build-spec-telemetry-2026-10-27.md": "Lane-T",
}

DECLUTTER = [
    "repo-declutter-recommendation-2026-11-18.md",
    "review-declutter-01-start-path.md",
    "packet-declutter-02.md",
    "review-declutter-02.md",
    "packet-declutter-03.md",
    "review-declutter-03.md",
]

SUPERSEDED = {  # archived file -> what superseded it (header "Superseded by X on 2026-11-18")
    "lane-rules-2026-11-12.md": ".agent/lane-rules-vps-2026-11-12.md",
    "current-plan-pointer.md": ".ai/NOW.md",
}


def new_location(old: str) -> str:
    """`old` is a repo path under `.agent/` tracked at BASE; returns where it lives after step 4
    (before any split: a split sheet's new location is its folder's `spec.md`)."""
    assert old.startswith(".agent/"), old
    rel = old[len(".agent/"):]
    if rel in KEEP:
        return old
    if rel in SPECS:
        return f"specs/{SPECS[rel]}/spec.md"
    if rel in DECLUTTER:
        return f"specs/DECLUTTER/{rel}"
    if "/" not in rel and rel.startswith("owner-") and rel.endswith(".md"):
        return f"owner/{rel}"
    return f"{ARCHIVE}/{rel}"
