# Codex handoff (kept current by the Claude coordinator)

Owner rule (23 Nov): when Claude's weekly usage reaches 99 %, Codex picks up implementation from this
file. The coordinator refreshes it after every merge and every owner decision. Last refreshed: 23 Nov, landing at 98 % usage.

## 1. The demo goal (read first)

- Audience: executives of mini-grid, EV-charging and cold-chain operators. Goal: convert them by
  showing value beyond monitoring tools: findings with money attached, decisions valued against
  doing nothing, and actions tracked and verified (`owner/owner-demo-objective-*.md`, memory
  "Demo objective").
- Four outcome categories frame every figure: Grow revenue; Optimize cost and efficiency; Protect
  asset and capital; Assure performance and returns.
- Honesty rules the owner enforces: one model-computed figure per quantity, loyal to the operating
  world, nothing fitted to a story; missing data reads "Not available yet", never 0; plain client
  language, no system vocabulary; the mockup (vNEXT) is the layout spec.
- The demo world: three operators (Lakeside Power mini-grids Kobo, Kisiwa, Mto; Harvest Cold rooms
  Mwea, Thika, Kirinyaga; Metro Bus depots Embakasi, Kasarani, Ruiru), readings 1 Jul to
  6 Nov 06:00, story date 6 Nov (story clock WK-SC approved, not built).

## 2. How to work

- Read `AGENTS.md`, then `.ai/START_HERE.md`, `.ai/ROLE_CONFIG.md`, `.ai/RULES.md`. `.ai/NOW.md` and
  `.agent/coordinator-handoff.md` are STALE (22 Nov); this file wins.
- One branch and worktree per part; never edit or switch `main`'s checkout. Build from the part's card
  (`specs/<lane>/cards/<part>.md`) and the code, test-first, each new test shown failing first. Never weaken an
  assertion; a moved literal cites its ruling; a figure that looks wrong is reported, not pinned.
- Tests from the worktree ROOT: `tools/heavy-slot.sh --db-lane -- pwsh tools/run-host-tests.ps1 -- <files>`
  (one call per step; `test_dd1b1_prepare_clock` collects only after `test_demo_combined_mill`). Databases: only
  `*_test` and `<prefix>_audit*` in container assetopsv1-postgres-1. Vitest only through `tools/heavy-slot.sh`;
  worktrees have no `node_modules`: link main's, `npx --no-install`, remove the link, never commit it.
- Guards before any merge or commit of shared files, exit codes read WITHOUT a pipe:
  `python3 tools/check-decision-index.py`, `pwsh tools/check-agent-workflow.ps1`,
  `.venv/bin/python tools/checks/statement_catalogue.py`, `pwsh tools/check-architecture.ps1` (with
  `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`). Never cite a decision ID main does not index.
- Merge: `git merge --no-ff --no-commit`, run the guards, commit only if all are 0. For DD or simulator merges also
  `simulator/tests/world` (PYTHONPATH=simulator:contracts:backend:host; 526 passed on 23 Nov), the backend test files
  that import a changed module, and for any `frontend/src` change the WHOLE frontend suite.
- Compare failures with `.agent/main-baseline/b27f7c32c.md` (partial). An id not listed there is run on main before
  it is called main's. Frontend: one whole run on main gave 12 failed, 4440 passed; some ids are flaky.
- Evidence under `/opt/assetecon/evidence/<slice>/`. Leave no job, plant edit or node_modules link behind.
- BLOCKER, model or owner-level questions stop the item and go to the Architect or owner; others keep a default,
  recorded in the packet. Rulings go in `specs/<lane>/rulings*.md` with index lines in `.ai/decisions/`.
- A review is by a session that did not author the work. Nothing merges without a review ACCEPT. The owner has said
  Codex picks up implementation; the owner has NOT said whether Codex may review or merge. Default: build, have a
  fresh session review, and hold the merge until the owner answers.

## 3. State on 23 Nov (landing at 98 % usage)

Main: merged are IA-P (all), 6a, 6c, 6h, DD1, DD2a, DD2b, DD3a, DD3b, DD3c, DD3d-a, DD4a, DD4b and follow-up, DD5a,
T1b (second DB lane). DD: 48 of 61.75 units merged; 13.75 left, plus WK-SC 3.0.

Open branches. Each was asked to land clean with its own handoff; START FROM THE BRANCH'S HANDOFF:

| Lane | Branch, worktree | Handoff to read | Next |
|---|---|---|---|
| DD3d-b | `task/DD3d-b-fuel-cost`, AssetOpsV1-dd3db | `specs/DD-demo-data/DD3d-b-handoff.md` last "Run" | finish run 5 (below), then run 6 |
| 6f1 U1 | `task/6f1-decisions`, AssetOpsV1-6f1 | `specs/6f-decisions-screen/6f1-handoff.md` last session | finish fix round 2, re-review, merge |
| Shell tests | `fix/main-shell-tests`, AssetOpsV1-shellfix | `specs/IA-P-product-shape/main-shellfix.md` | finish round 2, re-review, merge |

HEADS: `task/DD3d-b-fuel-cost` e20ffeac4 (clean); `task/6f1-decisions` bf90f6f3b (clean); `fix/main-shell-tests` 7c0403b80 (clean).

- DD3d-b run 5 = merge `task/DD3d-b-rulings-29` (ae818b36c, D-DD rulings round 29) then main, then: untracked text
  compared both ways (G9, `judge_month`) and the range line; the cost line "taken at its budget line" and four
  "reconciled" strings; 5c standing and Postgres test_9; G4, DDR fixture, `test_7`, S5/S8, runbook; L5; plants. Run 6 =
  DD3d.5 (run-rate budget, the owner-approved rule; `M` commit writes dispatch-3.3 and deletes the 3b1 t1 / 3b3 t6
  `.replace`; generate 2 and 3 byte-identical; iap sites 6 and 8 must pass; MTO plan classes), all plants, the reach
  set once, packet, state entry, in_review. Then an independent review. State at b4ab57601: pure 2373 passed, 2
  failed (iap sites 6 and 8, held); Postgres 186 passed, 1 failed (5c test_9). Report served figures before and
  after; the headline is projected about -195.30, never measured.
- `fix/main-4d-litre` is inside the DD3d-b branch; it does not merge on its own.
- 6f1 U1 (bf90f6f3b, landed clean, nothing known red, NOT ready for re-review): rulings D-P6.94-99 on main; all of fix
  round 2's code, words, whole Pages and fixtures are done. NOT done, commands in the handoff's "Ninth session": 52 of
  69 plants (incl. `latestcost`, `nonewer`, `docnow`, `levelev`, N2, the Postgres one); the whole reach set (36 + the 6f
  files, not started; 6a, 6c, 6h and Postgres not rerun); packet, state entry, in_review. The re-review is verification,
  plus discovery on `records.py`, the Postgres read and `stated_changes`. A third fix round triggers W7 (stop rule).
  State line: next free number in `.ai/state/index-4.md`.
- Shell tests (7c0403b80, landed clean, NOT accepted): three whole runs, each 2 failed / 4457 passed. Always red:
  evActionFixRound "over 31 days" (Q-SF-1). Intermittent, not in main's one run: evEnergy R347, evEnergy
  `energy_states_table_loading`, temporarilyUnavailable "a loaded board after a retry" (one-line awaits, in the note's
  "Next"). Then a re-review. This was round 2: if a third round is needed, W7 applies.
- Q-SF-1, a PRODUCT DEFECT found there, against D-IAP.24 P.9 and the owner's range rule: on a range over 31 days, cold
  tabs, EV Work tabs and the mini "Manage in Incidents" link carry only a 31-day window. Default: its own fix slice
  (`linkBound` for links, a 731-day gate), then re-pin evActionFixRound. Not started. Q-SF-2 (Low): past 731 days the
  refusal still says "31 days"; keep until Q12.

## 4. Remaining work, in order (units)

1. DD3d-b (4.25 u): above. DD parts are strictly one after another.
2. DD5b (4.25 u, `specs/DD-demo-data/cards/DD5b.md`): load, disorder and fuel steps; round 28 and 29 gains apply.
3. DD6 (5.25 u, `cards/DD6.md`): the world built and served.
4. WK-SC story clock (3.0 u, `spec-WK-SC.md`, `cards/WK-SC.md`): prepares the ten decisions.
5. 6f1 (6.0 u, at its cap), in parallel with DD: U1 merges first, then U2 (list) and U3 (page) from
   `specs/6f-decisions-screen/cards/6f1-U2.md` and `6f1-U3.md`; U3 merges before U2. Then 6f2 (choice on screen).
6. Shell-test fix (above), any time; then the Q-SF-1 product fix (not sized).
7. IA-PD demo routes (0.5 u, D-IAP.36) before the next demo build; rebuild the world rung once before the next WK run.
8. 0K4f, Q11 (cold and EV monthly figures), Q12 (31-day cap; main's range-cap test failures may belong here).
9. Refresh `.ai/NOW.md` and `owner/SUMMARY.md` (both lag; any time; before the alignment pass).
10. Design-doc and vNEXT mock alignment pass, AFTER DD (owner). A deliverable; section 6.
Backlog after the demo: `.agent/backlog-post-demo.md`.

Warnings: no walkthrough can be prepared from main between DD3d-b's merge and DD6. After 6f1 U2 the Decisions list,
inbox and waiting columns are empty until WK-SC; do not rebuild a demo app from main in either gap without telling
the owner.

## 5. Open owner questions

- May Codex review and merge, or should merges wait? (default: hold merges)
- D-P6.98 (not blocking, before the first pilot Site): should an option's projected value on a Site with real records
  read "Estimated" instead of "Recorded"? Recommended Estimated; default until answered Recorded.
- D-DD.166 approved 23 Nov (run-rate budget, DD3d.5). Answered: none else open.

## 6. Design and document alignment pass (specified for whoever picks it up)

State: NOT done. DD builders already swept moved figures from the design docs and most
go-to-market docs. The narrative documents and the mockup were deliberately left.
All Docs paths below are under `Docs/demo-sprint/product-direction-layer4/`.

- Narrative documents to realign (write-up, HTML versions regenerated after): `layer4-transformation-design`,
  `product-transition-and-roadmap`, `phase-plan-and-acceptance`, `demo-site-scenario-manifest.yaml`
  (manifest header notes are current to rev 16.23; the doc text around it is not).
- vNEXT mockup (`interactive-mockup-vNEXT/`), items recorded by builders for this pass:
  - Thika incident: chart series and "50-90 °C·min" in `screens.js` (71, 77-78; window text 51, 399,
    627; `portfolio.js` 18, 21). Use `/opt/assetecon/worlds/DD4a-0c5d5fab7b90/` readings: peak
    5.477 °C at 20:24, above 5 °C 20:08-20:32, 72 min without cooling, hand start 20:22.
  - Kobo kit strings (18 `screens.js`, 5 `screen-manifest`, plus 40 kW ×4 and 0.30 L/kWh ×3):
    declared kit is 36 kW generator, 42 Pylontech US5000 (191.5 kWh), 0.2917 L/kWh.
  - Kasarani: 7 missed departures, 840.00 penalties, 2 short a night, stopgap 225.00 (was 2 / 240 / 1 / 90).
  - Cold energy: 1304 kWh + 0.0554 kWh/crate-day model; October bills 315.26 / 354.27 / 422.72;
    Kirinyaga +14 %, repair +149.26 net over 12 months.
  - Kisiwa: 904 L October diesel becomes 903 L and 1,173.90 cost, result +1,696.10, candidate share
    20.7 / 16.1 / 0 / 10.6 % (owner-accepted); GEN-KS-02 evening load ~70 %, not 95 %; Mto 32 L.
  - Portfolio headline and fuel-vs-target literals: after DD3d-b (D-DD.163 and the owner-approved
    run-rate budget D-DD.166, about -$197 behind plan); do not align these before DD3d-b merges.
  - `gen_docs.cjs`, `CHANGE-REGISTER.md`, `fixture-mapping.md`, `derivation-register.md` rows, and
    the generated `index.html`/`screen-manifest` follow `tools/ia_gates.cjs` (110/110, ~95 min) and
    the two shot runs, with no NaN/undefined and "Not available yet" for missing figures.
- Order: (1) refresh NOW and SUMMARY, (2) after DD6, regenerate the docs' derived figures with the
  D-DD.30 chain, (3) realign the narrative docs, (4) the mockup with its gates, (5) owner walkthrough.
- Rules: `.ai/RULES.md` §10 (owner document brief: existing to new, mechanism to value, change on
  merit, person in loop, short and illustrated). Plain client language, no system vocabulary. Every
  figure tagged to its source path as the DD sweeps did. The check is `check_manifest.py`, at main's
  count.
