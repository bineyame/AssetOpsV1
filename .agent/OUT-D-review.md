# OUT-D final review: declared objectives and status

Reviewer: fresh Claude Reviewer (did not author the slice). Branch `task/OUT-D-declared-objectives` at 35578dd5, against
main 9ebb3d1c. Focus: U5, U6, dd22af4f and the whole slice. U1-U4 were reviewed earlier (`AssetOpsV1-plan2/.agent/
OUT-D1-3-review.md`, `OUT-D4-review.md`).

## Verdict: ACCEPT

There are no High or Medium findings. The four Low findings below do not block.

## What I verified

### U5: Portfolio Assure clause

`PortfolioOutcomes.tsx:180` `assureDetailText` matches the Architect's M2 ruling (decisions log, 2026-10-31) case by case:

| Unread | Count | Text | Code |
|---|---|---|---|
| 0 | n >= 1 | "targets declared at {n} {site\|sites}" | :184 |
| 0 | 0 | "no targets declared" | :183, the only path that gives it |
| > 0 | n >= 1 | "..., {u} {site\|sites} not checked" | :184 |
| > 0 | 0 or null | no clause | :182 |
| Summary not loaded or refused | | no clause | `summary` is null, so `n` is null |

- A backend without the field (an older backend) gives `undefined ?? null`, which omits the clause. "No targets" therefore
  appears only when every Site was read and none declared one.
- Backend `read.py`:
  - `objective_site_count` counts only the Sites whose board loaded and whose `objectives_read` is true. It is null when
    no Site was read.
  - `objective_sites_unread = len(sites) - read_sites`, so failed boards are included.
- Type `estateClient.ts:492-495` matches. The fixture `portfolioFixtures.ts` defaults are 0/0.
- The four new vitests cover (3,0), (1,0), (0,0), (2,1), (1,2), (0,1), (null,3) and a refused summary. Each one also runs
  the w1 vocabulary scan.
- The existing A6 expectations changed correctly: with no summary read, they no longer claim "no targets declared".

### U6: captures

`.agent/OUT-D-captures/shots/raw-evidence.json`, product sha b4e834f9:

- Overflow is 1425/1425 at 1440 and 358/358 at 390. The only console error is a favicon 404.
- The Portfolio Assure card reads "No verified result yet · targets declared at 1 site · no evidence gaps".
- The "Declared objective" lines carry Met, Missed or Not checked yet chips:
  - GreenHarvest: CC-1 and CC-6 Missed.
  - Depot: EV-1 Missed, "1 interrupted".
  - Kobo: three Not checked yet, with Assure "0 of 3 declared objectives met · 3 not checked yet".
- The lines read as plain language. I saw no codes on screen and no money on a leading measure. EV-2, the only VALUE
  measure, has no board line (R583).
- The two failed claims are not a timing quirk; see L1. The cold capture still proves what it must: board status
  `loaded`, 3 of 3 rows open, every declared line present, and a fully rendered screenshot (I viewed the 390 one).

### Explainer paragraph

- It is wording the Architect ruled on (L1-explainer), and it sits in the "About this view" dialog,
  `OutcomeBoard.tsx:60-61`.
- It carries an inline MOCK DEVIATION comment.
- `outcomeBoard.test.tsx` asserts it is the last paragraph.
- It reads well and states that the demo targets are not the customer's target. See L3 for the register wording.

### dd22af4f

- The fix is correct. `type(objectives).__dict__["_same_key"]` returns the `staticmethod` object, so the restore puts
  back a static method. The old code read the attribute, which unwraps it, and restored a plain function.
- I found no similar pollution in the D tests:
  - The only other class or module mutation is d5's `monkeypatch.setattr(mini, "mini_readings", spy)`, which pytest
    undoes.
  - The `b4._serve` and `_pin_kobo` helpers use `monkeypatch`.
  - d4's `replace_fake` mutates a per-test `Fake`.
  - d2 and d3_declare use local fakes.
- The patch-by-assignment in d3 store remains brittle. `monkeypatch.setattr(type(objectives), "_same_key",
  staticmethod(...))` would remove the class of bug, but that is a preference.

### Migration

- `0038_out_objectives` has `down_revision` `0035_w5_ev_work`.
- CC-M (`task/CC-M-combined-schema`) has `0036_cc_mini_contribution` and `0037_cc_trial_cost_comparison`, also from
  0035. The revision ids are distinct, so there is no clash. E adds the merge revision 0039, as ruled.
- Expect a textual conflict in the head-literal test files at E's merge: D sets them to 0038 and CC-M to 0037. That is
  E's work.

### Process

- Nothing is tracked under `var/`.
- The capture DBs are `*_outd_test` (inside the 2026-10-18 authorisation) and producer scratch `*_outd_audit*` (inside
  the 2026-10-24 extension). The README records them all as dropped.

## Checks I ran

| Check | Result |
|---|---|
| `pytest tests/test_out_d2_objectives.py tests/test_out_d3_declare.py tests/test_out_d4_board.py -q` (plan2 venv) | 66 passed, 1.28 s |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run src/estate/__tests__/estatePortfolio.test.tsx src/sites/__tests__/outcomeBoard.test.tsx` | 2 files, 52 passed (vitest ran in this worktree) |
| `tools\check-all.ps1` with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv | All 11 guards passed |

## Not verified by me

- The Postgres tests (d1, d3 store, d5 and the 20 head-literal files). The dispatch excluded them because the DB is in
  use.
- The full backend and vitest suites. I cite the implementer's runs:
  - `-Tier all` at eeef72a8, run `20261031-030148-43b8cd`: 4458 tests, 4455 passed, 3 failed (d5 pollution), 0
    skipped, 2295 s.
  - Rerun of d3 store plus d5 at dd22af4f, run `20261031-034147-0a63eb`: 4 passed.
  - Vitest at eeef72a8: 3531 passed, 3 known w1f4 failures.
- dd22af4f changes only that test file, so the full-run evidence still applies to the product code at 35578dd5.

## Findings

### L1 (Low, evidence accuracy): the cold "app rendered" failure is a deterministic predicate false positive, not timing

- **Where:** `.agent/OUT-D-captures/capture-outd.mjs:150`, inherited from the OUT-B/OUT-W tools. Packet
  `.agent/OUT-D-packet.md:98`.
- **What is wrong:** `READY` rejects any leaf `main p`/`div` whose text matches `/^Loading\b/`. On the cold board the
  contributor label "Loading and door records" ("Not available yet") matches, so the wait can never succeed on a cold
  Site. It runs out after 30 s, the 1.5 s settle follows, and then the measure and screenshot are taken.
- **Why it matters:** every cold capture will keep "failing" this claim. The packet, and the dispatch, describe it as a
  timing quirk, which hides a known false negative.
- **Fix:** tighten the predicate to the real loading copy, for example `/^Loading(…|\.\.\.)?$/`, or use a
  `data-loading` hook in the shared capture tool. Correct the packet wording.
- **Non-blocking because** the capture evidence shows the board loaded with 3/3 rows open.

### L2 (Low, packet accuracy): two Kobo datasets are reported as one

- **Where:** `.agent/OUT-D-packet.md:43-47`.
- **What is wrong:**
  - "MG-2 has 0 avoidable / 60 unclear minutes" comes from the D5 test, which uses the `b4._build_kobo` estate build.
  - The quoted capture text "0 min longer than needed on this day" comes from a different DB, the s501 owner
    walkthrough.
  - With 60 unclear minutes the code (`mini.py:397`) would render "60 min not yet clear on this day", which d4
    `test_mg2_unclear_minutes_are_not_checked_yet` pins. Both statements can be true only because the datasets differ.
- **Why it matters:** a reader comparing the packet with the code would suspect a copy bug.
- **Fix:** name the dataset for each Kobo fact.
- **Related readability note (preference):** "0 min longer than needed" beside a "Not checked yet" chip gives no
  reason on the line itself. The reason, an unsettled day, is only in the row's Unknown state. Leave it for the
  post-sprint copy pass.

### L3 (Low, register completeness): two deviations are not fully described in the register

- **Where:** `.agent/mock-departure-register.md:577` (R580) and `:583` (R586).
- **What is wrong:**
  - The explainer paragraph is said to "fall under R580", but the R580 row describes only the contributor line.
  - R586 does not mention the ", {u} sites not checked" variant or the omitted clause when Sites are unread.
- **Why it matters:** owner rule: every mock departure is registered.
- **Fix:** extend R580's "What is shown instead" with the "About this view" paragraph, and R586 with the unread
  variants.

### L4 (Low, preference): test-file tidiness

- **Where:** `frontend/src/estate/__tests__/estatePortfolio.test.tsx:11-13`.
- **What is wrong:** a `type` alias is declared between import statements, and the helper passes `answer as never`.
- **Fix:** move the alias below the imports and type the `withOutcomeSummary` argument.

## Residual risk not named in the packet

- An unread Site with `n >= 1` produces the longest Assure detail, "targets declared at 2 sites, 1 site not checked ·
  evidence gap at 1 site". It was not captured at 390. The card text wraps, so the risk is low.
- The "MOCK DEVIATION D2 (R453)" line visible at the top of the Site page is pre-existing (`operatorSiteTabs.tsx:153`)
  and not part of this slice.
