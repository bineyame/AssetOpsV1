# Review packet: mock-up vNEXT, demo workflow items wired

Status: in_review. Branch `task/pack-recreate-integrate`. Base 70016422d. Commits: 92c3623cc (wiring), e12bc32e3 (check extended), 07fe47d08 (check: a missing card is reported as a failure, not a crash), plus this packet.
Open: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/index.html`.
Sources: design rev 16.8 §2.4 to §2.6, Figure 6c, OD-13 to OD-20; `worked-portfolios.md` §1.1 and §1.5; `MANIFEST.demo_workflow.tenants[].items[]` (fixtures from 098d0df8c, unchanged).

## Screens
| Screen | Change |
|---|---|
| The plan `#/portfolio/act-first/plan` | Each item card shows "Chosen by, so owned by" with the person, from `chosen_by`/`owner`, and the state as a word (Chosen or Released, from `item_state`). The rule cross-checks it and logs `console.error` on a mismatch. The huller card is marked Capital. In place of an Action list, it says that it waits as capital and that David creates its Action only after Amina approves; the stated `actions_after_approval` text is listed. A declared Kisiwa service card is added in every case: label, Declared by Halima, Chosen, spend 0 with its basis, 1 crew visit in December (1 of 3), "No factor (upkeep or compliance)", "Upkeep, no value claimed", depends on the Kisiwa repair with its reason, service date 8 Dec, and the action note. The approval panel now has three meters: budget, crew visits in November and crew visits in December. The approval sentence reads "4 waiting Actions and 5 items, $3,660 of one-off spend, including $1,200 of capital (the Mto rice huller)" and names who creates the later Actions. The crew-visit table lists the service. |
| Act first | Who decides comes from `chosen_by`. The side panel has November and December crew meters. The Actions line adds the 2 items whose Actions are created after approval. |
| Decision pages | Step 2 names the chooser from `chosen_by`, says that this person owns the item, and gives the item state. On `mto-demand`, step 3 shows the after-approval Action and step 4 shows "Waiting as capital". |
| What changed | The review table covers all version-1 items, the proactive one included (this was the TypeError). New columns: Item owner, Item state, Action owners. For the huller and the service, the Action-owner cell says when their Action is created. The KPI line adds the items with later Actions. |

Code: `loop-portfolio.js`, the workflow helpers (`itemOf`, `planItemsV1`, `releaseOf`, `itemStateOf`, `itemOwnerLine`, `laterActions`, `crewByMonth`/`crewMeters`, `waitingSummary`, `deciderOf`, `proactiveCard`) and `planScreen`/`whatChangedScreen`; `loop-site.js` `whoDecides`; `theme.css` (three rules). `releaseOf` uses `planned_spend`/`crew_visits` for a PROACTIVE item and never calls `DOPT` for it. A capital item always waits (OD-17).

## Checks (final source, 07fe47d08)
- Rebuild per README: rebase, evaluator, gen_fixtures (0 differences, fixtures unchanged), build.
- `node tools/render_text.cjs`: 205 renders, 0 script errors (60 s).
- `node tools/vocab_check.cjs`: 205 scanned, 0 hits (earlier-view residual 256 on 60 routes, not failing, unchanged).
- `python3 tools/hand_typed_scan.py`: count 0, manifest count 0, allow-list 46, none unused.
- `python3 ../check_manifest.py`: 4026 passed, 0 failed. `python3 ../check_alignment.py`: 96 passed, 0 failed.
- `node tools/plan_switch_check.cjs`: 164 passed, 0 failed, 0 script errors (was 66). New: item owner and state on every card, the proactive card's content, case items plus declared items, one meter per month with a stated limit, capital waiting with no Action, the approval spend with capital, and the chooser on each decision page.
- Plants, each reverted with `git checkout`:

  | Plant | Result |
  |---|---|
  | chooser taken from the first Action's creator | 1 failed (mto-inverter: David) |
  | proactive card dropped | 16 failed |
  | December meter dropped | 15 failed |
  | old approval spend, without capital | 8 failed |
  | state code shown instead of the word | 12 failed |

## Not run
- Playwright audit, screenshots and layout evidence were not run: there is no browser. `tools/rendered_strings.cjs` (Part B input) needs Chromium, so the new demo_workflow strings are not in `rendered-manifest-strings.json`. By hand: their only digits are ID codes (GEN-KS-01/02) and day-month dates (9 Nov, 6 Nov), which Part B masks.
- `CHANGE-REGISTER.md` and `browser-audit.md` were not regenerated.

## Gaps (no value invented)
1. The huller's due date (5 Dec in `worked-portfolios.md` §1.5) is not in the data, so it is not shown.
2. Decisions with no item (Kisiwa O&M credit, Mto billing, Ruiru connector and expansion) still take the chooser from the §2.4 role-by-subject rule.
3. The December meter appears only for Lakeside. Harvest and Metro state no `*_dec` limit.
4. Asset tags (GEN-KS-02, INV-MT-02) are shown verbatim from the data labels.
5. No evaluated case drops the Kisiwa repair. If one did, the service card would mark its dependency "not in this case".
6. Approve and Send back are still not wired.
7. No `specs/INDEX.md` and no `.ai/state/` in this worktree, so no index row or built-state entry was written.
