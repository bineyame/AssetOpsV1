# S2-02 fix round 1 - focused re-review

Reviewer: a fresh Claude reviewer, independent of the S2-02 author and of the fix-round implementer.
Target: `task/S2-02-ingestion-site-evidence`, fix commits `cf3dd82..0d8ae84` (`15f5c62`, `888a836`, `c128129`, `1eb52ea`, `8aa35a6`, `293ccc1`, `0d8ae84`).
Judged against: `.agent/S2-02-review.md` F1, and `.agent/architect-batch-answers-4.md` "Before the owner walkthrough" items 1-4.
Date: 2026-10-09.

## Verdict

**Accept with findings fixed on the branch.**

All five required items are met in code and tests:
- F1;
- Q28 (uncertain COMMIT);
- Q26 (store-root binding);
- Q32 (a live rejected sibling);
- the 246/293 count explanation.

No code finding blocks. One walkthrough-document finding (R1) should be fixed before the owner uses the document, because the owner cannot reproduce a state the document tells them to check. The fix is a document edit only. Owner acceptance is separate from this review, and Q37-Q40 are with the Architect.

## Required items

| Item | Result | Basis |
| --- | --- | --- |
| F1 forwarded scheme | **Met** | See note 1 below. |
| Q28 uncertain COMMIT | **Met** | See note 2 below. |
| Q26 store root | **Met** | See note 3 below. |
| Q32 rejected sibling | **Met** | See note 4 below. |
| 246/293 | **Met (explained, expected)** | The recorded run shows the count stopping at 245/292 after run-to-end. The advance to 15:10Z adds exactly one batch with one envelope: `battery-pcs-controller/state-of-charge`, source time 15:00:00Z, published 15:10:00Z, publication profile v2. It is identified by a diff of the gateway's sealed batches, not inferred. |

1. **F1.**
   - `gateway_api.py:133-137` returns 426 for any gateway-network request that carries `X-Forwarded-Proto` or `Forwarded`, whatever the ASGI scheme.
   - `serve_tls.py:35` passes `proxy_headers=False`.
   - The new test wraps the app in uvicorn's real `ProxyHeadersMiddleware` (trusted `*`), so the scheme really is rewritten to https. The test is not vacuous.
2. **Q28.**
   - `ProvisioningRefused` is the only proven rollback, and it still removes the file. Any other exception reconciles through `issue_outcome`, which discards the pool and does a fresh read.
   - Full match gives ISSUED. No selector row gives NOT_ISSUED: the file is removed and nothing is claimed about the old credential. Anything else, or an unreadable database, gives `ISSUE_OUTCOME_UNKNOWN`: exit 3, the file is kept, the path is printed, and nothing is reissued.
   - Tests cover committed-but-response-lost, rolled back, and unreadable (committed and not committed). The lost-response test runs the real `issue_outcome` against Postgres.
3. **Q26.**
   - Report schema v3 carries `store_root`, which is the sha256 of the normcase/resolved evidence and commit roots. `permits_cutover` closes on a missing or different root, and v2 reports stay closed.
   - The gate reads the current root on every `scope()`, and the architecture guard was extended to require it.
   - A Postgres test with the same database, tenant, Site and zero inventory from another root gives 409 on every route, with no path or root in the response.
   - I independently recomputed the developer workspace root (read-only). It equals the regenerated `.agent/S2-02-legacy-comparison-KOBO-001.json` value `sha256:2196b88e...5b17`, so a restarted 8000 server on this branch should open. The report contains no path or username.
4. **Q32.**
   - Step 8b posts a labelled FAULT FIXTURE Batch V2 over the normal authenticated HTTPS route.
   - The recorded output shows `200 {accepted 1, rejected 1}`, with ordinal 1 rejected as `BINDING_NOT_REGISTERED` on `source.signal_id`. On a fresh read afterwards, the rejection route lists it and Site Evidence lists the batch.
   - The script and the walkthrough both say the sealing gateway never emits such input. Crash/202 and outside-period rejection stay labelled as Postgres test evidence, as ruled.

## Findings

### R1 - Medium - BLOCK for the owner walkthrough (document fix only). The interactive STALE step cannot be reproduced as written

- **Where:** `.agent/S2-02-owner-walkthrough.md:23` (step 2), checked against `tools/s2_demo_walkthrough.py:667-680` (`serve`) and `gateway/assetops_gateway/__main__.py:110-113`, `ipc.py:227-258`, `uploader.py:410-418`.
- **What is wrong:** the step says "Stop `serve`, wait over two minutes, start it again, and reload before the gateway's next report: you will see ... STALE". That cannot happen, for three reasons:
  - Stopping `serve` also stops the Lab/product API, so nothing can be read during the silence.
  - On restart, `serve` starts the TLS server, then the gateway, and only then the Lab API.
  - The gateway emits a diagnostic for the new cadence slot as soon as it starts, and its uploader thread delivers immediately when it starts. In `serve` it then delivers again every 15 s.

  So by the time the page can be reloaded, the server has already received a fresh report, and the owner will see CURRENT.
- **Why it matters:** the owner is told to verify a state that will not appear. That reads as a product defect, when it is really an inaccurate instruction. The scripted run did record STALE correctly, because it stops only the gateway and keeps the API up.
- **Fix:** rewrite step 2 to rely on the recorded UNKNOWN -> CURRENT -> STALE -> CURRENT sequence in `.agent/S2-02-demo-run-output.txt`, or give a procedure that stops only the gateway while the API stays up. Whichever is chosen, it should be one the Implementer has actually run.

### R2 - Low - fix with R1. Two smaller walkthrough inaccuracies

- **`npm` in PowerShell.** `.agent/S2-02-owner-walkthrough.md:18` and `tools/s2_demo_walkthrough.py:683` give `npm run dev`. On this machine PowerShell refuses `npm.ps1` (`UnauthorizedAccess`). Use `npm.cmd run dev -- --port 5310 --strictPort`.
- **The 318 count is not explained.**
  - The page and the recorded step 11 show `accepted: 318`. The walkthrough explains only 246/293 and never says what makes up 318.
  - 318 is presumably 293 (main run) + 24 (gap run's 20 batches) + 1 (the fault fixture's valid sibling). The gap run's envelope count is not printed, so I could not confirm the decomposition.
  - The Architect asked that no count change be presented unexplained. State the composition, or print it from the script.

### R3 - Low - CARRY (Architect, with Q37/Q38). A definitive pre-transaction failure is reported as `ISSUE_OUTCOME_UNKNOWN`

- **Where:** `backend/assetops_backend/evidence/provision_gateway.py:103` (`except Exception`).
- **What happens:** a failure that provably precedes any transaction is treated as ambiguous. Examples are `LedgerUnavailable("DATABASE_URL is not set...")`, or a refused connect. The fresh read then also fails, so the operator gets exit 3, a kept unissued file, and a "halt rotation" instruction.
- **Why it is only a carry:** this is fail-closed and loses no secret. The cost is an alarming message and an operator check. Narrowing it would need a reliable "never reached the database" signal, which is an Architect call alongside Q38.

## Residual risk not already named in the packet

- **The fault fixture adds a fabricated accepted reading to the isolated demo ledger.** The valid sibling is a copy of a real reading, shifted +30 s, under `fault-fixture-epoch`. It is accepted, counted and queues recompute work in `assetops_s2demo`. The walkthrough labels it, and the database is isolated and recreated by `run`. It must never be reused as S3 input without excluding that epoch.
- **Test string literals.** `test_s2_legacy_comparison.py` and `test_s2_site_evidence_postgres.py` build `ROOT` from non-raw literals such as `"c:\ws-a\var\evidence"`, where `\v` is a vertical-tab escape. The assertions are still meaningful, because only digest equality and inequality is tested. This is cosmetic only.

## Checks I ran (what I saw)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | "Architecture check passed." |
| `tools/check-agent-workflow.ps1` | "Agent workflow check passed." |
| Focused fix-round tests against `assetops_test` (55432): `test_s2_gateway_access_postgres`, `test_s2_legacy_comparison`, `test_s2_rejection_placement`, `test_s2_site_evidence_postgres` | **56 passed**, 0 failed (48 s) |
| Developer store-root recompute (read-only, in-process) | Matches the v3 report's `store_root` |
| Secret scan of `.agent/S2-02-*.txt/.md` for `aog1.<32 hex>.<secret>` | 0 matches |
| Code review of `cf3dd82..0d8ae84` | Read in full: backend, tests, tool, guard script, packet, walkthrough and questions-7 |

## Not verified

- **Full suites not re-run:** backend 1760, gateway 164 and host 662. These are the Implementer's numbers, and the frontend was untouched in this round.
- **Isolated walkthrough rerun:** not reproduced. I judged it from the recorded output and the script source.
- **R1:** inferred from the code paths, not reproduced in a live `serve` session. I did not start any servers.
- **Non-vacuity mutations:** the packet's claims were not re-run. The F1 and Q26 tests are non-vacuous by construction, as read.

## Cleanup

No owner servers (8000, 5173/5183/5199/5213/5291) and no `var/` writes were touched; `var/` was only read. No processes were started besides pytest. No repository files were changed except this review.
