# W1-UX-05 — Foundation, Readiness, SLD, Health and battery presentation

Status: implementation-ready. Branch `task/W1-UX-05` after W1-UX-01 **and reviewed/merged S7-01b**; inspect its actual files at merge. Frontend only; owner walkthrough deferred to combined W1. Scope: `foundation`, `readiness`, `sld`, `health`, `asset`. Use [umbrella](W1-UX-mockup-fidelity.md), v69 named screens/manifest, S1-01/02/03 and S7-01b packets.

## Visible result

Foundation leads with what equipment and operating settings are recorded for the selected period, using a compact equipment/configuration graphic. Readiness leads with what still needs connecting or confirming and a next-step list. SLD keeps the real configured diagram but makes reporting/unknown links and legend readable before part IDs. Health leads with source contact and reported fact age in separate visual lanes; a recent receipt never implies healthy equipment or fresh facts. Battery asset detail prominently says physical condition cannot be judged when the required causal inputs are missing, lists the missing inputs and preserves accepted SOC/rating as separate facts. No warranty, replacement or remaining-life statement.

Initial seams `StoredFoundationViews.tsx:183,367-426,494-675`, `FoundationBindingsPanel.tsx:158`, `ReadinessOverview.tsx:264,347-400,512-570`; S7-01b Health/asset components are merge dependencies. Move exact revision, signal/diagnostic/binding IDs and raw status basis into `DigDeeper`; retain precise selected-time, record and diagram links. Preserve `MissingClaim` for unsupported commissioning, firmware, uptime, signal strength and physical condition. No “green zero” for absent reporting. Clearly separate not registered, never received, stale contact, old facts, unavailable read and not configured battery.

Shared acceptance applies to this slice: opt every owned route into the W1 vocabulary set as it migrates; scan default, graphics, accessibility and Analysis/Evidence prose. With the exact-reference disclosure closed, test each applicable non-positive state for a visible plain state sentence, scope and “as of <time>” outside it. Keep material limitations beside the headline, and substantive depth in the owning contextual tab/view link at 1440 and 390. Preserve labelled exact references, authored/test-data qualification and fail-closed assertions. Capture 1440/390 served app versus `frontend/mockups/v69/index.html#/<id>` using a per-slice Playwright evidence script following `tools/v01a-foundation-evidence.mjs`; record each skipped capture as **not run** with its blocking precondition.

## Phases and proof

| Phase | Deliverable | Focused proof |
| --- | --- | --- |
| 1 | Foundation/Readiness/SLD headings, visuals, disclosures | Selected-effective version, missing bindings, unconfirmed commissioning, absent gateway facts, SLD gap tags; 1440/390 served app/mock evidence for three screens. |
| 2 | Health/asset freshness and Unknown visuals, all five screen audit | Six S7 central cases, old facts with fresh receipt, no source, never received, wrong Site/asset/refusal, battery missing input and exact links/reload; 1440/390 `health`/`asset` comparison. |

Focused tests per phase; final full `npm.cmd test`, type check, vocabulary scan, registry checker and relevant guards. Fresh independent review checks all five screens and diffs S7-01b fail-closed tests; any weakened assertion blocks review. No owner walkthrough until combined W1.

## Architect ruling

Questions answered by `D-2026-10-16-w1-ux` in `.agent/architect-W1-ux-answers.md`. Its destination, vocabulary and honest-state boundaries govern this packet.
