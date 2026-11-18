# V-01b fix round 2: fresh Claude re-review

Reviewer: a fresh, independent Claude Reviewer. I did not build the slice, either fix round, or the previous review.
Tree: `task/V-01b-evidence-lab-visual` at `32226cf`.
Diff reviewed: `e9d2d68..32226cf`. I judged it against Findings A and B in `.agent/V-01b-fix-rereview.md`. The round was directed by the owner in `.agent/owner-V-01b-second-return-2026-10-13.md` ("option 1").

## Verdict: ACCEPT

Both findings are fixed for the states they describe. I observed each fix myself rather than taking it from the packet.

There is one minor, non-blocking carry, D1. While the execution read is still loading, the strip briefly shows the new sentence, and that sentence is false in that moment. The previous code was false in the same moment, so this is not a regression. I recommend folding in the one-line fix (below) when the branch is next touched. It is carried rather than returned because it is transient: it clears as soon as the execution read answers.

## Finding A: `tools/layout-evidence.mjs:5562-5563`, the TDZ crash. Fixed.

**The change.** `OWNER_PORTS` is now a `const` inside `registeredRunGate()`, so it is created on every call. Nothing remains to be in a temporal dead zone.

**What the gate reads.**

- `BASE` (line 48).
- `process.env`.

**What the opt-in path reads**, if the gate allows it:

- `LAB_SITE` (84) and `LAB_START`/`LAB_END` (102-103);
- `submitRunSetup` (655), a const arrow;
- `visit` (557) and `report` (773), which are function declarations;
- `cdp` (1194).

All of these are initialised before both call sites, at lines 1213 and 3060. Neither call site can hit a TDZ through the gate or the code behind it.

**The real script against an unused port.** Nothing was listening on 5399. I set `ASSETOPS_CDP_PORT=9477`. The command was `ASSETOPS_LAYOUT_V01B_ONLY=1 node tools/layout-evidence.mjs http://localhost:5399`, and it printed:

```
=== V-01b registered Kobo Lab run (create + execute) ===
  not run  run creation is opt-in: set ASSETOPS_LAYOUT_CREATE_RUNS=1 and point BASE at a private disposable store; its Draft, drawing and Gateway & Ingestion claims are unverified

AT LEAST ONE CLAIM FAILED
```

The exit code was 1. The script reached `finishRun()` without throwing, and `not run` sets `allPass` false, so it is never a pass.

**The same script without `V01B_ONLY`.** Against 5399, it ran the earlier sections and reported FAILs against the absent server. I stopped it at my 240 s limit, before it reached the end.

On that path, the call at line 3060 is reached only when `configurationStore(KOBO)` returns `POSTGRES`. A dead port returns null. So the main-path call site cannot be reached by a real run without a registered store, and I did not start one.

For that call site I rely on two things:

- the ordering argument above;
- the harness below, which keeps the real ordering.

After stopping the run I checked for leftover processes. No headless Chrome, no process on CDP port 9477, and no `layout-evidence` node process remained.

**The owner-port refusal, by harness, with no traffic.** The harness extracts the gate text verbatim from the file. It builds a module that calls `registeredRunGate()` from a top-level `await` placed above that text, which is the real ordering. It then imports the module for each case.

| BASE port | `ASSETOPS_LAYOUT_CREATE_RUNS` | Result |
| --- | --- | --- |
| 5173, 5183, 5199, 5213, 5291, 5360, 5361, 5362, 5363 | unset | "is a default/owner port (…); run creation refused" |
| same ports | `1` | refused |
| 5399 | unset | "run creation is opt-in: …" |
| 5399 | `1` | `null`, so it would proceed |

There was no ReferenceError in any case.

**A disclosure about a mistaken command.** I issued one command in error: `node tools/layout-evidence.mjs http://localhost:5173`, with V01B_ONLY and CREATE_RUNS set. Its output was discarded, and I cannot tell whether the process got far enough to make its startup `fetch` attempts. If it did, those were two read-only GETs: `/api/sites` and `/api/sites/MG-001`.

- Nothing was listening on 5173. `Get-NetTCPConnection -LocalPort 5173` returned no rows, so no server received any request.
- If execution had got that far, the gate would have refused port 5173 before any create.
- No Chrome or node process from it remained.

## Finding B: `frontend/src/shell/RunIngestionOverview.tsx:39,248`, the false "commit status could not be read" sentence. Fixed for the unavailable-execution state.

**The new sentence.** When there is a delivery with receipts but no evidence link, the new sentence is: "Reports were received centrally, but the run's execution could not be read, so no Site Evidence link is offered."

It is true and plain-language when the execution read has failed. In that state the badge reads "Execution unavailable" and the Commit read succeeded.

**The test is real.**

- I restored `RunIngestionOverview.tsx` from `e9d2d68` and ran `v01bLabIngestion.test.tsx`.
- The result was 1 failed, 11 passed. The failure was `expected 'The commit status could not be read, …' to match /execution could not be read/`.
- I restored the file with `git checkout`. On current code the full file passes.

## The other branches of `receivedStatement` (lines 232-254)

The function is called only when `evidence` is false, which means no receipt or no projection.

| # | Condition | Sentence | True? |
| --- | --- | --- | --- |
| 1 | Delivery null, commit loaded, legacy object commit | "Not a registered Site: no Site Evidence link…" | Yes |
| 2 | Commit null | "Loading the commit status." | Yes |
| 3 | Commit not loaded | `COMMIT_UNREADABLE` | Yes. Delivery is derived from the Commit read, so it is genuinely unknown. |
| 4a | Delivery present, `withReceipt === 0` | `NOTHING_RECEIVED` | Yes |
| 4b | Delivery present, receipts, execution unavailable | `RECEIVED_EXECUTION_UNREADABLE` | Yes |
| 4c | Delivery present, receipts, execution still loading | `RECEIVED_EXECUTION_UNREADABLE` | **No, transiently.** See D1. |
| 5 | Commit loaded, no delivery, `NOT_COMMITTED` | `NOTHING_RECEIVED` | Yes |
| 6 | Commit loaded, no delivery, otherwise | `DELIVERY_UNREADABLE` | Yes, and it matches ReleaseFacts "Not readable" |

## Carries

### D1 (minor, non-blocking, not a regression): `RunIngestionOverview.tsx:248`

**The defect.** `projection` is null both while the execution read is in flight (`execution === null`) and after it has failed. `RunFrame` loads the execution and the Commit independently, so the Commit read with receipts can answer first.

**Evidence.** I appended a temporary probe test to `v01bLabIngestion.test.tsx`, then removed it with `git checkout`. In the probe, `getExecution` never resolves and the Commit is `released(RECEIPT)`. The strip rendered:

> Released to gateway Execution loading 1 of 2 batches have a central receipt … Reports were received centrally, but the run's execution could not be read, so no Site Evidence link is offered.

The badge says "loading" while the sentence says "could not be read". The code before this round said "The commit status could not be read" in the same moment, which was also false.

**The fix.** Pass `execution` into `receivedStatement`. When it is null, return a loading sentence such as "Reports were received centrally; loading the run's execution." Add one test where the execution read never answers.

**Where to carry it.** Append it to `.ai/MILESTONE_REVIEW_BACKLOG.md` with the V-01b carries.

### The packet's claims

The fix-round-2 claims in `.agent/V-01b-review-packet.md` match what I observed:

- the `not run` output;
- the harness result;
- the test going from 1 failed to 12 passed;
- the check counts.

It correctly records two runs as not run: the full layout evidence, and the create-and-execute path with the opt-in. The corrected C2 backlog entry is accurate.

### Residual risk, not new

- The gate's port list is fixed. A private store on any other port is accepted once the opt-in is set, which is by design.
- The create-and-execute path itself has still never been observed through the gate. That needs a private disposable store with the opt-in, and it remains an open evidence gap for the layout claims behind it.

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd vitest run` (frontend) | Test Files 57 passed (57), Tests 1384 passed (1384). The sandbox did not block it on this run. |
| `npx.cmd tsc --noEmit` | Exit 0. |
| `tools/check-all.ps1 -Python python` | All 6 guards passed: architecture seams, navigation truthfulness, agent workflow, dependency registry, delivery checker fixtures, and screen ledger (110 screens, 88 models, 258 panels). |
| `layout-evidence.mjs`, V01B_ONLY, BASE 5399 | Gate printed `not run`, then `AT LEAST ONE CLAIM FAILED`, exit 1, no throw. |
| `layout-evidence.mjs`, full path, BASE 5399 | Stopped at 240 s. It cannot reach line 3060 without a registered store. |
| Backend pytest | Not run. The diff touches no backend files. |
| `npm.cmd run build` | Not run. The change is one function line and one test, and `tsc` is clean. |

I did not start any server. No request went to any listed owner or backend port beyond the disclosed 5173 attempt, where nothing was listening. Nothing under `var/` was touched.
