# W5-02b K3a + K3b review (cold Incidents and Maintenance tabs)

Reviewer: independent Claude reviewer, 2026-10-23. Branch `task/W5-02b-K3-cold-cases` at `554bf935`, base `f164c49d`.
I read: the build spec K3 cards and rulings 1-16; K2 rulings 1-24 where cited; the register rows R65-R94; the handoff; the evidence README, the measurements JSON and the 44 PNGs; the v69 mock lines `index.html:333-343`; and the diff for frontend/src, tools/w502* and the ledger and contract JSON.

## Verdict: REVISE

The screen code is faithful to the ruled v69 reading, and the MINIGRID path is isolated. The tests are real, and the guard extension is non-vacuous. The registry literals match P-K3b-1-4 exactly.

The revision is needed for two reasons. The "all disclosures open" evidence measures a state the rulings did not define, and that wider state causes most of the cap failures. The case-cell ID wrapping also contradicts a spec sentence. The remaining items are Architect rulings (below) or Low.

Counts: **High 0, Medium 3, Low 5.**

## Checks I ran (on 554bf935)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run` on `coldWorkCases`, `siteWorkCases`, `coldWorkActions`, `w1f4ChangesWorkStructure` | 4 files, 88/88 pass |
| `npx.cmd vitest run` on `operatorSiteTabs`, `operatorRouteFrames`, `siteDetailRoute` | 3 files, 88/88 pass |
| Guard non-vacuity (my own mutation): removed the `cold-work-maintenance` `SCREEN_LEADING` entry | 5 of 24 `coldWorkCases` tests fail; reverted, tree clean |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `tools/check-all.ps1` | see the final line of this file |
| `ast.parse` of `tools/w502_cold_work_walkthrough.py`; `node --check tools/w502-cold-work-evidence.mjs` | OK |
| Backend diff `f164c49d..HEAD -- backend` | empty |

Vitest ran under this session, so the focused suites are verified. The full frontend suite and `npm run build` were not rerun. For those I rely on the implementer's batch figures (120 files, 2832 passed, build green), which I could not verify.

No focused Postgres run was done. No backend file changed, and no backend test imports `tools/w502_cold_work_walkthrough.py`, so `test_w502_*` would not exercise the K3 changes. The producer, `serve` and `attest` paths are verified only by the implementer's batch run and by the manifest-derived claims in the measurements JSON. I could not rerun `prepare`, `serve` or captures: they need Chrome, seven APIs and dev servers.

## Findings

### Medium

**M1. The all-open capture opens every `details`, not every `Read full text`. That inflates the page heights the Architect is asked to rule on.** `tools/w502-cold-work-evidence.mjs:420` (`openAll`), used at `:472`.

`openAll` clicks every closed `tbody details` six times over. This opens `UTC and IDs`, both `Finding version` disclosures, `Activity recorded` and `Outcome note` (23/23 and 27/27 in the JSON). Ruling 16 defines the exempt state as "the five-row worst-case state with every `Read full text` disclosure open". Ruling 12 needs the parent `Activity recorded` and `Outcome note` open too, so their nested control is reachable.

In the PNGs, the `UTC and IDs` fact lists are the dominant height, about 270-310 px per row:
- `w502b-desktop-maintenance-worstcase-all-open.png` shows six to eight stacked facts per row;
- `w502b-desktop-incidents-worstcase-all-open.png` shows five.

So the three failing page-main numbers (2203, 3140 and 3214) measure an undefined state, not the ruled one.

Why it matters: the Architect is asked to judge a cap against a number that includes about 1300-1500 px of identity facts the ruling never opened.

Fix:
1. Add a ruled `worstcase-all-open` state that opens only `Read full text` and the parents needed to reach it. Gate the page-main cap on that state.
2. Optionally keep today's state as an INFO-only `worstcase-every-disclosure`.
3. Re-capture and report the new heights.

**M2. Disclosure IDs now wrap mid-UUID inside case cells, against the spec's "IDs/codes stay one line in the table scroller".** `frontend/src/sites/w1f4-action.css:229-232` (`.disclosure__body code { overflow-wrap: anywhere }`) and `:241-244` (stacked fact grid).

The spec says this at `.agent/W5-02-build-spec.md:78`. In every opened `UTC and IDs` and `Finding version`, each 36-character UUID breaks across two lines, at both 1440 and 390. Examples: `ba1f7572-73ce-4b5e-8030-` / `15c96827cd73`, and `325dfca5-14a2-440e-9b8c-` / `f0aa2ff0c89d`.

The capture fix replaced a worse defect (one character per line) and the stacking is a real improvement. But the wrap itself is an implementer layout decision that no ruling covers. It also doubles the height of every ID fact, which feeds M1.

Why it matters: a split UUID is hard to copy or compare by eye, and the spec sentence is explicit. At 390 the table already scrolls horizontally, so one-line IDs are feasible there.

Fix: either keep `code` on one line (`white-space: nowrap`) and let the disclosure body or table scroll, or obtain an Architect ruling that disclosure-body IDs may wrap inside a fixed-width case column at 1440. See Architect item 4.

**M3. At 390 the cold Incidents table inherits W4's 224 px vertical inner scroller, and Maintenance does not. Incidents' cap passes hide rows inside a two-axis scroll box.** `frontend/src/sites/w4-work-cases.css:134` applies to cold, because the rule is not scoped by `data-cold-cases`.

The PNGs show the effect:
- `w502b-narrow-incidents-worstcase.png` shows two and a half rows, with row 3 (`INC-000005`) cut under the horizontal scrollbar;
- `w502b-narrow-incidents-worstcase-all-open.png` shows one row's opened facts filling the whole 224 px box.

The README reads "Incidents stays at 353 in every state" as a pass. It is really the W4 scroller absorbing the content, while the same opened content on Maintenance grows the panel to 2608.

The v69 `cold-work-incidents` 390 table scrolls horizontally inside its panel (`index.html:342`, spec `:78`), with no vertical box. The mock shows only one row, so this is not a departure from a defined mock state. It is still an unruled nested vertical scroll on a cold screen, and it is inconsistent between the two sibling tabs.

Why it matters: the claims "panel <= 650" and "no clipping" pass for Incidents only because of a W4 rule built for the mini-grid stocked list. A user on a phone reads five cases through a 224 px window.

Fix: an Architect choice (item 5). Either scope the W4 rule out of `[data-cold-cases]` so both tabs grow and are capped alike, or extend it to cold Maintenance and record the vertical inner scroll as a departure row.

### Low

**L1. The positive and historical captures are byte-identical, and the tool comment calls one of them "Positive CURRENT".** The comment is at `tools/w502-cold-work-evidence.mjs:439`.

The MD5s match for all four pairs, for example `083F88F220` for both `desktop-incidents-positive` and `-historical`. The two `known_at` values differ by 0.26 s (`20:07:20.736` and `20:07:20.471`), and both read `HISTORICAL`. So there is no distinct positive state in the evidence. The README discloses this, but the code comment is wrong.

Fix: correct the comment, and see Architect item 3.

**L2. The Site-local Window splits its own value at 1440.** `frontend/src/sites/siteWorkCases.tsx:704`.

The cell renders `22 Oct · from` / `19:11 UTC and IDs` in every 1440 Incidents capture. The mock value `6 Oct · from 19:11` is one phrase.

Fix: `white-space: nowrap` on `[data-work-window]` inside `[data-cold-cases]`, so only the `UTC and IDs` control wraps.

**L3. A dead duplicate CSS rule.** `frontend/src/sites/w1f4-action.css:225-227` (`margin-top: 2px`) is fully overridden by `:251-256` (`margin: 0`) on the same selector. Delete the first rule.

**L4. Long-text test coverage is title-only for the replace behaviour.** `frontend/src/sites/__tests__/coldWorkCases.test.tsx:383-414` proves preview removal and restore for the Case title only.

For Activity, it checks only that the nested summary exists and can take focus. Nothing covers the Incident `What happened` or Maintenance `Outcome note` long text, or the inner preview being replaced while the outer disclosure is open. `CaseLongText` is shared code, so the risk is low.

Fix: one parametrised case over narrative, activity and outcome_note that opens the inner `Read full text` and asserts the preview is gone and the value appears once.

**L5. The manifest records the requested record time, not the returned one.** `tools/w502_cold_work_walkthrough.py:306` stores `record_occurred_at: iso(r_at)`, the requested value. The INC and WR times are re-read from `work_case`, but the performed record time is not re-read from `work_record`. Ruling 7 says "Store/assert actual returned times and IDs".

Fix: read the record's `occurred_at` from `xr`, or from the DB, and assert that it equals `r_at`.

## Code-quality notes (no finding)

- **`site` prop.** `SiteAnalyticsFrames.tsx:2105` passes `site` for every type. `cold` is non-null only for `COLDCHAIN` (`siteWorkCases.tsx`, `SiteWorkCases`), so MINIGRID and EV take the unchanged W4 branches:
  - the W4 strip and its status label;
  - `CoverageLine`;
  - W4 cells with `DecisionContext`;
  - the W6 notice;
  - the W4 form.

  The `mini-grid isolation` test covers MINIGRID Incidents. There is no EV or MINIGRID-Maintenance test, but the branch is a single conditional.
- **`CaseLongText`.** It is a line-for-line copy of K2's `LongText` (`SiteWorkActions.tsx:672-699`), as rulings 14 and 12 permit. The `parentElement === wrapper` toggle filter is correct for `Disclosure`, which renders `details` as the direct child.
- **Cold CSS.** Every new rule is under `.work-cases[data-cold-cases]`, and `data-cold-cases` is set only on cold, so MINIGRID is unaffected.
- **Producer and attest.**
  - Ruling 7 literals: correct.
  - `pad160`: asserted.
  - Ruled minutes and keys: correct.
  - Interval order: asserted.
  - The zero window `[D-8d, D-1d)`: uses `d16.replace(hour=0)`.
  - Case reads: at each read's returned cutoff.
  - The no-reads backlog gap: closed.
  - The served 403/503: checked on both case reads.

  The `W502B_CASE_GATE` router is limited to the two refusal processes, as ruling 8 requires.
- **Registry.** The three ledger rows and three panel contracts match the spec `:88-90` literals. `unresolved_panels: []` is correct, because no `GAP` prefix remains. `follow_on`, `interaction` and `unknown_or_empty` are preserved (ruling 15).
- **Mock fidelity.** Checked across all 44 PNGs:
  - strip literals and the `→` arrow;
  - five mock columns in order;
  - subtitles;
  - `WORK_EMPTY` titles and bodies;
  - the domain foot notice;
  - plain INC codes;
  - `Finding {id8}` with its version disclosure;
  - `generator-1 · backup generator`;
  - `Unverified`;
  - the R72 gap;
  - R91 notice placement and tone.

  Every remaining difference from v69 maps to a register row (R01, R65, R66, R68, R70-R73, R89, R90-R94) or to ruling 9 (W4 `Refused`). I found no unlabelled departure in a state the mock defines.

## Items for the Architect

1. **Case panel cap of 440 at 1440 (builder open point 1, four failures: 486 and 539 on both tabs).**
   - **Cause:** content, not a layout defect. Each worst-case row holds a two-line preview plus the one-line `Read full text` control, about 68 px, so five rows take about 340 px against about 146 px of fixed chrome (heading, subtitle, table head, Pages and basis). Staying within 440 needs 59 px or less per row, which is impossible with ruling 7's two-line preview and a separate control line.
   - **The mock:** one short row per tab, panel 183 px (`.agent/W5-02-04-mock-measurements.md`).
   - **Precedent:** K2 ruling 2 declared the same 440/650 cap "invalid" for five long rows on Actions and raised it to 650/850.
   - **Recommended ruling:** set the case panel cap to **650 at 1440**. Closed measures 486 and one-open 539. Keep 650 at 390, where Maintenance measures 430 and 526 and Incidents 353 (see item 5).
2. **All-open page-main caps (builder open point 1, three failures: 2203, 3140 and 3214).**
   - **Cause:** mainly the capture tool opening every disclosure, including the identity fact lists (M1), with ID wrapping doubling those lists (M2). Neither is the ruled `Read full text` state.
   - **Recommended ruling:** (a) the builder re-measures with only the `Read full text` controls and their required parents open. (b) If the page still exceeds 1400/1800, apply the K2 ruling 24 precedent: for the all-open state only, keep the page cap at the K2 cold-Actions value of **1600/2000**. Do not exempt the page cap outright.
3. **No CURRENT positive capture (builder open point 3).** Every capture currently carries an explicit `known_at`, and W4 returns `HISTORICAL` for any explicit past cutoff. So positive and historical are the same image (L1).
   - **Recommended ruling:** add one positive capture per tab with `from,to` only (no `known_at`) on the positive DB. Record the returned `known_at` and status in the manifest, and assert `CURRENT` with no notice. If the spec's "every capture uses an exact returned cutoff" is meant to forbid this, say so instead and accept the component tests (`coldWorkCases.test.tsx:190-226`, the CURRENT path) as the CURRENT proof. In that case, relabel the `historical` state as redundant or drop it.
4. **Disclosure ID wrapping (M2).** Rule whether UUIDs inside an opened `UTC and IDs` or `Finding version` body may wrap inside a fixed case column at 1440.
   - **Recommended ruling:** keep IDs on one line (spec `:78`). Let the disclosure body scroll horizontally at 1440, as the table already does at 390. Keep the fact-stacking fix.
5. **Narrow Incidents vertical inner scroller (M3).** Rule whether the W4 224 px vertical box (`w4-work-cases.css:134`) applies on cold.
   - **Recommended ruling:** scope it out of `[data-cold-cases]`, so cold Incidents behaves like cold Maintenance and the v69 horizontal-only table scroll (`index.html:342`). The 650 px narrow panel cap then applies honestly to both tabs. The all-open exemption from ruling 16 still applies.
6. **WR state stays OPEN (builder open point 2).** W4's `post_record` does not change request state. But W4 does support `ASSIGN` (OPEN to IN_PROGRESS) and then `COMPLETE` with `maintenance_record_id` (IN_PROGRESS to COMPLETED) through `WorkService.post_event` (`backend/assetops_backend/work/model.py:100-104`, `service.py:257-285`). So a completed WR is producible with existing W4 commands and no product change.
   - **Recommended ruling:** in the producer, complete the **one fixture WR** with `ASSIGN` and then `COMPLETE`, citing its performed record, under the same SERVICE principal and idempotency-keyed. The positive capture then shows the mock's `Completed` chip from real state. Leave the four worst-case WRs OPEN, so the captures also show the non-completed chip under ruling 3.
   - Before ruling, confirm this does not change K2's captured Actions evidence or K4's `Related activity` expectations. If it would, keep OPEN, which is honest under ruling 3, and rely on the component test (`coldWorkCases.test.tsx:263-299`) for `Completed`.
7. **(Information) 403 strip copy.** On the W4 refusal, the strip reads `Count unknown · work source unavailable` for a 403 as well as a 503 (`w502b-*-forbidden-403.png`). This is W4 behaviour that ruling 9 keeps unchanged. No action is recommended in K3. Flag it for the W1-conclusion copy pass if the owner finds "unavailable" misleading for a permission refusal.

## Residual risk not named in the packet

- The 1440 cap verdicts are only as good as the all-open state definition (M1). Until the re-capture, the page-cap numbers are not evidence for or against the ruled state.
- The full frontend suite and production build were not independently rerun here, so they rest on the implementer's batch run.
- The producer, `serve` and `attest` were not rerun. Producer correctness rests on the batch run and the manifest contents embedded in the measurements JSON.

`tools/check-all.ps1` result on 554bf935: all 11 guards passed. This includes Screen ledger (110 screens, 258 panels), Dependency registry, Missing-claim scan and Navigation truthfulness.

