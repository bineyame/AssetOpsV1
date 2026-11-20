## CH6b3-R: rulings on the CH-6b3 pre-flight (Architect, Claude, 2026-11-06)

Pre-flight: `.agent/CH-6b3-preflight.md` at `beecf4309`. Binding checked: Claude (ROLE_CONFIG, owner 2026-10-27). **CH-6b3: 1.0 → 1.1** (Q4b only; Q1-Q3 stay inside 1.0). No owner question. No screen departs from `frontend/mockups/v70`, so no new MOCK DEVIATION.

**Three pre-flight claims were wrong. These rulings correct them:**
1. PERIOD board nodes and summary nodes do not name the same days (Q1).
2. `?date=` is ignored for Cold and EV, so the per-date read is wrong for them (Q3).
3. `count.open_threads` counts threads, not Sites, so it cannot feed "priority sites" (Q4b).

**Stop rule, for every comparison below.** A new COH-17 or COH-18 finding on the clone or on L3m means stop and report: window, Site, field, both values, and the files. Do not tune, do not edit the code, and do not add an `expected-*.json` entry. The Architect rules on it. The one exception is the Q1 information list, which is its own rule.

### Q1. COH-17 field table (demo-critical: these are the numbers on the page)

All rows are estate windows only (`week`, `S`, `month`), under the existing equal-Site-set rule. Chain = `chain_estate.{w}`, summary = `summary.{w}`, board = `board_summary.{w}.{code}`, Portfolio = `portfolio.{w}`. Chain `sites[].code` matches summary `sites[].site_code`. Every row except the first is gated on a new manifest stamp, `full_claims: true`, so older fixtures are not judged.

| # | Claim | Compared | Rule |
|---|---|---|---|
| C1 | Count (existing) | chain `counts` vs Portfolio `summary.claims`; chain vs `findings_all` | Value, basis, text. Portfolio takes all four backend keys. |
| C2 | Count | `cards.PROTECT_ASSET.claim` vs chain `counts["count.sites_disrupted"]`; `cards.ASSURE_PERFORMANCE.claim` vs chain `counts["count.verified_results"]` | Value, basis, text |
| C3 | Cards | chain `cards` vs summary `cards` | Whole-dict equality |
| M1 | Money | chain `money_total` = summary `money_total` = `cards.GROW_REVENUE.claim` | Whole-dict equality |
| M2 | Money sum | `money_total.value.amount` vs the sum of `Decimal(money2(c.value.amount))` over chain `sites[].earnings[l]`, for `l` in `INCOME_LABELS`, where `c.value` has an amount | Decimal equality, as `money2` strings. One currency only. |
| M3 | Money, mixed | More than one currency among the contributors | `money_total.value` must be null |
| M4 | Money, named | Every earnings claim | One `money_total.lines` entry starts with "{site name}: " |
| M5 | Money, shown | `cards.GROW_REVENUE.parts.income` | Equals `" · ".join(money_total.lines)` when `lines` is not empty |
| M6 | Money per Site | `sites[].earnings` chain vs summary | Whole-dict equality |
| V1 | Verdict | chain `rows[cat].{state, state_label, lead}` vs summary row `{state, state_label, lead_outcome}` | Every Site. Chain's field is `lead`; summary and board call it `lead_outcome`. |
| V2 | Verdict | summary row `{state, state_label, lead_outcome, headline}` vs board row | Every Site, every window. `headline` is added because "Why?" reads it. |
| V3 | Nodes | chain `rows[cat].nodes` vs summary row `nodes` | Whole-dict equality, every Site |
| V4 | Nodes | board row `nodes` vs summary row `nodes` | Whole-dict equality, **mini Sites on the `S` window only** |
| L1 | Legacy (Q4b) | `summary.verified_resolution_count` = `progress.verified_resolution_count` = chain `counts["count.verified_results"].value`; `summary.priority_site_count` = number of chain `sites[]` with `threads.open + threads.in_hand > 0` | Exact |

**Import, do not copy:** `money2` and `INCOME_LABELS` from `chain.vocabulary`, in the manner of `_coh7a_window`.

**Trap in the tool.** Its `CLAIM_KEYS` must gain `count.sites_disrupted`, but `CLAIM_KEYS[2:]` feeds the Findings comparison at `chain_coherence.py:1118`. Findings carries only `count.opportunities` (`estate/index.py:377`). Replace that slice with `("count.opportunities",)`.

**PERIOD board nodes are not compared. The pre-flight's "same days" premise is wrong.**
- The composers receive the contained event's window (`site_outcomes/read.py:384-388`, CH6b1-R3), and cold and EV build nodes over `local_days` of it (`domain_nodes.py:17-19`).
- With no contained event, `local_days` of a UTC-midnight pair in Addis names one day more than `window_days` (CH6b1-R Q1).
- The summary re-evaluates over `window_days` (`_window_parts`). So the two frames differ by design in both cases, and a strict comparison would fail on correct code.

**In its place, an information rule (demo-critical, because the presenter must know it; not a failing rule).** Add `info_coh17_period_nodes` to `INFO`. For each non-mini Site, window, category and part (`kpi`, `earnings`, `potential`), it lists board and summary `text` and `days` wherever they differ. The table goes in the packet, so the walkthrough knows which Site boards read an event rather than the whole window.
- **What the builder does:** where a part's `days` objects are **equal** and its `value` or `text` differs, that is not explained by the frame. Stop and report it, as the stop rule says.
- Every other difference is listed, not judged.
- Mini on `week` and `month` is not compared, by design (CH6b1-R Q1, Q4).
- A strict comparison on a shared frame is **BL-33**.

**Tests**, in `tools/checks/test_chain_coherence.py`, on a new `clean_full` bundle:
- It passes clean.
- A planted break fails, one per row: C2, C3, M1, M2 (one Site's amount), M3, M4, M5, M6, V1, V2, V3, V4, L1.
- A planted PERIOD node difference with unequal `days` produces no finding, and appears in the info list.
- An unstamped bundle has none of these rows judged.

### Q2. COH-17 "why" (demo-critical: "Why?" must trace the number, CH6b2-R Q2b)

Accepted.
- **Collect:** `why_estate.{w}.{category}` from `GET /api/estate/chain/why` with `from`, `to`, `category`, for the four `CATEGORIES` and three estate windows: 12 reads, under `full_claims: true`. The route is absent from today's bundle (checked: `Collector.estate` has no such fetch).
- **W1.** Per Site, per category: why `sites[].text.say` = the summary row's `headline or state_label`.
- **W2.** PROTECT only, when `count.sites_disrupted.value` is not null: the number of summary Sites where some `text.comes_from` line starts with `"{site_name or site_code}: "` equals that value. Match on Site names, so the early-warning line never counts.
- **Not compared:** the "{kWh} kWh × {price}" line. It belongs to the board day on a mini Site and carries no total. Stated as a Known Deviation in the packet.
- **Tests:** a planted wrong `say` fails W1. A planted extra Site line fails W2. The early-warning line alone gives 0.

### Q3. COH-18 (demo-critical: "on the days checked" is shown to clients)

The sum rule is accepted; **the read form is overridden.** `board_window` (`outcome_api.py:123-133`) reads `date` only for mini. On Cold and EV it ignores it and falls back to the overview's default window, so `?date=d` would judge the wrong days. The range form is valid for them: PERIOD keeps the requested window on the body, and `local_days` of a UTC-midnight pair always contains every `window_days` date, in any time zone. `MAX_WINDOW` is 31 days and the month window is exactly 31.

**Collector** (in `Collector.estate`, estate windows only, after the summary, using `summary.sites[].domain`):
- **Mini Site:** for each `window_days` date of each window, deduplicated: `chain_day.{code}.{d}` from `/api/sites/{code}/chain?date=d`.
- **Cold or EV Site:** `chain_span.{w}.{code}` from `/api/sites/{code}/chain?from&to`, with the estate window's bounds.
- Pass an existing estate window id as the request's `window`, so `bundle.windows[...]` lookups hold. Do not name these bodies with a `board` prefix (COH-9b reads those).
- Manifest stamp `day_bodies: true`.
- **Cost:** about 31 + 6 = 37 reads on polish (not 93), about 31 per L3m variant.

**Rule `coh18_day_grades(bundle, gap_days=None)`**, on the stamp, for each estate window:
- `dates = window_days(at(from), at(to), None)`. All three windows are UTC midnights, so no time zone is used. Import it, as `_coh7a_window` does.
- **Grade of (Site, d):** the entry of the Site's body `days[]` whose `day == d`. Not `days[0]`. No entry is a finding.
- **R1.** Tally the grades. Chain `sites[].days` must equal the tally on `requested, expected, complete, partial, low, no_data, not_expected, pending`. `expected = requested - not_expected`. `enough_data_days` is left out: a day grade cannot derive it and no screen shows it. A null `days` is a finding.
- **R2.** Each of `counts[*].days` must equal the Site tallies summed over `CLAIM_DAY_KEYS`.
- A non-200 day read is COH-0's, and the stop rule applies.
- **Out:** node and earnings `days` and day windows (**BL-34**). Grow's own days line is proved by L2m (Kobo) and L0 (Cold and EV).
- **L0 tests:** a planted wrong-day mapping fails R1 (the sheet's test), a wrong count `days` fails R2, a missing date entry fails, and an unstamped bundle is not judged.

### Q4a. `gap_days` and the CHECKED_DAYS assertion (demo-critical)

Accepted. The sheet's wording is replaced by this, because L3m is Kobo only and the `states` set lacks D6-D9.
- **Fixture:** `expected-mechanism.json` gets `gap_days: [{"site_code": "KOBO-001", "day": "<D7 date from SPEC>", "gap": "GAP-K7"}]`. `expected-today.json` gets no such key, so only R1 and R2 run on polish.
- **Plumbing:** `load_gap_days(path)` returns the list or None. `check(..., gap_days=None)` passes it to COH-18, as it does `threads` for COH-10. The CLI loads it from `--expect`.
- **R3 (only with `gap_days`).** A built day is a graded day that is not `NO_DATA` or `NOT_EXPECTED`. Every built day not listed must be `COMPLETE`.
- **R4 (only with `gap_days`).** A CHECKED_DAYS basis is allowed only in a window that holds a listed gap day or a `NO_DATA` day for that Site (for a Site-level claim) or for any Site (for an estate claim). It checks `counts[*].basis`, `count_basis(sites[].days)`, `sites[].earnings[*].basis` and `money_total.basis`.
- **Limit accepted:** a day built with no readings cannot be told from an unbuilt one. The MD-0 tests own that case, and the packet states it.
- **L0 tests:** a built PARTIAL day not listed fails R3 and passes when listed; a CHECKED_DAYS claim in an all-COMPLETE window fails R4 and passes with a `NO_DATA` day. With no `gap_days`, neither is judged.

### Q4b. Legacy fields (demo-critical: "None confirmed" beside "Fixes confirmed · 1" contradicts itself on one page)

Checked: `EstatePortfolio.tsx:460,537,796` render them beside the claims. **Option A is accepted in aim, overridden in form. +0.1.**
- **Why not as proposed:** `count.open_threads` sums threads across Sites (`chain/claims.py`), so "{n} priority sites" fed from it would be false. Its text also drops the mock's phrase (v70 `index.html:284`).
- **Fix on the server, in `estate/portfolio.py`.** After `counted = self._claims(...)` (`:852`), and only when `self.count_claims is not None`:
  - `verified_resolution_count` = `counted.claims["count.verified_results"].value`, in both `prog` and `summary`;
  - `priority_site_count` = Sites with `t["open"] + t["in_hand"] > 0` in `counted.threads`, or None if any entry is None;
  - `counted is None` gives None for both. The browser then shows its existing "Unknown" and "Not assessed".
  - With no `count_claims` wired, the `thread_progress` values stay, so unit tests of that path hold. Deleting it is **BL-35**.
- **Why in_hand counts:** a Site with a fix in hand still needs attention until it is verified, and `count.open_threads` already counts it. So priority Sites > 0 exactly when open threads > 0.
- **Frontend, one line, `EstatePortfolio.tsx:796`:** "1 priority site" in the singular, as the neighbouring pulse items do. The same phrase, so not a mock departure. `:460` and `:537` are not edited.
- **Tests:**
  - L0 in `backend/tests/test_w303_portfolio_api.py` with a fake `count_claims`: both fields follow the claim, in both places; `counted` None gives null.
  - One vitest in `estatePortfolio.test.tsx` for the singular.
  - COH-17 row L1 on real bodies.
- **Scoped runs:** `test_w303_portfolio_*`, `test_ch3_rows.py`. A changed number in `test_w303_portfolio_comparison_postgres.py` is listed old → new. If a test shows the claim means something different from the field, stop and report.
- **Packet:** re-read the values from this head; CH-5a's "1 against 0, 0 against 1" predates the CH6b2-R2 lifecycle cutoff. List "Fixes confirmed" and "priority sites" old → new per window. Confirm each change from the thread events (`cause_known_at` against the window's cutoff). If the events do not explain it, stop and report (CH-5a `:691`).

### Q5-Q9: accepted as written, with one correction

- **Q9.** §B6 also says "L2m asserts D12/D13 eligible". No such assertion exists in `test_ch6b_estate_postgres.py`. The acceptance is only that the order line is recorded, so **no test is added** (**BL-34**). The §B6 line cites the L3 Kobo Potential value. If that value is not from CH-9's daylight study, stop and report.
- **Q6** applies to the new rows: `full_claims` and `day_bodies` each need compared > 0.

### Acceptance additions

The CH-6b3 entry and the Scope cut stand, with these changes:
- COH-17 means the table above; COH-18 means R1-R4.
- L3 clone: 0 new. L3m: 0 unexpected. Each report carries `{compared, skipped}`.
- The packet carries the PERIOD information table and the Q4b old → new list.
- **Backlog added:** BL-33, BL-34, BL-35 (not demo-critical; reasons in `.agent/backlog-post-demo.md`).

## CH6b3-R2: KD-3b, the four test failures and the Q4b table (Architect, Claude, 2026-11-07)

Input: `.agent/review-packet-CH-6b3.md` at `6bc8acfa1`. **CH-6b3: 1.1 → 1.3** (the four tests 0.1, the drained clone 0.1). No owner question. No screen changes. Written for a fresh Sonnet builder: do steps 1-5 in order, in this worktree, on this branch. These rulings come from reading code and the bundles on disk; nothing was re-run.

### KD-3b: not a product defect. The bullet is restated, and one measurement is added

**Cause on `mechanism_db()`, from the code.**
- That database has no Performance comparison report (Coordinator note, `build-sheet-DD-1.md:462`). So `performance_gate` is closed (`main.py:401-411`).
- `dispatch` then raises (`site_outcomes/read.py:255`, `_open`), and `finding_index_gate`, built on the same gate (`main.py:556`), closes too (`read.py:238`).
- `dispatch is None` makes `base` False (`mini.py:422`), so every outcome reads UNKNOWN / PRODUCER_NOT_SETTLED, the board reads PARTIAL and "Generator use" reads "could not be loaded". With the Finding index closed, the board has no heads and so no thread lines.
- **D13's chain omitting the generator thread is by design and separate:** `threads_of` lists a thread only with an occurrence or an event in the window (`_in_window`). D13 has neither.
- The L2m bullet can therefore never hold on this data. It is a **wrong bullet on Kobo-only mechanism data**.

**The real question is a different finding: the L3 polish clone also reads Optimize UNKNOWN on every Kobo day, for another reason.**
- Bundle `var/ch6b3_bundle`: all 10 built Kobo days have `critical_served` PENDING, so `day_settled` is False and all four Kobo rows read UNKNOWN on every board, with "No fuel cost estimated for this day".
- CH-9's packet (`review-packet-CH-9.md:311`) already names this: after migration 0049, `critical_served` reads PENDING until the queued service work drains. The L3 steps (create, backfill, settle) never drain it.
- `tools/demo_combined.py` `prepare` runs `drain_mini()` (`:438`), and so does `add-day` for Kobo (`:533`), so the demo build should settle.
- Its self-check hard-asserts `OPTIMIZE_COST` NEEDS_ATTENTION with `PRIMARY_FINDING_OPEN` on day S (`demo_combined_finish.py:185-187`, CO-1), and `prepare` fails if that fails. CO-2 asserts the "Fix verified, monitoring" line on S+1.
- **What is not proved:** the last CO-1 result on disk (`var/ch6b3work/check.json`, 2 Nov) predates CH-9 (`fbf8973fe`, 5 Nov). So reading code says a client should not see an empty row on a demo story day, but no run since CH-9 shows it.
- COH-17's V rows on this head compared Kobo rows that were all UNKNOWN, so they did not judge the demo's real verdicts. Hence step 2.

### Step 1: the four failing tests (0.1). All are stale tests; none is a product defect; fix them here

Each cause is a commit already in main (all ancestors of base `9b1c53ae3`), so all four fail on main today. Not demo-critical as behaviour, but the E2 full suite must not meet them first. **They merge with CH-6b3, no separate fix, no order issue.** Change only these lines.

| Test | Cause | Fix |
|---|---|---|
| `test_w303_portfolio_comparison_postgres.py::test_selected_action_window_workflow_and_withdrawal` | `progress` gained `f_rows` in `3cea423fd`; the spy at `:88` takes 4 arguments | `def spy(a_sites, a_rows, k, selected_pairs, *rest):` and pass `*rest` to `real_progress` |
| `::test_operating_cost_first_match_wins_across_partitions` | `link_ref` added to the wire in `1c3e3a075` | Add `"link_ref": card["link_ref"]` to the dict at `:252` |
| `::test_ev_window_money_has_no_finding_attribution` | Same | Add `"link_ref"` to the set at `:330` |
| `test_ch5a2_chain_api_postgres.py::test_estate_chain_has_one_read_per_key_and_count_claims` | `count.sites_disrupted` added in `6b4e682f2` (CH-6b2) | Add it to the set at `:117`; the comment becomes "the four" |

- **The first test has never reached its assertions on this code,** including the verified counts at `:157`, `:193-195`, `:211`. It builds `Portfolio(engine, tenant)` with no `count_claims`, so Q4b's claim path does not run there (`estate/index.py:213`, `:221`) and its numbers should not move. **If a number fails after the spy fix, do not change it: stop and report it with both values.**
- Run those two files, then the packet's scoped list. Expect 215 passed, 0 failed.

### Step 2: the measurement (0.1, demo-critical: all four Kobo rows depend on it)

On a new polish clone, using the same commands as `var/ch6b3_l3.log`:
1. create, backfill, settle;
2. drain: `python -m assetops_backend.mini_depth.worker run-pending --limit 500` against the clone until a pass returns fewer than 500 outcomes (as `drain_mini`);
3. settle again;
4. collect, then check with `expected-today.json`.

Packet table: for `board.day_kobo_trial-before_2026-10-31` (S), `board.day_kobo_trial-after_2026-11-01` (S+1) and `board.day_kobo_overuse_2026-10-24`, give each row's state, `MG-2` outcome and reason, headline, and each day's `critical_served` grade.

**Expected:**
- `critical_served` is not PENDING.
- S: Optimize NEEDS_ATTENTION, `PRIMARY_FINDING_OPEN`, a thread line "Before the change", as CO-1.
- S+1: not `PRIMARY_FINDING_OPEN`, line "Fix verified, monitoring (ACT-001)", as CO-1b (corrected from CO-2 by CH6b3-R3).
- COH-17 and COH-18: 0 new.

**Stop and report, do not tune, if any of these happen:**
- PRODUCER_NOT_SETTLED remains on any of the three days. That would be a real demo defect in every Kobo row.
- The S row differs from CO-1.
- There is a new COH finding.
- The Q4b counts differ from the table below.

The earlier undrained L3 result stays in the packet, labelled undrained. Drop the clone afterwards.

### Step 3: the restated bullet

Replace the L2m bullet "the Optimize row on D13 reads the ACT-K1 verdict" with:
- **L2m:** the generator thread is RESOLVED_MONITORING since D12 on D13 (already `test_md0_mechanism_postgres.py:268`), and the estate row equals the board row (`test_ch6b_estate_postgres.py:210`). No new assertion.
- **The board verdict is proved where the gate is open:** the step 2 table here, and CO-1 and CO-2 in every combined `prepare`.

In `test_ch6b_estate_postgres.py:207-208`, replace the comment with: "On `mechanism_db()` no Performance comparison report exists, so the Performance gate is closed and every Kobo row reads UNKNOWN (CH6b3-R2). The verdict is proved on the drained clone and by CO-1 and CO-2." In the packet, mark KD-3b closed by this ruling; the acceptance row reads "Restated".

### Step 4: Q4b table, confirmed

"Fixes confirmed" 1/1/1 → 0/0/1 and "priority sites" 0/0/0 → 3/2/2 (week/S/month) are what the story should show:
- **Week and S** end before the fix is verified (effective 1 Nov, after S on 31 Oct), so 0 confirmed is true. Kobo's fix is in hand, so Kobo is a priority Site.
- **Month** runs to 3 Nov, so Kobo's fix is confirmed (1) and Kobo leaves priority.
- **Priority Sites:** week = Kobo, Cold and EV; S = Kobo and Cold (EV's event is outside S); month = Cold and EV. These also fit `count.open_threads` 4/3/3.
- The old 0/0/0 was the fault: `thread_progress` read null Cold and EV states.

**One wording correction in the packet.** With no `known_at`, every event is visible. The state differs because it is read on the window's last day against the event's `effective_day` (`threads_of`, `lc.state_on`), not because of a "known" time. Replace "at their cutoff" and the "known 1 Nov" and "known 2 Nov" reasons with this. If the reasoning then fails for any row, stop and report.

These values are the polish build's. DD-1 may change them; the CH6b2-R2 DD-1a1 trap still applies.

### Step 5: the packet

Update size 1.3, the scoped-test result, the step 2 table, KD-3b closed, the Q4b wording, and BL-36. Then the batched review.

### Lane 2 (coordinator relays; DD-1 +0)

DD-1b2 F-THREADS must also report, on every shown Kobo story day, each row's state, and fail on `PRODUCER_NOT_SETTLED` or a PARTIAL board. CO-1 covers only day S.

### Backlog

**BL-36** (not demo-critical): `count.verified_results` counts only threads with a Finding occurrence in the window, so a Portfolio opened on one later day (for example 1 Nov) can read "None confirmed" while Kobo's board that day reads "Fix verified, monitoring". The story links open the week and the month, which agree. **DS-1 must keep the Portfolio on those two windows.** (Premise withdrawn and BL-36 restated by CH6b3-R3.)

## CH6b3-R3: the CH-6b3 review, H1, M1, M2 and the residual (Architect, Claude, 2026-11-07)

Review: `.agent/review-CH-6b3.md` at `b32e77648` (REVISE). Checked against the code and `var/ch6b3r2_bundle`: **the reviewer is right.** I withdraw CH6b3-R2 step 4 and BL-36's "the week and the month agree". On the week and S windows, the claim read the thread on 31 Oct while the rows, the drawer, "Why?" and the board report what is known now.

**CH-6b3: 1.3 → 2.1** (H1 0.3, M1 0.15, M2 0.25, COH rows 0.1, re-runs 0.1). All of H1, M1, M2 are **demo-critical**: they are on ST-1, the opening screen, and the plan says "The Assure card agrees with the Site rows". **They are fixed here, on this branch**, with one fresh Claude re-review. **No owner question:** the fix restores what ST-1 and ST-2 already say ("After verification the thread reads Resolved, monitoring"); only my R2 ruling and the CH-5a note (`:686-691`) said otherwise. Both are overridden.

Fresh Sonnet builder: do steps 1-7 in order. **Stop rule from CH6b3-R stands:** any value below that differs, or a new COH finding, means stop and report; never tune.

### Ruling on H1: the one truthful statement

**The count answers: of the problems found in this window, what is their status as known now?** A window selects which problems (the existing occurrence rule, `_finding_threads`); the state is the thread's latest event visible at the request cutoff `k`.

- **A fix verified on 1 Nov does count for a window ending 31 Oct,** because the problem was found in that window and it has since been confirmed.
- **The row does not change:** Group Monitor, "Verified". The Assure headline, the drawer and "Why?" already read what is known now. That is why this is one change at the claim, not a patch to five surfaces.
- **Rejected: reading everything as of the window's last day.** It would need Action facts, labels, placement, the Assure headline and the board's Earlier column all bound by day, and would break CO-1 and CO-3, on a window whose story is "here is the problem, and the fix that followed". **Rejected: reviewer option (b):** it keeps two statements and only words around them.
- **What stays day-bound, on purpose:** board rows and the Site dots. On S, Kobo Optimize reads "Needs attention", with "Before the change on 1 Nov" (CO-1). That is a dated statement about that day. The presenter says so. The packet states it.

### Step 1: the claim (H1, 0.3)

- `backend/assetops_backend/chain/claims.py`, `counted_threads` (`:72-81`): replace `day=window_day(lo, hi, site.timezone)` with `day=LATEST_KNOWN`, a module constant `LATEST_KNOWN = date.max`, with a comment citing CH6b3-R3. `lc.state_on` then returns the last event visible at `lifecycle_cutoff(k)`. `chain_api.py:379` calls the same function, so the Protect "Why?" follows.
- **Do not change:** `site_chain.threads_of`'s other callers, `site_parts`, `attach_threads`, `workflow_label`, `place`, `mini.py`, CO rows.
- **Wording.** "1 confirmed on the days checked" would say the confirming happened on those days. In `chain/vocabulary.py` `COUNT_TEXT["count.verified_results"]`, the third form (CHECKED_DAYS, n >= 1) becomes `"{n} confirmed, from the days checked"`. The zero form stays. Add the inline `MOCK DEVIATION MD-CH6-8` (no mock example of this form) and register row **R708** citing `frontend/mockups/v70/index.html:296`.
- **Tests:**
  - `test_ch5a2b_claims.py:45` takes the new text.
  - New L0 in `test_ch6b2_portfolio_cards.py`, on the existing fake request: (a) a VERIFIED event effective after the window's last day and known by `k` counts in `verified_results`, not `open_threads`; (b) the same event known after `k` leaves ACTION_IN_HAND; (c) a thread with no Finding occurrence in the window is not counted; (d) a later RECURRED event counts as open.
  - CH6b2-R2 L0 case (5) (Site chain state = claim state) now holds only when no event is effective after the window's last day. Restrict it so, and say so in its comment.
  - `test_ch5a2_contract.py:176` and its golden: if the value moves, list old → new with the event that moves it. If no later event explains it, stop.
- **Expected on the drained polish clone (week / S / month):** `verified_results` 1/1/1; "Fixes confirmed" 1/1/1; priority Sites 2/1/2 (Cold, EV / Cold / Cold, EV); `open_threads` 3/2/3; `sites_disrupted` 2/1/2. The Assure card reads "1 confirmed, from the days checked". This replaces the CH6b3-R2 table.

### Step 2: M1, one meaning for "days checked" (0.15)

"Checked" means graded COMPLETE (the server `days_line`). The coverage figure counts days with an assessment, a different thing under the same word.
- `estate/portfolio.py` `card_notes` (`:659-670`): remove the clause. Protect's note is None; Assure's is recovered value and evidence gap. Delete `checked_days_clause` and `note.checked_one`, `note.checked_many` from `chain/vocabulary.py`. Keep `summary.checked_days` on the wire. Remove those M1 cases from `test_ch6b2_portfolio_cards.py` (this overrides that part of CH6b2-R2 M1) and add a case asserting neither note holds "days checked".
- `estate/coverage.py:37`: `DAYS_CHECKED = "{c} of {n} days assessed · {g} {unit} not available yet"`. CO-6 imports the constant, so it follows. Literal strings in `test_cov_partial_portfolio.py` or `test_w301_estate_coverage.py` take the new word (grep `days checked` in `backend/tests`).
- `frontend/src/estate/EstatePortfolio.tsx:785`: `not checked:` becomes `not assessed:`. Update `estatePortfolio.test.tsx` at `:1314`, `:1339`, `:1352` to the new strip text. The Findings notice reads the same server text. The strip already carries MOCK DEVIATION R622, so note the word in that register row.

### Step 3: M2, the estate "Why?" days are the card's days (0.25)

- `chain_api.py` `_estate_why` compose: `summary = service.summary(sites, lo, hi, parsed.known_at)`; `cards = summary["cards"]`; `days_used = (cards.get(category) or {}).get("days_line") or cards[PROTECT_ASSET]["days_line"]`. (Optimize has no days line; Protect's is the Sites' days.)
- `chain/why.py` `estate_text`: new parameter `days_used: str | None = None`; when given, it replaces the join at `:336`.
- **"Checking 32 more days" (`would_change`):** add `open_days: int = 0` to `Trace`, set at `:249`. New `estate_text` parameter `window_open: Mapping[str, int] | None = None`, by Site name, computed in the route as `expected - complete` from `service.estate_counts(...).days`. A Site with `open_days > 0` uses `why("why.change.days", n=window_open[name], s=...)`, and is skipped when that is 0.
- `sites[].text` and the Site "Why?" route do not change.
- **Tests:** L0 for `estate_text` with both parameters. Route test on the existing Why postgres file: on a month window the text holds no "32", and `days_used` equals the card's `days_line`.
- **Timing:** this adds a summary read to the route. Report the route's time on the clone, before and after, in the packet. Over the page budget: report, do not optimise here.

### Step 4: why COH-17 and COH-18 passed, and the rows to add (0.1, each guards what is shown)

**They passed because they were right about what they compared, and my table left these out.** Every row compared a value with itself across routes (chain, summary, board) or with its own day grades. No row compared the note with the days line on one card, the "Why?" days with the card, or a table row and the Assure text with the claim. Gap in my table, not in the builder's work.

Add to `_coh17_full`, under `full_claims`, per estate window:

| # | Compared | Rule |
|---|---|---|
| L2 | `summary.verified_result_count` vs chain `counts["count.verified_results"].value` | Equal when both are not null |
| L3 | Distinct `thread.id` over `portfolio.{w}` rows with `workflow_label == "Verified"` vs the same claim value | Equal |
| W3 | Why `text.days_used` vs `(cards[cat].days_line or cards.PROTECT_ASSET.days_line)` | Equal |
| N1 | `portfolio.{w}` `summary.card_notes` values | Neither holds the text "days checked" |
| C2 fix | Reviewer L3: a card or count key absent | Is a finding, not `{} == {}` |

- **L3m:** on the `states` variant the D14 recurrence reads open, while an older row stays "Verified", so L3 may fire. Only for that cause, add `expected-mechanism.json` entries with `variants: ["states"]`, naming CH6b3-R3 and BL-07. Any other cause: stop.
- `clean_full` has no generator in the repo: edit its JSON by hand so it passes, then one planted break per new row in `test_chain_coherence.py`.

### Step 5: run the frontend tests

The worktree has no `frontend/node_modules`; `AssetOpsV1-plan2\frontend` does. First compare `frontend/package-lock.json` in both; if they differ, stop and report. Then, from PowerShell:
```
New-Item -ItemType Junction -Path C:\Users\assef\Bineyame\AssetOpsV1-ch6b3\frontend\node_modules -Target C:\Users\assef\Bineyame\AssetOpsV1-plan2\frontend\node_modules
```
From `frontend`: `npx tsc --noEmit`, then `npx vitest related --run src/estate/EstatePortfolio.tsx src/estate/PortfolioOutcomes.tsx`. Remove the link with `cmd /c rmdir frontend\node_modules` (never `Remove-Item -Recurse`, which would follow it). This also closes the review's "frontend not verified", including `namesOnePrioritySiteInTheSingular`.

### Step 6: re-runs

1. Scoped backend: the eleven files of run 2, `test_w303_portfolio_comparison_postgres.py`, `test_ch5b_why*`, `test_ch5a2_contract.py`.
2. A new drained polish clone as CH6b3-R2 step 2, then `demo_combined_finish.py check` is **not** required, but CO rows must not be edited. Collect and check: 0 new.
3. L3m collect and check on the existing template (no rebuild unless `status` says `usable: false`).
4. Guards A, W, N, V, M, L, D, one at a time.

### Step 7: packet and Lows

- Replace the Q4b table with step 1's values and the rule; list the Assure and Protect note text old → new; state the day-bound dot.
- **Lows:** rename the test and fix the docstring at `test_ch6b_estate_postgres.py:158-160`. Correct "as CO-2" to **CO-1b** in the packet and in CH6b3-R2's reading.
- Record for the walkthrough: Portfolio Cold and EV rows read "No action agreed yet" on the week, while ST-4 and ST-5 show those Actions in hand on their boards. It is outside this slice (their row cutoff, known COH-2 entries on the month). **DD-1b2 F-THREADS reports it on the combined build;** the walkthrough judges it.

### Residual: the Cold failure-day board

**No client link reaches it in that state, from what I can read.**
- `tools/demo_combined.py` `story_links` opens Cold on the day's event window (`start`, `end` from `days.json`), not the local-midnight pair.
- Portfolio Site links are the bare `overview_href` (`site_outcomes/read.py:781`), which uses the overview's default window.
- The local-midnight pair is the collector's choice (`chain_coherence.py` `day_windows`), and I found no frontend code building it.
- **Likely cause, not proved:** that pair does not contain the selected window, so `event_window` is None, and the composer reads the pair itself with an overview that has no settled currentness (`cold.py:138`). A presenter typing that URL would see Unknown.

**Owner: DD-1b2 F-THREADS (coordinator relays, DD-1 +0).** It replaces the note in CH6b3-R2. For **all three Sites**, it reads every `story_links` board plus the bare `/sites/{code}` (and `/sites/{code}/ev`) board, reports each row's state, and fails on `PRODUCER_NOT_SETTLED` or a PARTIAL board. Making a local-midnight Cold pair settle is **BL-37** (not demo-critical).

### Backlog and DS-1 (replaces the CH6b3-R2 text)

- **BL-36 restated:** a window containing no occurrence of the thread (for example 1 Nov alone) reads "None confirmed", while the board's work-window count reads "1 verified result". **The week and month story links now agree, and L2 and L3 guard it.**
- **DS-1:** the Portfolio stays on the week and month story links, for this reason only. The presenter says: "these are the problems found this week, and where they stand today."

## CH6b3-R4: the four L3m findings, the template and the Why run (Architect, Claude, 2026-11-07)

Input: packet "CH6b3-R3 final runs" at `b705917e3`, `var/ch6b3r3_l3m_report.json`, `var/ch6b3r3_l3m_bundle`. **CH-6b3: 2.1 → 2.2.** No owner question. **No third template rebuild** (section 3). Fresh Sonnet builder: read sections 1-3, then do steps A-C in order. Stop rule stands: any other finding means stop and report.

### 1. L3 on week and month: it is the D14 recurrence, not H1 (expected entries, as proof only)

**Confirmed from the bundle.** `chain_day.KOBO-001.2026-11-01.json`: thread `3f4db97f` is RECURRED since 2026-11-01 with occurrences 22 Oct, 29 Oct, 1 Nov (D4, D11, D14; `test_md0_mechanism_postgres.py:242`). 1 Nov is D14 (`backend/tests/mechanism_dataset.py:98`).
- Week: the 29 Oct row is segment 1, "Verified". The claim reads the latest state, RECURRED: `open` 1, `verified` 0.
- Month: two segment 1 rows read "Verified", and the segment 2 row reads "No action agreed yet". Same claim.
- Both sides are true: that fix was verified, and the problem then came back. Polish has no recurrence (L3 = 0 there), and the demo does not present one (BL-07).

**Exact entries.** In `tools/checks/fixtures/chain_coherence/expected-mechanism.json`, `"expectations"` becomes:
```json
[
 {"rule": "COH-17", "site_code": null, "window": "week", "subject": "L3", "variants": ["states"],
  "reason": "D14 recurrence: an older row reads Verified, the thread now reads RECURRED (CH6b3-R4)", "owner": "BL-07"},
 {"rule": "COH-17", "site_code": null, "window": "month", "subject": "L3", "variants": ["states"],
  "reason": "D14 recurrence: an older row reads Verified, the thread now reads RECURRED (CH6b3-R4)", "owner": "BL-07"}
]
```

### 2. N1: one more branch, and one browser twin (demo-critical: same word, same page)

**Replacement.** `backend/assetops_backend/chain/vocabulary.py:512`: `"note.gap.zero_checked": "no evidence gaps on the days assessed"`. Keep the key. The evidence-gap count follows coverage (`estate/portfolio.py` `evidence_known`), so "assessed" is the true word under CH6b3-R3 M1.

**Why polish gave 0 findings.** This branch needs gaps = 0 on a CHECKED_DAYS estate. Polish has gaps 1 on week and month and null on S, so the sentence never appears there, and N1 only tests what the data reaches. The combined build could reach it, so it is fixed regardless.

**What else escapes that way:**
- **Notes:** nothing else. `card_notes` is built only from the recovered value and `evidence_gap_text`, and `note.gap.zero_checked` is the only branch holding the phrase. New L0 in `test_ch6b2_portfolio_cards.py`: for gaps in (None, 0, 1, 2, 4, 6) and both `checked` values, the text holds no "days checked". Update `:237` to the new text.
- **The browser twin:** `frontend/src/estate/EstatePortfolio.tsx:102` `NONE_ON_CHECKED_DAYS`, used only by the evidence-gap pulse (`:803`), says the same thing on the same branch, and N1 cannot see it. Change its value to `"None found on the days assessed"`; update any literal in `estatePortfolio.test.tsx`.
- **Left alone, on purpose:** the count claims' "on the days checked" forms and `OPPORTUNITY_NONE_DETAIL`. They follow the graded basis, which is what "checked" now means. On polish, with 0 COMPLETE days, "None found on the days checked" is thin but not false, and DD-1's full days change that. For the walkthrough.

**Register:** no new row. In `.agent/mock-departure-register.md` **R670**, replace `Assure "no evidence gaps on the days checked"` with the new text and name the pulse's new text. Both spots already sit under R670.

### 3. No third rebuild: the proof does not need one

Read from code and the template's own tag:
- The fingerprint covers the data trees (`backend/conversions`, `backend/migrations`, `backend/tests/fixtures`, `config/site-templates`, `contracts`) and every repo module the build loaded, **with `chain/**` excluded** (`DERIVE_TREE`, `backend/tests/mechanism_dataset.py:1056`, `:1071`).
- `chain/vocabulary.py` is therefore **not an input**. Nor are `frontend/`, `tools/checks/`, `.agent/`, or a `backend/tests/*.py` test file the build does not load. The tag on `assetops_mechanism_tpl_abc64763_test` holds 367 modules, including `estate/*` and `chain_api.py`. The last stale fits the `estate/` and `chain_api.py` edits in `c60bd8c07`.
- **Condition:** this round edits only the files named here. An edit under `backend/assetops_backend/` outside `chain/` makes the template stale; if you think you need one, stop and report.
- The template stays valid, so the rerun below is the normal procedure on the same data, not a shortcut. Merging this text to main does not stale the template either.

### Step A: edit and confirm

Sections 1 and 2 only. Then `python tools/mechanism_dataset.py status` must print `usable: true` for `states`. If not, stop and report; do not build.

### Step B: runs

1. L0: `tools/checks/test_chain_coherence.py`, `backend/tests/test_ch6b2_portfolio_cards.py`, `backend/tests/test_w303_portfolio_api.py`.
2. Frontend, with the junction and commands from CH6b3-R3 step 5: `npx tsc --noEmit`, `npx vitest related --run src/estate/EstatePortfolio.tsx`.
3. L3m: `derive --variant states` (about 72 s), collect (about 436 s), `check --variant states --threads var/mechanism/expected-threads.json`. **Expected: 0 unexpected;** the two L3 entries matched; N1 = 0; W3, L2 and COH-18 still 0; no RESOLVED entry.
4. **Not re-run, with the reason in the packet:** L2m and the polish clone. Only one text value, one browser constant and an expectation file changed. No read path or number moved, and polish never reaches this branch.
5. Guards V and M, one at a time.

### Step C: packet

Add "CH6b3-R4 run": the fingerprint unchanged at `abc64763`, the L3m result, the two entries with their cause, the N1 text old → new, and the reason for each run not repeated. No further Architect round unless the stop rule fires; the coordinator chooses whether a short fresh look at this small diff is needed.

### The named Why run: accepted, nothing owed

`test_ch5b_why_postgres.py` passed and covers the Site route. The estate month Why is proved on real data: W3 compares `days_used` with the card on each window and category in the bundle, in L3m (9 pairs, no "32", "Checking 21 more days") and in `var/ch6b3r3_bundle` (12 pairs). The in-memory M2 route test stays, as the re-review's Low accepted. The packet says this in place of the re-review's named run.
