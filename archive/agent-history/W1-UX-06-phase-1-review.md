# W1-UX-06 phase 1 review

Reviewer: fresh independent Claude reviewer (not the author). Revision under review: `28441130` (diff `23afc7c4..28441130`, excluding `.agent`). Worktree `AssetOpsV1-review5`, detached.

## Verdict: ACCEPT

All four parts of phase 1 meet the packet and `D-2026-10-17-w1-ux-06`. There are no High or Medium findings. The four Low findings below do not block. Phase 2 (combined walkthrough, final 1440/390 capture set) is not part of this review, and nothing here is owner acceptance.

## What was verified

- **Width check** (`tools/evidence-checks.mjs`). `widthVerdict` requires `innerWidth === requested` and `clientWidth` in `[requested-20, requested]`, and treats non-finite values as a failure. `requireWidth` throws on failure before any measurement, records a failure claim even when `record: false`, and the window fallback counts only if the recheck then passes. All 23 browser scripts import the shared guard and call it after each resize, `Page.navigate`, `Page.reload` and `history.back/forward`, including the capture resize. No script navigates any other way: no `location.reload/assign/href=`, single-quoted CDP method or `navigateToHistoryEntry` was found in `tools/*.mjs`. The one exempt script, `run-store-browser-evidence.mjs`, gives a reason. The `s302` failure path counts the failure, skips measurement and exits 1. `layout-evidence` has a single trigger site, inside `visit()`, and it is guarded immediately before MEASURE.
- **Guard is non-vacuous (rerun by me).**
  - Deleting the guard after `history.back()` (`s701-health-evidence.mjs:214`) failed the inventory test at `s701...:212`.
  - Deleting the capture-resize guard (`w1-ux-01-evidence.mjs:135`) failed it at `w1-ux-01...:133`.
  - Both were restored with `git checkout`, and the tree is clean.
- **Real Chrome:** `node tools/evidence-checks.mjs --self-test` gave 4/4.
  - Real 390 and real 1440 pass.
  - A 1400 px page at mobile 390 fails (innerWidth 1400, clientWidth 980).
  - Override 1440 claimed as 390 fails.
- **As-of.** Frontend `AS_OF_PATTERN` is byte-identical to the evidence copy (asserted by the guard), and it accepts only `As of D Mon YYYY, HH:MM UTC` or `As of: time not recorded`. `expectStateLineVisible` now enforces it. The Health `expectRefusedStateLine`, Foundation unavailable and Site Work unread cases call the shared helper and keep their exact `toBe("As of: time not recorded")`. `productStatus.test.tsx` imports the shared helper rather than a local copy. The remaining `/^As of /` matches in `evidenceClaimLimit.test.tsx:540,554` run after `expectStateLineVisible`, so they are redundant rather than substitutes.
- **Backend lag.** `receipt_lag()` returns None when `observed_at > received_at`, including by 1 ms, and keeps 0 and positive lag. The fixture changes `-90` to `null`. The contract test asserts that the untrusted-clock lag is null, that every lag is null or >= 0, and that 21600 is present. A UI test asserts that no negative or "reached the server" text appears for the clock-offset gateway.
- **Sentences.** The three backend sentences say "No channel-link set is in effect..." with the same trigger (`binding_set is None`) and the same unbound/Unknown/no-snapshot meaning. The three `NO_CHANNEL_LINKS_*` overrides are removed, and the screen shows `statement`/`reason` as sent. There are exact assertions in `test_s1_bindings.py` and `siteFoundationRevision.test.tsx`.
- **Labels against the ruling.**
  - Q1: badge `Set up to report`, `badge--configured`, legend updated.
  - Q2: strip `Set-up steps`. "Gateway registered" is registration only and "Commissioning confirmed" stays not-known.
  - Q3: `In contact; its latest report is old` appears only for CURRENT + OLD with `!factAgeUnknown`, and `factAgeUnknown` covers a null age, NEVER_RECEIVED, OBSERVED_AFTER_RECEIPT, UNTRUSTED and UNKNOWN. Otherwise it says `...age cannot be confirmed`. Both use tone limited, and the age is shown separately.
  - Q4: unrecognised Readiness gives the headline `Set-up state not recognised`, "Readings linked" is not-known, the badge is neutral and named, and the verdict sentence makes no judgment. An unrecognised Health code, or zero enabled outside `NO_REGISTERED_SOURCE`, gives `Gateway contact cannot be confirmed`. No-registered and all-disabled stay distinct.
  - A mutation that disabled the `factAgeUnknown` branch failed the untrusted-clock test; restored.
- **Changed tests.** I diffed every changed test. Only one existing assertion was loosened: the Health refused-state helper used to require `status.closest("details") === null` and now uses the shared `visibleOutsideClosedDisclosure`. That is equivalent for visibility, and the shared helper still asserts that every exact-reference disclosure is closed. Elsewhere, label strings were updated per the ruling, and `queryByText(/Ready to report/)` was widened to `/Ready to report|Set up to report/`, which is stricter. No fail-open path was found.

## Checks run (serial, by me, at `28441130`)

| Check | Result |
| --- | --- |
| `node --test tools/checks/test_evidence_checks.mjs` (and `node` direct) | 9/9 pass |
| Guard mutation x2 | each failed as expected; restored |
| `node tools/evidence-checks.mjs --self-test` (real Chrome) | 4/4 |
| `pytest test_s7_source_health_rules.py test_s7_health_contract_postgres.py test_s7_source_health_postgres.py test_s1_bindings.py test_s1_bindings_postgres.py test_s1_foundation_postgres.py` with the 5-path PYTHONPATH, private `assetops_w1ux06rev_test` (created, then dropped) | 77 passed, 263 s |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run` siteHealthBoundary, siteFoundationRevision, siteWorkActions, productStatus, evidenceClaimLimit | 5 files, 216 passed |
| `npx.cmd vitest run` t028Vocabulary, sharedVisualVocabulary, w1Vocabulary | 3 files, 35 passed |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` | both passed |

Vitest ran under this session, despite the standing brief's sandbox note. I did not run the full suites. For those I rely on the implementer's figures at `90699341` (backend 2590/0 skipped/0 failed, 1494 s; frontend 1812). The later commits up to `28441130` touch only `.agent`.

## Findings

1. **Low: a zero-enabled read under a non-no-source code keeps a reassuring state line.** `frontend/src/sites/healthHeadlines.tsx:191` (headline) and `:34-42` (`ALL_CURRENT` words); test `frontend/src/sites/__tests__/siteHealthBoundary.test.tsx:540`.
   - With zero enabled gateways and `ALL_CURRENT`, the headline is correctly `Gateway contact cannot be confirmed`.
   - The state line still reads "Every enabled gateway is in contact" (tone neutral), and there is no next step. The test asserts only the headline.
   - The server cannot produce this combination (`source_health.py:287` maps zero enabled to `NO_REGISTERED_SOURCE`), so it is defensive only. The ruling's "limited state line" is not met in that branch.
   - Fix: when `enabled.length === 0` outside no-source, use limited words, and assert the state line.
2. **Low: the server's readiness sentence still says "Ready to report means..." under the new badge.** `backend/assetops_backend/sites/binding_service.py:88-90`. The test at `frontend/src/shell/__tests__/siteFoundationRevision.test.tsx:2123` explicitly tolerates it with `(?! means)`.
   - The ruling covers the badge only, and the handoff names this. The badge and the sentence now use different words.
   - Fix: batch it into the W1 plain-language task, or get an Architect one-liner.
3. **Low: two gaps in how the width guard proves itself.**
   - (a) In `tools/checks/test_evidence_checks.mjs:98,113`, `GUARD_CALL` is tested on lines without filtering comments, so a commented-out `// await requireWidth(...)` within 6 lines would satisfy the proximity rule.
   - (b) `tools/layout-evidence.mjs:636` passes no `claim` and discards the result. A passing run therefore records no innerWidth/clientWidth in its output, although the packet asks that claim output record both widths. A failure still throws and names both.
   - Fix: skip comment lines in the guard-call scan, and log or claim the returned widths in layout-evidence.
4. **Low: the unrecognised Readiness test uses `in`, which follows the prototype chain.** `frontend/src/sites/FoundationBindingsPanel.tsx:113,154`. A server code such as `constructor` or `toString` would be treated as recognised and would render a function value. This is contrived.
   - Fix: use `Object.hasOwn(READINESS_WORD, state)` in both places, or the `setupReadinessWords(...).unrecognised` flag.

## Residual risk (not findings)

- No real evidence script has yet been run against the app with the guard in place; that happens in phase 2. Until then, any narrow claim from UX-01/03/04/05 remains **not established**.
- The `Browser.setWindowBounds` fallback is proven only by the unit fake.
- `tools/w1-ux-02-evidence.mjs` is not present. The inventory test will fail on it after the UX-02 merge unless it is guarded, which is intended.
