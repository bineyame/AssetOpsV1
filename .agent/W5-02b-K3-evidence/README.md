# W5-02b K3 evidence (cold Incidents and Maintenance tabs), final recapture under K3 rulings 17-24

The images were produced by `W502B_EVIDENCE=cases node tools/w502-cold-work-evidence.mjs .agent/W5-02b-K3-evidence/manifest.json .agent/W5-02b-K3-evidence`. The manifest is a copy of the one from `python tools/w502_cold_work_walkthrough.py --work var/w502b_cold_work_k3 --tag k3 prepare|serve|attest`, with the tool tree at `6815ae65` (backend unchanged).

- **prepare:** all five modes unblocked, 120 s.
- **attest:** OK.
  - The case reads have the expected counts.
  - The new `current` reads from `from,to` alone return `CURRENT` on both tabs.
  - The fixture WR is `COMPLETED`: ASSIGN at D+16h41m and COMPLETE at D+16h42m, both before its case link (ruling 22). The worst-case WRs read COMPLETED + 4×OPEN.
  - The served W4 case reads return 403 `SITE_SCOPE_FORBIDDEN` and 503 `WORK_STORE_UNAVAILABLE`, with the Site read healthy.
- **Claims:** 934 in total, **933 PASS and 1 FAIL**. There are 52 PNGs: 13 states × 2 tabs × 2 widths. The full record is in `w502b-k3-measurements.json`.

## States (each tab, at 1440 and 390)

| State | Gates and notes |
|---|---|
| current | Ruling 19. The URL has no `known_at`, the read is `CURRENT`, and no currentness notice shows. |
| positive | The recorded explicit cutoff; reads `HISTORICAL`. |
| historical | Cutoff K3. |
| zero | Complete zero. |
| worstcase | Five rows, closed. |
| worstcase-one-open | One `Read full text` open. |
| worstcase-all-open | Ruling 18: every `Read full text` open, nested parents opened as needed, IDs, versions and basis closed. No height caps. |
| worstcase-every-disclosure | Information only. No height caps. |
| pending, stale, unknown | Notice follows the returned status. |
| forbidden-403, unavailable-503 | W4 refusal unchanged (ruling 9). |

Ruling 17 caps apply to every state except the two expanded ones: panel <= 650 at 1440 and 390, page main <= 1400/1800, strip <= 100/150, notice <= 110/160.

### Measured heights, all states (panel / page main, px)

| State | Incidents 1440 | Incidents 390 | Maintenance 1440 | Maintenance 390 |
|---|---|---|---|---|
| current | 212 / 595 | 247 / 793 | 212 / 595 | 201 / 747 |
| worstcase | 486 / 930 | 599 / 1204 | 486 / 930 | 430 / 1036 |
| worstcase-one-open | 539 / 983 | **664** / 1270 | 539 / 983 | 526 / 1132 |
| worstcase-all-open (info vs page 1600/2000) | 700 / 1144 | 861 / 1467 | 1149 / 1593 | 1469 / 2075 |
| worstcase-every-disclosure (info) | 1659 / 2103 | 1714 / 2319 | 2334 / 2778 | 2199 / 2804 |

## The one FAIL (measured, not clipped; for the Architect)

**390 Incidents, `worstcase-one-open`: the panel measures 664 px against the 650 px cap (ruling 17), 14 px over.**
- Ruling 21 removed the vertical Incidents box, so all five rows now show. The opened 160-code-point title adds about 65 px to a 599 px closed panel.
- The page main is 1270, inside its 1800 cap.
- Containment, the five rows and no overflow all pass.
- Ruling 17 forbids clipping and row reduction, so this is reported unchanged.

## Ruling gates confirmed in this run

| Ruling | What the run confirms |
|---|---|
| 18 | The all-open controls are open, their previews replaced, each value shown once, and the other disclosures closed. Every disclosure summary takes keyboard focus and is not clipped. |
| 20 | Every opened UUID stays on one line, can be reached by scrolling its own body, and does not widen its cell. The Window value is on one line at both widths. |
| 21 | Every row sits inside the table scroller, with `max-height: none` on both cold tabs. |
| 22 | The single-row Maintenance states show `Completed`. The five-row states show `Completed` + 4 `Open`. |
