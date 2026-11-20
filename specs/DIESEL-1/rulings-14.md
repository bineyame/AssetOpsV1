## 9u. Ruling DIESEL-1-R3u — four-Site rehearsal failures (F-COH, MILL-5, KIS-8a, KIS-6), guard S-h, Kisiwa S−5d Protect

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only. Code read in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal` at eacdd5bad; it has no `backend/` or `config/` diff against its merge base f34376322). Evidence: `var/demo3_k9rehearsal` (`check.json`, the COH bundle `dd1b2-coh-havc4t61`, `kisiwa.json`). SELECT-only reads on `assetops_demo3_k9rehearsal_test`. No suites, no writes.

### 9u.1 Verdicts, item by item

**U1. UF1 (KIS-8a, F-COH week and S). Cause confirmed: false positive. Owner: K9 fix round.**
- `tools/checks/chain_coherence.py:1347-1348` pairs every fuel amount with every other same-currency amount. Kobo's Optimize earnings `value.low` is `0.00` USD (the schema pins `amount_low` to 0), so 119.57 + 0.00 and 180.43 + 0.00 are "found" in the Protect fuel line, which prints those amounts on their own. Nothing is added.
- **Fix: exclude a pair with a zero addend.** A sum with 0 equals its other addend, so it can never show adding. Excluding it loses no detection. I rejected the wider rule "drop any sum equal to a listed amount", because it could hide a real total that happens to equal another amount.
- Put one helper in `chain_coherence.py`. `demo_combined_rows.py` already imports from that file.
  ```python
  def nonzero_pair_sums(pairs: Iterable[tuple[tuple[Any, Decimal], tuple[Any, Decimal]]]) -> set[str]:
      """R3u: the two-place sums of same-currency pairs, neither addend zero (a sum with 0 shows no adding)."""
  ```
- Use it at all four places that search for a sum of two amounts. All four have the same zero-addend hole:
  1. UF1, `chain_coherence.py:1347-1348`;
  2. PV1, `:1299-1302`;
  3. `demo_combined_rows.py:380-381` (`pv_values`);
  4. the KIS-4 sum, fuel amount + dispatch `amount_high` and fuel + fuel (`demo_combined_rows.py` `kis4`, after `:431`).
- **Tests** in `tools/checks/test_chain_coherence.py` and `backend/tests/test_demo_combined_finish_rows.py`:
  - A Kobo low of `0.00` with Kisiwa 119.57/180.43 printed in the fuel line gives no UF1 finding. This is the rehearsal shape.
  - A planted non-zero sum, 119.57 + 15.13 = `134.70`, in a card string is still a finding. This is the non-vacuity case.
  - The same pair of cases for PV1 and for `pv_values`.
  - A KIS-4 case with a zero dispatch `amount_high`.

**U2. A1 (KISIWA-001, week/S/month). Cause confirmed: real product defect, demo-visible. Owner: new product unit DIESEL-K6c (K6b area).**
- The Assure headline counts `actions` and `opp` only (`site_outcomes/mini.py:572-573`). But `_assure` lists `fuel` verdicts as entries (`:1211-1222`).
- The bundle's Kisiwa S board reads headline "No verified result yet" beside "ACT-004 verified on example data" (`FUEL_VERDICT`). It is the same on all three windows.
- **Fix:**
  ```python
  verified = (sum(1 for a in actions if a.verification_state == "VERIFIED")
              + sum(1 for o in opp if o.outcome == "VERIFIED")
              + sum(1 for f in fuel if f.outcome == "VERIFIED"))   # R3u: the fuel verdicts `_assure` lists
  ```
- A fuel Action is a FUEL_BALANCE domain Action. It reaches the board only through `site_chain.fuel_verdict_actions` (`mini.py:492-494`), and its verification state is not counted VERIFIED among `actions`. That is why A1 fired. So there is no double count.
- Kisiwa's headline becomes "1 verified result" on boards whose work window holds ACT-004. This matches v69's count form, so it is not a mock deviation.
- `site_outcomes/read.py:521-522` `_verified_results` documents itself as "the Assure headline's number" (MB-1-R Q5). Add the same term to it: `+ sum(1 for f in comp.facts.fuel_verdicts if f.outcome == "VERIFIED")`.

**U3. L2 (summary `verified_result_count` against `count.verified_results`). Cause confirmed, two parts. Owner: DIESEL-K6c.**
- **Week 2 vs 3 and month 2 vs 3.** This is U2's cause, through `read.py:521`. The chain counts Kisiwa's verified fuel thread; the summary does not.
- **S, 2 vs 1. This is not Kisiwa, and it predates the K lane.** The bundle shows:
  - The summary sums each board's `_verified_results`. A mini board counts the VERIFIED Actions of its **work window** (`mini.py:450`, `WORK_WINDOW` back from the board day). Kobo's S board lists ACT-001 (trial, ACTION) and ACT-005 (mill, DOMAIN_VERDICT), so it gives 2.
  - The claim (`chain/claims.py:133-164`) counts only threads with a Finding occurrence meeting `[lo, hi)`, plus opportunity Actions whose opportunity occurrence meets `[lo, hi)`. On S, Kobo gives `verified` 1 (the ACT-001 thread) and `verified_actions` 0 (the mill's opportunity episode is not on the S day).
  - The two numbers have different definitions, so they agree only when every verified Action's episode is inside the window. They split on any one-day window.
  - With U2's fuel term alone, S would go to 3 vs 1, because ACT-004's night 10-31 is in Kisiwa's work window but not on S.
- **Fix: one computation.** The summary's legacy count becomes the claim's value, which is what CH6b3-R3 L2 states it should be. In `SiteOutcomeBoardService._summary` (`read.py:639-692`):
  - set `"verified_result_count": None if counted is None else counted.claims[VERIFIED_RESULTS].value`, with `VERIFIED_RESULTS` imported from `chain/claims.py`;
  - remove the `verified += body.get("_verified_results", 0)` sum;
  - keep `verified_read` for `verified_sites_unread`, which is unchanged.
- The field has no reader on screen (`frontend/src/estate/estateClient.ts:660` types it; nothing renders it). So there is no visible change and no mock question. L2 now holds by construction and stays as a guard against regression.
- **K6c tests** (new file `backend/tests/test_k6c_assure_fuel_count.py`, plus edits):
  1. Mini compose with fakes: one VERIFIED `FuelVerdictFact`, no trial or mill. The headline is "1 verified result", the verified entries are 1, and the A1 rule (`_coh17_a1`) passes.
  2. A fuel verdict that is PENDING, INEFFECTIVE or INCONCLUSIVE is not counted.
  3. A VERIFIED trial, mill and fuel verdict together give "3 verified results".
  4. `board(...)["_verified_results"]` includes the fuel verdict (extend `test_mb1_opportunity_board.py:280-313`).
  5. A summary where the board-sum would be 2 and the claim is 1 (the S shape) reports 1. Without a chain reader it reports None.
  6. Update `test_out_b4_read.py:250-259` to rule 5. Keep its `verified_sites_unread` assert.
  7. Non-vacuity: dropping the fuel term fails 1 and 4. Restoring the board-sum fails 5.

**U4. MILL-5. Cause confirmed: mechanical. Owner: K9 fix round.**
- `tools/demo_combined_finish.py:966` uses `psycopg` in `mill5` (`:955-970`) with no local import. Eleven other rows import it locally (`:359`, `:429`, …).
- `demo_rows.mill_assure` (`:965`) returned before the error, so WD-1m holds. The stored-outcome SQL never ran.
- **Fix:** add `import psycopg` as the first statement of `mill5`.
- **Test:** an L0 AST test over `tools/demo_combined_finish.py`. Every function that names `psycopg` must import it in its own body, because the module has no top-level import. Planting the rehearsal shape (removing the import) must fail it.

**U5. KIS-6. Cause confirmed: mechanical. Owner: K9 fix round.**
- `kisiwa.json` `verdict` is a dict, `{…, "state": "VERIFIED", "stored": true}` (`demo_combined_kisiwa.py:688`). Line `demo_combined_rows.py:1140` compares the whole dict with the string.
- **Fix:** `want = 1 if (kisiwa_doc.get("verdict") or {}).get("state") == "VERIFIED" else 0`. In the assert message, report `(kisiwa_doc.get("verdict") or {}).get("state")`.
- **Tests:**
  - a dict verdict VERIFIED with `threads.verified` 1 passes;
  - a dict verdict INEFFECTIVE with `threads.verified` 1 fails;
  - a case runs past `:1143`, so the Assure card claim and the H2 asserts are reached.

**U6. Watermark guard stop S-h (`unlisted_modules`, 5). Legitimate reach, predates K9. Owner: DIESEL-K6c (`config/` is hashed into `code_version`, so this is a product-side change).**
- **What the list is.** It is the clock-guard scan set (`backend/tests/test_ch5c2_clock_guard.py:3`). An unlisted module that a stored compose runs is a hole in the static wall-clock scan. It is not a wrong read: `untracked []`, `unresolved []`, 0 non-200.
- **Which unit introduced each:**

  | Module | Introduced | Reached in compose through |
  |---|---|---|
  | `actions.fuel_verification` | K6b (aa7020754) | the fuel verdict read (`actions/verification.py:427-495` lazy imports); its ports are built lazily (`actions/composition.py:130-163` `_Lazy`, K6b) |
  | `actions.verification_families` | CH-9b2 (cbbf3325d); fuel family registered by K6b, value code by MV-1 | `verification.py:368-392`, `:523` lazy imports, through the mill verdict value (`mini.py:1179` `verdict_value`, PV-1/MV-1) and the fuel path |
  | `financials.composition`, `financials.assumptions` | S4-02a (28668d956); the productive-price builder by MV-1 (4791d7b27) | `VerificationPorts` builders (`actions/composition.py:114`, `:126`) and the lazy `PRODUCTIVE_PRICE_KEY` import (`financials/composition.py:164`), first run inside a compose |
  | `financials.fuel_cost_v2` | FUEL-1 A1 (972dc747f) | the consequence store or read (`postgres_consequence_store.py:33`, `consequence_read.py:37`), built when K6b's lazy fuel-balance store is first used (`fuel_balance/composition.py:39`) |

- **All five predate K9.** They are ancestors of K8 (ffc23b202), and K9 has no product or config diff.
- **Why the guard missed them.** K8's guard run (+2 modules) used a database without both the mill VERIFIED verdict and Kisiwa's fuel verdict. This rehearsal is the first guard run where both exist in one estate, so these lazy paths ran for the first time.
- **No forbidden reach.**
  - `fuel_verification` still imports no `financials`, `fuel_cost*` or price module (its docstring, `:16`).
  - The financials modules are reached through lazy port construction, which is the `_Lazy` design.
  - Grep of the five files finds no `datetime.now`, `utcnow`, `date.today`, `time.time`, `now()`, `clock_timestamp` or `current_timestamp`.
- **Fix:** add the five names to `config/chain/stored-composer-modules-v1.json` in sorted order, as a reviewed diff. `test_ch5c2_clock_guard.py` must pass with them listed. Any hit from it is a stop to report, not an allowlist edit.
- **Proof:** the post-fix guard run (§9u.2 step 3) uses `--modules-out`. The observed list must equal the committed list exactly. Any other unlisted module is stop **R3u-s2**.

**U7. Kisiwa S−5d board: Protect UNKNOWN, MG-8 PRODUCER_NOT_SETTLED. K10 does not decide it, and the evidence conflicts. Owner: K9 fix round (pin) and the runner.**
- **K10 settles MG-5 and MG-4.** It makes declared-absent days settled, so `base` is true (`mini.py:510`, `:521-522`), and Grow, Optimize and Assure settle with them.
- **K10 does not touch MG-8.** MG-8 settles from night D−1's window, its assessed state and the fuel Finding read (`mini.py:525-526`). It does not depend on `productive_kwh`.
- **The R3s2 expectation is met without K10.** The rehearsal's own served body of the same board (`dd1b2-coh-havc4t61/board.day_kisiwa_fuel-morning_2026-11-01.json`, window 10-31T21Z to 11-01T21Z, AVAILABLE) reads:
  - Protect `NEEDS_ATTENTION`, lead MG-8;
  - MG-8 `{state: NEEDS_ATTENTION, reason: PRIMARY_FINDING_OPEN}`;
  - MG-5 and MG-4 UNKNOWN.
- **The data agree with that body.** Night 10-31's window exists, revision 1, `UNEXPLAINED`, recorded 2026-11-01T12:30Z. Kisiwa has 0 unconsumed `finding.revised` events.
- **The packet's UNKNOWN quote is a second, unreconciled read.** I cannot reproduce it from code or data without a compose, which would write cache rows to the kept database. So I treat it as unexplained, not as the product state.
- **Pin (K9 fix round, in KIS-OV, which already reads the S−5d board through `ctx.get(date=…)`):**
  - assert that the S−5d Protect row `state` is `NEEDS_ATTENTION`;
  - assert that its MG-8 outcome entry is `{state: NEEDS_ATTENTION, reason: PRIMARY_FINDING_OPEN}`;
  - do not assert the lead, because with K10, MG-5 and MG-4 may settle;
  - when the assert fails, the row records the board's `read_state` and `warnings`, and a second read of the same day by the local `from`/`to` pair.
- **Stop R3u-s1:** UNKNOWN on the post-fix clone. That is a demo beat; report it to the Architect with both reads and do not patch.
- **Tests (L0):** a NEEDS_ATTENTION board with that MG-8 entry passes; the packet's UNKNOWN/PRODUCER_NOT_SETTLED shape fails.
- **Note, not a fix.** The Protect headline "Battery and generator condition are not assessed" is the fixed `PROTECT_HEADLINE` literal (`mini.py:579`). K10 does not change it.

**U8. KIS-7 item 3 and stop S-s4: asserted again (K9 fix round).**
- R3s2 made them report-only only while d1 was unsettled. K10 settles d1 (§9t.4).
- **Fix:** restore the R3s2-relaxed assert and its L0 break cases (an unpriced d1, or a d1 amount that differs, fails again).
- The check that exercises them runs only with K10 in (§9u.2). If K10 is held, revert to R3s2's report-only form with its quoted reason.

### 9u.2 Order: no re-check on the kept DB; one clone serves K10 phase 2 and the post-fix check

**Can a product fix be checked on the kept DB without a new prepare?**
- **No new prepare is needed.** Every fix is read-side: a board headline term, a summary field, a config list and check-tool code. No stored row, prepare step or story changes.
- **But it cannot be checked on the kept DB.** `code_version` hashes every backend `.py` **and every `config/` file** (`chain/adapters/file_code_version.py:3`, `:46-54`). So K6c, which includes the module list, and K10 both make every stored body stale. A `finish check` would then recompose and write read-through rows into the kept database, and the kept database would stop being the rehearsal evidence.
- **The kept DB stays untouched.**
- **No tools-only re-check on the kept DB either.** K9's tools-only fixes (U1, U4, U5) do not change `code_version`. But such a run would still fail A1/L2 and costs about 20 minutes of machine time, so it is folded into the clone check below.

**One clone, three code states, in this order** (the runner is the K10 phase-2 builder, in one context):
0. **Clone.** Create `assetops_k9_audit_r3u` from the kept DB (authorized scratch pattern), and copy `var/demo3_k9rehearsal` to `var/demo3_r3u`. Reads are in process (TestClient), with no server and no ticks, as in the rehearsal. Then the clone's facts never move, and only `chain_response` rows are added.
   - If K10's proof must use `serve` with ticks, it takes this clone, and step 3 takes a **second fresh clone** of the kept DB. That costs minutes, not a prepare.
1. **Code A = main + K9** (as merged, fix round included or not; the K10 baseline does not read the failing rows). Take the K10 baseline reads (§9t.4, cold builds).
2. **Code B = A + K10.** Run the K10 proof: K10-s1 to s4, and the Kobo declared-absent sets (§9t3).
   - K6c is **not** in A or B. Its summary-field change would otherwise show up in K10-s1's Portfolio body comparison.
3. **Code C = B + K9 fix round + K6c,** merged locally in the proof worktree. Run `finish check <clone-url> var/demo3_r3u` (all rows), then `tools/chain_watermark_guard.py --modules-out`.
   - Expect 50 pass and 0 fail, including KIS-7 item 3, S-s4, the KIS-OV pin, F-COH (A1, L2, UF1), MILL-5 (`stored_outcome` VERIFIED) and KIS-6 (Assure card and H2 reached).
   - Expect the guard to show `unlisted_modules []` and exit 0.
   - Stops: R3u-s1 (U7), R3u-s2 (U6), any K10 stop, and any new failing row (report it; do not patch).

**What must land before step 3** (each one reviewed ACCEPT): the K9 fix round (U1, U4, U5, U7 pin, U8) and DIESEL-K6c (U2, U3, U6). K10 is already ACCEPTED.
- Steps 0–2 do not wait for them. They start now, overlapping the two builds.

**Merge order to main after step 3 passes:** K9 → K10 → K6c.
- K6c branches from main now (`task/DIESEL-K6c-assure-fuel-count`).
- K10 also edits `mini.py`, near the headline block (`:575-589`), and is adjacent to U2's `:572-573`. K6c rebases after K10 merges. Any conflict is textual only.
- No re-run after the rebase if the reviewer confirms that the rebased diff equals the reviewed diff.

### 9u.3 Size, critical path, cuts

- **K9 fix round** about 0.06:
  - U1 (helper at 4 sites and tests) 0.03;
  - U4, U5 and U8 0.01;
  - U7 pin 0.01;
  - re-review (Sonnet) 0.01.
- **DIESEL-K6c** about 0.07: code 0.02, tests 0.03, review 0.02.
- **Step 3** about 0.04: the check takes about 20 minutes, the guard about 4 minutes, plus the packet.
- **Critical path.**
  - Both builds run in parallel with K10 steps 0–2, which are already in the base estimate.
  - The path adds step 3 and any wait for the builds: **about +0.05 to +0.08**.
  - That makes about **9.8–10.08** before cuts, against the accepted 9.75–10.0.
- **Cuts, in order:**
  1. §9t.5 cut 1: move the K8c four-Site Kisiwa Overview capture to the demo-day prepare (−0.05).
  2. §9t.5 cut 2: move the Service empty-default-day check to the polish batch (−0.02).
  3. §9t.5 cut 3: narrow K10's served proof to Kisiwa d1 and S−5d plus Kobo S body equality (−0.04).
  4. R3u-a: one reviewer reviews the K9 fix round and K6c together, two diffs in one context (−0.02).
  5. R3u-b: step 3 runs only the affected rows (F-COH, KIS-1…KIS-10, KIS-OV, MILL-1…MILL-5, PV-A, CO-6, CH5D1-O1), if `finish check` can select rows (−0.03).
- After cuts 1–2 the path is about 9.73–10.01. After 1–4 it is about 9.71–9.99. **That is inside the range the owner accepted.**
- §9t.5 cut 4 (moving the proof to demo day) is withdrawn. The post-fix check needs the clone anyway.
- **Never cut:** U2, U3, the U6 list and guard re-run, the U7 pin, or the full F-COH run.

### 9u.4 Owner question

None. The path stays inside the accepted range after cuts 1–4. U2 is a correctness fix that makes the screen honest ("1 verified result" beside the listed ACT-004 entry), with no new product choice.

**Plan HTML (coordinator):** add to the rulings table: "DIESEL-1-R3u: rehearsal 46/4 ruled.
- UF1: false positive (0.00 addend); zero-addend pairs excluded at 4 sum checks.
- A1: real defect (Assure headline omits fuel verdicts); new unit DIESEL-K6c.
- L2: summary legacy count = the claim value (one computation; the S 2-vs-1 was a pre-K work-window vs [lo,hi) split).
- MILL-5 and KIS-6: mechanical, in the K9 fix round.
- Guard S-h: 5 lazily reached modules (K6b/MV-1/FUEL-1 A1), legitimate; added to the list in K6c.
- S−5d Protect: NEEDS_ATTENTION in the served body, and K10 does not touch MG-8; pinned in KIS-OV.
- One clone, three code states (K10 baseline, K10 proof, then the full check plus guard); the kept DB is untouched.
- Path about +0.05–0.08, inside the accepted range after cuts 1–4. No owner question."

## 9t4. Ruling DIESEL-1-R3t4 — K10 stop K10-s1 (Kobo pre-mill days), KIS-7 rounding, step-3 gates

Claude Architect (binding: Claude). Read-only. Trigger: `.agent/review-packet-K10.md` (37a7082fe on `task/DIESEL-K10-declared-absent`), clone `assetops_k9_audit_r3u`. This ruling amends R3t3's adapter rule. `declared_none_day` stays as it is.

### 9t4.1 K10-s1: a Site that has ever declared productive equipment is never "declared absent" (option c)

**Cause.** Kobo's revisions valid from 2026-09-29 declare no mill. The mill appears 2026-10-08 11:25Z. So Sep 30 to Oct 7 pass R3t3's per-day rule, and the S, S−5d and d1 gap lines gain the note. The note says "no productive-use equipment declared for this site", which is false for Kobo today.

**Rejected options.**
- **(a)** Note only when the window end declares none. This fixes the sentence, but Kobo's pre-mill days would still be taken out of settlement and counts, with no statement anywhere. That is the silent drop the owner rejected.
- **(b)** Only from the Site's first evidence. Kobo's pre-mill days *have* evidence, so (b) does not stop this.

**The rule (c).** Productive use is "declared absent" only on a Site where **no revision known at `k` declares productive equipment, at any validity time**. On such a Site, each day still needs R3t3's whole-day coverage (`declared_none_day`).
- A Site with productive equipment anywhere in its known setup history keeps today's rule: a day with no productive row is a gap, "not assessed", conservative.
- This makes the note's sentence true whenever it appears.
- It keeps the owner's rule: a missing contributor is never treated as checked, and it is never dropped silently.
- **Known at `k`** means the D2 form: recorded by `k` and not superseded at `k`. A mill revision that was corrected away before `k` does not count; one recorded after `k` does not count.

**Code** (`PostgresChainRead.declared_none_of`, still one statement):
- Drop the validity-span filter. Select every known-at-`k` revision of the Site (`valid_from`, `valid_to`, `content`); a Site has only a few.
- Pure gate in `chain/reader.py`:
```python
def site_never_declared(revisions: Sequence[tuple[datetime, datetime | None, bool]]) -> bool:
    """R3t4: True when no known revision (any validity) has a productive load; else no day is declared absent."""
    return not any(has for _, _, has in revisions)
```
- In the adapter: if `site_never_declared(revs)` is False, return `frozenset()`. Otherwise, apply `declared_none_day` per day over the revisions that overlap that day.

**Tests** (pure, in `test_k10_declared_none_rule.py`; the adapter suite adds the Kobo history as a case):
1. **Kobo history**: a no-mill revision from 2026-09-29, and a mill revision from 2026-10-08T11:25Z.
   - The result is `frozenset()` for windows ending on the S, S−5d and d1 dates.
   - It is also `frozenset()` for a window that ends 2026-10-05, before the mill.
2. **Kisiwa history** (no-mill revisions only): the R3t3 per-day results are unchanged.
3. A mill revision superseded before `k`, with no-mill revisions otherwise: declared-absent days are still given.
4. A mill revision recorded after `k`: it does not block.
5. A mill revision whose validity starts after the window: it blocks.
6. All 11 R3t3 cases still hold on a never-declared Site.

**Kisiwa stays the same.** No Kisiwa revision declares a productive load (R3s2: ESSENTIAL_SERVICE, HOUSEHOLD, HOUSEHOLD). So the gate passes, and the d1 and S−5d results in the packet stay as they are: Grow "No productive-use equipment declared · 0 kWh", Optimize "0.00 to 26.28 USD", the Protect, Assure and MG-8 states, and the gap lines with their note.
- The re-run asserts these results unchanged.
- If any Kisiwa result changes, that is stop **K10-s5**.
- Kobo's declared-absent set must be empty on all R3t3 windows (S, S−5d, d1, and the one-, three- and four-Site Portfolio windows), and its bodies must equal the K9 baseline. Otherwise K10-s1 stands.

### 9t4.2 K10-s3 flag: KIS-7 item 3 compares through the product's `money2`

- The board's 26.28 is the product's display rule: `chain/vocabulary.py:320-325` `money2`, two places, half even (the twin of `frontend/src/ui/money.ts`).
- KIS-7 item 3 asserts `money2(board amount_high) == money2(stored head amount_high)`, and that the currencies are equal. It imports `money2` and does not choose its own rounding.
- The same applies to `amount_low` when present.
- This is a check-side change in K9's file (`tools/demo_combined_rows.py:1226`), so K9 owns it. If K9 is already merged, K10 makes it on its branch.
- Add L0 cases: an unrounded stored head passes, and a 1-cent difference fails.

### 9t4.3 Step-3 environment: run the product's tool, do not restamp

- **Step 3 runs `python -m assetops_backend.performance_migration run --tenant demo --site <S>` on the clone**, for each Site the prepare compares (KOBO-001, KISIWA-001). Use the clone's environment and the copied var folder. This is the product's own tool, as in the R3s precedent.
- **Restamping report files by hand is withdrawn**, including in the builder's proof trees. It edits gate evidence outside the product. Steps 1–2 bodies taken under restamped reports are kept, but are confirmed again under the tool's reports (§9t4.4).
- **Stop:** if any report is not PASSED, or a gate is still closed, report it. Do not restamp.
- **After-demo list (product issue, not demo-critical).** A Performance report stamped with the DB name closes the gates on any clone or restore. The fix is to bind the stamp to a stored instance identity, or to rerun the comparison on restore. The demo-day prepare runs on its own DB and is not affected.

### 9t4.4 Order, size, path

**Order:**
1. The §9t4.1 code and tests, plus L0 for §9t4.2. The K9 owner makes the KIS-7 change in parallel.
2. Targeted tests: the rule, the adapter (Postgres) and the board.
3. On the clone: `performance_migration run` for both Sites.
4. Rerun steps 1–2, limited to the Kobo windows (empty sets and equal bodies) and the Kisiwa d1 and S−5d windows (unchanged).
5. Step 3 as in R3u.
6. Re-review the §9t4.1 diff, named items only, with Sonnet. It may be folded into the K10 phase-2 review.

**Size:** about +0.10 on K10:
- code 0.03;
- tests 0.02;
- `money2` compare 0.01;
- tool runs 0.02;
- partial rerun 0.02.

**Path.**
- About +0.06–0.08, because items 1–2 overlap the K9 and K6c builds. That takes R3u's post-cut 9.71–9.99 to about **9.77–10.07**.
- Apply R3u cut 5 (−0.03, selected rows in step 3) and the new **cut 6**: fold the §9t4.1 re-review into the K10 phase-2 review (−0.02). That gives about **9.72–10.02**, at the top of the owner-accepted 9.7–10.0.
- **Tripwire:** if, at the start of step 3, the projected path is over 10.0, the coordinator asks the owner, in plain language: "Kisiwa's fix is proven but the final full check would end slightly past the agreed time; run it in full (a little late) or check only the affected rows now and the rest on demo day?" Otherwise, no owner question.

**Plan HTML (coordinator):** "DIESEL-1-R3t4: K10-s1 (Kobo pre-mill days got the 'none declared' note) → declared absent only on a Site with no productive revision known at k, any validity (site_never_declared gate + R3t3 per-day coverage); Kisiwa unchanged (K10-s5 if not); KIS-7 item 3 compares via product money2 (K9 file); step 3 uses performance_migration run on the clone, restamping withdrawn, DB-name stamp to after-demo list; +0.10 on K10, path ~9.72–10.02 after cuts 5–6; owner question only if >10.0 at step 3."

## 9v. Ruling DIESEL-1-R3v — step-3 failures CO-2 and F-COH (COH-18 Kisiwa month)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only. Code read on `task/DIESEL-int-r3u` (`AssetOpsV1-int`, d5582fe61 = K9 18b3eac00 + K10 51c037445 + K6c 96b27e26d). Evidence: `.agent/r3u-step3-results.md` (int branch), the F-COH bundle `AssetOpsV1-k10/var/demo3_r3u/dd1b2-coh-flv026yn` (31 `chain_day.KISIWA-001.*` bodies, `chain_estate.{month,week,S}.json`), `check.json` and `check-rehearsal.json`. No suites, no DB writes; no DB read was needed.

### 9v.1 CO-2: environmental. Confirmed

- The row asserts `overview.freshness.state == "CURRENT"` (`tools/demo_combined_finish.py:253-256`). Freshness compares the schedule heartbeat with the wall clock (300 s limit).
- The clone has no ticks, and the check ran about 1 h 40 min after the last tick (heartbeat age 6119 s). The same row passed in the rehearsal (`check-rehearsal.json` CO-2: overview CURRENT, index CURRENT), where the self-check runs straight after the prepare's ticks.
- No K9, K10 or K6c code is on this path. **Not a defect; no fix.** It fails on any later read of this clone, so it is left out of the re-check (§9v.4). The demo-day prepare's own self-check covers it.

### 9v.2 F-COH (COH-18 R1 and R2): cause found. K10 applies declared-absent in the counts but not in the per-day chain body

**The two sides.**
- **Counts side (applies the rule).** The chain's Site `days` come from `grade_counts_of(facts, measures)` → `_counts(..., facts.none_declared)` (`backend/assetops_backend/chain/reader.py:142-147`, `:94-127`), which grades each day over `applicable_measures` (`reader.py:81-91`). `ChainRequest.day` fills `DayFacts.none_declared` (`chain/read.py:357-361`, `:363-380`).
- **Per-day body side (ignores it).** The `/api/sites/{code}/chain` route builds `days` with `site_chain.days_of(p["facts"], …)` (`backend/assetops_backend/chain_api.py:221`). `days_of` calls `day_grade(per, measures)` **without** `none_declared` (`backend/assetops_backend/chain/site_chain.py:32-41`, the call at `:39`), so `productive_kwh` with no row is still graded NO_DATA and drags the day to NO_DATA.
- COH-18 R1 compares these two (`tools/checks/chain_coherence.py:1664-1688`, the day grades from `_site_day_grades` `:1602-1613`). R3t §9t.3 item 2 listed `_day_grades`, `readiness_of`, `day_grade`, `day_settled` and `day_gaps` as the places that take `none_declared`, but not their **callers outside `chain/read.py`**. `days_of` is one such caller, and it was missed. K10's test 7 checked the pair `grade_counts_of` = `_counts`, not the pair COH-18 checks (the chain body's day grades = `grade_counts_of`).

**The 3 days, from the bundle.** Recomputing each Kisiwa `chain_day` entry's grade over its own `measures` map without `productive_kwh` gives PARTIAL on exactly **2026-10-28, 2026-10-29 and 2026-11-07**. All three have every other measure PARTIAL or COMPLETE and `productive_kwh` NO_DATA. All other 28 days stay NO_DATA because another applicable measure is NO_DATA (for example 10-30 to 11-06: `avoidable_gen_min` NO_DATA). That is exactly the chain's `partial 3, no_data 28`.

**R2 is the same 3 days.** R2's "Sites summed" side is built from the same per-day bodies (`chain_coherence.py:1674-1679`, `:1694`), so Kisiwa contributes partial 0 / no_data 31 there, while the claim carries the chain's partial 3 / no_data 28. 11 = 8 (Kobo) + 3, and 70 = 67 + 3. R2 has no separate cause. The week (10-31…11-06) and S (11-06) windows hold none of the 3 days, which is why only the month failed.

**Not K9 and not K6c.** K9 changed the check tool's sum pairs (UF1), not COH-18. K6c changed the Assure headline and the summary's verified count, not day grades. The defect is K10's.

### 9v.3 Which side is honest: PARTIAL, on both sides (the counts side is right; the per-day body is wrong)

- Owner, verbatim: "The component contributor being non existent doesn't mean it is checked." Then, on the R3t question "Its days then count only for what Kisiwa actually has: generator, fuel, service and solar … A day only counts if the site setup really says 'none'": "Build it (Recommended)".
- So a day with declared-absent productive use and its other measures PARTIAL grades **PARTIAL**, everywhere. PARTIAL is not "checked": it is never COMPLETE, never in `enough_data_days`, and readiness stays LIMITED. Productive use is not graded at all on that day, and the screen says "not assessed … (0 kWh)".
- NO_DATA would be the dishonest side here. It contradicts the board, which settles d1 (2026-10-28) and prices it (KIS-7 item 3, passing), and it files a declared fact as missing data, which R3t §9t.1 rejected.
- A declared-absent day whose other measures include NO_DATA stays NO_DATA (the 28 days). That is unchanged and correct.

### 9v.4 The fix (owner: K10, on `task/DIESEL-K10-declared-absent`)

**1. `backend/assetops_backend/chain/site_chain.py` `days_of` (`:32-41`).** Grade the day by the one rule, and state the left-out measure on the day entry.
```python
def days_of(facts: DayFacts, measures: Sequence[str]) -> list[dict[str, Any]]:
    """... R3v: the day grade is over the day's applicable measures (`facts.none_declared`, the rule `_counts` uses),
    so a chain body's day grades always sum to the chain's Site `days` (COH-18 R1)."""
    declared = getattr(facts, "none_declared", None) or {}
    out = []
    for d in facts.days:
        per = {m: list((facts.grades.get(d) or {}).get(m, {}).values()) for m in measures}
        per = {m: g for m, g in per.items() if g}
        nd = declared.get(d, ())
        entry = {"day": d.isoformat(), "grade": day_grade(per, measures, none_declared=nd),
                 "measures": {m: day_grade(per, [m]) for m in measures}}
        left_out = [m for m in measures if m not in applicable_measures(per, measures, nd)]
        if left_out:
            entry["none_declared"] = left_out   # R3v: stated, never silently dropped; only when non-empty
        out.append(entry)
    return out
```
- Import `applicable_measures` from `chain/reader.py`. No new rule: `day_grade` and `applicable_measures` are the existing shared functions.
- The `measures` map is unchanged. `productive_kwh` keeps its own grade, NO_DATA, which is true (there is no reading). The new `none_declared` key says why it is not in the day grade. Together: no reading, declared absent, not assessed.
- The key appears only when a measure was actually left out (a row wins; a day with no other row is never left out). So Kobo, Cold and EV bodies are byte-identical, and no frontend reads `days` (`frontend/src/sites/chainClient.ts` has no `measures` or `grade` reader). MOCK DEVIATION: none; this is wire-only, with no screen text.

**2. Not changed, on purpose.**
- `chain/why.py:136-138` `day_grades` (the "Why" trace's days line) also calls `day_grade` without `none_declared`. It is conservative: it can only call a declared-absent day "not available", never checked. No check compares it, it is not on a demo beat, and the R3t "other measure" condition would need the trace's measure subset rather than the Site's. **After-demo list**, not this fix.
- `chain_api.py`, `reader.py`, `read.py`, the board and the check tool: no change.

**3. Tests (targeted only).** Add to `backend/tests/test_k10_declared_none_rule.py`:
1. **The COH-18 identity (the test that would have caught this).** For a Kisiwa-shaped `DayFacts` over the 31 days with `none_declared` on the day-rows days (shapes of 10-28, 10-29, 11-07, 10-30 and a no-row day), the tally of `days_of(facts, measures)` grades (complete, partial, low, no_data, not_expected, pending) equals `grade_counts_of(facts, measures)` field by field. Expect partial 3. Non-vacuity: with `days_of` called the old way (no `none_declared`), the test fails.
2. The same identity on Kobo-, Cold- and EV-shaped facts with `none_declared` empty. The `days_of` output equals the pre-R3v output byte for byte (no `none_declared` key on any entry).
3. Day entry shape: on the 10-28 shape the grade is PARTIAL, `measures.productive_kwh` is NO_DATA, and `none_declared == ["productive_kwh"]`. On the 10-30 shape the grade stays NO_DATA and the key is present. On a no-row day the grade is NO_DATA and the key is absent. A day with a `productive_kwh` row has no key.
4. Re-run the three K10 test files, `test_ch5a1_reader.py` (it calls `days_of`) and `tools/checks/test_chain_coherence.py`. No full suite.

**Review:** a fresh Sonnet reviewer, named items only (the `days_of` diff and the three tests), folded into the K10 phase-2 review record.

### 9v.5 Re-check: targeted COH-18 and Kisiwa rows on the same clone. Sound; no full 22-minute run

**Why a targeted run is sound.**
- The fix changes one function, `site_chain.days_of`, which only the `/api/sites/{code}/chain` route calls (`chain_api.py:221`). Every other body is built by code that is unchanged.
- `code_version` changes, so every body recomposes. But the clone's facts do not move (no ticks), and the composition is deterministic over the same rows, so the other bodies equal those that passed at d5582fe61.
- The 48 passing rows were run on this clone with code that differs only in this function. The demo-day prepare's own self-check runs all rows again anyway.

**Steps (the runner is the K10 builder, one context):**
1. Commit the fix and tests on K10. Re-merge K10 into `task/DIESEL-int-r3u` (ort, as before). The diff of int against d5582fe61 must be `site_chain.py` and the test file only.
2. Use the same clone `assetops_k9_audit_r3u` and work folder `AssetOpsV1-k10/var/demo3_r3u`, cwd `int/backend/tests`, as in step 3. Copy `check.json` to `check-r3u-full.json` first, to keep the 48/50 evidence. Delete no `chain_response` rows: under the new `code_version` none is reused.
3. Run a **scratch harness** (in the session scratchpad, not committed; its text goes in the packet). It imports `tools/demo_combined_finish.py`, keeps `CHECKS` in its order, filtered to the rows below, calls `run(url, work)`, and then renames the output to `check-r3v-rows.json`. No change to the tool. Rows:
   - the rows that read a Site chain route or the COH bundle: **F-DRAIN, F-COH, F-COH3, F-CAL, MILL-3, MILL-3b, F-THREADS, MILL-4, MILL-5, KIS-8** (KIS-8 scans the bundle's bodies, which now carry the new key);
   - every Kisiwa row: **KIS-1, KIS-2, KIS-3, KIS-4, KIS-5, KIS-6, KIS-7, KIS-8a, KIS-9, KIS-10, KIS-OV**;
   - the four-Site rows: **CO-6, CH5D1-O1, PV-A**.
   - The runner lists, from a grep of `demo_combined_finish.py`, every row whose function or helper calls `ctx.get("/api/sites/…/chain…")` or reads `ctx.cache["coh"]`, and shows that each one is in this set. A row that is missing is added to the set, not argued away.
   - A selected row that fails because an unselected row had filled a `ctx.cache` key is not a product failure: add the producer row and run again.
4. **Expect:** every selected row passes. F-COH has no COH-18 finding. The Kisiwa month `chain_day` bodies grade 10-28, 10-29 and 11-07 PARTIAL with `none_declared: ["productive_kwh"]`, and the other 28 days NO_DATA. Record those three entries in the packet. KIS-7 item 3 stays "priced and equal". KIS-OV keeps S−5d Protect NEEDS_ATTENTION.
5. **Do not re-run the watermark guard.** The module set is unchanged: `site_chain` is already in the stored-composer list, and no import was added outside `chain/`. If the reviewer finds a new import outside `chain/reader.py`, re-run the guard with `--modules-out` (about 4 minutes).
6. **Stops (report; do not patch):**
   - **R3v-s1:** any Kobo, Cold or EV `chain_day` or `chain_span` body gains a `none_declared` key.
   - **R3v-s2:** any selected row fails other than for a missing cache key.
   - **R3v-s3:** a Kisiwa day count other than partial 3 / no_data 28 for the month.
   - A comparison gate reads closed: re-run the product tool for that Site (§9v.6) and record it. Never restamp.

**After it passes:** merge order to main is unchanged from R3u: K9 → K10 → K6c. CO-2 is accepted as environmental on the record of §9v.1.

### 9v.6 Process call: the builder's `evidence_migration run --site KOBO-001` on the clone. Accepted

- It is the product's own tool, run on the clone with the clone's environment. It is not a hand restamp, so it meets R3t4 §9t4.3's rule ("run the product's tool, do not restamp"). The report read PASSED with cutover permitted.
- R3t4 named only `performance_migration` because only those reports had been seen to close a gate. The Kobo Evidence (S2) comparison report has the same DB-name binding. Running its own tool is the same precedent, not a new one.
- Replacing the `var` junction with a real copy is also accepted. The junction made the Site file appear twice, so the copy is the correct environment, not a change to the evidence.
- **After-demo list (amends §9t4.3's item; one item, not two):** "Evidence (S2) and Performance comparison reports are stamped with the DB name, so a clone or restore closes their gates until the product tools are re-run. Bind the stamp to a stored instance identity, or re-run the comparisons on restore." Not demo-critical: the demo-day prepare runs on its own DB.
- Add to the same list: "`chain/why.py:136-138` days line does not apply declared-absent (R3v §9v.4 item 2)."

### 9v.7 Size, critical path, owner question

**Size: about 0.07.**
- code 0.01;
- tests 0.02;
- Sonnet review 0.01;
- re-merge, targeted run (about 12–15 minutes: the F-COH collection dominates) and packet 0.03.

**Critical path.** None of this overlaps other work, because it is the last gate before the merges. So the path is **about +0.07, taking 9.72–10.0 to about 9.79–10.07** (central about 9.93). The full 22-minute run instead of the targeted one adds about 0.02, so about 9.81–10.09.

**Owner question.** The top of the range crosses 10.0, so R3t4's tripwire applies. The coordinator asks it now, in parallel with the build, and does not wait for the answer:

> "Kisiwa's fix is proven but the final full check would end slightly past the agreed time; run it in full (a little late) or check only the affected rows now and the rest on demo day?"

- **Recommendation and default: check only the affected rows now** (§9v.5). It is sound by the code argument in §9v.5. The other rows passed on this clone at d5582fe61, and the demo-day prepare's self-check runs all of them again.
- If the owner chooses the full run, run `finish check` in full in place of step 3 of §9v.5. Expect 49 pass and CO-2 failing for the environmental reason in §9v.1.

**Plan HTML (coordinator):** add to the rulings table: "DIESEL-1-R3v: step 3 at 48/50. CO-2 environmental (no ticks on the clone; passed in the rehearsal). F-COH = K10 miss: `site_chain.days_of` (`site_chain.py:39`, the chain route's per-day grades) did not pass `none_declared`, while the counts did; Kisiwa 10-28, 10-29 and 11-07 read NO_DATA in the day bodies and PARTIAL in the counts; R2 is the same 3 days. Honest side: PARTIAL (the owner's 'count only for what Kisiwa has'; never COMPLETE). Fix in K10: one-rule grade plus a stated `none_declared` key on the day entry, Kobo/Cold/EV byte-identical; COH-18 identity test. Targeted re-check (F-COH, chain/bundle rows, all KIS rows, four-Site rows) on the same clone. `evidence_migration` re-run accepted (same precedent as R3t4); one after-demo item for the DB-name stamp. About 0.07, path about 9.79–10.07; owner asked (default: affected rows now)."
