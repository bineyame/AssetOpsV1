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

## Round 2 (verification): units 1 and 2 (backend), fix rounds 1 and 2

Reviewer: Claude (fresh; did not author the work), 2026-11-21. Branch `task/5c-deep-dive-screen` at `b47ef1003`
(worktree `AssetOpsV1-5cbe`), against round 1 at `519c8a305` and rulings D-5C.19 to D-5C.25 (spec rev 3). Depth W5/W6:
the named findings, their sweeps, and the new per-row currency change, which I read whole. One new class found
(H3), so this round escalates past a plain re-check.

**Summary (verdict: ACCEPT WITH FIXES)**
- H1, H2, M1, M2, L1, L2, L3, L5 and KD3 are closed as ruled. Every plant named in the guide fails its test.
- In World A every remaining "$0.00" is a real figure: O&M and staff, which match their targets, and in-transit cash.
- **H3 (new, High).** The currency fix covers the Site rows only. Portfolio rows still print in R's currency (USD
  when R has none), so a KES sum prints as "−$730.00". A Site whose own actual and target differ in currency prints
  its figures in the portfolio's currency.
- **M3 (new, Medium).** That same Site's `out` line says "not a mini-grid Site, not included". The sentence is false.
- L7 (the currency mismatch is never stated) and L8 (D-5C.21's residual placement is untested) are Low.
- Totals across currencies do not exist, and that is right: 5b returns None and the screen reads "Not available
  yet". A one-currency partial total is a real figure, though, and must print in its own currency (H3).
- check-all: 42 of 42 guards pass. The statement guard passes with 6 files adopted, and its self-test passes 78 of 78.

### Checks run (b47ef1003)

- `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1` (with
  `ASSETOPS_GUARD_PYTHON` set): "check-all: 145.3 s wall (0.2 s waiting for a slot), 4 jobs at once. All 42 guards
  passed (blocking; 0 advisory, 0 warned)." It includes "Statement catalogue (SC-1): OK … scan (6 adopted)" and
  "self-test: 78 of 78 plants behave".
- Focused (`test_5c_deep_dive_view.py`, `test_5c_deep_dive_api.py`, `test_sc1_statements.py`): 562 passed.
- Test 9 (`--db`, `assetops_test` clone): `test_5c_deep_dive_postgres.py`: "2 passed, 2 warnings in 9.37 s" (it ran after the plants had been restored).
- Plants. Each was planted in the worktree, run against the view and SC-1 tests, and then restored. The tree was
  clean afterwards.
  - P6a, "(at budget)" dropped from the cell: fails test 3.
  - P6b, the same in the drawer row: fails test 3.
  - P22, the headline served unmapped: 7 fail (test 3, and the class test for A, D and L1 to L4).
  - P23, `SCREEN_EVIDENCE = {}`: 11 fail (test 3, the class test L2, 4 b, and test 5's DECLARED rows).
  - P24, drivers flattened: fails 4(H).
  - P26, ANALYSING's comma restored: fails the no-comma case.
  - Currency plants: PC1 (`own_cur` returns the portfolio's currency), PC2 (the by-Site row uses `self.cur`) and
    PC3 (the residual stop uses `self.cur`). Each fails 4 i.
  - Mine:
    - RP3, a group value of `sum or 0`: fails 4 i.
    - RP4, the residual-last sort removed: **survives** (L8).
  - P25 is unit 3's (test 11). On the backend, test 3 asserts that there is no `more` key.
- Probes, in a scratch test that imports the view tests' helpers (`rv-5cbe2/probe`, since deleted):
  - cur1: Kobo and Kisiwa in KES, Mto in USD, Mto's fuel cost not available;
  - cur2: Mto's own root with actual and target in different currencies, the row `bridge.py:202` builds
    (`currency` None, actual and target kept, `CURRENCY_MISMATCH:KES,USD`).

Not verified: unit 3. I did not rerun the full backend suite. These findings are in 5c's view, and no shared code
changed in the fix rounds apart from the two record words.

### Round 1 findings

- **H1, closed.**
  - `view.py:144-151`: `group_sums` carries None.
  - `:221-224`: the tile split and rest appear only when R has an effect.
  - `:346-347`: no drawer effect line without an effect.
  - `:120-122`: no residual stop without a figure.
  - `:385`: the group value.
  - `test_4_i_nothing_compared` (`test_5c_deep_dive_view.py:450`) asserts:
    - the headline `[]`;
    - tile 2 "Not available yet" with no lines;
    - every group and step "Not available yet", and every drawer `["3 of 3 Sites"]`;
    - both cards;
    - the by-Site total;
    - "$0.00" left only in Sites' own rows;
    - the residual stop.
  - In World A's fixture the 22 "$0.00" strings are O&M and staff (actual equals target, at the portfolio and every
    Site), their drawer lines, Kisiwa's carried "$0.00 (at budget)", and in-transit cash for Kobo and Kisiwa.
    Each is a real zero.
- **H2 / D-5C.19, closed.**
  - `words.py:48-56`: `SCREEN_EVIDENCE` maps DECLARED to RECORDED before `money_word`, so §2.4's origin-first order
    decides.
  - Test 5 (`:530-536`) has DECLARED with observed-financial and bench-tested ("Recorded"), source-emulated
    ("Emulated"), demo-simulated ("Simulated"), unknown and no origin ("Estimated"), and mixed ("Emulated").
  - 3A7's `standing.text` and `details` pass through untouched: test 9 asserts SC-1f's "(Declared)" in them, while
    the money words read Emulated and Estimated.
- **M1, closed.** `test_5c_deep_dive_postgres.py:51-58` holds A_TEXT "(Declared)" and A_DETAIL "Fuel cost (Recorded,
  Emulated and Declared): ". `:113-114` maps unit 1's injected literals and asserts each occurs twice. `:141` holds
  B's text.
- **M2 / D-5C.20, closed.**
  - `view.py:166-178`: the gap's word is R's. When a heading is named, it adds that heading's weakest word through
    `W.word`.
  - `test_3_headline_evidence_is_the_figures_words` (`:289`) runs over A, B, D and L1 to L4. In L2, where Grow is
    named, it asserts both words.
  - The headline reads `["Estimated, not yet reconciled"]` in A, `["Estimated"]` in B and `[]` when nothing is
    compared.
- **L1 / D-5C.23, closed.** `tables.py:91-93`'s `CELL_FORM[True]` is "AT_BUDGET". The cell (`view.py:421-422`) and
  the drawer row (`:355-356`) share it. The `carried` sentence keeps "(estimate)", as ruled.
- **L2 / D-5C.21, closed.**
  - `view.py:292-325`: drivers are nested with `key` and `children`. Test 4(H) asserts the §3.5 literal.
  - One gap remains: no world holds a residual driver (L8).
- **L3 / D-5C.22, closed.** Test 3 asserts there is no `more` key on `by_site`, `not_available` or the drawer
  `sites`. `actions` keeps its cap.
- **L5 / D-5C.25, closed.** `vocabulary.py`: BILLING and LOSS_BAND are reworded, and World A's revenue stop and
  not-available rows follow. `test_5_record_words_hold_no_comma_outside_brackets` covers every `record` entry.
- **KD3, closed.** ANALYSING reads "the running record's analysis (still in progress)" in both the vocabulary and
  spec §2.3's table, which has a note.

### New findings

**H3 (High; acceptance gap, honest numbers: "no amount with the wrong currency"). Portfolio figures print in R's
currency, not their own. A Site with a currency mismatch prints in the portfolio's currency.**
- **Where:**
  - `view.py:81`: `self.cur = self.R.currency or "USD"`.
  - Every portfolio figure is printed with `self.cur`, whatever its row's currency:
    - `:380` the step values;
    - `:385` and `:162` the group values and the headline's named sum;
    - `:344-347` the drawer lines;
    - `:339` the driver details;
    - `:322` the driver values;
    - `:411-413` the by-Site total;
    - `:424-442` the cash sentence and total;
    - `:554` the cards.
  - `:93-96`: `own_cur` falls back to `self.cur` when a Site's own root has no currency, which is exactly the case
    when that Site's actual and target differ in currency (`bridge.py:202`).
  - `:144-151`: `group_sums` adds steps' effects without checking that they share a currency.
- **Probe cur1.** Kobo and Kisiwa are in KES, Mto in USD, and Mto's fuel cost is not available. R is a mismatch, so
  `self.cur` falls back to "USD". 5b's fuel cost row sums Kobo and Kisiwa in KES (`currency` "KES", k = 2), and the
  screen prints it as "−$730.00" in all of these places:
  - the Optimize group;
  - the fuel cost step;
  - the drawer lines ("Actual $4,595.00 · Target $3,865.00 · Difference +$730.00");
  - the by-Site total;
  - the Optimize card.
- **Probe cur2.** Mto's own root has its actual and target in different currencies (5b §5's case (h)). Mto's by-Site
  row prints its actual and target as "$810.00" and "$915.00", in the portfolio's currency. In real data one side
  would be KES, printed with "$".
- **Why it matters.**
  - It is the class the coordinator named: a KES amount printed with "$". Test 4 i does not reach it, because there
    every portfolio row is a mismatch and so reads "Not available yet".
  - Both states are designed. 5b sums a one-currency subset with k < n, and §5 (h) tests a Site's own mismatch.
- **Fix (5c only).**
  - Print each portfolio figure in its own row's currency (`row.currency`), falling back to `self.cur` only where
    the value is None. In `cash`, use the cash rows' currency.
  - `group_sums`: a heading whose steps' effects are in more than one currency is None, reading "Not available
    yet".
  - `own_cur`: when the Site's root currency is None, print the actual in the actual side's currency and the target
    in the target side's (`sb.actual.values[root].currency`, `sb.targets.structure.values[root].currency`), or read
    "Not compared". Never use the portfolio's currency.
  - Tests: add cur1 and cur2 as 4 i variants, asserting no "$" on a KES figure anywhere in the payload.

**M3 (Medium; a false sentence, spec gap). A mini-grid Site out of k for a currency mismatch reads "not a mini-grid
Site, not included."**
- **Where:**
  - `view.py:270-277` `out_line`: with no `actual:` or `target:` reasons it falls to `NOT_MINI_GRID`;
  - `portfolio.py:104-107`: a Site whose root effect is None gives `()` when nothing is unobserved, which is the
    currency mismatch case.
- **Probe cur2.** The revenue drawer's `out` reads ["Mto: not a mini-grid Site, not included."].
- **Why it matters.** Mto is a mini-grid Site, so an executive is told something untrue about it. §2.5 has no `out`
  wording for this case.
- **Fix.**
  - Use `NOT_MINI_GRID` only when the code is not in `self.sb`, or for 5b's `NOT_DECLARED` and `sites_excluded`
    reasons.
  - For a Site whose own row stops on a currency mismatch, use a currency `out` variant. The Architect supplies the
    literal, for example "{site}: not compared: the actual and the target are in different currencies (KES and
    USD).", reusing the §2.5 stop.
  - Add a test.

**L7 (Low; spec question). The portfolio's currency mismatch is never stated.**
- **Where:** 5b's `PortfolioRow.note` (`CURRENCY_MISMATCH:KES,USD`) is read nowhere in `view.py`.
- **What happens.** In 4 i the headline reads "Contribution for October is not available yet.", and nothing on the
  page says why, although the reason is in the payload's inputs.
- **Fix.** The Architect decides whether `headline_na` (or a notice) names the currencies. This is not blocking.

**L8 (Low; test gap). D-5C.21's residual placement is not exercised.**
- **Where:** `view.py:306-316`.
- **What happens.** My plant RP4 (the residual-last sort removed) survives. No test world has a `residual:<x>` row
  under a step, so nothing checks a residual's parent or its last-place order.
- **Fix.** Add a small case: a step with a split child and its residual, asserting the residual is the last child
  of its parent.

### Answer to the coordinator's question: totals across currencies

They should not exist, and they do not. 5b's `_row` returns no sums and no effect when the included Sites hold two
currencies (5b spec §2, "sums and effect None"). 5c then prints "Not available yet" for R, the groups, the steps,
the cards and the by-Site and cash totals, as 4 i asserts. That is honest: no figure is invented, and none is shown
as 0.

A total over one currency's Sites (k < n) is a real figure, labelled with its "k of n Sites". It must print in its
own currency (H3). Spec §3.2's `total` ("R's actual, target, effect") and §3.3 ("total from the portfolio rows")
assume one portfolio currency. The fix keeps them true by printing each row in its own currency.

### Residual risk

- With H3 fixed, a page can show a KES step beside a USD step, with the headline "not available yet". That is honest,
  but the mix is easy to misread, and L7's wording would help.
- Unit 3's fixture must carry H3's and M3's results only if the screen's tests use a mixed-currency world. World A
  is USD and is unaffected.

### Disposition

ACCEPT WITH FIXES. H3 and M3 are fixed on the branch before units 1 and 2 merge, with M3's literal from the
Architect. Then a verification round checks H3 and M3 only. L7 goes to the Architect. L8 is fixed with H3's tests
or recorded.

## Round 3 (verification): units 1 and 2 (backend), fix round 3

Reviewer: Claude (fresh; did not author the work), 2026-11-21. Branch `task/5c-deep-dive-screen` at `1f6d60f0b`
(worktree `AssetOpsV1-5cbe`), against round 2 at `a3bf31fdf`. Depth W6: H3, M3, L7 and L8 with their sweeps, plus my
own probes over currency mixes the builder did not use. Paths below are under `backend/assetops_backend/`.

**Summary (verdict: ACCEPT WITH FIXES)**
- **H3 closed in code.** `self.cur` is gone. Every amount in four new probes prints in its own rows' currency.
- **M4 (new, Medium).** H3's R-currency path has no test. My plants RP5 and RP6 put "USD" back and both survive.
- **M3 open (Medium).** The sentence is no longer "not a mini-grid Site", but the new literal is still untrue in the
  builder's own case: Mto's target is in USD. The reference currency is also arbitrary when no portfolio currency
  exists.
- L7 is closed in behaviour; I recommend rewording its literal. L8 is closed (RP4 now fails).
- **L9 (new, Low).** A card whose heading mixes currencies reads "Not available yet" beside an evidence word.
- H1, H2, M1 and M2 still hold.
- check-all: 42 of 42 guards pass. The statement guard passes (6 adopted), and its self-test passes 78 of 78.

### Checks run (1f6d60f0b)

- Focused (`test_5c_deep_dive_view.py`, `test_5c_deep_dive_api.py`, `test_sc1_statements.py`, from `backend/`):
  569 passed.
- Test 9 (`--db`, the handoff's command; the harness clones a run-owned `_test` database):
  `test_5c_deep_dive_postgres.py` 2 passed in 9.34 s.
- `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1` (with
  `ASSETOPS_GUARD_PYTHON` set): "check-all: 146.7 s wall (0.2 s waiting for a slot), 4 jobs at once. All 42 guards
  passed (blocking; 0 advisory, 0 warned)." It includes "Statement catalogue (SC-1): OK … scan (6 adopted)" and
  "self-test: 78 of 78 plants behave".
- Plants, each restored afterwards; the tree was clean after every one.
  - The builder's, spot-checked:
    - C3 (a heading over mixed currencies sums): fails `…a_heading_over_two_currencies`.
    - C12 (the `own_cur` side fallback returns "USD"): fails `…a_sites_own_sides_differ`.
    - L7 (the headline reason dropped): fails 4 i and `…one_currency_subset`.
    - M3 (the `out_currency` branch dropped): fails `…a_sites_own_sides_differ`.
  - Mine:
    - RP4 (the residual-last sort) now fails `test_4_h_residual_is_last_of_its_parent`.
    - **RP5** (`view.py:235` `cur = "USD"`) **survives**. **RP6** (`view.py:431` the totals' actual in "USD")
      **survives** (M4).
- Probes, in a temporary test file in `tests/` (deleted), with the whole payload dumped:
  - P1: Kobo KES, Kisiwa TZS, Mto USD;
  - P2: Kisiwa alone in KES;
  - P3: Kobo TZS, Kisiwa EUR, and Mto's own actual KES with its target USD;
  - P4: Kobo and Kisiwa KES, and Mto's actual KES with its target USD;
  - P5 and P6: the Optimize heading over KES and USD steps.

Not verified: unit 3, and the full backend suite (no shared code changed; the diff is 5c's view, words and
statements).

### Round 2 findings

**H3, closed in code; its R path is untested (M4).**
- `self.cur` is removed. No "USD" default is left in `deep_dive/`: grep finds only the comment at `words.py:75`.
- P1 and P2: R, every step, heading, card and total read "Not available yet", and the headline gives the L7 reason.
  Every Site's by-Site, drawer and cash cells print in that Site's own currency (KES, TZS or USD), "(at budget)"
  included.
- P3: Mto prints its actual in KES and its target in USD (`view.py:445-446`). Kobo prints in TZS and Kisiwa in EUR.
- P4 (R in KES): every portfolio figure prints in KES. That covers the tiles, the bridge title, the totals, groups,
  steps, drawer lines, by-Site total, cash sentence and total, cards and headline.
- P5: the fuel cost step reads "−KES 730.00" and O&M "$0.00", while the Optimize heading and its card read "Not
  available yet" (`view.py:152-170`).
- The two exclusions from the whole-payload check are sound.
  - Notices print in `check.currency` (`view.py:267-268`).
  - The organisation's budget lines print in `line.currency` (`view.py:402-403`).
  - Both are the currency of the budget they quote. The patched worlds change only bridge rows, so those budgets stay
    in USD while the bridge rows turn to KES. That is an artefact of the test worlds, not a wrong label.
  - A line with no currency is now dropped (`view.py:403`). That is acceptable, since a money budget line without a
    currency cannot be printed honestly.
- "XXX" pass-through (`words.py:76`, `:84`). `reconciliation.money_word`'s text is `{word}` alone, so the carrier
  never prints, and no probe string contains "XXX". It reaches a visible word in one case only (L9).

**M3, open (Medium; the literal is still not true).**
- `view.py:313-324` with `deep_dive.py:365-367`: "{site}: its figures are in {currency}, not {portfolio_currency}, so
  it is not included."
- The `out` branch fires only when the Site's own root stops on `CURRENCY_MISMATCH` (`view.py:302`). That is 5b case
  (h): its own actual and target are in different currencies. So one of the Site's own currencies is always among
  its figures.
  - In the builder's own test (cur2), "Mto: its figures are in KES, not USD", Mto's target is in USD, and the by-Site
    row beside it prints "$915.00".
  - In P4 it reads "Mto: its figures are in USD, not KES", while Mto's actual is "KES 810.00".
  - In P3 it reads "…in KES and USD, not TZS". TZS is just the first other Site's currency; no portfolio currency
    exists, because Kisiwa is in EUR.
- The reference rule (the step row's, else R's, else the first other Site's, else its own target's, else the last
  held) has no honest answer when the portfolio has no currency, so the sentence names one that isn't there.
- **Fix.** Drop the reference and state the real reason, reusing the spec's §2.5 stop literal
  (`spec.md:184`, "Not compared: the actual and the target are in different currencies ({a} and {b})."):
  "**{site}: not compared: its actual and its target are in different currencies ({currencies}).**" `currencies` is
  the held pair from the reason. `portfolio_currency` and the reference chain go. Update the case in
  `tests/statement_cases/deep_dive.py` and the `outs` assertion in `…a_sites_own_sides_differ`. The Architect confirms
  the literal.

**L7, closed in behaviour; literal: recommend reword.**
- `view.py:196-197`. It fires only when the gap is None and R's note is a currency mismatch. In P1, P2 and P3 the
  statement is true, and it is not shown in P4, where R sums.
- The literal "Not available yet: the Sites' figures are in different currencies." is honest and plain. It drops the
  subject and the month, though, which every other headline carries, including the one it replaces ("Contribution for
  October is not available yet."). A reader landing on the page is not told what is not available.
- **Recommendation:** reword it to "**Contribution for October is not available yet: the Sites' figures are in
  different currencies.**" That means a headline variant with the month slot instead of a bare `deep_dive.text`
  piece. It uses no number word, so LITERAL_NUMBER_WORD passes. If the Architect keeps the bare piece, accept it as
  it is; it is not blocking.

**L8, closed.** `test_4_h_residual_is_last_of_its_parent` asserts nested order with two residuals, and RP4 fails it.

**H1, H2, M1 and M2 still hold.**
- `test_4_i_nothing_compared` (H1) passes with only the headline literal changed.
- Test 5 and test 9 (H2, M1) pass.
- `test_3_headline_evidence_is_the_figures_words` (M2) passes. The named heading's word now carries
  `group_cur(subject)` (`view.py:204`), which is reached only when that heading's sum exists.

### New findings

**M4 (Medium; test gap on H3's own class). No world puts R in a currency other than USD.**
- **Where:** the R figures printed with `R.currency` (`view.py:193`, `:235-253`, `:431-432`, `:458-459`).
- **What happens:** my plants RP5 (the tiles in "USD") and RP6 (the totals' actual in "USD") survive all 161 view
  tests. Every test world's R is USD or None. A regression to a USD default, the bug H3 fixed, would pass.
- **Fix:** add a 4 i variant with every Site in KES (or P4's world). Assert no "$" anywhere in the payload outside
  `.notices` and `.lines_org`, and that the tiles, totals and headline start with or contain "KES". Then confirm RP5
  and RP6 fail.

**L9 (Low). A card over mixed currencies shows a word beside no figure.**
- **Where:** `view.py:603-604`. The card's `word` comes from `heading_evidence` whatever the sum, and `W.word` carries
  "XXX" when `group_cur` is None.
- **Probe P6:** Optimize's steps are fuel cost in KES, O&M in USD and staff in KES. The card reads value "Not
  available yet" with word "Emulated". Everywhere else a missing figure reads "Not available yet" for both.
- **Fix:** the card's word is "Not available yet" when `group_cur(category)` is None. The same could be done in
  `W.word` for a None currency, which would retire "XXX". Not blocking.

### Residual risk

- Mixed-currency pages show KES, TZS and USD cells side by side with every total "Not available yet". That is
  honest, and the L7 headline now says why. Unit 3 should check that the narrow by-Site table stays readable with
  "−TZS 1,445.00"-length cells.
- `out_line`'s currency branch (`view.py:302`) overrides every other `out` reason for that Site. That is right while
  the root itself stops, because nothing of the Site is compared.

### Disposition

ACCEPT WITH FIXES. Fix M3 (the literal and dropping the reference, Architect to confirm) and M4 (the all-KES test) on
the branch before units 1 and 2 merge. A verification round then checks those two only. L7's reword and L9 are
recommended, not blocking; the Architect logs the L7 literal decision.

## Backend fix r5 (verification, D-5C.26 to D-5C.28, KD1, KD2, PF1)

Branch `fix/5c-backend-r5` at `1ec0a46fc`, diff against `4b13c0afe` (merge base). Fresh reviewer, verification depth
(W5) on spec rev 4 §11 "Backend fix", rulings D-5C.26 to D-5C.28 and `packet-backend-fix-r5.md` (KD1, KD2, PF1).

**Summary (verdict: ACCEPT).**
- D-5C.26: every figure slot's word (tiles 0 and 1, steps, drivers, Grow and Optimize cards, cash, headline evidence)
  goes through `_View.figure_word` (`view.py:143-148`); L9's line is gone, `NO_CURRENCY` is deleted, and no other
  `W.word` caller remains. Class test 16 holds in all 11 worlds.
- D-5C.27: `bridge_bars` (`view.py:56-90`) follows §3.2. I recomputed A and V1 to V6 by hand and all match.
- D-5C.28: `shares()` returns `{}` at a gap of None or 0 (`view.py:323-327`); World X and the gap-0 payload carry
  no share and no "Offsets it".
- KD1 is honest in A and in the five currency worlds. KD2: a gap of 0 renders with no rest line. PF1: the route's 500
  on the emulated budget is gone. I confirmed this on a `*_test` database, with a control run that still shows the 500.
- Two Low findings, neither blocking. Every check is green.

### Hand recomputation (D-5C.27)

- **World A** (−97, −755, gap −852): b1 = 97/852 × 100 = 11.38497…, b2 = 100, lo 0, hi 100. Revenue {0.00, 11.38,
  lowers}; fuel cost L = 11.38497… → "11.38", W = min(88.61502…, 100 − 11.38497…) → "88.62", lowers. O&M and staff
  have effect 0, so null. Scale {0.00, 100.00}. This matches `A_BARS`/`A_SCALE` and the hand-edited fixture.
- **V1** (+50, −150; −100): spans 0→−50 and −50→100, so lo −50 and hi 100. The bars are {0.00, 33.33, raises} and
  {0.00, 100.00, lowers}, and the scale is {33.33, 100.00}.
- **V2**: the bars are {0.00, 0.80 (floor of 0.10)} and {0.10, 99.90}.
- **V3**: [None, {0.00, 100.00}].
- **V4** (gap None) and **V5** (gap 0): every bar and the scale are None.
- **V6** (−150, +50; −100): spans 0→150 and 150→100, so hi is 150. The bars are {0.00, 100.00, lowers} and {66.67,
  33.33, raises}. The second width is capped at 100 − 66.666…, and the scale is {0.00, 66.67}.

All six match `test_bars_vectors`. The page does no arithmetic: the slice serves only strings, and no frontend file
changes.

### KD1 in the worlds (printed payloads, my probe)

| World | Headline evidence | Optimize card |
|---|---|---|
| A | ["Estimated, not yet reconciled"]. The gap and the heading share one word, deduplicated as before. | −$755.00 "Estimated, not yet reconciled", unchanged |
| X, nothing, two | [] | null figure, null word |
| subset | [] | −KES 730.00 "Emulated". This is fuel cost's word, the only step its sum adds. Before KD1 it read "Not available yet". |
| all_kes | ["Estimated"] | −KES 755.00 "Estimated" |
| sides | ["Estimated"] | −$730.00 "Estimated" |

The word always describes what the sum adds, so KD1 is honest. A step with effect 0 (O&M "Estimated") still counts
toward the word, as it should, because 0 is a figure.

### Plants

The packet's P-a and P-b reproduce: P-a fails 3 tests and P-b fails 7. My own plants, applied to a scratch copy and
not to the worktree:

| Plant | Result |
|---|---|
| Pr2: KD1 reverted | fails `test_16[subset]` |
| Pr3: the width cap from a rounded `left` | fails `test_bars_vectors[V6]` |
| Pr4: `"L"` dropped from `UNIT_WORDS` | fails 10 tests, among them `test_1_driver_units_have_words` and `test_4_h_kobo_litres` |
| Pr1: `bar_effect` ignores the row's currency | survives |
| Pr5: the contribution tile's word built from `R.effect` instead of `R.actual` | survives |

Pr1 and Pr5 survive, and I traced why neither is a gap.

- **Pr1.** The ruling's "row's currency is not R's" clause cannot be reached through the real bridge. A Site whose
  root has no effect returns no child rows (`bridge.py` `made(..., rows=())` on GAP_NOT_AVAILABLE and on
  CURRENCY_MISMATCH). So every step's Sites are a subset of R's Sites, and they share R's currency.
- **Pr5.** A portfolio row's actual is present only when its effect is, so the two words are the same.
- **What a forced Pr1 world shows.** I forced the Pr1 case by blanking only a Site's root effect while keeping its
  child rows, which the bridge never produces. In that world the headline raised `CONDITION_TYPE` ("more_than_gap"
  over two currencies). The fault is in code that predates this slice and that world cannot occur, so I record it as
  residual risk, not as a finding.

### Findings

**L1 (Low; preference/tidy). `view.py:9-13`: a second `from collections.abc import Sequence` line, out of order.**
- It sits after `datetime`, beside the existing `from collections.abc import Mapping`.
- It has no behaviour effect, and check-all passes.
- Fix: merge it into one `from collections.abc import Mapping, Sequence`. This can wait for the screen fix's merge of
  `main` or the next touch of the file.

**L2 (Low; test). `test_5c_deep_dive_view.py:748`: `test_1_driver_units_have_words` skips any unit with other than
one non-money dimension.**
- `driver_detail` (`view.py:422`) indexes `T.UNIT_WORDS[others[0]]` for every non-money unit.
- Today every reachable MINI_GRID unit has exactly one non-money dimension: KWH, L, MONEY/KWH or MONEY/L. I listed all
  29 reachable factors.
- If a two-dimension unit (say L/kWh) became reachable, the test would skip it silently, while the route could raise
  `KeyError`, which is a 500.
- Fix: assert `len(others) <= 1` for every reachable factor instead of `continue`, so a new shape fails the test.
  This is not an acceptance gap.

No acceptance gap. Each of §11 items 1 to 6 holds as the packet states:
- the key orders `key, label, value, share, word, sites, bar, drawer` and `title, totals, scale, groups, by_site`
  are asserted in test 3;
- the schema id is unchanged;
- the fixture was edited by hand;
- `deep_dive_worlds.py` provides `world_h`, `world_x`, `in_kes` and `gone`;
- `test_4_i_currency_card_word_beside_no_figure` runs on `world_x()` and asserts a null word.

### Checks run (this reviewer, at `1ec0a46fc`)

- Focused tests, from `backend/` through the slot: `test_5c_deep_dive_view.py`, `test_5c_deep_dive_api.py`,
  `test_5b_attribution.py`, and the three non-Postgres `test_3a7_*` files. Result: `382 passed, 1 skipped, 1 warning
  in 6.80s`.
- Test 9, through `heavy-slot.sh --db --wait-seconds 3000` and `run-host-tests.ps1`, on
  `backend/tests/test_5c_deep_dive_postgres.py`: `2 passed, 2 warnings in 9.44s`, exit 0.
- Statement catalogue: `OK statement catalogue: load, coverage, legacy, scan (6 adopted), keys, imports`, exit 0.
- Check-all, fast, through the slot: `All 42 guards passed (blocking; 0 advisory, 0 warned).` It took 146.0 s; the
  estate and pool self-tests were skipped as unchanged.
- The PF1 route check used a throwaway detached worktree of main `06a5b9e3e` (DDR's base) with this branch's
  `backend/` diff and DDR's diff applied. Nothing was committed, and the worktree was removed afterwards.
  - DDR's `test_3_the_emulated_budget_loaded_fails_g3` (`-k emulated_budget`) was given one extra assertion: S7 and
    S10 exit 0.
  - With the fix: `RV-EXITS {'S7': 0, 'S10': 0}`, `1 passed`.
  - Control, with `deep_dive/{view,tables,words}.py` reverted to base: `RV-EXITS {'S7': 500, 'S10': 500}`, `1 failed`.
  - So the original 500 on the emulated `budget.csv` through `/api/portfolio/month` is gone with this fix.

### Not verified, and residual risk

- **Layout evidence: not applicable.** No page changed in this slice. The screen fix carries the gates on A, X and H.
- **The screen branch still uses the names this slice removes.** `task/5c-unit3-screen` still calls `self.word`, keeps
  `NO_CURRENCY`, and uses `t._in_kes` and `t._gone` in `make_screen_worlds.py`. The screen fix's item 1 (merge `main`,
  rewrite the generator on `deep_dive_worlds`) must drop all of them, or its merge fails on import.
- **A latent crash in code that predates this slice.** The headline crashes if a heading's currency ever differs from
  R's (`CONDITION_TYPE` above). The bridge cannot produce that today. If 5b's portfolio rule changes so that a Site
  with no root effect still contributes step rows, this crash becomes a 500.

### Disposition

ACCEPT. L1 and L2 are optional and do not block. The merge can go ahead under the screen fix's own gates.
