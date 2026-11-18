"""Declutter step 5 (Docs and tools): the move map, in one place (executable form of specs/CITATION_MAP.md, step 5).

Each entry: old path -> (new path, status). Status is the header line's first sentence; None means the file
moves byte-for-byte with no header:
- a live document that only changes home (owner-facing HTML out of `.agent/`);
- owner words or an owner draft (verbatim; never edited, as in step 4 O4) and JSON data (no comment form).
  Their status is recorded in the README of the archive folder instead.
Every other archived file gets one header line, "<status> Archived from <old> on 2026-11-18 (declutter step 5).",
in its own comment form, so an old `:line` is +1.

Choice of homes:
- Docs generations -> `Docs/archive/2026-09/` (recommendation 3.4: Docs keeps its own archive beside the live
  client and product documents).
- Retired scripts and their data -> `archive/<original path>` (`archive/tools/`, `archive/frontend/docs/architecture/`),
  not `tools/archive/`: `archive/` is already outside every default read and grep (RULES 9), outside
  `tools/select-tests.py` backend triggers (`archive/*` selects nothing) and outside the `tools/*.mjs` browser-script
  inventory of `tools/checks/test_evidence_checks.mjs`; a folder inside `tools/` would stay on all three paths.
"""
from __future__ import annotations

BASE = "d05bf668c"  # main at the owner's step-5 instruction; the tree the moves start from
DATE = "2026-11-18"
MARK = f"on {DATE} (declutter step 5)."

V4 = "Docs/simulator_design_v4.md"
SITE_FIRST = "frontend/docs/architecture/production-shaped-mvp.md and site-first-execution-plan.md"
FIN = "Finished; historical."
D9 = "Docs/archive/2026-09"

MOVES: dict[str, tuple[str, str | None]] = {
    # --- Docs: September design generations (recommendation 1.5, 3.4) ---
    "Docs/simulator_design.md": (f"{D9}/simulator_design.md", f"Superseded by {V4} on {DATE}."),
    "Docs/simulator_design_v2.md": (f"{D9}/simulator_design_v2.md", f"Superseded by {V4} on {DATE}."),
    "Docs/simulator_design_v3.md": (f"{D9}/simulator_design_v3.md", f"Superseded by {V4} on {DATE}."),
    "Docs/simulator-design-v2-alignment.md": (f"{D9}/simulator-design-v2-alignment.md", f"Superseded by {V4} on {DATE}."),
    "Docs/simulator-design-v3-alignment.md": (f"{D9}/simulator-design-v3-alignment.md", f"Superseded by {V4} on {DATE}."),
    "Docs/multi-vertical-capability-read.md": (f"{D9}/multi-vertical-capability-read.md",
                                               f"Superseded by {SITE_FIRST} (Site-first) and {V4} on {DATE}."),
    "Docs/multi-vertical-build-plan.md": (f"{D9}/multi-vertical-build-plan.md",
                                          f"Superseded by {SITE_FIRST} (Site-first) and {V4} on {DATE}."),
    "Docs/mini-grid-demo-architecture-and-roadmap.md": (f"{D9}/mini-grid-demo-architecture-and-roadmap.md",
                                                        f"Superseded by {SITE_FIRST} (Site-first) on {DATE}."),
    "Docs/declared-capability-and-what-checks-it.md": (f"{D9}/declared-capability-and-what-checks-it.md",
                                                       f"Superseded by .ai/decisions/ on {DATE} (it was a reflection, never a decision)."),
    # owner words / owner draft: verbatim, status in Docs/archive/README.md
    "Docs/multi-vertical-brief-verbatim.md": (f"{D9}/multi-vertical-brief-verbatim.md", None),
    "Docs/queue-review-feedback-verbatim.md": (f"{D9}/queue-review-feedback-verbatim.md", None),
    "Docs/lab-cockpit-proposal.md": (f"{D9}/lab-cockpit-proposal.md", None),
    # --- owner-facing documents: their home is Docs/ (step 4 KEEP note), live, no header ---
    ".agent/convertion_potential.html": ("Docs/demo-sprint/convertion_potential.html", None),
    ".agent/decision-intelligence-mechanism-2026-11-14.html":
        ("Docs/demo-sprint/decision-intelligence-mechanism-2026-11-14.html", None),
    # --- retired advisory guards (PIPE-1 A6) and the data only they read ---
    "frontend/docs/architecture/check_v69_dependency_registry.cjs": (
        "archive/frontend/docs/architecture/check_v69_dependency_registry.cjs",
        "Retired guard (PIPE-1 A6; v69 is not read (O2) and the S1-S7 queue is built); the live gap catalogue is "
        "frontend/docs/architecture/check_mock_gaps.cjs."),
    "frontend/docs/architecture/delivery_next_work.cjs": (
        "archive/frontend/docs/architecture/delivery_next_work.cjs",
        "Retired (PIPE-1 A6): the S1-S7 next-work checker; the S1-S7 queue is built (.ai/NOW.md)."),
    "frontend/docs/architecture/test_delivery_next_work.cjs": (
        "archive/frontend/docs/architecture/test_delivery_next_work.cjs",
        "Retired (PIPE-1 A6): fixtures of the retired S1-S7 next-work checker."),
    "frontend/docs/architecture/check_v69_ledger.py": (
        "archive/frontend/docs/architecture/check_v69_ledger.py",
        "Retired guard (PIPE-1 A6; the v69 mock is not read, O2)."),
    "frontend/docs/architecture/v69-subject-area-briefs.json": (
        "archive/frontend/docs/architecture/v69-subject-area-briefs.json", None),
    "frontend/docs/architecture/v69-model-homes.json": ("archive/frontend/docs/architecture/v69-model-homes.json", None),
    # --- the S1-S7 queue tables (their only readers were the retired guards) ---
    "tasks/README.md": ("tasks/archive/site-first-2026-10/queue-tables.md",
                        f"Superseded by tasks/README.md (short live queue) and .ai/NOW.md on {DATE}."),
}

TOOLS_FINISHED = [  # one-off probes and evidence scripts of finished slices; no live reference (packet: method)
    "ap1_parity_probe.py",
    "dd1a1_degraded_check.py", "dd1a1_fullday_compare.py", "dd1a1_fullday_probe.py", "dd1a1_r12_check.py",
    "dd1a1_r3_check.py", "dd1a1_r7_check.py", "dd1a1_r8_check.py", "dd1a1_r9_check.py",
    "dd1a2_addday_l2.py", "dd1b1_coh3_probe.py",
    "dd1b2a_days.py", "dd1b2a_evidence.py", "dd1b2a_m2.py", "dd1b2a_m3.py", "dd1b2a_probe.py", "dd1b2a_seam.py",
    "lr01-money-evidence.mjs", "pr2a-price-page-evidence.mjs", "pr3-price-entry-evidence.mjs",
    "s405-provenance-evidence.mjs", "s5-overview-evidence.mjs",
    "v01b-lab-evidence-evidence.mjs", "v01b_lab_evidence_walkthrough.py",
    "w1-fidelity-audit-index.mjs", "w502-cold-work-evidence.mjs", "w504-ev-work-evidence.mjs", "w5f1-d3-evidence.mjs",
]
for _t in TOOLS_FINISHED:
    MOVES[f"tools/{_t}"] = (f"archive/tools/{_t}", FIN)


def header(old: str) -> bytes | None:
    """The one header line for an archived file, in its comment form; None for a verbatim move."""
    new, status = MOVES[old]
    if status is None:
        return None
    text = f"{status} Archived from {old} {MARK}"
    if new.endswith(".html"):
        return f"<!-- {text} -->\n".encode()
    if new.endswith((".py", ".sh")):
        return f"# {text}\n".encode()
    if new.endswith((".mjs", ".cjs", ".js")):
        return f"// {text}\n".encode()
    return f"> {text}\n".encode()


def new_location(old: str) -> str:
    return MOVES[old][0] if old in MOVES else old
