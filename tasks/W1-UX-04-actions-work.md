# W1-UX-04 — Action, work, change and verification presentation

Status: implementation-ready. Branch `task/W1-UX-04` after W1-UX-01 **and reviewed/merged S6-02b and S6-03**; re-inventory their actual files at merge. Frontend only; owner walkthrough deferred to combined W1. Scope: `recommendation`, `changes`, `action-overview`, `action-plan`, `action-execution`, `action-evidence`, `action-history`, `verification`, `sitework`. Use [umbrella](W1-UX-mockup-fidelity.md), v69 named screens/manifest, S6-01b/S6-02b/S6-03 packets and the S6 verification decisions.

## Visible result

Make each screen answer a user question: what is proposed; what work happened; what evidence was planned/received; did the measured trial meet its goal without harmful trade-offs; what remains to do. Use one Action story across Overview/Plan/Execution/Evidence/History, plus two-window comparison graphic in Verification and chronological change/effect strip in Changes. Site Work shows scoped persisted Actions and next step, with a watermarked proved-zero state only after successful bounded read. The Action root and selected historical outcome stay visible across child links and reload. Distinguish applied, completed, resolved and verified; activity never establishes effectiveness or savings. A withdrawn older VERIFIED outcome is historical with current reassessment state. Keep guardrail failure prominent in plain language with measured value, threshold and unit; unknown required evidence yields “We cannot tell yet” without hiding known failures.

Initial seams `SiteRecommendation.tsx:145-203,343-416`, `SiteAction.tsx:290-367,451-580`, `SiteFoundationChange.tsx:108-182`; S6-02b Plan/Evidence/Verification and S6-03 Site Work components are merge dependencies. Put plan IDs, event IDs, source digests, rule versions, typed reason codes and opaque cutoff tokens in labelled exact detail; slot tables stay in the owning Evidence view; keep the plain “as of <time>” bound beside every zero, current and historical claim in the default reading, retaining exact links. Keep accepted snapshot, latest-current default, persistent historical selector and wrong-Site/refused states from source tasks. No verification verdict derived in Site Work.

Shared acceptance applies to this slice: opt every owned route into the W1 vocabulary set as it migrates; scan default, graphics, accessibility and Analysis/Evidence prose. With the exact-reference disclosure closed, test each applicable non-positive state for a visible plain state sentence, scope and “as of <time>” outside it. Keep material limitations beside the headline, and substantive depth in the owning contextual tab/view link at 1440 and 390. Preserve labelled exact references, authored/test-data qualification and fail-closed assertions. Capture 1440/390 served app versus `frontend/mockups/v69/index.html#/<id>` using a per-slice Playwright evidence script following `tools/v01a-foundation-evidence.mjs`; record each skipped capture as **not run** with its blocking precondition.

Effort: **M in two phases**. Phase 1 covers the six workflow screens; phase 2 covers the three Plan/Evidence/Verification screens, including the large merged verification component. If merge re-inventory exceeds this boundary, split phase 2 before implementation rather than weakening proof.

## Phases and proof

| Phase | Deliverable | Focused proof |
| --- | --- | --- |
| 1 | Recommendation/Action/Work/Changes headline and workflow visuals | Accepted/proposed/applied/pending/failed and proved-zero versus unknown; exact links and selected event, 1440/390 v69 comparison for six named screens. |
| 2 | Plan/Evidence/Verification comparative visuals and disclosure; finish all nine screens | VERIFIED/INEFFECTIVE/INCONCLUSIVE, guardrail/target misses, missing slots, withdrawn historical state and different-Finding hold; 1440/390 served comparison for Plan/Evidence/Verification. |

Focused UI tests per phase; final `npm.cmd test`, type check, vocabulary scan, registry checker and relevant guards. Fresh independent reviewer checks all nine screens and diffs `siteActionVerification.test.tsx` against S6-02b; any weakened fail-closed assertion blocks review. The reviewer checks S6-02b's fail-closed tests and selected URL persistence before merge. No owner walkthrough until combined W1. Backend change only if Architect confirms an absent label cannot be derived from an exact read.

## Architect ruling

Questions answered by `D-2026-10-16-w1-ux` in `.agent/architect-W1-ux-answers.md`. Its destination, vocabulary and honest-state boundaries govern this packet.
