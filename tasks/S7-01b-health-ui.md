# S7-01b — Site Health and battery Unknown UI

Status: active (activated 2026-10-16 from main `f3de235a`; S7-01a merged); was implementation-ready (plan re-review: S3-02b R1 applied by coordinator; S7-01b R2 carried). USER_REVIEW_REQUIRED: true; owner walkthrough before merge. Size M, two phases. Branch `task/S7-01b-health-ui` from reviewed/merged S7-01a. Depends on its central fixture and two read contracts. Authority: `.agent/architect-W1-remaining-answers.md`, `.ai/DECISIONS.md` `D-2026-10-16-a-s7-health`; registry `I-source-health-ui`, `I-asset-boundary-ui`, `health:2#a`, `asset:3#a`. Mock `frontend/mockups/v69/index.html` / `screen-manifest.json` `health`, `asset` guides layout only; positive physical `asset:3#b` stays unmapped.

## Verified seams and UI behavior

Existing gateway client is `frontend/src/sites/gatewayHealthClient.ts:3,68`, S2 source explanation `frontend/src/sites/LedgerSiteEvidence.tsx:528-550`; Site shell/routes `frontend/src/shell/operatorSiteRoutes.ts:1,230-244` and `SiteDetailFrame.tsx:35-43`. **New:** Site Health and battery asset detail routes/components/clients and focused UI tests. Do not use S2 Evidence Analysis contact text as asset condition.

Health presents gateway contact against declared cadence beside reported-fact observed time and age, source-specific contact only if supplied, queue/clock/disk last-reported values, registration and diagnostic IDs, server receipt, `read_at` and watermarks. Distinguish no registered source, never received, stale contact, old facts despite fresh receipt, stale projection only if the S7-01a read has a derived projection, and unavailable read. No green zero or equipment-condition claim. Asset detail pins effective basis/asset/binding IDs and shows physical condition `UNKNOWN` with missing causal inputs or `NOT_CONFIGURED`; optional accepted SOC and declared rating remain explicitly separate. Withhold replacement/warranty/remaining-life claims. Scope changes, reload and exact diagnostic/binding links must preserve selection; 401/403/404 are refusals.

## Phases and proof

| Phase | Deliverable and focused checks |
| --- | --- |
| 1. UI | **New** routes/components/clients plus `frontend/src/sites/__tests__/siteHealthBoundary.test.tsx` (new). Cover six central cases, never received, no source, wrong Site/asset, store failure, stale projection only when S7-01a has a derived projection, configured missing input and unbound battery; keyboard/focus, reload, 1440/390, links. Run `tools/layout-evidence.mjs` or record `not run` with its unmet precondition. Run `npx.cmd tsc --noEmit` and `npm.cmd test` from `frontend/`. Backend code is not planned; if changed, run one full final-revision suite per `backend/TESTING.md:104,112-125` on private `*_test` DB. Any new SQL writer must pass statement-level rule 8 and `python tools/writer_guard_probes.py`; any new migration re-chains after main `0018` and unmerged S6-02a `0019_verification_core`. |
| 2. Review | Run registry checker and `tools/check-all.ps1`; independently review app versus mock, central lineage, missingness and exact links. Resolve High/Medium findings, then owner walkthrough before merge/panel promotion. User-facing copy and visual polish carry to W1 conclusion. |

## Reproducible owner walkthrough

**New** `tools/s701_health_walkthrough.py` offers `prepare|serve|deliver|attest|drop`; private DB prefix `assetops_s701_owner*`, work prefix `var/s701_owner*`, reserved API/web ports 8947/5447. `prepare` registers a distinct gateway per central case and publishes the six S7-01a cases through authenticated central ingestion so latest-per-gateway selection exposes each case; use separate gateways for disk pressure/stop and recovery so both remain visible. It also prepares never-received and configured-but-missing battery on KOBO-001, plus a second Site with no registered source and an absent/unbound battery. `serve` prints verified exact backend/frontend start commands and both Sites' Health and asset URLs. Run `deliver` through the authenticated central path immediately before viewing to give current-heartbeat and old-facts-freshly-received cases fresh server receipt times; `attest` checks their current receipt states. Open the printed `http://127.0.0.1:5447/sites/KOBO-001/health` and second-Site Health/asset URLs; record diagnostic IDs, receipt and fact times, watermarks, Unknown reasons and reload. Compare app with `index.html#/health` and `#/asset` at 1440/390; keyboard links and Back. Stop servers and `drop` private fixture. The wrapper must print authoritative URLs if routing differs.

From repo root run `python tools/s701_health_walkthrough.py --db assetops_s701_owner1 --work var/s701_owner1 prepare`, then the same command ending `serve`; in a second PowerShell at `frontend/`, run `$env:ASSETOPS_API_PORT="8947"; npm.cmd run dev -- --port 5447 --strictPort`. The wrapper runs `python -m uvicorn lab_app:app --host 127.0.0.1 --port 8947` from its prepared host with private DB env and prints exact URLs for KOBO-001 and the second Site at `http://127.0.0.1:5447`. Run the same wrapper command ending `deliver` immediately before opening the URLs, then `attest`, stop servers and run `drop` with the same DB/work arguments.

## Architect questions

1. **Recommendation:** make the asset route use the configured effective asset ID, with a typed `NOT_CONFIGURED` Site entry state when no battery exists. An asset ID outside the effective basis, including a foreign or superseded-revision asset, returns 404/typed refusal rather than a healthy or Unknown row for that ID.

## Plan fix round 1

Made all health cases reachable in the walkthrough with per-case gateways, fresh receipts and a second Site; clarified projection, asset identity and layout evidence.
