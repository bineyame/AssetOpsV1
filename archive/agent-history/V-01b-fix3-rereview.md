# V-01b fix round 3: fresh re-review

Reviewer: fresh Claude reviewer, independent of the fix-3 implementer.
Branch: `task/V-01b-evidence-lab-visual`, HEAD `ef1ddc5`. Scope: `ee4474b..ef1ddc5`, judged against the Architect's Q1 ruling (`.agent/architect-V-01b-answers.md`) and carry D1 (`.agent/V-01b-fix2-rereview.md`).

## Verdict: RETURN (tooling only)

The product change is correct, and I accept it as it stands. Q1 is implemented the way the Architect ruled, D1 is fixed, and the tests fail before the fix and pass after it. The return is for one stale evidence tool. `tools/v01b-lab-evidence-evidence.mjs` still waits for, and asserts, the Q1 label that this round removed. Run against fix 3, it would now fail two claims, so the packet's "101/101" for acceptance criterion 2 no longer describes the code. The fix is a few lines in the tool. A re-review only needs that tool diff and, if possible, one private run of it.

## Findings

### F1 (medium, acceptance-evidence gap): `tools/v01b-lab-evidence-evidence.mjs:202` and `:385-386`
- **What is wrong.** `STAGE_LABEL = "This is the gateway's local Stage statement. Central receipt is shown under Release and ingestion."` Line 385 calls `waitFor` until the opened Stage disclosure's `innerText` includes that text, and line 386 claims "the Stage disclosure, opened, carries the Q1 label". Fix 3 deleted this text from `GatewayLedgerView.tsx`. The tool now times out after 20 s and records a FAIL at both 1440 and 390, which is 2 failed claims.
- **Why it matters.** This tool is the packet's evidence for acceptance criterion 2 (`.agent/V-01b-review-packet.md:27`, "101/101"; `:68`, "Evidence tool (c1, unchanged product since): 101/101"). Fix 3 changed the product, so that count is stale. The fix-3 notes at packet `:111` say only `layout-evidence.mjs` was updated to match. They do not mention this tool.
- **Fix.** Replace the constant and the claim with the new copy. Wait for `[data-gateway-delivery-neutral]` to contain "does not establish upload or central receipt state". Optionally also assert that `[data-gateway-upload]` and `[data-gateway-receipts]` are absent and that "Upload pending" is not in the disclosure text. Then rerun the tool against a private store, or record it as `not run` with its blocking precondition, and correct packet lines 27 and 68.

### F2 (nit, comment only): `frontend/src/shell/RunIngestionOverview.tsx:20-21`
The module docstring still says "(V-01b Q1: the Stage's own upload line is the gateway's local statement)". That line no longer exists. Reword it to say the Stage's constant upload fields are not shown. This is not blocking.

## Verification

**Q1.**
- I searched every non-test source under `frontend/src` for `upload_state`, `upload_statement`, `receipts`, `data-gateway-upload`, `data-gateway-receipts` and "no receipt exists". The only renderer of the Stage ledger is `GatewayLedgerView`, mounted at `RunFrame.tsx:1210` for `stage.status === "gateway"`. The fields are now referenced only in the type and validator (`runSetupClient.ts:869-870` and `:1998-2001`), not rendered.
- The neutral row (`GatewayLedgerView.tsx:66-73`) reads: "This Stage read does not establish upload or central receipt state. See Release and ingestion for what was released and received." It is true and in plain language. "Release and ingestion" is always mounted (`RunIngestionOverview.tsx:195`), so the pointer always resolves.
- The snapshot, epoch, queue, sealed batches, envelopes and holds are unchanged.
- The non-gateway Stage branch (`RunFrame.tsx:1219` on, `stage.stage.statement` and the Registered/Legacy basis line) is untouched by the diff. Legacy gateway runs get the same neutral copy, which is still true for them.
- Other upload and receipt copy (`RegisteredDeliveryView.tsx`, `GatewayPublicationPanels.tsx`) comes from the authoritative delivery and diagnostics reads, not the Stage constant.
- The backend validator still requires the constant `PENDING` with empty receipts. That is the later backend/gateway-contract slice the Architect named, and it is correctly left open in the backlog.

**D1.** I enumerated every branch of `receivedStatement`. It is reached only when there is no Site Evidence link, meaning no receipts or no loaded projection.
- Legacy object commit: "Not a registered Site…". True.
- Commit null: loading commit. True.
- Commit not loaded: commit unreadable. True.
- Delivery present with 0 receipts: nothing received. True.
- Delivery present with receipts and execution null: the new `LOADING_EXECUTION` (`:255`). True. This was D1.
- Delivery present with receipts and execution not_found or unavailable: "execution could not be read". True enough. It was unchanged and accepted before.
- No delivery and `NOT_COMMITTED`: nothing received. True.
- No delivery and another string state: delivery unreadable. True.

No branch now states something false.

**Fail before, pass after.** I restored `GatewayLedgerView.tsx` and `RunIngestionOverview.tsx` from `ee4474b` and ran the two test files. 3 failed and 19 passed: gatewayLedgerStage 1, plus the v01bLabIngestion Q1 test and the D1 loading test. I then ran `git checkout HEAD --` on both files, and the tree is clean apart from the coordinator's handoff file.

**Tooling.**
- `tools/layout-evidence.mjs:1287-1312` is updated correctly: the neutral text is present and the constant fields are absent.
- `tools/v01b-lab-evidence-evidence.mjs` is stale (F1).

## Checks I ran
- `npx.cmd vitest run`: 57 files, 1385 tests, all passed. Vitest did run in this session.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-all.ps1 -Python python`: all 6 guards passed (architecture, navigation truthfulness, agent workflow, dependency registry, delivery checker fixtures, screen ledger).

## Not verified
- **`tools/v01b-lab-evidence-evidence.mjs` was not run.** `prepare` and `drop` in `tools/v01b_lab_evidence_walkthrough.py` (lines ~193 and ~291) connect to the maintenance database `assetops` to issue `CREATE/DROP DATABASE`. My dispatch forbids touching that database, so I did not prepare a private store, and no servers or Chrome were started. F1 rests on reading the code. It is unambiguous: the awaited string no longer exists anywhere in `frontend/src`.
- **`tools/layout-evidence.mjs` was not run.** It needs Chrome, the backend and a dev server. The packet records it as not run.
- **The production build (`npm.cmd run build`) was not run.**

## Carries
- Q1 backend: retire the obsolete Stage `upload_state`, `upload_statement` and `receipts` fields, or give them local-only semantics (already in the backlog).
- F2: comment wording, to fix at the next touch.
- Q8: drawing claims remain unmeasured, as the Architect ruled. This round does not change that.
