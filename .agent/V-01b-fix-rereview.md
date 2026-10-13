# V-01b fix round: fresh Claude re-review

Reviewer: a fresh, independent Claude Reviewer. I did not build the slice or the fix.
Tree: `task/V-01b-evidence-lab-visual` at `0a74e9b`.
Diff reviewed: `6ae57df..0a74e9b`, against `.agent/V-01b-review.md` (verdict RETURN, Finding 1, carry C2).

## Verdict: RETURN

The fix for Finding 1 works and its tests are real. The C2 gate is correct in isolation, but in the real file it throws before it can refuse anything. That makes `layout-evidence.mjs` crash on registered stores: the gate never prints `not run` and never reaches the sections after it. There is also one residual false sentence in the strip.

Both fixes are small. A third fix round can be accepted on a targeted check of these two points; it does not need another full review.

## Findings

### A. `tools/layout-evidence.mjs:5560` (blocking): the C2 gate throws a ReferenceError instead of refusing

**Defect.** `const OWNER_PORTS` is declared at line 5560. `registeredRunGate()` reads it, and `registeredKoboLab()` calls `registeredRunGate()`. But `registeredKoboLab()` is called from top-level `await` statements at lines 1213 (`ASSETOPS_LAYOUT_V01B_ONLY`) and 3060 (the main path whenever KOBO-001 is POSTGRES). Module evaluation has not reached line 5560 at either point, so `OWNER_PORTS` is still in its temporal dead zone. The file already warns about exactly this at line 5462: "A function declaration, not a const: registeredKoboLab runs above where this text sits, and a const here would not be initialised yet".

**Evidence.** I extracted lines 5560-5570 verbatim into a scratch harness, placed the call above the const as the real file does, and contacted no server.

- Default BASE: `THROWS: ReferenceError Cannot access 'OWNER_PORTS' before initialization`.
- BASE `http://localhost:5399`: the same ReferenceError.

**Gate logic in isolation.** With the declaration hoisted above the call, the gate behaves as intended:

| BASE | Flag | Result |
| --- | --- | --- |
| 5173 (also the default), 5183, 5199, 5213, 5291, 5360-5363 | unset | refused |
| same ports | `ASSETOPS_LAYOUT_CREATE_RUNS=1` | refused |
| 5399 | unset | "run creation is opt-in…" |
| 5399 | `ASSETOPS_LAYOUT_CREATE_RUNS=1` | null, so it would run |

**Why it matters.**

- An uncaught rejection in a top-level await crashes the script. Every invocation on a registered store (the main path at line 3053) now dies at this point:
  - with no `not run` line;
  - with no report of the sections after it (the legacy Kobo precondition report and everything from line 3060 onward);
  - with no `finishRun`, so Chrome is not cleaned up.
- The owner's store is still not mutated, because the crash happens before any create. But the fix does not do what the packet says. The packet says it "prints `not run` with the reason and returns false (never PASS)".
- The recorded command in the packet, which now carries the opt-in, would crash too.
- The packet does say the gate was only checked with `node --check`. That check cannot catch an evaluation-order error.

**Fix.** Make the port set function-scoped or hoisted. For example, declare it inside `registeredRunGate`, or use `function ownerPorts() { return new Set([...]); }`. Then run the script once against an unused port with no server, or use an equivalent harness that keeps the real ordering, so a `not run` line is actually observed.

### B. `frontend/src/shell/RunIngestionOverview.tsx:247` (minor, but a false statement on screen): receipts read, yet the strip says the commit status could not be read

**Defect.** When `delivery !== null` and `delivery.withReceipt > 0`, the function returns `COMMIT_UNREADABLE`. That branch is reached whenever there are receipts but the execution read is not loaded: `evidence` requires `projection !== null`, so the Evidence link is withheld and `receivedStatement` runs. In that state the Commit read succeeded, so the sentence is false.

**Evidence.** I added a temporary probe test (deleted afterwards): execution `unavailable`, Stage `GATEWAY`, Commit `released(RECEIPT)`. The status strip rendered:

> Released to gateway · Execution unavailable · 1 of 2 batches have a central receipt · … · The commit status could not be read, so what was received centrally is not known.

The strip contradicts itself on one line, and it contradicts `ReleaseFacts` below it.

**Why it matters.** It is the same class of defect as Finding 1: an honest-missing-state sentence that is untrue. It is less severe, because it understates rather than overstates, and the old code said "Nothing … received", which was worse.

**Fix.** Return a true sentence for this branch. For example: "Received centrally, but the execution could not be read, so the Site Evidence link for its interval is not available." Add one test with an unavailable execution and a released commit with a receipt.

## Finding 1 verification

- **Where "Nothing from this run has been received centrally." appears.** It is now returned only when `delivery.withReceipt === 0`, or when there is no delivery and the commit is a loaded `NOT_COMMITTED` (lines 246-251).
- **Unread commit.** `commit.status !== "loaded"` returns "The commit status could not be read…". This matches `ReleaseFacts` line 518.
- **Unreadable delivery.** A registered release with no delivery returns "The gateway delivery could not be read…". This matches "Not readable (…)" at line 534.
- **Wording.** Both sentences are plain language.
- **Legacy path.** A loaded legacy commit (an object) still returns the legacy-Site sentence first. Unchanged.
- **The tests are real.** I temporarily restored `RunIngestionOverview.tsx` from `6ae57df` and ran `v01bLabIngestion.test.tsx`.
  - The old code gave 2 failed and 9 passed. Both new tests failed with `expected 'Nothing from this run has been receiv…' to match /commit status could not be read/` and `/gateway delivery could not be read/`.
  - I reverted with `git checkout`, and the current code gives 11 passed.

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd vitest run` (frontend) | Test Files 57 passed (57); Tests 1383 passed (1383). The sandbox did not block it on this run. |
| `npx.cmd tsc --noEmit -p .` | Exit 0. |
| `tools/check-all.ps1` (`.venv` present, default Python) | All 6 guards passed: architecture seams, navigation truthfulness, agent workflow, dependency registry, delivery checker fixtures, and screen ledger (110 screens, 88 models, 258 panels). |
| Backend pytest | Not run. The diff touches no backend, contracts, gateway or host files. |
| `npm.cmd run build` | Not re-run. The fix changes one function body and one test; `tsc` is clean. |
| `tools/layout-evidence.mjs` | Not run. No servers were started, and no request was sent to any port. The gate was exercised only through the scratch harness described in Finding A. |

The tree is clean apart from the pre-existing `.agent/coordinator-handoff.md` modification, which I did not touch.

## Carries

- C1 and C3-C6 are recorded correctly in `.ai/MILESTONE_REVIEW_BACKLOG.md`.
- The C2 entry there says "FIXED". It should not stay that way until Finding A is fixed and a `not run` line has been observed.
- The packet's 398 PASS / 5 FAIL layout run predates the gate, and it remains the Implementer's unverified number.

## Not verified

- Layout evidence and screenshots: no browser or servers were used.
- Owner visual acceptance is still pending.
