# V-01b fresh Claude review — Lab and Evidence visual fidelity

Reviewer: fresh independent Claude Reviewer (did not build the slice). Tree `task/V-01b-evidence-lab-visual` at `8ab5589`; slice diff `b1ac0a8..6d5fba9`; merge `8ab5589` brings only planning/docs/registry/ledger files (no product code), and every check below was run on `8ab5589`.

## Verdict: RETURN (one small finding; fix round, then ACCEPT without a further full review)

The slice is sound. Every displayed Evidence and Lab value I traced comes from a real read, the missing states are specific and honest, the guard change is stricter where it matters and demonstrably fails when broken, and all checks pass. One status line states something false in a degraded state, and the review rule treats a false statement as a finding, not a carry. The fix is a few lines and one test.

## Findings

1. **`frontend/src/shell/RunIngestionOverview.tsx:229-242` (`receivedStatement`): "Nothing from this run has been received centrally." is shown when the facts are unknown.**
   - Defect: the function returns `NOTHING_RECEIVED` for every non-null commit except a loaded legacy commit. That includes (a) a Commit read that failed (`status` is `not_found` or `unavailable`), and (b) a registered run whose Commit read is `RELEASED_TO_GATEWAY` with `registered_release.status === "GATEWAY_UNAVAILABLE"` and `delivery: null`. In both cases the screen cannot know whether receipts exist. In case (b) the run has been released, so receipts are likely. `ReleaseFacts` in the same component handles both cases honestly ("could not be read…" / "Gateway delivery: Not readable…"), so the status strip contradicts the panel below it.
   - Why it blocks: it is a false statement on screen, not imperfect naming (WORKFLOW Review Packet: "this name is false is still a finding"). It also contradicts the slice's own rule (`RunIngestionOverview.tsx:21-23`: an absent read "is said so… never a mock value"). No test covers it: `v01bLabIngestion.test.tsx:388` keeps the commit read pending forever, so the `unavailable` path is never rendered.
   - Fix: return "Nothing from this run has been received centrally." only when `delivery !== null && delivery.withReceipt === 0`, or when the loaded commit is `NOT_COMMITTED`. When the Commit read is not loaded, say that the commit status could not be read. When `registered_release` is present but `delivery` is null, say the gateway delivery could not be read. Add one test for each of the two states.

## Checks I ran (actual results)

- `npx.cmd vitest run` (frontend): **Test Files 57 passed (57); Tests 1381 passed (1381)**. On this run the sandbox did not block esbuild config loading.
- `npx.cmd tsc --noEmit -p .`: exit 0.
- `npm.cmd run build`: "✓ built in 13.27s", exit 0 (chunk-size warning only).
- `powershell -File tools/check-all.ps1` (`.venv` present, default Python): **All 6 guards passed** (architecture seams, navigation truthfulness, agent workflow, dependency registry, delivery checker fixtures, screen ledger "110 screens, 88 distinct models, 258 panels").
- Backend pytest: not run. `git diff b1ac0a8..8ab5589 -- backend contracts gateway host` is empty, so nothing backend-adjacent changed.
- `tools/layout-evidence.mjs` and `tools/v01b-lab-evidence-evidence.mjs`: **not run by me.** They need Chrome, private servers and the walkthrough DBs, and I started no servers. The 398 PASS / 5 FAIL and 101/101 results are the Implementer's and remain unverified by this review.

## Specific verifications

1. **Values trace to real reads; no invented conclusions.**
   - Evidence Overview reads only `counts`, `sources`, `states`, `extent`, `migration` and gateway health. Analysis reads only `listRecords` and the record detail.
   - The badge is the neutral "No capability conclusion yet". It never shows "Evidence limited", a score or a ranking.
   - `evidence:3` lists silent sources explicitly as "a fact, not a recommendation".
   - Lab boxes and panels come from the execution, Stage and Commit reads (`registeredDelivery`, `decisionLine`, `compactLines` of a stored envelope).
   - Every unsupported mock portion is a specific "Not available yet: …" sentence that names the missing rule or read. Apart from Finding 1, the missing states are honest.
   - The conflict "Original reading" column renders `conflicts_with_source_time` and `conflicts_with_evidence_id`, with "not stated" when absent. A test proves it; no stored instance exists.
2. **Guard `tools/checks/shell-overflow.ps1` 2b.** Net effect: the allowed set is widened to admit `.app-frame--lab`, while the check itself becomes stricter.
   - Each part must now *start with* the shell class, followed by a word boundary. Previously, any part that *contained* `app-frame--operator` passed.
   - The operator half is now required to be non-empty (previously only "any shell rule").
   - A Lab half is newly required.

   I probed `primitives.css` four times. Each probe was reverted with `git checkout`; the tree is clean apart from the pre-existing `coordinator-handoff.md` modification.
   - P1, bare `.app-frame .nav-rail` in the 640px block: exit 1, "not scoped to .app-frame--operator or .app-frame--lab".
   - P2, every `.app-frame--lab` renamed `--labx`: exit 1, seven "not scoped" lines plus "No narrow-width .app-frame--lab rule…".
   - P3, `body .app-frame--operator .app-frame__side`, which the old guard accepted: exit 1. This proves the check is stricter.
   - P4, operator parts removed: exit 1, "No narrow-width .app-frame--operator rule… vacuous".

   The widening is backed by the Lab phone layout, which is browser-measured (Implementer evidence) and asserted in `overflowContainment.test.tsx` (`app-frame--lab` class). It still amends an Architect scoping rule, so it is a carry for Architect ratification (C1), not a finding.
3. **`tools/layout-evidence.mjs`.**
   - The 5 FAILs are reported as FAIL / "not run" and never as passes.
   - The Q8 drawing FAIL ×3 is detected from the page's own refusal text, so it is a genuine measurement.
   - The T022 fuel-loss FAIL and the legacy-Kobo FAIL are emitted unconditionally whenever the Lab Site or KOBO-001 is registered. They are honest preconditions, but they are assumed, not detected (C3).
   - Creating Drafts on the measured store is not new: the legacy section already created and executed Drafts. New: `registeredKoboLab` creates **and executes** a registered run on whatever store BASE points at (default `http://localhost:5173`). It never commits, so it cannot add central evidence. Executing a registered run does, however, admit envelopes into that store's shared gateway ledger, and `gateway/tests/test_gateway_upload.py:131` shows that a batch sealed with another run's envelopes is never releasable. Safe on private walkthrough copies; not safe as a default against an owner's store (C2).
4. **Lab 390px fix, "Open Site Evidence", Q1 label.**
   - The shell fix is minimal: a class plus mirrored selectors, and the operator rules are unchanged.
   - "Open Site Evidence →" appears only with a registered delivery that has at least one central receipt and a loaded execution, and it links to the run interval.
   - The Q1 label is honest: the stale Stage line is still shown verbatim, under Advanced details, next to a label that points to the Commit read's receipts. The real fix stays a backlog carry.
   - Keyboard: every new control is a native button, link or `<details>` summary. Code reading only; I did no browser check.

## Carries (record in `.ai/MILESTONE_REVIEW_BACKLOG.md`; none blocks)

- C1. The Architect should ratify the 2b amendment: phone rules may now name `.app-frame--lab`, and the guard is anchored. The guard does not check that `SimulatorLabShell` carries the class; only `overflowContainment.test.tsx` does.
- C2. `layout-evidence.mjs` default BASE plus `registeredKoboLab` executes a registered run on the measured store, using the same KOBO-001 day as the walkthrough's released run, and grows its gateway ledger. Gate the registered run creation behind an explicit opt-in or a non-default BASE, or refuse when BASE is the default dev server.
- C3. The T022 and legacy-Kobo precondition FAILs are unconditional on `LAB_REGISTERED`. Detect the precondition (tank capacity versus starting level), so a registered Site that could run is measured rather than assumed failing. Executed-run (T022) coverage is now absent on registered-only stores.
- C4. Flow box 2 puts execution `reported_count` next to Stage `envelopes.length` ("321 … / 329 admitted") with no explanation (already the packet's owner focus).
- C5. The Evidence heading "Data sources · data quality, not equipment condition" keeps the mock's "data quality" while the quality grade is "Not available yet". This is mock wording and honest because of the adjacent missing state; owner's call.
- C6. `runIngestion.css` hard-codes the private/public flow-box colours as local custom properties rather than theme tokens. Cosmetic.
- Already carried by the packet, confirmed: Q1 stale Stage `upload_state`; the `.action` cascade overriding `.action--primary` elsewhere; the gateway-unavailable Evidence state is an intercepted 503; there is no stored contradictory instance.

## Not verified by this review

Layout-evidence and evidence-tool results (398/5, 101/101), the screenshots, and visual density at 1440/390: no browser or servers were run. Owner visual acceptance remains pending, as the packet states.
