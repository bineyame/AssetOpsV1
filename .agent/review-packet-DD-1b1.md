# Review packet: DD-1b1 story-time Actions (READY for review)

Branch `task/DD-1b1-story-time-actions`, size 1.5. Rulings: DD1b1-R, R2, R3 in `.agent/build-sheet-DD-1.md` (R3 wins over R2, R2 over R).
Main (CH-6b3, f7c045bee) is merged in; backlog keeps main's rows plus BL-30..32 and BL-38 (renamed from BL-33).

## Outcome
Cold and EV story Actions are story-dated after their Finding (thread ACTION_IN_HAND), the whole-UTC-day story link lists the Action "Open" under Already in hand, Protect is Needs attention, the chain carries "Action agreed", and COH-3 evaluates real pairs. Objectives are recorded per Site at that Site's own first knowledge instant.

## Acceptance, with evidence
- Prepare-only clocks (`prepare_clock.py`, store override, story clock hooks), refused outside `assetops_polish_*` / `*_test`; unset behaviour unchanged: `test_dd1b1_prepare_clock` 17 pass; guard A passes (prepare_clock reads the DB name without a driver import).
- R2/R3 read fix: `read.py` passes `actions_to` = requested end when an event is found; `cold.compose`/`ev.compose` read `[actions_hi - WORK_WINDOW, actions_hi)` (both bounds from one end). Plans, incidents, visits keep `work_lo`/`hi`. Mini, Kobo, the Action index service and `k` untouched (`git diff main` over `backend/assetops_backend` touches only cold.py, ev.py, read.py compose, prepare_clock, objective store).
- Whole-UTC-day Cold/EV story links and collector windows (`story_links`, `chain_coherence.day_windows`); Kobo unchanged. `test_demo_combined_links`, `tools/checks/test_chain_coherence.py` pass.
- Per-Site objective instants (`objectives_instants`: Kobo S-29d 12:00, Cold S-26d 06:30, EV S-26d 07:00), each asserted before that Site's first built day; `demo_declare_objectives.py <url> <file> <site> <iso>` per Site.
- R3 root cause confirmed by test: the R2 read asked 32 days and the real `parse_index_request` refused it (`INVALID_WINDOW`), swallowed by `Reads.call`.

## Re-probe (R3), `.agent/DD-1b1-coh3-probe-r3.json`: PASS 49/49, 123 s, 1 tick, own routed `*_test` DB (dropped)
- coh3_pairs: 1 per Site (EV, Cold), all linked; 0 COH-3 findings.
- UTC-day boards: Finding in issues; Action row exactly "Open", no suffix; Cold Protect NEEDS_ATTENTION; `read_state` AVAILABLE, equal to the event-window value; `domain_action_index` failed on neither board (hook records failed reads by name; none failed on any board).
- Chain "Action agreed" for both Sites. Event-window boards: Finding shown, Action not listed (the rule, BL-38). Week board lists the Action for each Site.
- Cold read three ways on one DB: UTC day lists ACT-001 "Open"; event window shows the Finding (so `known_at` is not the cause); local day lists it "Open - linked finding outside this view" with Protect UNKNOWN.
- 0 thread events from the tick; `objectives_instants` resolved on real v3 for all 3 Sites; objectives declared end to end for Cold and EV (Kobo "SITE_NOT_IMPORTED" skip: probe builds no Kobo).
- Observation: the EV UTC-day and week boards list the Action row twice in `in_hand` (ACT-002, both "Open"); not a pass condition, not investigated. Owed to DD-1b2.

## Tests (own routed DB via conftest on base `assetops_test`; shared DB never reset)
- Scoped, 315 tests: `test_ch1b_*` (4 files), `test_ch6b1_r5_dated_lead`, `test_ch6b2_portfolio_cards`, `test_out_b3_cold_ev` (27, incl. real-parser L0s), `test_dd1b1_prepare_clock`, `test_demo_combined_links`, `test_chain_coherence`, host `test_s6_verification_replay`: first run after the merge 313 pass, 2 fail (`test_ch6b1_r5_dated_lead`, composer fake lacked `actions_to`); fake fixed, that file re-run 2 pass. Not re-run as a whole after the fix.
- Mutation: restoring `work_lo` as the lower bound fails 3 tests (both `actions_to` L0s and the real-parser L0). Earlier R2 mutation (drop `actions_to`) covered by the same `actions_to` tests. Not run: the DD1b1-R mutation proofs on the coh3 window test and the objective-store refusal (the refusal is covered by the prepare_clock tests, not mutated).
- Guards A, W, N pass; V (110 screens) passes; M 14 pass.
- Regression: exact event window and no-event reads are byte-equal by L0 (arguments `hi-31d, hi`); week boards now list a post-event Action (probe). No other board test moved in the scoped set. Kobo: mini branch and `mini.py` not in the diff vs main; `test_s6_verification_replay` passes.

## Not run (barred or deferred)
Full backend suite, check-all, demo prepare, baseline build, `test_demo_combined_postgres`, add-day run (by construction; DD-1b2), frontend suites (no frontend change), layout evidence (none).

## Owed to DD-1b2 (R2 section 6, R3 section 6)
- Finish rows needing the Action read the day window.
- Finish assertion that `domain_action_index` is not a failed read on Cold and EV story-day and week boards.
- List/avoid/state any in-app link with an exact event window that the script follows (it lists no Action, by rule).
- Reconcile COH rules on the new Cold/EV day windows with `expected-today.json`.
- The EV board's duplicated Action row (observation above).

## Residual risk / user review
Week, month and Portfolio boards with an event now list post-event Actions and drop Actions older than 31 d before the window end (intended). USER_REVIEW: none required; the Architect rulings cover the behaviour change.
