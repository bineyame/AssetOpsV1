# AP-1 live check (D-SR.80 Q1 merge gate), 2026-11-13

Result: **PASS on all four items.** Every listed day was checked. Nothing was accepted as ruled.

## Setup
- Code: AP-1 `task/AP-1-analytics-port` HEAD `249e83a58`, exported unchanged with `git archive` into a scratch tree. The AP-1 worktree was not edited.
- Why a copy: store roots are `REPO_ROOT`-relative with no env override, and `REPO_ROOT` comes from `__file__`. The Performance gate binds `store_root` (resolved evidence and commit roots).
  - The copy's `var/evidence` and `var/commits` are symlinks to `/opt/assetecon/AssetOpsV1-walk/var/polish_walk1113/tree/var/...`. They resolve to the build tree's identity.
  - `var/sites/kobo-001.yaml` is a byte copy. A first attempt symlinked all of `var`, which broke the registered-import path check on `/api/sites` (a setup artefact). That instance was discarded, and every result below comes from a fresh second instance.
  - Code diff check: the scratch backend equals the AP-1 worktree backend, and the build tree differs from AP-1 only in AP-1's own files.
- Env: `Demo("assetops_polish_walk1113_test", ".../var/polish_walk1113").serve_env()`, imported from the walk worktree. It matches the running 8990 process env: DB URL, keys.json cursor keys, `ASSETOPS_OPERATIONAL_ENTRY=on`, `ASSETOPS_PREBUILT_ROUTES`, `ASSETOPS_PERIOD_READ_KINDS=dispatch.day,evidence.claim,mini_depth.renewable,mini_depth.fuel,mini_depth.service,mini_depth.backup`.
  - `PYTHONPATH` is the scratch copy's `backend:backend/tests:contracts:simulator:gateway:field:host:tools`.
  - One addition: `ASSETOPS_RESPONSE_STORE=off`, so the probe could not write `chain_response` rows (no DB writes). `/analytics` is not a stored-response route.
- Serve: `python -m uvicorn lab_app:app --port 8991`, cwd `host`, with no scheduler and no tick. Stopped by PID afterwards. 8990 and 5490 were not touched (8990 got four read-only GETs on `/dispatch` and `/findings` for comparison).
- UI: no browser is available (no Playwright or Chromium). The Evidence component choice was verified from code plus the live API bodies. Vite was not started.

## 1. KOBO-001 and KISIWA-001: every day with a selected dispatch-3.2 revision
- Days found: the latest `analytic_run_selection` per window (`analytic_id='dispatch'`), then the `analytic_run_assessment` revisions with `model_version='dispatch-3.2'`.
  - KOBO-001: 30 days, 2026-10-14 to 2026-11-12. Of these, 27 have an INTERVAL revision; 11-01, 11-07 and 11-12 have WINDOW only.
  - KISIWA-001: 12 days, 2026-11-02 to 2026-11-13. Of these, 11 have 2 INTERVAL revisions each; 11-13 has WINDOW only.
- Calls per day:
  - `GET /api/sites/{code}/analytics?from=<day>T00:00:00Z&to=<day+1>T00:00:00Z`;
  - `GET /api/sites/{code}/performance/dispatch/windows/{day}/claim-limit?revision=<id>` for every INTERVAL revision of that day.
- Panel not-available set: the roles of `readiness.missing_evidence` entries with kind `COVERAGE_GAP` (label mapped to role), plus a separate Generator state flag. Load rows are per feeder: clinic-meter, mill-meter and residential-meter were all available on every day.
- Section gap set: `claim_limit.reasons` with code `MISSING_ROLE` and a role. As a cross-check, the AP-1 test's wider set (all `GAP_CODES` with a role, except `GENERATOR_UNOBSERVED`) was also collected, along with `GENERATOR_UNOBSERVED` and the `capability.roles` spans that are not COVERED.
- Also checked on each day:
  - `assessed_intervals` equals the number of INTERVAL revisions;
  - the claim-limit `current_selection.revision_ids` equals that day's selected revisions.
- Result: all 42 day reads returned 200 (none 409, 422 or 503). All 55 claim-limit reads returned 200.
- The panel set was `{}` and the section set `{}` on every day. The wider set, the generator-unobserved flag and the not-COVERED capability roles were also empty, so no role is shown available where the section names a gap.
- Note: the walk1113 story has no coverage gap on any of these days, so the equality holds as empty = empty. The non-empty case is covered only by AP-1's fixture tests.
- Extra check, Site-local day windows (Africa/Addis_Ababa, Africa/Dar_es_Salaam): 42/42 returned 200, level FULL, with 0 gaps.
- Evidence page component choice:
  - `/evidence` returns 200 with `store: POSTGRES`, so the page takes the `isLedgerEvidence` branch to `LedgerSiteEvidence`. `SiteEvidence` passes `declaration` and `profile`.
  - `/analytics` returns 200, passes `isDeclaration`, and has 1 analytic (`dispatch`), so its status is `loaded`.
  - `capabilityTableShown` then holds, `storedReadinessShown` is true, and `CapabilityReadinessTable` renders in "What we can conclude now" with the badge "Evidence · Overview". The `capability-conclusions` line does not render.
  - Site-wide readiness: KOBO-001 is FULL with 27 intervals; KISIWA-001 is FULL with 22 intervals.

| Site | Day | Selected revisions | /analytics (time) | claim-limit status | assessed | panel gaps | section MISSING_ROLE / wider set / gen unobserved | capability not COVERED | Result |
|---|---|---|---|---|---|---|---|---|---|
| KOBO-001 | 2026-10-14 | 1 INTERVAL + 1 WINDOW | 200 (0.8 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-15 | 1 INTERVAL + 1 WINDOW | 200 (0.779 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-16 | 1 INTERVAL + 1 WINDOW | 200 (0.72 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-17 | 1 INTERVAL + 1 WINDOW | 200 (0.709 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-18 | 1 INTERVAL + 1 WINDOW | 200 (0.705 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-19 | 1 INTERVAL + 1 WINDOW | 200 (1.093 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-20 | 1 INTERVAL + 1 WINDOW | 200 (0.974 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-21 | 1 INTERVAL + 1 WINDOW | 200 (1.176 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-22 | 1 INTERVAL + 1 WINDOW | 200 (1.05 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-23 | 1 INTERVAL + 1 WINDOW | 200 (1.109 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-24 | 1 INTERVAL + 1 WINDOW | 200 (1.007 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-25 | 1 INTERVAL + 1 WINDOW | 200 (1.063 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-26 | 1 INTERVAL + 1 WINDOW | 200 (1.102 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-27 | 1 INTERVAL + 1 WINDOW | 200 (0.983 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-28 | 1 INTERVAL + 1 WINDOW | 200 (0.958 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-29 | 1 INTERVAL + 1 WINDOW | 200 (1.023 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-30 | 1 INTERVAL + 1 WINDOW | 200 (0.922 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-10-31 | 1 INTERVAL + 1 WINDOW | 200 (0.928 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-01 | 0 INTERVAL + 1 WINDOW | 200 (0.938 s) | n/a (no INTERVAL revision) | 0 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-02 | 1 INTERVAL + 1 WINDOW | 200 (0.71 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-03 | 1 INTERVAL + 1 WINDOW | 200 (0.687 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-04 | 1 INTERVAL + 1 WINDOW | 200 (0.745 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-05 | 1 INTERVAL + 1 WINDOW | 200 (0.776 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-06 | 1 INTERVAL + 1 WINDOW | 200 (0.883 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-07 | 0 INTERVAL + 1 WINDOW | 200 (1.333 s) | n/a (no INTERVAL revision) | 0 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-08 | 1 INTERVAL + 1 WINDOW | 200 (1.044 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-09 | 1 INTERVAL + 1 WINDOW | 200 (1.019 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-10 | 1 INTERVAL + 1 WINDOW | 200 (1.26 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-11 | 1 INTERVAL + 1 WINDOW | 200 (1.229 s) | 200 | 1 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KOBO-001 | 2026-11-12 | 0 INTERVAL + 1 WINDOW | 200 (1.391 s) | n/a (no INTERVAL revision) | 0 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-02 | 2 INTERVAL + 1 WINDOW | 200 (0.765 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-03 | 2 INTERVAL + 1 WINDOW | 200 (0.659 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-04 | 2 INTERVAL + 1 WINDOW | 200 (0.696 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-05 | 2 INTERVAL + 1 WINDOW | 200 (0.713 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-06 | 2 INTERVAL + 1 WINDOW | 200 (0.596 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-07 | 2 INTERVAL + 1 WINDOW | 200 (0.714 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-08 | 2 INTERVAL + 1 WINDOW | 200 (0.59 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-09 | 2 INTERVAL + 1 WINDOW | 200 (0.824 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-10 | 2 INTERVAL + 1 WINDOW | 200 (0.716 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-11 | 2 INTERVAL + 1 WINDOW | 200 (0.723 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-12 | 2 INTERVAL + 1 WINDOW | 200 (0.705 s) | 200, 200 | 2 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
| KISIWA-001 | 2026-11-13 | 0 INTERVAL + 1 WINDOW | 200 (0.587 s) | n/a (no INTERVAL revision) | 0 | {} / gen unobs False | {} / {} / gen unobs False | {} | PASS |
## 2. COLD-LAB-001 and EV-LAB-001
- Both return `/analytics` 200 with `analytics: []` and `readiness_window: null` (site types COLDCHAIN and EV_CHARGING).
- In the UI, `served()` returns null for an empty `analytics` list, so `storedReadinessShown` is false and the existing `capability-conclusions` line ("Not available yet: ...") stays, with the badge "No capability conclusion yet". **PASS**

## 3. First read on the fresh 8991 API (before it, only `/api/health`)
- KOBO-001: 200 in 1.195 s
- KISIWA-001: 200 in 0.410 s
- COLD-LAB-001: 200 in 0.010 s
- EV-LAB-001: 200 in 0.009 s

All are under 2 s. **PASS**
- The discarded first instance gave similar first reads: Kobo 1.445 s, Kisiwa 0.501 s.
- The slowest day-ranged read was 1.391 s.
- Not in scope, but observed: KISIWA-001 `/overview` took 12.6 s on its first read with the response store off.

## 4. "Awaiting evidence migration"
- On all four Sites, `/evidence`, `/overview` and `/analytics` returned 200 with no `AWAITING_EVIDENCE_MIGRATION` code. Every Site's `configuration_store` is POSTGRES.
- `/performance/dispatch/cutover`:
  - KOBO-001: permitted true;
  - KISIWA-001: permitted true (the gate is open, with no Kisiwa 409);
  - COLD-LAB-001 and EV-LAB-001: permitted false. This is a 200, not the migration refusal.
- So the Evidence, Overview and Performance-Dispatch pages do not reach the "Awaiting evidence migration" panel. **PASS**
- Fact recorded for completeness: the legacy file routes `/api/sites/{code}/dispatch` and `/findings` still answer 409 `AWAITING_EVIDENCE_MIGRATION` on all four Sites. The current main (8990) answers the same, so AP-1 does not change this.
  - The only UI reads of these routes are `SitePerformance`'s non-stored branch (not taken for POSTGRES Sites) and the `SiteFindings` fallback.
  - That fallback renders a generic "unavailable" panel with the server message, not the "Awaiting evidence migration" heading.

Raw evidence (scratch): `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/c6d26aed-1fa9-4f4e-a150-d6f87dd20a07/scratchpad/days.json`, `localdays.json`, `first-*.json`, `first-timings.txt`, `routes.txt`.
