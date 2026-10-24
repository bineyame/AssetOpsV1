# W5-02c K4 evidence: cold-action at 1440 and 390

**Current run (supersedes the figures further down).** Code tree `de57ee51`, with main E4/E6 `48b0bf84` merged and
build rulings 14-22 applied.
- **Producer:** `prepare` took 121 s and blocked no mode. `serve` started 7 healthy APIs and `attest` returned ATTEST OK.
  Served detail reads: `action-current` HTTP 200 CURRENT with work COMPLETED; `action-not-linked` HISTORICAL with no
  work; `action-worstcase` CURRENT with no work.
- **Action captures:** 292 PASS, 0 FAIL. Heights are unchanged from the table below.
- **`cases-recheck/`:** 934 PASS, 0 FAIL. The four former ruling-20 failures now pass at 1440 and 390:
  - `incidents-worstcase-every-disclosure`: 20 opened UUIDs (10 fact values and 10 direct-code bodies).
  - `maintenance-worstcase-every-disclosure`: 25 opened UUIDs, all fact values.
  - Every one renders on one line inside its own scroller.
- **Cleanup:** the 7 Vite processes, the APIs and the databases were stopped and dropped by PID or with the tool's `drop`.

## Earlier run (pre-rebase, tree `5db28f19`)

Producer: `tools/w502_cold_work_walkthrough.py --work var/w502b_k4 --tag k4`. Code tree `5db28f19`. `prepare` took 187 s
and blocked no mode. `serve` started 7 APIs on 8971-8977 and `attest` returned ATTEST OK. The served detail reads were:

| Read | Port | Result |
|---|---|---|
| `action-current` | 8971 | HTTP 200, CURRENT, work COMPLETED |
| `action-not-linked` (`known_at` = K1) | 8971 | HTTP 200, HISTORICAL, work all null, intent null |
| `action-worstcase` | 8972 | HTTP 200, CURRENT, work null, intent null |

The negative attest proof used a manifest with positive `detail_reads` and worstcase `reads` removed. It returned
`ATTEST FAILED: positive: detail reads [] != ['action-current', 'action-not-linked']; worstcase: no reads (None)`.
The manifest was then restored.

Captures: `ASSETOPS_CDP_PORT=9481 W502B_EVIDENCE=action node tools/w502-cold-work-evidence.mjs <manifest> .agent/W5-02c-K4-evidence`,
on Vite 5471-5477. The run gave **292 PASS, 0 FAIL** (`w502c-k4-measurements.json`, 24 PNGs).

The first run had 20 FAIL. Each failure came from the capture tool, not from the product:
- The first navigation hit a cold Vite compile, so the tool now warms each server first.
- The containment probe counted boxes inside a closed `<details>`, which Chrome keeps behind `::details-content`.
  Closed disclosure bodies are now skipped.

Heights in px against the ruling-7 final caps (page 1500/1900, strip 140/200, criteria 500/760, Related 360/500,
notice 110/160):

| State | 1440 main / strip / criteria / related / notice | 390 main / strip / criteria / related / notice |
|---|---|---|
| positive (CURRENT) | 755 / 42 / 292 / 168 / 42 | 1115 / 65 / 433 / 272 / 60 |
| positive, Finding version open (exempt) | 799 / 86 / 292 / 168 / 42 | 1137 / 86 / 433 / 272 / 60 |
| not linked (K1) | 626 / 42 / 103 / 168 / 42, currentness 42 | 852 / 42 / 126 / 278 / 60, currentness 42 |
| historical (K3) | 815 / 42 / 292 / 168 / 42, currentness 42 | 1175 / 65 / 433 / 272 / 60, currentness 42 |
| pending / stale / unknown | 815 / 42 / 292 / 168 / 42, currentness 42 | 1193 / 65 / 433 / 272 / 60, currentness 60 |
| worstcase Action 1 | 684 / 42 / 103 / 168 / 42 | 978 / 114 / 126 / 278 / 60 |
| not found / 403 / 503 / 422-client (state panel) | 220 / 315 / 315 / 315 | 266 / 361 / 361 / 384 |

Server 422 for `known_at=not-a-time`: `{"code":"INVALID_KNOWN_AT","message":"'known_at' must be one UTC instant no later
than the read time.","intent":null,"results":null}`. This is recorded beside the browser's client-side refusal
(P-K4b-1).

`cases-recheck/` reruns the K3 case capture with the ruling-12 CSS: 930 PASS, 4 FAIL. All four failures are the K3
ruling-20 one-line-UUID claim in `UTC and IDs`. See `.agent/W5-02c-K4-questions.md` Q1.

Cleanup:
- The 7 Vite PIDs were stopped by PID.
- The tool's `drop` stopped the APIs and dropped the 5 `w502b_*_k4_test` databases.
