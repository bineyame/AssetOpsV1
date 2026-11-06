# DD-1a1 handoff (builder 14: R6 fix landed, R6 assertion 7 needs an Architect ruling; R9 Lows fixed)

## Landed earlier
- R8 (builder 11), R9 (builder 12): see `.agent/review-packet-DD-1a1.md`. Helpers in `C:\Users\assef\dd1a1w\`
  (env.sh, d12.sh `<with|without>`, deg.sh, mkdb.py).

## Landed (builder 14)
- `6340405fa` R6 fix (tool only): the gateway's background uploader delivers on start, which drained the withheld half
  through later complements. Post-outage complements now start their gateway with no `upload` block
  (`tools/demo_combined_kobo.py` `publish_first_half(outage_continues, withheld_run)`; `_OUTAGE` is epoch -> story run).
  Check script: grade per story window, stray rows on any later day, no analytic-run count compare.
- `ac9655668` + `33dfe724b` R9 review Lows 1-2 in `actions/verification.py` (`meets` fails closed on an unreadable
  start; `_baseline_target` equality required for `reselected`), two tests, each proven to fail without its fix;
  fixture class fixed to `CANDIDATE_AVOIDABLE`. R9 unit + S6 verification files: 125 passed.
- R6 check (`deg_compare.log`): 1-6 PASS, 7: 0 AMBIGUOUS and findings PASS, **grade FAILS** (details and cause in the
  packet's R6 section: the delivered half follows random source-id order; the with day also holds the night
  interval). Stopped per R6. Architect question is in the packet.
- R5-R9 re-check: one `with` build (981 s) + r9/r8/r7 checks all PASS.
- All DBs dropped; no processes left.

## Resume here
1. Get the Architect's ruling on R6 assertion 7 (packet "R6 degraded-day check"). Apply it, rerun `deg.sh`.
2. Then: the five R3 L2 checks (need with/without builds; no tooling yet), the mill day (0 generator starts, CH-9b
   mill outcome), Q8 cost per full Kobo/Cold day, the Cold failure day, guards V, A, W, N, M (M with NODE_PATH =
   plan2 `frontend/node_modules`), then the packet's Open section.
