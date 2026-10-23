# W5-02b K3 evidence (cold Incidents and Maintenance tabs)

The images were produced by `W502B_EVIDENCE=cases node tools/w502-cold-work-evidence.mjs <manifest> .agent/W5-02b-K3-evidence`. The manifest came from `python tools/w502_cold_work_walkthrough.py --work var/w502b_cold_work_k3 --tag k3 prepare|serve|attest`, with the tool tree at `a0c3c17e` (backend unchanged).

- **attest:** OK. All five modes are unblocked, with the expected case counts:
  - positive, historical and every non-worst-case mode: 1 Incident and 1 Maintenance request;
  - worstcase: 5 of each, 5 rows each;
  - complete zero: 0.
- **Served refusals:** the 403 is `SITE_SCOPE_FORBIDDEN` and the 503 is `WORK_STORE_UNAVAILABLE`, on both W4 case reads. The Site read stays healthy.
- **Claims:** 738 in total, 731 PASS and 7 FAIL. The full record is in `w502b-k3-measurements.json`.
- **Layout fixes before this run:** the earlier run exposed layout defects, which are now fixed in `w1f4-action.css`:
  - the facts in `UTC and IDs` stack inside a case cell, where they used to wrap one character per line;
  - `Read full text` is a compact one-line link.

## States (each tab, at 1440 and 390)

| State | What it shows |
|---|---|
| positive, worstcase | The recorded query, at the Action read's window and its returned cutoff. The returned case status is `HISTORICAL`, so the blue notice shows. |
| historical | Read at cutoff K3. |
| zero | The ruled `[D-8d, D-1d)` window, read as CURRENT. Shows the mock empty card. |
| worstcase-one-open | One `Read full text` open. |
| worstcase-all-open | Every disclosure open. |
| pending | Amber notice. |
| stale | Amber notice. |
| unknown | Blue notice. The Incident has 1 Finding link (ruling 21). |
| forbidden-403 | W4 `Refused`, unchanged: title and fixed sentence, no Retry (ruling 9). |
| unavailable-503 | W4 `Refused`, unchanged: title and fixed sentence, no Retry (ruling 9). |

## The 7 FAIL claims (measured, not clipped; for the Architect)

| Width | State | Gate | Measured |
|---|---|---|---|
| 1440 | incidents-worstcase (closed) | panel <= 440 | 486 |
| 1440 | incidents-worstcase-one-open | panel <= 440 | 539 |
| 1440 | maintenance-worstcase (closed) | panel <= 440 | 486 |
| 1440 | maintenance-worstcase-one-open | panel <= 440 | 539 |
| 1440 | incidents-worstcase-all-open | page main <= 1400 | 2203 (panel 1759, exempt) |
| 1440 | maintenance-worstcase-all-open | page main <= 1400 | 3140 (panel 2696, exempt) |
| 390 | maintenance-worstcase-all-open | page main <= 1800 | 3214 (panel 2608, exempt) |

The 390 worst-case panels hold their caps: Incidents 353 and Maintenance 430/526/2608. At 390 the existing W4 table scroller limits its own height and scrolls vertically inside the panel, so Incidents stays at 353 in every state.

## Other observations

- **WR state stays OPEN.** Every producer WR is still `OPEN` after its performed record, because W4 `post_record` does not complete a request. The Activity cell therefore shows the real `Open` chip, not the mock's `Completed`, which is correct under K3 ruling 3. The mock's completed example would need a W4 completion step in the producer.
- **No CURRENT positive capture.** A pinned explicit cutoff reads `HISTORICAL`, so no CURRENT positive capture exists. The CURRENT state is shown by the complete zero and covered by the component tests.
