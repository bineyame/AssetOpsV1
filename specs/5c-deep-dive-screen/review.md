# 5c review

## Round 1: units 1 and 2 (backend), discovery review (W5)

Reviewer: Claude (fresh; did not author the work), 2026-11-21. Branch `task/5c-deep-dive-screen` at `4b18a2c77`, diffed
against merge-base `d615685d5`. Scope: `backend/` and its tests, the statement cases, the `ADOPTED` entries. Unit 3 is
not reviewed here.

**Summary (verdict: ACCEPT WITH FIXES)**
- World A holds: $1,443.00 against $2,295.00, −$852.00, 3 of 3, Estimated. No "$1,693.00" anywhere. Every by-Site and
  cash total reconciles to the cent.
- The standing is read once, at `served.as_of`. Real data needs a person of the served tenant. Plants P3, P10 and P14
  and two of my own each fail their test.
- **H1.** When nothing is compared (R.effect None, the designed `headline_na` state), five places print "$0.00" for
  missing figures. The owner's rule is "never 0".
- **H2.** SC-1f breaks 5c. On a scratch merge of `task/SC-1f-declared-word`, Emulated money steps read "Declared, not
  yet reconciled". That contradicts D-5C.3 and §2.4. 5 unit-1/2 tests and test 9 fail. D-SC1F.6 has 5c merge `main`
  after SC-1f lands, so this has to be resolved before 5c merges.
- **M1.** Test 9 pins 3A7's "(Recorded)" wording. It breaks on SC-1f (MBQ1), and it is outside the fast check-all.
- **M2.** The headline's evidence `["Estimated"]` carries no standing. The same −$852.00 reads "Estimated, not yet
  reconciled" on the tile.
- Lows L1 to L6 are below. Flags (a) to (d) each get a recommendation.
- check-all: 42 of 42 guards pass. The statement guard passes with 6 files adopted.

### Checks run (this revision)

- `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1`
  (`ASSETOPS_GUARD_PYTHON` set): "check-all: 159.4 s wall … All 42 guards passed (blocking; 0 advisory, 0 warned)." It
  includes "Statement catalogue (SC-1): OK … scan (6 adopted)" and "self-test: 72 of 72 plants behave".
- Focused: `test_5c_deep_dive_view.py test_5c_deep_dive_api.py test_sc1_statements.py`: 541 passed.
- Test 9 (`--db`, `assetops_test` clone): `test_5c_deep_dive_postgres.py`: 2 passed.
- Scratch merge of 4b18a2c77 with `task/SC-1f-declared-word` (detached scratch worktree, since removed):
  - focused: 5 failed, 541 passed (`test_3` :198, `test_4_b` :285, `test_5[DECLARED-…-Recorded]` :435, and the two
    `test_8` fixture comparisons);
  - test 9: 1 failed (`(Declared)` != `(Recorded)`, and `Fuel cost (Recorded, Emulated and Declared)`).
- Plants, each in a scratch copy and restored afterwards:
  - P3 (`known_at=None`): fails `test_9…snapshots_instant` at :128 (`b == a`) and `test_8_world_a_is_the_fixture`;
  - P10 (`if real_data:` made `if False:`): fails `test_8_real_data_needs_a_person_of_the_tenant`;
  - P14 (`named` ignores the sign): fails the L5 lead vector. L1 to L4 alone would not catch it, so the builder's L5 is
    needed;
  - reviewer RP1 (`CELL_FORM[True]` "SIGNED", carried cell without "(estimate)"): fails test 3 and both test-8
    fixture cases;
  - reviewer RP2 (any signed-in person, of any tenant): fails `test_8_real_data_needs_a_person_of_the_tenant` (the
    "theirs" cookie).
- Probes (scratch):
  - the view with every portfolio row emptied (H1);
  - `words.cash` with one sub-figure absent (L4);
  - `rules_digest()` timing (§8): 1.90 s first call, 328 files, then cached per process.

Not verified: unit 3's screen. I did not rerun the full backend suite; it is not needed for these findings.

### Judged against spec §3 to §4 and tests 1 to 9

- **World A.** The fixture's values match §3.5 string for string, apart from the PF2/D-4A.12/.20 record changes. I
  checked each of those against D-4A.12's `RECORD_KEYS` and `RECORDS` order. They are consistent: revenue's stop now
  opens with "the billing export" (adjustments and tariff map to BILLING) and adds METER_READS and LOSS_BAND.
- **Arithmetic I did by hand.**
  - by-Site: 883 − 250 + 810 = 1,443; 1,445 − 65 + 915 = 2,295; −562 − 185 − 105 = −852; revenue +38 − 55 − 80 = −97;
    fuel −600 − 130 − 25 = −755.
  - cash: 3,180 + 3,800 + 1,890 = 8,870 = 9,688 − 150 − 668.
  - cost share: (8,245 − 700) / 8,245 = 91.5%. Shares: 97/852 = 11%, 755/852 = 89%.
- **Precision.** One precision per quantity: money to 2 places, shares to 0, the cost line to 1, litres normalised.
- **The standing.** It is read once, at `served.as_of` (`deep_dive/read.py:52`). Test 8 asserts
  `recon.asked == [(tenant, None, "2026-10", AS_OF)]`. Test 9 (a)/(b)/(c) holds the clock sequence of R2.
- **Real data.**
  - `deep_dive_api.py:52-57` uses `person_from_request` and the tenant check.
  - With real data on and no accounts service it answers 503, which fails closed.
  - Store faults raised while the tenant or the person is read are inside the `unavailable` catch.
- **KD2.** The fixture was generated and then checked. That falls short of the guide's W2 wording. But test 3 asserts
  every §3.5 literal by hand, and I independently checked the values §3.5 does not state: the per-Site om and staff
  rows, the cash rows and nav. I accept it. No value in the fixture is unexplained.
- **The text guard.** `tables.py` holds codes only. `words.py`, `view.py`, `read.py` and `deep_dive_api.py` build no
  English, and every string comes through a statement. The guard passes.

### Findings

**H1 (High; acceptance gap, owner rule "missing is Not available yet, never 0"). Missing figures print "$0.00" when
nothing is compared.**
- **Where:**
  - `deep_dive/view.py:138-144`: `group_sums` starts each heading at `Decimal(0)` and skips None.
  - `:201`: `tile_split` runs even when `R.effect` is None.
  - `:327-338`: a group's value is the sum of `effect or 0`.
  - `:292`: `drawer_effect(row.effect or Decimal(0))`.
  - `:504`: the grow and optimize card values come from `group_sums`.
  - `:116`: a residual with effect None prints "$0.00".
- **Probe.** World A with every portfolio row emptied (k = 0; a currency mismatch across Sites gives this, or a first
  month without billing for any Site). The headline correctly reads "Contribution for October is not available yet."
  But the screen shows:
  - tile 2 "Grow $0.00 · Optimize $0.00";
  - groups "Grow revenue $0.00" and "Optimize cost and efficiency $0.00";
  - every step drawer "Effect on contribution $0.00";
  - the Grow and Optimize cards "$0.00", with the word "Not available yet" beside them.
- **Why it matters.** `headline_na` is a designed state, so this is reachable. It is the exact class P4 guards against.
- **Fix.**
  - Carry None through `group_sums`: a heading with no step effect is None, and `amount(None)` gives "Not available
    yet".
  - Omit `tile_split` when `R.effect` is None, or give it an absent variant.
  - Omit `drawer_effect` when the effect is None.
  - Add a view test, an "R not available" world, that asserts no "$0.00" in tiles, groups, drawers and outcomes.

**H2 (High; contract conflict, merge blocker). After SC-1f, Emulated money reads "Declared".**
- **Where:** `deep_dive/words.py:67-71`. `word()` hands §2.4 to the shared evidence vocabulary through `money_word`.
- **What happens.** D-SC1F.1 moves `DECLARED` to `by_evidence_first`: "Declared" for every origin. A step row's
  evidence is DECLARED (its budget target) with emulated origins. On the scratch merge, revenue, fuel cost and staff
  read "Declared, not yet reconciled", and Grow's card does too, where §3.5 says "Emulated, not yet reconciled".
- **Why it matters.**
  - D-5C.3 and §2.4 (5c's rule "on this screen only") put the origin first for non-observed origins (D14: an emulated
    figure is never shown as if it were real). "Declared" on revenue −$97.00 hides that the records are emulated.
  - Test 5's row `("DECLARED", field-integrated) → "Recorded"` also flips.
  - D-SC1F.6's gate has 5c merge `main` after SC-1f lands, so this hits before 5c can merge.
- **Fix (5c-side, keeps §2.4 true either way).**
  - In `word()`, apply §2.4's order before calling `money_word`. With a non-observed weakest origin the word is the
    origin's. For observed origins, map `DECLARED` to `RECORDED`, so "Recorded" is §2.4's own word.
  - Add §2.4 rows for DECLARED with `source-emulated` and `demo-simulated`.
  - Then merge `main` (with SC-1f) and rerun the focused 5c tests and test 9.
- **Route.** The Architect confirms that §2.4 (not D-SC1F.1) governs this screen's figure words. D-SC1F.1 was written
  for a declared setting, the tolerance.

**M1 (Medium; MBQ1, a pin that will break). Test 9 pins 3A7's evidence wording.**
- **Where:** `tests/test_5c_deep_dive_postgres.py:52-54` (`A_TEXT` "…within 1% (Recorded)."), `:120-121` (`details`
  "Fuel cost (Recorded and Emulated): …"), `:139-140` (B's "…within 1% (Recorded).").
- **What happens.** SC-1f changes all three, to "(Declared)" and "(Recorded, Emulated and Declared)". This is confirmed
  on the scratch merge. Test 9 needs `--db`, so the fast check-all will not show it, and a merge could leave it red on
  `main`.
- **What is fine.** No 5c code depends on the wording. The view passes `standing.text` and `details` through unchanged
  (PF11). Unit 1's fixture and test 8 hold an injected literal and are unaffected by 3A7 itself (they break only
  through H2's words).
- **Fix.** On merging `main` after SC-1f, update these literals to SC-1f's wording, by hand (W2), and run test 9
  under `--db` before the merge. Name `test_5c_deep_dive_postgres.py` in the merge note. Keep the spec §3.5 decision
  (MBQ1) with the Architect.

**M2 (Medium; acceptance gap against D-5C.4, Architect to confirm PF8). The headline's evidence carries no standing.**
- **Where:** `deep_dive/view.py:157-159`, `words.py:126-127`.
- **What happens.** The headline is `{"text", "evidence": ["Estimated"]}` in both A and B (probed: building the facts
  with `Evidence(…, reconciled=False)` still serves `["Estimated"]`, because `served` drops the flag). The tile showing
  the same −$852.00 reads "Estimated, not yet reconciled".
- **Why it matters.** D-5C.4 says every money figure's word carries the standing, so one figure has two words in L1.
  L1's status line ("Not yet reconciled with the management accounts.") mitigates it.
- **Fix.** Pass each served evidence word through `money_word`, or have `served` honour the reconciled flag. Or the
  Architect rules that the status line covers the headline, and §3.5 records `["Estimated"]` as intended. PF8 is still
  awaiting that confirmation.

**L1 (Low; consistency). Kisiwa's carried O&M is labelled in one place and not the other.**
- **Where:** `view.py:298-300`.
- **What happens.** The by-Site cell reads "$0.00 (estimate)", but the O&M drawer's per-Site row reads plain "$0.00".
  The `carried` line follows it in the same drawer.
- **Fix.** Use `T.CELL_FORM[own.carried]` for the drawer row too, if the Architect agrees. §3.2 does not require it.

**L2 (Low; spec question before unit 3). Drivers carry no depth or parent.**
- **Where:** `view.py:306-312`; spec §3.2.
- **What happens.** In World H the flat list holds "Diesel used −$600.00" and then its three children (−37.50,
  −412.50, −150.00), which sum to it. The screen cannot nest them, and an executive could add them to −$1,200.00.
- **Fix.** Add `depth` (or `parent`) to each driver, or have the Architect rule on the nesting.

**L3 (Low; ambiguity). The caps are not in the payload.**
- **Where:** spec §3.2 says drawer `sites` and `by_site` show "at most 10, then `more`". The view returns every Site
  and no `more` key (`view.py:295-300`, `:348-361`). §3.1's `by_site` keys list no `more`, and §3.4 says only of
  not-available that "the JSON holds all".
- **Fix.** The Architect says whether the JSON or the screen caps. Lakeside (n = 3) cannot exercise it.

**L4 (Low; robustness). A missing sub-figure in `deep_dive.cash` is an unanswered 500.**
- **Where:** `i18n/statements/en/deep_dive.py:361-375`; `deep_dive_api.py:281-285`.
- **What happens.** `deep_dive.cash` `requires` expected, outstanding and in transit all present. With collected
  present and any of them absent, `render` raises `REQUIRES_FAILED` (probed). The route catches only `BadMonth` and
  `unavailable`, so the answer is a 500 without `no-store`.
- **Reachability.** It is not reachable today. 5b's portfolio rows give a SUM child whenever its root has an effect,
  and the collected target always comes with its actual. So this is brittle, not wrong.
- **Fix (optional).** Add a fallback variant that names the missing part "not available yet".

**L5 (Low; wording, D-4A.20's consequence, route to the Architect). The revenue stop asks for the billing export that
revenue came from.**
- **Where:** fixture `bridge…revenue.drawer.sites[*].text`.
- **What happens.**
  - The stop opens "Not split further until the billing export, …", but revenue itself is read from the billing export.
    It needs the adjustment and tariff lines within it.
  - LOSS_BAND's words hold a comma ("…of each feeder, declared in the Site's setup, the productive-use tariff…"). That
    makes the list hard to parse.
- **Fix.** None in 5c code: the wording is in the shared `record` vocabulary.

**L6 (Low; residual, stated). `create_app` now builds four more stores and hashes the code once.**
- **What happens.**
  - With `DATABASE_URL`, `create_app` builds 3B7a's structure read, the commercial reads, the snapshot store and 3A7's
    reconciliation. Engines are lazy, and they are disposed on shutdown, but only under lifespan: a bare
    `TestClient(create_app())` never disposes, which is the existing pattern.
  - `rules_digest()` hashes 328 files (1.90 s) on its first call. It is `lru_cache`d, so this is once per process, not
    per app.
  - A failure in any of the four builders now stops `create_app`, as the peer compositions do.
- **Fix.** None required. Composition and dispose are correct: all three are disposed, and an earlier store is
  disposed when a later builder raises (test 8).

### The one-figure flags (handoff, earlier 5c report)

**(a) Kisiwa's carried O&M, "$0.00 (estimate)" / "taken at its budget line (estimate)".**
- **Honest?** Yes, with a better label.
  - The $0.00 is the O&M effect under 5b's explicit carry (`CARRY_AT_TARGET`): actual taken at budget. It is a real
    component of the $1,443.00 total and of Kisiwa's by-Site row (−55 − 130 + 0 + 0 = −185).
  - "Not available yet" in that cell would break the row's reconciliation and contradict the total, which includes the
    carry. So it should not read "Not available yet".
  - It should, under the owner's "labelled by its source": "(estimate)" does not name the source. Recommend "$0.00 (at
    budget)" or "(budget line, estimate)" in the cell, the same in the drawer row (L1), and the existing drawer and
    not-available lines naming the missing invoice.
- **Ownership.** The carry rule is 5b's (D-5B). The words are 5c's: spec §2.5 `carried` and the §3.2 cell suffix, an
  Architect literal. The 5c builder implements. It does not block units 1-2.

**(b) "Actual · Target" pairs, including "Target 0 L".** Keep them.
- They are plan against actual, the case the owner's rule allows, and 0K4's change list item 8 checked 5a targets as
  allowed.
- "Target 0 L" for candidate and unexplained litres is 5a's declared `LEAK_ZERO` rule (`structure/targets/rules.py:34`),
  not a hand-entered value.
- Optional wording for the Architect: name the basis, for example "Target 0 L (none avoidable)".

**(c) World H's 330 L of candidate litres.** No 5c change.
- 5c serves 4d's figure. World H is 4d's test inputs (`LakesideInputs`), and the walkthrough world reads "Not available
  yet" (0K4 change list item 7).
- When 0K4e changes the dispatch rule, test 4(H)'s literals (330 L, −$412.50, 730 L, −$37.50) may move. 0K4e's
  select-tests sweep should name `test_5c_deep_dive_view.py::test_4_h_kobo_litres` and update them by hand.

**(d) KD1, the diesel-price driver.** Accept.
- The price row composes NONE, so 5b gives the portfolio row no actual or target, and §3.2's rule yields `detail`
  null.
- The shown value is the effect (Modelled litres times the price difference), so "Modelled" is the honest word for
  it.
- The Architect amends §3.5 H's literal. A Site-level price at k = 1 could be a later refinement; it is not needed.

### MBQ1

Nothing in 5c's code pins 3A7's standing wording; it passes through unchanged. The pins are the test-9 literals (M1),
and they will break on SC-1f. The larger break on SC-1f is the evidence word (H2), not the standing text.

### Residual risk the packet does not name

- The SC-1f merge order (H2, M1). D-SC1F.6's gate makes 5c take SC-1f before it merges.
- The "R not available" state (H1) has no test world. A currency-mismatch portfolio (KES plus USD Sites) is the
  realistic way in.
- The flat driver list (L2) will reach unit 3 unless it is ruled before the screen is built.

### Disposition

ACCEPT WITH FIXES. Fix H1 and H2 on the branch. H2's fix needs the Architect's one-line confirmation that §2.4
governs. Then merge `main` (with SC-1f), fix M1's literals, rerun the focused 5c tests and test 9 (`--db`), and run
check-all once. M2 and L1 to L3 go to the Architect, with the defaults above. L4 to L6 need no action.
