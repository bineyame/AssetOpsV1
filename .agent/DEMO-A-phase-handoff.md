# DEMO-A phase handoff

Source: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-DEMO-COMBINED.md` (rev 1). Branch
`task/DEMO-A-combined-dataset` from main `e19bb687`.

## State (2026-10-31)

- **U1 probe: done, STOP RULE FIRED** (cost check not calculated). Findings: `.agent/DEMO-A-probe.md`.
  - Tick does not create an F-104 revision or withdraw ACT-048's resolution (stop rule 1 clear).
  - Freshness CURRENT on S and S+1 after S2 + two ticks (stop rule 2 clear).
  - Cost check UNAVAILABLE / PRICE_MISSING (stop rule 3 fires): price revisions are stamped at real time, the
    hook reads the price as known at the story evaluation clock. Needs an Architect ruling before U3.
- **U2: not started**, per the dispatch ("If a U1 stop rule fires, STOP and report").
- Probe DBs dropped; the probe work folder `var/demo3_probe` (gitignored) removed.

## Resume

- Wait for the Architect ruling on the cost-check cause (probe doc, options 1-3), then build U2 per sheet §3 U2.
- U2 wall cap basis: probe Kobo chain + S2 + 2 ticks + Performance = 246 s (one Site only).
- U5 risks already found (probe (h)): EV scenario YAML start must shift in memory; `Chain.open` hardcoded setup
  clock in the w205b test module.
- U3 risk (probe (e)): without objectives the S board places ACT under Protect with "linked finding outside this
  view" and lists no F-104 item; re-check after objectives.
