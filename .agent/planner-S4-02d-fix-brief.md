# Planner brief: S4-02d plan fix round 1 (2026-10-14)

Role: Planner (Codex). Branch `plan/S4-02c-architect`. Read the RETURN review `.agent/S4-02d-plan-review.md` in full, the packet `tasks/S4-02d-analytic-finding-worker-schedule.md` and `.agent/planner-S4-02d-notes.md`, and verify against the code it cites (`postgres_assessment_store.py` `_LIVE_JOBS` ~:88 and reconcile, `finding_episode.py:12-14`, the S4 matcher consistency check / `match_state` / `finding_match_pass`, `tools/checks/configuration-persistence.ps1` rule 8, `backend/README-db.md`, `backend/assetops_backend/recompute_consequences.py`, `financials/recompute.py`, `tools/s402c_late_power_walkthrough.py`, `.ai/DECISIONS.md` ~:4049 commit-ordered fence ruling).

Amend the packet to resolve H1, H2, M1-M5, L1-L4 as the review proposes:
- H1: run S4 every tick after the S3 stage; per-window currentness gate (no live S3 job over the window, `match_state.matched` true, no outstanding consequence work); a documented requeue recovery for terminally FAILED S3 jobs; replace the phase-1 proof.
- H2: choose one of the review's two options for Leg A (prefer: assert the `FINDING_REVISION_SUPERSEDED` no-op and cite S4-02c evidence for Leg A) and drive every step by ticks so the recorded commands show no hand-run Leg B steps (W4).
- M1: name migration 0013 for heartbeat/cursor/claim records and the new database writer; state the rule 8 guard amendment needed and put it in scope, AND list it under "For the Architect batch" in the notes for ratification (do not treat it as already approved).
- M2: define "active Site" so built fixture Sites (lifecycle PLANNED, e.g. KOBO-001) are processed (e.g. Sites with registered evidence or an explicit schedule enrolment), and address global S3 job leasing.
- M3: retire or fold the S4-02c per-Site consequence timer in README-db; name per-environment ownership.
- M4: carry the pre-0012 `NO_WORK_RECORDED` heads (backfill or explicit reporting so a stale head never looks idle and healthy).
- M5: phase 3 records S3 limits and asserts only what the currentness seam reports; positive path uses the existing source-ordered variant; no S5 money assertion.
- L1: S5 seam rests on the commit-safe job/match comparison, DB time, existing S3 read status, `match_state`/`finding_match_pass`, `pending_work`; define the seam's inputs and outputs. L2: server-side statement timeout plus killable child process per stage; proofs inject both; relate to the 5-minute S3 lease. L3: forbid overlapping S3 leasing on the same Site during matching; typed `FENCE_MOVED` failure. L4: move timer installation and runbook to phase 2.
- Risks: add "do not install the schedule on an owner-visible host before `I-late-reading-series-and-money-limit` lands (it would move late evidence to the run-1 too-low consequence on the S4-02b money panel automatically)"; `reconcile_all` every tick; S4-02c I3/I4 ownership.
- Keep USER_REVIEW_REQUIRED false only if no owner-facing copy/UI is added; say so explicitly.
- Add a "Plan fix round 1" section mapping each finding to its resolution.

Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs`, `--next-work --out .agent/next-work-2026-10-14k.json`, `--verify-report .agent/next-work-2026-10-14k.json`. Edit only the packet, `tasks/README.md` (if wording changes), the registry JSON (only if needed) and the notes. Do not commit.
