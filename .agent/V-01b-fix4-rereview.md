# V-01b fix rounds 4 and 4b: fresh re-review

Reviewer: fresh Claude reviewer, independent of the fix-4 and fix-4b implementers.
Branch: `task/V-01b-evidence-lab-visual`, HEAD `5b9f464`. Scope: `4bfe481..5b9f464`, judged against F1 and F2 of `.agent/V-01b-fix3-rereview.md`, the "Fix round 4" and "Fix round 4b" sections of `.agent/V-01b-review-packet.md`, and the changed line in `.agent/V-01b-owner-walkthrough.md`. Owner direction: `.agent/owner-V-01b-fix3-return-2026-10-13.md` (option 1).

## Verdict: ACCEPT

F1 and F2 are fixed. I ran the evidence tool myself on a freshly prepared private store, and it printed exactly what the packet and the walkthrough say: `101/101 claims passed; 2 not run`, exit 1. Both Stage claims passed at 1440 and at 390. The robustness changes cannot turn a failure into a pass. Every page or claim that is not reached now ends up as FAIL or `not run`, and either one makes the exit code non-zero. No blocking findings. The items below are carries.

## F1: Stage claims (`tools/v01b-lab-evidence-evidence.mjs:212`, `:405-408`)

- **Neutral copy.** The tool waits for `details[data-disclosure="stage"] [data-gateway-delivery-neutral]` to contain "does not establish upload or central receipt state". That string and attribute exist only at `frontend/src/shell/GatewayLedgerView.tsx:70-71`. The old Q1 label is gone from the tool.
- **Not vacuous.** At `ee4474b`, before fix 3, the component had no `data-gateway-delivery-neutral` attribute. Run against that version, this claim would have timed out and failed.
- **Absence claim on `[data-gateway-upload]` / `[data-gateway-receipts]`.** I treat this as a **carry, not a finding**.
  - It cannot fail against the current tree, because nothing renders those selectors.
  - It still works as a regression guard. If anyone reintroduces the old fields under their old attributes, it fails. The unit tests (`gatewayLedgerStage.test.tsx:214-215`, `v01bLabIngestion.test.tsx:348-349`) and `layout-evidence.mjs:1288-1289` use the same pattern.
  - The packet discloses it honestly ("weak by construction", packet Fix round 4, first bullet). It also adds nothing to the evidence for acceptance criterion 2 beyond the positive claim.
  - The claim's name overstates it slightly. "shows no upload or receipts field" really means "has no element with the two old attributes". It does not check for text such as "Upload pending". Optional at the next touch: rename the claim, or also assert that "Upload pending" is absent from the disclosure text.

## Tool robustness (`684e0d4`)

- **Ready state.** `go()` already returned the `waitFor` boolean (`:124-129`). The overview and analysis functions now use it.
  - When the page never becomes ready, they print a FAIL that shows what the page displayed instead, skip the dependent claims as `not run`, and return without throwing.
  - The overview's ready condition is stricter than before. It now also requires that the "Data sources…" and "Most useful next evidence" panels exist.
  - Both ready claims are real. In my run, all four PASS lines (Evidence overview and analysis, at desktop and narrow) came from actual waits that resolved.
- **Nothing that used to fail can now pass silently.**
  - The only claim the change turned into something other than a FAIL is the old "a stored READY draft exists" claim. It is now `not run`, and `not run` makes the exit code non-zero (`:496`).
  - Every claim that asserted something before still asserts it.
  - The calls to `go()` that still ignore the return value (the second analysis visit at `:320`, the empty and missing-Site states, `labRun`, and the empty Lab runs) are unchanged from before. Each is followed by positive assertions that would fail on a page that is not ready, for example `adv.length > 0`, `rows > 0`, `gi >= 0`, and the exact-text checks.
- **Missing READY draft.** It prints `not run` with the fixture reason (`:440-441`). The header no longer promises a fallback that intercepts the response (`:13-15`).

## F2 and the documents

- **F2.** The docstring at `frontend/src/shell/RunIngestionOverview.tsx:20-21` now reads "the Stage's constant upload fields are not shown". That is accurate.
- **Packet formatting.** The packet is 144 lines and contains no non-empty line of two characters or fewer. The "Fix round 4" section reads normally. The one-character-per-line damage from `f22ac56` is repaired.
- **Packet claims.**
  - The packet says the fix-4b result is not comparable to c1's 101/101, and gives the reason: it adds 4 ready-state claims and lacks the 4 not-committed claims. That is correct (2 widths × 2 ready claims = 4 added; 2 widths × 2 not-committed claims = 4 missing).
  - The packet's cleanup account and its checks match what I saw.
- **Walkthrough (`.agent/V-01b-owner-walkthrough.md:17`).**
  - The expected-result line ("on a freshly prepared store it prints `101/101 claims passed; 2 not run`…") is what I reproduced.
  - Step 2 of the same Start list (`:11`) tells the owner to run `prepare`, and `serve` is step 3. So the owner is told that `prepare` must come first. This matters because the walkthrough databases do not exist yet.

## Carries (non-blocking)

- **C1 (nit), `.agent/V-01b-review-packet.md:27`.** Acceptance criterion 2 still says "see Fix round 4 for the measured fix-4 result (not 101/101)". The current measured result is the fix-4b one (`101/101 claims passed; 2 not run`), which line 68 states correctly. Point line 27 at Fix round 4b.
- **C2 (nit), `tools/v01b-lab-evidence-evidence.mjs:490`.** The summary line mixes units. "N/M claims passed" counts claims, but "K not run" counts skipped groups. Each draft group stands for 2 claims, and a skipped overview or analysis group stands for several. The listed reasons make this readable, but the number alone undercounts. The walkthrough could also say that the run exits 1 on a fresh store, so the owner does not read that as a failure.
- **C3 (residual risk), acceptance criterion 2, the not-committed Lab state.** It is no longer measured on the owner's walkthrough store. The last screenshot measurement is c1's, taken on a store that held READY drafts and before fix 3. Fix 3 did not touch that code path (`labStates.check`, the ingestion status and the flow box), so the risk is low. Still, an owner walkthrough on a fresh store will not show that state. A fixture that creates a READY draft would close this.
- **C4 (carry), absence claim naming.** See F1 above.
- **Carried from earlier rounds, unchanged:**
  - Q1 backend: retire the obsolete Stage `upload_state`, `upload_statement` and `receipts` fields, or give them local-only semantics.
  - Q8: the drawing claims remain unmeasured.

## Checks I ran

- **Evidence tool on a private store.**
  - Prepare: `python tools/v01b_lab_evidence_walkthrough.py --db assetops_v01brr4 --empty-db assetops_v01brr4empty --work-name v01b-rr4 prepare` ("Prepared."; the evidence store comparison PASSED; cutover permitted).
  - Serve: `serve --port 8894 --web-port 5394 --empty-port 8895 --empty-web-port 5395`, with Vite on 5394 and 5395 using `ASSETOPS_API_PORT` 8894 and 8895 and `--strictPort`.
  - Run: `ASSETOPS_CDP_PORT=9394 node tools/v01b-lab-evidence-evidence.mjs http://localhost:5394 <scratch> http://localhost:5395`.
  - Result: `101/101 claims passed; 2 not run`, exit 1. The released run was `run-234889a36d0a4333a1e8877bf5015762`, and there was no not-committed draft. The four Stage claims passed, the four ready-state claims passed, and the status bar showed "198 of 198 batches have a central receipt".
  - Before preparing, I checked that ports 8894, 8895, 5394, 5395 and 9394 were not listening.
- **Cleanup.**
  - I stopped all four servers by their listening PIDs. The gateway exited with them.
  - Ports 8894, 8895, 5394, 5395 and 9394 were not listening afterwards. No process left matched `v01b-rr4`, `assetops_v01brr4` or `9394`, which also means no tool Chrome was left running.
  - `drop` printed "dropped assetops_v01brr4", "dropped assetops_v01brr4empty", "removed …\AssetOps\v01b-rr4". A read-only `pg_database` query for `%rr4%` returned `[]`, and `Test-Path` on the work folder returned False.
  - I made no request to any forbidden port. I did not write to any owner or shared database, and I did not touch `var/`.
- `npx.cmd vitest run` returned "Test Files 57 passed (57); Tests 1385 passed (1385)". Vitest did run in this session.
- `npx.cmd tsc --noEmit` exited 0.
- `tools/check-all.ps1 -Python python` returned "All 6 guards passed."

## Not verified

- I did not run `tools/layout-evidence.mjs`. This round changed no layout, and the packet records it as not run for fix 3 onward.
- I did not run the production build (`npm.cmd run build`) or the backend pytest suite. This round changed no backend code.
