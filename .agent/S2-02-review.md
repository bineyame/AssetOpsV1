# S2-02 review - Authenticated ingestion and Site Evidence

Reviewer: a fresh Claude reviewer (independent of the S2-02 author). This is the first independent review of S2-02 under the 2026-10-09 owner routing; the single Codex review of S2-01c + S2-02 follows separately.
Target: `task/S2-02-ingestion-site-evidence` at `3ea80a9`, diff `6e42818..3ea80a9`.
Date: 2026-10-09.

## Verdict

**Accept with findings fixed on the branch.** One blocking finding (F1) needs a small fix and a regression test before merge. Everything else is a carry or residual risk. The slice is substantively sound:
- authentication happens before any processing, and the principal comes only from the credential;
- per-ordinal decisions are atomic and resumable;
- the credential file ordering and Windows DACL corrections are correct;
- the cutover gate is fingerprinted and fails closed;
- Lab Commit claims full release only from the server view;
- the Evidence copy is plain-language and draws no health, dispatch or capability conclusion.

The packet is honest about what is test-only and what was not done.

Owner acceptance is separate from this technical review. Questions 4, 5 and 6 are with the Architect and are not decided here.

## Findings

### F1 - BLOCK (fix on branch). Medium. `X-Forwarded-Proto` bypasses the TLS boundary under default uvicorn serving

- **Where:**
  - `backend/assetops_backend/gateway_api.py:130` tests `request.url.scheme != "https"`.
  - `backend/assetops_backend/serve_tls.py:34` calls `uvicorn.run(...)` with the default `proxy_headers=True`.
- **What is wrong:** uvicorn trusts `X-Forwarded-Proto` from `127.0.0.1` by default (`forwarded_allow_ips`), and rewrites `scope["scheme"]` before the app sees it. So a plaintext credentialed request from loopback that carries `X-Forwarded-Proto: https` is treated as HTTPS.
- **Reproduced:** `xfp_probe.py` in the reviewer scratchpad, uvicorn 0.52.4. It runs the real `install_gateway_tls_boundary` on a plain-HTTP uvicorn with default config.
  - Without the header: `426 GATEWAY_TLS_REQUIRED`.
  - With `X-Forwarded-Proto: https`: `200 {"reached":true,"scheme":"https"}`.
- **Which servers are exposed:** any plain-HTTP uvicorn launch of `assetops_backend.main:app`, such as the development server. `serve_tls` has the same default; there it can only fail closed, but it should be explicit.
- **Why it matters:** this directly contradicts the Architect's Q10 ruling (`.agent/architect-S2-batch-answers-2.md:29`: "do not let an arbitrary `X-Forwarded-Proto` bypass it") and the task text (`tasks/S2-02-ingestion-site-evidence.md:26`, "`X-Forwarded-Proto` is not trusted"). The packet claims "426 plaintext" without qualification.
- **What limits the impact:** the AssetOps gateway itself refuses non-`https` URLs (`gateway/assetops_gateway/uploader.py:112`), so this is a server-side boundary gap, not a demonstrated secret leak.
- **Fix:**
  1. Pass `proxy_headers=False` in `serve_tls.py`.
  2. Make the middleware fail closed regardless of how the app is served, for example by refusing any gateway-route request that carries `X-Forwarded-Proto` or `Forwarded`. App middleware cannot see the pre-rewrite scheme.
  3. Add a regression test that sends a plaintext request with the header and expects 426.

### F2 - CARRY to owner checkpoint / Architect Q32. Medium. The owner-review list is not fully demonstrated live

- **Where:** `tasks/S2-02-ingestion-site-evidence.md:40`, set against packet "Known deviations" and Q32.
- **What is wrong:** the task asks for these on persisted APIs and screens at owner review:
  - a rejected sibling beside accepted records;
  - a partial server crash/resume.

  The demo also never produces a live closing-boundary rejection (Q36). All of these are Postgres test evidence only.
- **Tests confirmed:** I ran them and they pass (79/79 below):
  - `test_a_rejected_sibling_does_not_erase_valid_decisions`;
  - `test_a_crash_after_a_committed_chunk_resumes_from_the_watermark`;
  - `test_a_bounded_request_returns_202_in_progress_until_terminal`;
  - `test_a_closing_boundary_reading_is_outside_its_half_open_period`.
- **Why it matters:** the owner should know that these screens never show a live rejection or a partial batch. The packet labels this honestly, so it is not a packet defect. Whether test evidence satisfies the owner list is the Architect's Q32 decision plus the owner's call.
- **Fix:** none required of the Implementer until Q32 is ruled.

### F3 - CARRY. Low. "Delayed/pending" is not a window-level Evidence state

- **Where:**
  - `backend/assetops_backend/evidence/ledger_reads.py:276-285`: states are `NO_DATA`, `REJECTED_ONLY` or `ACCEPTED`, plus `PARTIAL_BATCH`, `CONFLICTING`, `STALE_PROJECTION` and `OUTDATED_CONFIGURATION`.
  - `frontend/src/sites/LedgerSiteEvidence.tsx:224-225`.
- **What is wrong:** AC7 asks the page to distinguish "no data" from "delayed/pending". Readings still queued at the gateway are visible only in two places:
  - the Analysis gateway detail ("Readings waiting at the gateway");
  - the Overview contact sentence (CURRENT/STALE/UNKNOWN).

  For a period whose readings are still waiting at the gateway, the Overview headline says "No readings were received for this period". That is literally true, but it does not tell the owner the readings may still arrive.
- **Note:** `PARTIAL_BATCH` covers server-side pending.
- **Why only a carry:** the server cannot attribute a gateway queue to a source-time window, so a window-level state would need a design decision.
- **Fix (suggested):** when `NO_DATA` coincides with a gateway `queue_count > 0` or `STALE`/`UNKNOWN` contact, qualify the headline ("...; the gateway reports N readings still waiting" / "the gateway has not been heard from recently").

## Residual risk not named in the packet

- **Old diagnostic fields can read as current.** `adapters/postgres_gateway_access.py:186` picks the "latest" diagnostic by `received_at DESC`. A backlog diagnostic uploaded late after an outage becomes "latest", so its older queue count, pressure and offset show beside a CURRENT status. The gateway-stated time is shown alongside, so a reader can notice, but the queue/pressure facts may be older than they look.
- **The Site Evidence overview read does not scale with Site history.** `site_window` reads every rejection for the Site, and every referenced batch's full `batch_text`, on each read, then filters the window in Python (`postgres_evidence_ledger.py:541`, `545-563`). This is fine at demo scale; S3 or a long-running Site will need a source-time column or index on rejections.
- **Oversized uploads without a declared length are read whole.** An oversize body without `Content-Length` (chunked) is read fully into memory before the 413 check (`evidence_api.py` `post_batch_v2`; `gateway_api.py` diagnostics). This applies to authenticated callers only.
- **Released-state blocker may be lost on host restart.** `PUBLICATION_REFUSED` is derived from in-memory `session.staging_notes` (`host/lab_execution.py` `_delivery_view`). After a host restart, only the schedule-based gap blocker remains. That is still fail-closed for gaps, but a non-gap refusal note would no longer block `fully_released`. I did not verify whether any non-gap refusal can occur.

## Checks I ran (what I saw)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` (`-ExecutionPolicy Bypass`) | "Architecture check passed." |
| `tools/check-agent-workflow.ps1` (`-ExecutionPolicy Bypass`) | "Agent workflow check passed." |
| Focused backend suite against `assetops_test` on 55432 | **79 passed**, 0 failed, in 210 s. Files: `test_s2_evidence_ledger_postgres`, `test_s2_gateway_access_postgres`, `test_s2_site_evidence_postgres`, `test_s2_legacy_comparison`, `test_s2_receipt_v2`, `test_s2_rejection_placement`, `test_s2_registered_commit_api`. |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd test` | **53 files / 1270 tests passed** (115 s). The sandbox esbuild failure in the standing brief did not occur this time. |
| `npm.cmd run build` | exit 0 (chunk-size warning only); `frontend/dist` is gitignored |
| TLS boundary probe (scratch script, uvicorn 0.52.4) | 426 without the header; 200 with `X-Forwarded-Proto: https` (F1) |
| Secret scan of `.agent/S2-02-*` evidence files for `aog1.<32 hex>.<43>` | 0 matches |

## Not verified

- **Suites not re-run:** the full backend (1750), gateway (164), simulator (265) and host (662). I re-ran only the S2-02 backend Postgres files listed above.
- **Not reproduced:** the recorded end-to-end TLS demo (`tools/s2_demo_walkthrough.py`) and `tools/layout-evidence.mjs`. Both need Chrome, servers and isolated stores. The packet records layout as ALL CLAIMS HOLD, with a documented non-vacuity check. It honestly records the C3/N2 full seeded layout run as **not done**, and that carry stays open.
- **Windows DACL code:** I read the code paths (`gateway_credential_file.py`, the reader's re-check) but did not run a hostile-ACL probe beyond the Implementer's tests.
- **Q35 (two Lab runs' readings side by side):** I have no view on this beyond the packet; it is the Architect's ruling.

## Owner servers and cleanup

I touched no owner servers (8000, 5173 and others) and no `var/`. The probe used port 8797 in-process and stopped. No files were changed in the repository except this review.
