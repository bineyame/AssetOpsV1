# S3-02b — Evidence Analysis selected claim limit UI

Status: implementation-ready. USER_REVIEW_REQUIRED: true; owner walkthrough before merge. Size S, two phases. Branch `task/S3-02b-claim-limit-ui` from reviewed/merged S3-02a. Authority: `.agent/architect-W1-remaining-answers.md`, `.ai/DECISIONS.md` `D-2026-10-16-s302-capability`; registry `I-evidence-analysis-claim-limit-ui`, `evidence-analysis:2#b`. S2's delivered `#a` remains distinct. Mock `frontend/mockups/v69/index.html` / `screen-manifest.json` `evidence-analysis` guides layout only.

## Verified seams and UI contract

Existing S2 Evidence Analysis view and status explanation `frontend/src/sites/LedgerSiteEvidence.tsx:93-161,762-775,1115`; S3 dispatch client/view `frontend/src/sites/performanceDispatchClient.ts:1`, `PerformanceDispatch.tsx:68`; selected revision route `backend/assetops_backend/performance_api.py:99-101`. **New:** claim-limit client and selected-assessment section in Evidence Analysis, focused frontend tests. Keep Site, UTC day/window and exact S3 assessment revision in URL/selection; echo read basis and watermarks. Show supported classification ceiling only from current S3-02a result; name missing roles, poor quality, conflict, open bound, cohort/source/configuration limits. Historical exact revision is marked audit-only; pending/failed/stale/unassessed never show current positive claim. Link every selected accepted ID to exact Evidence drill-down and the pinned assessment revision. Wrong Site/revision, unsupported rule and unavailable read are visible refusals. No physical capacity or gateway-contact substitution.

## Phases and proof

| Phase | Deliverable and focused checks |
| --- | --- |
| 1. UI | **New** `frontend/src/sites/__tests__/evidenceClaimLimit.test.tsx` covers full/missing/conflicting/late fixture, exact accepted ID links, selection/reload, stale response cancellation, 401/403/404/refusal, keyboard and 1440/390. Run `npx.cmd tsc --noEmit` and `npm.cmd test` from `frontend/`. Backend code is not planned; if changed, one final-revision full suite per `backend/TESTING.md:104,112-125` on private `*_test` DB. Any new writer must satisfy statement-level rule 8 and `python tools/writer_guard_probes.py`; any migration re-chains after main `0018` and unmerged S6-02a `0019_verification_core`. |
| 2. Review | Run registry checker and `tools/check-all.ps1`; independent review checks rule-backed ceiling, exact lineage, app/mock 1440/390 and keyboard selection. Resolve High/Medium findings, then owner walkthrough before merge or `#b` promotion. User-facing copy/visual polish belongs to W1 conclusion. |

## Reproducible owner walkthrough

**New** `tools/s302_claim_limit_walkthrough.py` offers `prepare|serve|late|attest|drop`; private DB prefix `assetops_s302_owner*`, work prefix `var/s302_owner*`, reserved API/web ports 8932/5432. `prepare` reuses the reviewed S3-02a public-ingestion fixture and verifies its selected IDs; `serve` prints exact backend/frontend commands. Open its printed `http://127.0.0.1:5432/sites/KOBO-001/evidence/analysis?date=<day>&assessment_revision_id=<id>` URL (wrapper must print authoritative route), full and missing cases, then `late` to withdraw currentness. Record revision, run/cohort, source/analytic watermarks and accepted Evidence drill-down after reload; keyboard selection and Back. Compare app with `index.html#/evidence-analysis` at 1440/390; stop servers and `drop` private fixture.

From repo root run `python tools/s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 prepare`, then the same command ending `serve`; in a second PowerShell at `frontend/`, run `$env:ASSETOPS_API_PORT="8932"; npm.cmd run dev -- --port 5432 --strictPort`. The wrapper runs `python -m uvicorn lab_app:app --host 127.0.0.1 --port 8932` from its prepared host with private DB env and prints full/missing exact selected-revision URLs at `http://127.0.0.1:5432`. Run `late`, reload, run `attest`, stop servers and run `drop` with the same DB/work arguments.

## Architect questions

1. **Recommendation:** preserve the existing S2 explanation as its own section and render the S3 ceiling beneath it only when a selected assessment revision is explicit.
