# W1-UX-04 handoff - PARTIAL (phase 1 in progress)

Branch `task/W1-UX-04`, worktree `C:/Users/assef/Bineyame/AssetOpsV1-review3`, last commit `cbfca6d9`. Stopped at a clean commit near the implementer context budget. Resume phase 1 at the **Recommendation** screen.

## Landed (commit cbfca6d9)

- `frontend/src/sites/actionPresentation.tsx:76` `applicationWords(code, failedAttempts)` - domain-local `ProductWords` for the application state (PENDING -> waiting, or problem after a failed attempt; APPLIED -> `limited` "Applied; effect not yet measured", never positive; unknown -> `UNRECOGNISED_SENTENCE`, `unrecognised: true`). `:105` `plainEventWords(kind)` - like `eventWords` but an unknown kind never shows its raw code.
- `frontend/src/sites/SiteAction.tsx:728` `actionAsOf` (cutoff, else last event); `:736` `WorkCard` (`action-execution`: question "What work was done, and what is next?", state line, 4-step "The work so far" strip, History + Verification links, exact references); `:817` `HistoryCard` (`action-history`: chronological numbered event strip, `HISTORICAL` currentness words for an earlier selection, latest link, exact references incl. selected event / cutoff). Mounted at `:600` and `:887`. The old Application/History panels keep their content; their heading ids were renamed to `site-action-application-heading` / `site-action-history-heading` (the card now owns `site-action-state-heading`).
- Tests `frontend/src/sites/__tests__/siteAction.test.tsx:809-` (new; no existing assertion changed): W1 set scan, closed-disclosure scan, `expectStateLineVisible` for pending/applied Application and for latest/earlier History, tone never positive, historical never "current", `event_id` kept in the address.
- Probe result (W1 set, before changes): recommendation available had one violation, label "Input digest" -> rename to "Input reference" (`SiteRecommendation.tsx`). Unavailable/accepted recommendation, execution and history had none.
- `siteAction.test.tsx` + `siteActionVerification.test.tsx`: 57 passed; `tsc --noEmit` clean. The duplicate-key UUID warning in the verification test predates this slice.

## Next (in order)

1. Phase 1 remainder: `recommendation` (`SiteRecommendation.tsx:145-203,343-416`; lead "What action should be accepted, and how will success be judged?"; fix "Input digest"), `changes` (`SiteFoundationChange.tsx:108-182`; test `siteFoundationChange.test.tsx`, known flake), `sitework` (`SiteWorkActions.tsx`, test `siteWorkActions.test.tsx`; proved-zero only after a successful bounded read, plain as-of beside it). Add a `W1-UX-04:` W1-set test per route following `siteAction.test.tsx:809`.
2. Phase 2: Plan/Evidence/Verification in `SiteActionVerification.tsx` (1420 lines), `verificationWords.ts`, `recommendationVerification.tsx`. Diff-only additions to `siteActionVerification.test.tsx`; do not weaken any S6-02b assertion.
3. Proof at final revision: focused tests, `npx.cmd tsc --noEmit`, full `npm.cmd test`, `node frontend/docs/architecture/check_v69_dependency_registry.cjs`, `tools/check-all.ps1 -ExecutionPolicy Bypass`, 1440/390 captures via `tools/w1-ux-01-evidence.mjs` with `s601b_action_walkthrough.py`, `s602b_verification_walkthrough.py`, `s603_site_work_walkthrough.py`. Then `.agent/W1-UX-04-review-packet.md`, task Status `in_review`, ACTIVE_CONTEXT and CODE_STATE.

## Notes and risks

- In bash on this machine `npx.cmd` from Git Bash fails ("C:\Program"); run vitest/tsc through PowerShell.
- StepStrip keys steps by label; repeated labels need numbering (done in History).
- Not run yet: full suite, guards, registry checker, captures.
