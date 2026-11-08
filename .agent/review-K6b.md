# Review: DIESEL-K6b, the fuel after-check (`fuel-residual-within-band-1`)

- Reviewer: Claude (Opus), independent first review; did not author the slice. 2026-11-08.
- Branch `task/DIESEL-K6b-fuel-verification` at `ccac8bcc8`, base `9d7641f9a`. Main is now `903ee5902`; the only
  change since the base is one `.agent/followups` line, so there is no code drift.
- Spec: build sheet DIESEL-1 §9m.1, §9m.4 (R3m), §9m2 (R3m2), §8.2 H1-H5. Packet: `.agent/review-packet-K6b.md`.

## Verdict: ACCEPT

There are no High or Medium findings. I found four Lows. None blocks the merge; each can be fixed on the branch or
put on the follow-up list. The family, the honesty rules, the links and the board entry match the card. The mill
path is byte-equal to the first-commit pins. Kobo, Cold and EV are untouched. The tests fail when the code is
broken: 8 of 8 mutations were caught, all re-run by me.

## Checks I ran (what I saw)

| Check | Result |
|---|---|
| Import resolution (plan2 venv, worktree PYTHONPATH) | `assetops_backend` and `demo_combined_rows` resolve into `AssetOpsV1-k6b` |
| L0 + adjacent: `test_k6b_fuel_verification_rules`, `test_out_b2_vocabulary`, `test_ch9b1_origin_readers`, `test_k6a_fuel_action_origin`, `test_ch5a2_refs` | 129 passed |
| Adjacent non-DB board/mill contracts: `test_ch5a1_board_contract`, `test_ch5a2_contract`, `test_ch6_contract`, `test_ch6b2_portfolio_cards`, `test_ch9b2_midday_plan`, `test_ch9b3_mill_verdict`, `test_mb1_opportunity_board`, `test_mb1_thread_line`, `test_out_b1_board` | 234 passed, 1 failed: `test_board_imports_only_outcomes_and_stdlib` (pre-existing, see below) |
| L2 `test_k6b_fuel_verification_postgres.py` on `assetops_k6_test` (harness clones; 3.26 GB free before) | 6 passed, 28 s. Includes item 5: the mill outputs equal the first-commit pins `k6b_mill_pins.json` |
| `test_mb1_site_actions_postgres.py` + `test_k6a_fuel_action_origin_postgres.py` on `assetops_k6_test` (3.19 GB free before) | 8 passed, 27 s |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run fuelVerification.test.tsx routeRefs.test.ts` | 76 passed (13 + 63). Vitest did run in this session, unlike the sandbox failure the standing brief predicts |
| `check-architecture.ps1`, `check-agent-workflow.ps1`, `check-navigation-truthfulness.ps1` (no `-ExecutionPolicy`) | see "Guards" at the end |
| Literals vs §9m.4 | I exec'd the spec's two code blocks (the constants and the client literals) and compared each name to the module's values: 0 mismatches over 21 literal names and the constants |

**Not run by me:**
- the full suite (forbidden);
- `check-all.ps1`;
- the 18-file adjacent Postgres/golden batch (I ran only the two files above);
- `test_w301_estate_golden_postgres` (not re-run; already logged as main drift, and it does not touch a K6b path);
- layout evidence: the packet records it honestly as `not run` with its blocking precondition (no persisted K6b
  dataset). K8's all-26 recapture owes it.

## Mutations, re-run on a scratch copy (repo files untouched; `git status` clean after)

The scratch copy of `assetops_backend` sat first on the path, and pytest ran from the scratch directory, so the
mutated package was the one imported. A first attempt run from `backend/` imported the worktree package instead,
because pytest puts the working directory first on the path. Every mutant "passed" on that run, so I discarded it.
After the fix:

| Mutation | Caught by |
|---|---|
| M1: the choice also filters on `passes` (choose by result) | test_2, test_3 band/gap, test_3 short/closed, test_6 (4 failed) |
| M2: `closed` uses `<` instead of `<=` | test_3 short/closed |
| M3: the gap ignored in `passes` | test_3 band/gap, test_3 short/closed, test_6 |
| M4: the FUEL_BALANCE branch removed from `action_wire_ref` | test_7 filter, test_8 refs |
| M5: `fixed_line` None in the wire head | test_5 (both), test_9 KIS-5 pass |
| M6: `*fuel` dropped from the `_assure` merge | test_7 board entry |
| M7: a 1e-5 L tolerance on `residual_low` | test_3 band edges |
| M8: `value` set non-null | test_5 (both), test_9 KIS-5 pass |

The L2 read-back check (`after == before` once a chosen night is revised to UNEXPLAINED) is not vacuous. A summary
that recomputed live would choose the revised night, give INEFFECTIVE, and fail that check.

I did not run a frontend mutation. The frontend test's added wait (`loadedPage`) waits for a terminal observable:
the page root `[data-fuel-state]` or an alert. That is a real async boundary: SiteScoped loads the site first, then
the fuel read resolves. It does not mask a flake. A wrong alert would still fail the assertions that follow.

## What I checked, and how it stands

1. **Night selection and the honesty rule.**
   - `later_nights`: the first night whose 18:00 local start is at or after `effective_from` (`<` pushes to `d0+1`).
     There are 14 candidates.
   - `complete`: `state != NOT_ASSESSED` and `unknown_slots == 0`. A gap does not affect it.
   - `passes`: exact `Fraction` band, checked first, then `gap_minutes == 0`.
   - `assess` picks the first 3 COMPLETE nights in date order, chosen by grade only, with no tolerance and none fitted.
   - Verdicts follow step 3: INEFFECTIVE names the first failing night; VERIFIED needs 3 chosen; INCONCLUSIVE needs
     the 14th night ended. Otherwise NOT_JUDGED, and nothing is stored.
   - `effective_from` = the earliest COMPLETE `work_event` over linked cases (the mill's statement). L2 asserts the
     column equals the COMPLETE `occurred_at`.
   - A stored verdict is read from `details`, never recomputed (L2 read-back).
   - Correct.
2. **Wording.**
   - All literals are verbatim from §9m.4 (checked by program) and H1 matches §8.2 byte for byte.
   - `fixed_line` is in the wire head, so it appears in every state, including NO_PLAN and NOT_JUDGED.
   - `value` and `cost_check` are always None. No money key appears (L0 test 5, L2 test 3, KIS-5).
   - The AST check shows no money import. H4 and guard V scans are clean (L0 test 4, `test_out_b2_vocabulary`, the
     frontend vocabulary scan).
   - Deviation 4: see L3 below.
3. **Links.**
   - `refs.FUEL_VERDICT`: `href_for`, `fuel_verdict_ref`, the frontend `routeFor`, `siteFuelVerificationHref`, the
     route in `App.tsx` and the `linkRefs` parser are all present.
   - `action_wire_ref`: FUEL_VERDICT for `action_domain == FUEL_BALANCE`, DOMAIN_VERDICT for the mill (that branch
     comes first and is unchanged), ACTION for Cold and MINI_TRIAL (L0 test 8).
   - The K6a residual is closed: the thread detail's fuel Action entry carries FUEL_VERDICT (L2 test 4).
   - The other `refs.action_ref` callers (`estate/index.py:204`, `estate/portfolio.py:291`, `site_outcomes/mini.py:789`,
     `cold.py:224`) read W1 or Cold rows, not a FUEL_BALANCE `domain_action`.
   - `site_index` flip: matches §9m2 exactly, and lineage False gives href None.
4. **Unchanged surfaces.**
   - `_SITE_ACTIONS` gains only the `action_domain` scalar subquery. The row set and order are unchanged.
   - The mill methods, `DOMAIN_PLAN_COLUMNS` and the mill wire are untouched. The L2 pins are equal.
   - `fuel_verdict_actions` keys on DOMAIN_INTENT + FUEL_BALANCE, so a Kobo, Cold or EV board gets an empty tuple.
   - `_verified_values(reads, ports, actions, opp)` keeps its signature and its call site; both are pinned by L0
     test 7.
   - The Assure entry reuses the `OpportunityActionFact` rendering branch. `fuel` is keyword-only, so existing
     positional callers are unaffected.
5. **Deviation 2 (the third port, `fuel_plan_context` filtered on the fuel rule): correct and necessary.**
   - Without `AND rule_id = 'fuel-residual-within-band-1'`, a mill Action that already holds a mill plan would have
     `ctx["plan"]` set. `freeze_fuel_plan` would then return `200 replayed` with the mill plan (read through
     `FUEL_PLAN_COLUMNS`) before the domain check could give 409.
   - The filter also lets `evaluate_fuel_plan` answer NO_PLAN for a mill Action (L2 test 1_3 asserts both).
   - `site_visits` as a third `VerificationPorts` field is the least invasive wiring: the global work read is used
     for `case_operational_records`, the composition imports composition, and the field defaults to None.
   - Returning `origin_window_id` and `site_code` from the context saves a second read and does not change behaviour.
6. **Register R709.**
   - Main and every DIESEL branch end at R708 today. K5's tip (`1e3ef1055`) adds no register row, so nothing collides
     now.
   - Risk: if K5 adds a row for its MD-FUEL-K5-* labels before merging, it will likely also take R709.
   - Whoever merges second renumbers. On K6b that means the register row and `data-mock-deviation="R709"` in
     `SiteFuelResidualVerification.tsx:156`.
7. **Pre-existing failures.**
   - `test_out_b1_board.py::test_board_imports_only_outcomes_and_stdlib` **confirmed pre-existing on main**. I ran it
     read-only in `AssetOpsV1-plan2` at `903ee5902`, without a DB: it fails with `AssertionError:
     assetops_backend.chain.vocabulary` (`board.py:14-15` on main).
   - K6b's `board.py` diff adds no import.
   - The 6 `test_w301_estate_golden_postgres` failures were not re-run (see above). The claims they cover are not on
     a K6b path.

## S-b4: file by file

| File | Decision | Reason |
|---|---|---|
| `backend/assetops_backend/work/site_index.py` | Not out of list | §9m2 adds it to K6b's list explicitly; the edit is the one line specified |
| `backend/tests/test_k6a_fuel_action_origin.py` | Confirm | §9m2: "Its L0 test flips the K6a assertion below to that address". The edit is the flip plus a lineage-False line |
| `frontend/src/shell/__fixtures__/route-refs.json` | Confirm (forced) | `test_ch5a2_refs.py:21` asserts that the fixture kinds equal `refs.KINDS`; §9m.4 says FUEL_VERDICT "joins every validator the kinds list feeds" |
| `frontend/src/shell/__tests__/routeRefs.test.ts` | Confirm (forced) | `:15` pins the sorted kind list; same reason |
| `frontend/src/test/linkRefs.ts` | Confirm (forced) | The card's frontend test demands "the `linkRefs` round-trip"; the parser had no FUEL_FINDING or FUEL_VERDICT pattern. Test helper only |
| `backend/tests/test_ch9b1_origin_readers.py` | Confirm | Allowlist counts for the new origin readers (`postgres_action_store.py` 15->19, `verification.py` 5->8, new `fuel_verification.py` "both"/7). These are count updates for code the card mandates, not a behaviour change (so not S-b5). `fuel_verification.py` is "both" because it writes `origin_opportunity_revision_id: None` beside the Finding origin |
| `.agent/mock-departure-register.md` (R709) | Confirm | The mock-deviation-label guard refuses an unknown register id (`tools/checks/fixtures/mock-deviation-labels/unknown-id.tsx.txt`); the page's deviation line needs a registered id. Collision risk noted above |
| `.agent/review-packet-K6b.md` | Confirm | Workflow artefact, required |
| `backend/tests/fixtures/k6b_mill_pins.json` | Not out of list | "their pins module" (item 5 of the list) |

There is no Kobo, Cold or EV served byte or golden change, so S-b4's second clause does not fire.

## Findings

### L1 (Low): an evaluable but unevaluated check reads "Not judged yet" with no outcome sentence
- Where: `backend/assetops_backend/actions/fuel_verification.py:377-380` (`fuel_summary_wire`, the live branch) and
  `assess` `:146-154`.
- What: once 3 COMPLETE nights are known (or the look-ahead has closed) but `evaluate_fuel_plan` has not yet run (the
  evaluation is explicit, with no tick stage), `live["decided"]` is True. `not_judged_text` is then None, so the
  wire is `state` NOT_JUDGED with `sentence` None and `not_judged_text` None.
- Failure scenario: the K7 story completes the third after-night, and the page is opened before the evaluate step.
  The page shows the headline "Not judged yet" and cards such as "3 of 3" and "Fuel accounted for 2 of 3 nights".
  If a night failed, a row reads "Outside the margin". The Outcome evidence panel holds only the H1 line, with
  nothing saying why it is not judged.
- Why it matters: this is an honest-state gap, not a false claim. Nothing claims a verdict, but the page gives no
  reason for the missing verdict.
- Fix (Architect's call; no new literal is needed if acceptable): either show the cards and night rows from the live
  result only when `not decided`, or let the Architect name a literal such as "Not judged yet: the check is ready
  but not yet judged". The spec did not foresee this state, because it assumed the live result always gives
  LATER_TEXT.

### L2 (Low): L2 test item 6 (board goldens) is delegated, not written
- Where: `backend/tests/test_k6b_fuel_verification_postgres.py` has no test 6. §9m.4 L2 item 6 says "Kobo, Cold and
  EV board goldens are byte-equal. Must fail if `_SITE_ACTIONS` drops a row or reorders."
- Failure scenario: a later edit to `_SITE_ACTIONS` that reorders rows would be caught only if someone runs the
  adjacent golden files. The packet relies on those (ch5a1/ch5a2/ch6/ch6b2, run in the builder's 18-file batch;
  I re-ran only the non-DB contracts and `test_mb1_site_actions_postgres`).
- Fix: name, in the packet's acceptance row, the existing golden test that fails on a dropped or reordered
  `_SITE_ACTIONS` row, or add a thin L2 test 6. This is an evidence gap rather than a code defect.

### L3 (Low): deviation 4. The Owner cell is omitted when `owner_label` is null, though a "Not assigned" precedent exists
- Where: `frontend/src/sites/SiteFuelResidualVerification.tsx:99` (Owner cell) and `:142` (Activity panel).
- Judgement on deviation 4:
  - **Site-visit row omitted:** spec-sanctioned (§9m.4: "If it is absent, the field is None and the row is
    omitted").
  - **Activity panel omitted when no COMPLETE case is linked:** the spec types `activity` as `{...} | None` and is
    silent on rendering. Omitting it is acceptable; there is no activity to show, and "Not checked yet" covers the
    cards.
  - **Owner cell omitted:** `domain_action.owner_label` is nullable (`0033_w5_cold_work.py:46`). The Cold and EV
    domain-Action pages already state the gap as "Not assigned" (`coldWorkPresentation.ts:31`,
    `evWorkPresentation.ts:32`). The project rule is to state missing data rather than hide it.
- Failure scenario: a fuel Action created without an owner shows a header with no Owner cell, while the same Action
  type on Cold or EV shows "Owner: Not assigned".
- Demo impact: nil if K7 sets an owner.
- Fix: render `owner_label ?? "Not assigned"`, reusing the existing literal (no new copy), or keep the omission and
  record it as a preference in the packet.

### L4 (Low): KIS-5 / KIS-10 DB plumbing passes string ids to UUID-typed store methods, untested until E3
- Where: `tools/demo_combined_finish.py`, inside `_kisiwa_fuel`: `fuel.window(t, s, p["window_id"])` and
  `fuel.windows(t, s, plan["basis"]["tank_asset_id"], ...)` pass `str`. The service passes `UUID(...)`
  (`verification.py`, `_fuel_windows` / `fuel_summary`).
- Failure scenario: if the fuel store's statements bind these as typed text rather than as unknown, Postgres refuses
  `uuid = character varying`, and KIS-5 errors at E3 rather than checking. It works today only if the driver leaves
  str untyped.
- Fix: wrap both in `UUID(...)` as the service does. The packet already lists "KIS plumbing untested until E3" as a
  risk; this is the concrete instance.

## K5 overlap: what whoever merges second must reconcile

K6b's FUEL_FINDING items are byte-identical to K5's (`refs.py` docstring line, the `KINDS` entry, the `href_for`
branch and `fuel_finding_ref`; `chainRef.ts`; `operatorSiteRoutes.ts` route constant, href builder and `routeFor`
case; `linkRefs.ts` pattern; the two `route-refs.json` rows). Expected textual conflicts:

- `backend/assetops_backend/chain/refs.py`: the `KINDS` tuple line (K5 ends `"FUEL_FINDING")`, K6b ends
  `"FUEL_FINDING", "FUEL_VERDICT")`) and the docstring and `href_for` blocks. Keep one FUEL_FINDING copy plus
  FUEL_VERDICT.
- `frontend/src/shell/__tests__/routeRefs.test.ts`: the kind-list line, which must end with both kinds. Keep K5's
  extra `routes a FUEL_FINDING ref` test.
- `frontend/src/shell/__fixtures__/route-refs.json`, `frontend/src/test/linkRefs.ts`, `frontend/src/sites/chainRef.ts`,
  `frontend/src/shell/operatorSiteRoutes.ts`: one copy of the shared items, plus K6b's FUEL_VERDICT additions.
- `frontend/src/App.tsx` and `frontend/src/shell/SiteAnalyticsFrames.tsx`: both add imports and a frame at the same
  spots. Keep both: K5's `SiteFuelFindingFrame` route and K6b's `SiteFuelVerificationFrame`.
- `backend/tests/test_out_b2_vocabulary.py`: both append to `_constants()`. Keep both blocks.
- The register: R709 renumbering, if K5 adds a row first.
- Until K5 merges, the verdict page's Source link (FUEL_FINDING) points at a route with no page. The spec accepts
  this (Kisiwa is opt-in until K7-F).

## Residual risk not named in the packet

- `_Lazy` (`actions/composition.py`) is not thread-safe. Two concurrent first fuel reads on the API's threadpool can
  build two engines, and one leaks. This is minor, beside the packet's "never disposed" note.
- `fuel_summary` raises 503 (`_fuel_ports`) for a NO_PLAN fuel Action when the ports are missing, rather than
  serving the NO_PLAN state. Ports are always wired in production, so this is noted only.
- A WorkStoreUnavailable from the `site_visits` port propagates out of `fuel_summary`, failing the whole page read
  instead of omitting the site-visit row.

## Guards

- `check-architecture.ps1`:
  - The first run had no `ASSETOPS_GUARD_PYTHON` set. It exited 1 because the chain-structure guard found no
    interpreter (the worktree has no `.venv`). It also printed two rule-8 "vacuous" notes about
    `financials/adapters/postgres_consequence_store.py`, a file K6b does not touch.
  - The re-run with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv printed "Architecture check passed." and exited 0.
- `check-agent-workflow.ps1`: passed.
- `check-navigation-truthfulness.ps1`: passed (this covers the new route).
