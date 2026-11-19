# Review packet: mock-up vNEXT professional pass

Branch `task/mockup-vnext-professional`. Base afbffd9bd. Commits: 6922e5559, b6bb46813 (first pass); a8fd856b6, 9e55785cb, bb3c2f6f7, aa7ff2562, plus the handoff/packet commit (second pass).
Open: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/index.html`.
Sources: design §2.4–§2.6, §2.8, OD-1 to OD-12; `worked-portfolios.md` §1.5; `demo-site-scenario-manifest.yaml` `demo_workflow`, which is read at runtime as `MANIFEST.demo_workflow`. Names, thresholds, due dates and plan state are all taken from that block, not typed into the code.

## Screens
| Screen | Change |
|---|---|
| Act first `#/portfolio/act-first` | Issues needing a decision are in the main column. Each row shows its site, what is at stake, who decides (role and illustrative name) and a link to the decision. The plan summary sits beside it: state, version 1, "proposed by the system · awaiting the operator executive's approval", approver, budget and crew meters, the modelled 12-month value, the Action count (released and waiting), both thresholds and the release rule, and "Open the plan". |
| The plan `#/portfolio/act-first/plan` (new, drill-down) | Each item is a card: site, reason, cost and who pays, crew visits, 12-month result, condition, and a link to the decision. Under each item are its Actions, each with creator, owner, due date and state (Released or Waiting for approval) and the reason, which is computed from the rule. The side panel holds the approval: opened and proposed dates, approver, meters, what approval releases, disabled "Approve" and "Send back" buttons, the thresholds and the switches. Below are the inverter paths, crew visits, items listed beside the plan, "Left out of the plan, and why", the four cases, and "Actions that return to their creator" when a case drops an item (OD-4). |
| Decision pages `#/decision/<id>` | A four-step "Who decides" strip: what the system recommends; who chooses; the Actions created (creator, owner, due date, and the item they count on); the release state with its reason. |
| What changed | A KPI row (plan version and state, Actions, overdue, review date). Then "Actions and their owners" (every Action), "The plan's review" (each item's predicted change, owners, and observed "not yet" until 31 Dec), then the existing verdicts and rights. |

## Checks (run on the final source)
- Rebuild per README: rebase, evaluator, gen_fixtures (0 differences between evaluator and stated fields), build.
- `node tools/render_text.cjs`: 205 renders, 0 script errors.
- `node tools/vocab_check.cjs`: 205 screens scanned, 0 hits. Earlier-view body residual: 256 hits on 60 routes, reported but not failing.
- `python3 tools/hand_typed_scan.py`: count 0; manifest count 0; allow-list 46 entries, all used.
- `python3 ../check_manifest.py` and `python3 ../check_alignment.py`: results in the report.
- New check, `node tools/plan_switch_check.cjs`: 66 passed, 0 failed, 0 script errors. It covers four Lakeside cases plus two each for Harvest and Metro: spend, value, item count, and each Action's state against the data. It also checks the Act first layout, version, state, executive, thresholds and meters.
  - Planted violation: every change treated as above the threshold gave 12 failed and 24 script errors. Reverted.

## Not run
- Playwright audit, screenshots and layout evidence were not run: there is no browser, and installing one was refused.
- `CHANGE-REGISTER.md` and `browser-audit.md` are not regenerated, so they do not yet list the plan screen.

## Gaps (no value invented)
1. **Who chooses.** The data does not say who chose each option. Where an item has Actions, the chooser shown is the creator of its first Action; for example, Mto inverter shows Joseph, the finance and commercial lead. For decisions with no Action, the role comes from the subject rule in §2.4 step 2: billing and claims go to the finance and commercial lead (Kisiwa service credit, Mto billing, Ruiru connector); capital goes to the executive (Ruiru expansion); the rest go to the Site manager. Architect to confirm.
2. **Version 1's items.** Version 1 is taken to be the evaluator's default case. Its items match the stated Actions' items exactly, but the data does not name the case.
3. **Item owner.** §2.5 gives each item an owner, but the data has none, so none is shown.
4. **Approval buttons.** "Approve" and "Send back" are shown but not wired (disabled).
5. **Plan review.** The observed column reads "not yet". The review date, 31 Dec, is derived from the plan period.
6. **Asset tag.** The Action text "INV-MT-02" is shown verbatim from the data.
7. **Earlier v7.0 views.** Their bodies still carry record codes.
