# Architect handoff: client-demo plan, 2026-11-04

Architect: Claude (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). This hands over from the Architect who wrote the plan and the CH-0 to CH-3 sheets. Nothing is committed by the Architect. The coordinator commits.

## 1. Where the agreed state lives

- **Plan, the current plan.** `Docs/demo-sprint/client-demo-plan.html`, agreed 2026-11-03 ("Let the build begin now"). Its Agreed table holds:
  - OD-P1 to OD-P10 (P9, the client date, is deferred and follows progress);
  - OL-1 and SWEEP-DS, with the owner's words verbatim;
  - the **Rulings** rows QW-R, CH0-R, CH1a-R, CH1b-R, CH2-R and CH3-R. These are binding Architect rulings on builder pre-flights and reviews. Read the row of a slice before ruling on it.
- **Where the rest of the plan sits:**

| Plan section | Content |
|---|---|
| §2.1 | Scope and units, including the CH-5c contingency (0–4 units) |
| §2.3 | DS-R1, "demo-shaped logic is fixed when touched" |
| §2.4 | OL-1: finding → outcome stays in `outcome_map.py`, reshaped by CH-6 into `OutcomeContribution` records, with an outcome-id ratchet guard; the CH-8 conversion recipe |
| §4 | The test ladder |
| §5 | The end-game E1 to E6 |
| §8 | Gates G0 to G6 by units; dates are non-binding |

- **Design.** `Docs/demo-sprint/implementation-logic-design-proposal.html`: AG-1 to AG-32, §4.3 (DDL), §4.4 (states), §5.2 (A0 to A6), §5b (catalogue), §8b (hard-wiring), §11b (with the **measured** QW-1 diagnosis), §12 to §15.
- **Register.** `Docs/demo-sprint/implementation-logic-portfolio-sites-findings-actions.html` (I-01 to I-25). The High issues are I-01 to I-08, I-10 and I-12.
- **Build sheets** (`.agent/`):
  - `build-sheet-CH-0.md`, `-CH-1a.md` (§5c holds the pre-flight rulings), `-CH-1b.md`, `-CH-2.md`, `-CH-3.md`;
  - `brief-MA-1-mock-addendum.md`, with its rulings in the plan's Rulings row.
- **Pointer:** `.agent/current-plan-pointer.md`.

## 2. Slice status and next sheets

- **Merged:** QW-1/QW-2 (memo removed), CH-0, MA-1, CH-1a, CH-2, CH-3 (`da5b18391`).
- **In integration:** CH-1b (lane 1), on top of CH-3. The migration chain is 0041 → 0043 → 0042 → 0045 → 0044 (CH-1b).
- **Sheets still to write, in order:**
  - **CH-4** (lane 2): opportunity threads, I-06, I-18.
  - **CH-5a** (lane 1): ChainReader, routeFor, the board no longer calling `mini_overview`, `finding_index` and `evidence_readiness`.
  - Then **CH-5b**, the CH-5c contingency, **CH-6**, **CH-9** (rebased onto CH-1b and CH-4, not CH-8), **DD-1** and **DS-1**.
  - CH-6 may need splitting into 6a and 6b (≤ 6 units each), because the OL-1 reshape and ratchet guard add about 0.5–1 unit.

## 3. Carried items, by owning slice

**CH-5a:**
- COH-8/I-01 `origin_revision_selected`: the exact-revision progress rule; progress rows come from threads.
- I-21: lens from the chain. This includes the COH-5 expected entries for the Kobo 17, 24 and 31 Oct PROTECT_ASSET vs COST findings, and COH-1 routeFor.
- A structured `thread_lines` field, replacing the copy-only lines.
- Remove the `board.py` thread-state tuple copies (an equality test guards them today).
- L5: thread lookups honour `known_at` everywhere.
- Perf: R1 (no repeated same-argument read per request), R2 (light Site list for the summary; decide the 409), R3 (profile the evidence selection; this decides whether CH-5c is used).
- Replace the Portfolio per-row `_cutoff` with the ChainReader per-Site cutoff.
- "Verified on example data" wording, derived from provenance (COH-12 lists it).

**CH-4:** the opportunity lens (COH-6), the fixed `UNSUPPORTED` claim (I-06).

**CH-6:** the OL-1 reshape and ratchet guard; Portfolio composition per Site-local day (A6), keeping CH3-R's per-Site-day rule; whether same-currency Grow figures may be summed (the MA-1 ruling).

**CH-9:** the daylight-window solar read, which replaces the "midday" labelled keep in CH-1a/CH-1b.

**DD-1:**
- Record Cold ACT-000002 and EV ACT-000003, plus their APPLIED and case causes, at story time. COH-3 must be non-vacuous (CH0-R).
- Extend the story days of Kobo, Cold and EV to their declared hours (Kobo and Cold 24 h, EV Tuesdays 08:00–16:00), using **existing scenarios only**.
  - The whole prepare may grow by at most 50%, to about 1,430 s.
  - Otherwise the grades stay PARTIAL or LOW, and the owner is told before E3.
- The backfill runs in `prepare`; finish-check rows for coherence and perf; the ST-7 add-day step.

**SWEEP-DS** (after the scope, before or with CH-7):
- the backfill running past the story end;
- the `basis: "assessed_window"` coverage of chamber and backup (D2, D3);
- the inferred Cold hours and the mismatch between scenario times (19:00 UTC) and story days (16:00 UTC);
- the clean-days close with a null cause time;
- dispatch constants, `reserve-trial-1`, and the rest of the plan's §2.2 list.

**Post-demo:**
- a priced-total cost check (credited money is never a summed per-kWh rate; CH3-R);
- probe → room mapping through Foundation relations (CH1b-R Q1);
- CH-7, CH-8 (with the OL-1 conversion), CH-10a/b, and slice F's F1, F2 and F4.

## 4. Conventions

- **Paths:** `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `M/` = `backend/migrations/versions/`. Cite `path:line`.
- **Ladder** (plan §4):

| Level | What |
|---|---|
| L0 | Pure tests |
| L1 | Fixture contracts |
| L2 | `pg_harness.fresh_database()` plus `setup_cache`; head pins use `pg_harness.alembic_head()`, never literals |
| L3 | `python tools/chain_clone.py create <n> --migrate` → `settle <n>` (evidence-migration record, then one bounded tick) → backfill → `chain_coherence.py collect`/`check` → `drop <n>`. Clone names only; `drop` removes only the files `settle` created. |
| L4 | SELECT-only or `--dry-run` against `assetops_polish_full_test` |

- `assetops_demo3_full_test` is never touched.
- No full suite or demo prepare until the end-game (OD-P4). The estate guard self-tests run only when a slice edits `configuration-persistence.ps1`.
- **Every sheet** carries a DS-R1 table, an OL-1 line, exact tests, and pre-flight items. Builders pre-flight, then stop.
- **Never tune a value to fit the data.** Report the difference; the Architect rules. Honest LOW or PARTIAL grades are shown, not hidden.
- Copy is plain language and goes through the vocabulary guard; new lines are MOCK DEVIATION candidates against MA-1.
- `expected-today.json` is tied to the polish build. At E4 the coherence check runs with **no** expectation file (EX-2 = 0 findings).

## 5. Open risks

- **Performance (EX-3).** Measured: board about 8 s warm, Portfolio about 7.2 s, summary about 9.7 s. The budgets (≤ 1 s cold, ≤ 300 ms warm) depend on CH-5a/CH-5c removing the recompute reads. A budget miss goes to the owner as a measured proposal before E1; it is never relaxed silently.
- **Demo story under honest calendars.** Until DD-1, Kobo is PARTIAL (the target reads "too early to judge"; the verified fix never closes, and its after-state reads "not judged yet"). Cold and EV are LOW (EV income is not in the Portfolio total). If DD-1's extension does not fit the cap, this is what the client sees, so the owner must decide.
- **Clone fidelity.** Clones need `settle`. The polish build ages (it is dated S = 31 Oct), so the final values are proven only at E4. Re-prepare if the build is more than about 3 days old.
- **Migration ordering across lanes,** and hand-merged test files (see CH3-R "for CH-1b").
- **Deferred full suite** (OD-P4). Late integration surprises land in E2; one fix round is reserved.
- **Date rule:** never prepare on the 3rd to 5th of a month.

## Update 2026-11-04 (Architect 2)

Architect: Claude. Nothing is committed; the coordinator commits.

### 1. New plan rows (`Docs/demo-sprint/client-demo-plan.html`)

**CH4-R**
- R1: an OPP study is an occurrence only if it has ≥ 1 eligible day. The Kobo headroom thread is OPP-000003 + OPP-000004.
- R2: an opportunity's episode is its eligible days (refines CH2-R M1).
- R3 (I-18): the board's observed range and the study's every-eligible-day value are two named claims; the wire carries `headroom_kw` + `window_hours`.
- R4: opportunity items are a separate, unpaged array shared by Findings and Portfolio.
- R5: `thread_signal_key` and `lens_flags` live in `outcome_map.py`.
- R6: SUPPORT_LOST applies to opportunity threads.
- R7: the board's opportunity signal stays on the renewable cards (keep → CH-6).
- MD-CH4-1 is reported to the owner: no Portfolio priority-table opportunity row until CH-6.

**CH5a-R**
- S1: split into CH-5a1 (6 units) and CH-5a2 (6 units).
- S2, lane 1: CH-1b → CH-5a1 → CH-5a2 → CH-5b → CH-6.
- S2, lane 2: CH-4 → MD-0 → CH-9 → DD-1 → CH-5c.
- R1: one read scope per request, with a ledger and a memo of frozen values; `knowledge_at` is excluded from the key for live reads.
- R2: the summary never 409s.
- R3: the profile sizes CH-5c.
- R4: board settledness comes from snapshots.
- R5: `readiness_of` over day grades.
- R6: the board day is Site-local.
- R7: one `site_cutoff` helper.
- R8: Findings are settled when the threads consumer has caught up.
- Lens: one per Finding, from the primary moved category; COH-5 checks primary issues only.
- Budgets: reported, never relaxed.

**BASE-1 (owner-agreed direction)**
- DD-1 becomes a normal baseline with the story days injected.
- MD-0 is the mechanism dataset.
- PC-1 is the presentation rule: claims carry `{value, basis, text}` in `chain/vocabulary.py`, with a new COH-17. CH-5a2 builds the counts, CH-6 builds money and verdicts. CH-4's D2 is fixed in CH-4's own fix round.

**FILL-1 (owner-agreed)**
- `add-day` already targets any free past day within S−30d.
- Its refusals: `DAY_HAS_EVIDENCE`, `DUPLICATE_DAY`, `OUTSIDE_BOARD_WINDOW`, `DAY_NOT_IN_PAST`, `PREPARE_ONLY_KIND`.
- DD-1 adds the steady kinds, the planned `missing` gap days and the ST-7 rule (a day is addable once it has ended).
- DD-1 grows from 5 to 6 units.

**DD0-R**
- Events are per reading row, because the writer issues one statement per reading.
- CH-1b fix round: `consume` pages through 500-event pages until the queue is empty or the stage time bound (`chain_seconds`) is hit, coalescing the dirty marks of each page.
- Acceptance: a 4,400-event Site-day drains in one tick, with the time reported against 50% of the stage limit.
- Fallback: writing readings as one statement per batch becomes a DD-1 item.

**Owner decisions**
- OD-P13: agreed (author two labelled steady-day scenarios).
- OD-P14: agreed (ACT-001 stays "monitoring").
- OD-P11 (baseline length) and OD-P12 (E3 build cap) wait for DD-0b.

**Totals**
- About 64 lane units, about 69 in total.
- Gates G4/G5/G6 = 61 / 67 / 67, plus 0–4 for CH-5c.

### 2. Sheets and briefs written

- `build-sheet-CH-4.md` (in review; D2 is fixed in its fix round).
- `build-sheet-CH-5a.md` (Part A = CH-5a1, Part B = CH-5a2).
- `brief-MD-0-mechanism-dataset.md`: a fixture through the product's writers, plus `late_fill` and `expected-mechanism.json`.
- `brief-DD-0-baseline-probe.md`, which produced `DD-0-probe-results.md`.

**Remaining sheets, in order:**
1. MD-0 full sheet (lane 2 after CH-4; CH-5a1 builds only after MD-0 merges).
2. CH-5b.
3. CH-6 (split into 6a/6b if over 6 units, because of the OL-1 reshape and the ratchet).
4. CH-9.
5. DD-1 (6 units: steady scenarios, story injection with EV events on Tuesdays, FILL-1, story-time Actions, backfill in prepare, finish rows).
6. CH-5c (sized by the CH-5a1 profile).
7. DS-1.

### 3. DD-0b ruling inputs (run after the CH-1b fix merges, about 20 min)

**Runs**
- C4 and E4: separate Cold's and EV's fixed and per-run cost. Cold today ranges 260–871 s per day; this dominates the range.
- K2, with a timed drain tick and one `add-day`: verify the drain fix and the cost of one injected day.
- A cProfile of one Kobo replay run (about 143 s per 8 h): split per-reading ingestion, about 80 recompute jobs per run, and the run's own ticks. Bulk ingestion for normal days is the big lever if ingestion dominates, and it is a DD-1 design item.

**Current estimates (partial probe)**
- B-22: about 4.4 h sequential or 2.7 h parallel (upper bounds 8.3 h / 5.4 h).
- B-16: about 3.2 h sequential or 1.9 h parallel.
- Parallel memory is marginal: about 2.2 GB free against the 2 GB floor.

**Provisional recommendation:** B-22 in parallel if it stays at about 3 h elapsed or less; otherwise B-16.

### 4. Open risks

- **Build cost versus the owner's "no long builds".** A multi-hour E3 is one-time but long; OD-P12 must set the cap.
- **EX-3 budgets.** CH-5a1/5a2 will not reach 300 ms warm on their own. CH-5c is likely needed, and a measured proposal goes to the owner before E1 if the budgets still miss.
- **CH-5a1's A/B allows only the listed changes E1–E5.** The overview and readiness replacements carry the most risk. Its pre-flight items P2 (dispatch-body fields) and P3 (finding-index head rule) must be answered before code.
- **Steady scenarios are new example content.** They must be reviewed as data, never tuned, and kept clear of DS-R1.
- **Cross-lane order.** CH-5a1 waits on MD-0, and CH-5a2 waits on CH-4.
- **Merge order.** Migrations stay linear (0045 → 0044); expect hand-merges of tests.
- **The Kobo opportunity reads "Limited evidence: mixed sources"** until CH-9, or until baseline studies come out single-source.
- **ACT-001 cannot close inside the story** (agreed). Closing is proven on MD-0 only.

## Update 2026-11-04 (Architect 4)

Architect: Claude. Nothing is committed; the coordinator commits. Context ran short after CH-9, so this Architect stops here.

### 1. Written

- `build-sheet-CH-6.md`: split into **CH-6a (6)** and **CH-6b (5)**, rulings CH6-R S1, R1–R15. Plan: the CH6-R row, §2.1 (CH-5b 6 per its R10, CH-6 11), §3 rows CH-6a/CH-6b, §4.2 row, totals about 70 lane / about 75 total, gates G4/G5/G6 = 67 / 73 / 73 (+0–4 CH-5c).
- `build-sheet-CH-9.md`: 4 units (unchanged), CH9-R R1–R8, plan row CH9-R. It adds migration **0046_daylight_hours** (lane 2); take `down_revision` from main at branch time.
- Away decisions logged: D-AW-4 (CH-6 split), D-AW-5 (no Grow total across Sites), D-AW-6 (I-22 in part), D-AW-7 (CH-9 before/after, not "verified"), D-AW-8 (daylight declaration file).

### 2. Points for the next Architect

- **PC-1 `Claim` type.** The CH-5a2 sheet never defined it. CH-6 §S.2 now fixes it for both slices. Tell the CH-5a2 builder to build it as written there (CH-6a pre-flight P3 checks).
- **MD-0 fixture change from CH-9:** Kobo gains its daylight declaration (CH-9 §3). Also check the MD-0 §7 CH-9 row.
- **Pending:** D-AW-2 (OD-P11/OD-P12, waiting on DD-0b) and D-AW-3 (recurrence while CHANGE_APPLIED, waiting on MD-0). CH6-R R15 leaves D-AW-3 out of CH-6 unless the ruling assigns it.

### 3. Remaining, in order

1. **`build-sheet-DD-1.md`** (6 units). Scope:
   - the baseline-plus-story dataset over OD-P11's length;
   - the two OD-P13 steady-day scenarios, derived from `kobo-daytime` / `kobo-mini-grid-evening` and `cold-normal` with their forcings removed, reviewed as data;
   - story days injected at their S-relative dates, with EV on declared Tuesdays;
   - the `mill-midday` kind (CH-9 R7);
   - planned `missing` gap days, and FILL-1's steady kinds in `add-day` (`tools/demo_story_days.py:200-231`, the children `tools/demo_combined_{kobo,cold,ev}.py`) with its five refusal codes and the ST-7 "addable once ended" rule;
   - ACT-002/ACT-003 recorded at story time, with their APPLIED and case causes, so COH-3 is non-vacuous (CH0-R);
   - the writers' clock seams that MD-0 P1 reports;
   - a commit-safe outbox cursor only if CH-1b's packet shows one Kobo day's consume above half the stage bound (CH1b-R2 item 2);
   - one statement per batch for readings if DD-0b shows ingestion dominating (DD0-R);
   - the backfill in prepare, and the finish-check rows (coherence, perf, expected threads);
   - `late_fill` parity with MD-0 (§7).
   - Tests are plan §4.2 DD-1 plus the §4.4 partial prepares. Its size depends on D-AW-2.
2. **`build-sheet-CH-5c.md`:** contingent, 0–4 units. Size it from CH-5a1's R3 profile (the Portfolio evidence selection about 3.8 s and money about 1.2 s): 1–2 units for batching, 4 for snapshots (CH5a-R R3). Wait for the profile.
3. **`brief-DS-1.md`:** the demo script. Story order ST-1…ST-7 (plan §1.1); per screen, the link (routeFor), the expected text from the L1 goldens, and a fallback capture; ST-7 live add-day as the last step (OD-P7); finalised after E5.

After each sheet, update the plan's §2.1 sizes and the §8 gates.

## Update 2026-11-04 (Architect 5)

Architect: Claude. Nothing is committed; the coordinator commits. The owner came back during this run, so from now on material items go to the owner as recommendations.

### 1. Written

- **CH5a1-R** (plan row; `build-sheet-CH-5a.md` §A12): Q1–Q12 ruled, and Part A corrected in place (C1–C10). C6 was found by the Architect: `action_facts` keeps `VerificationService.summary`, because a SQL "latest outcome" would lose PENDING and REASSESSMENT_PENDING. Part B carries the note that the PC-1 `Claim` is built exactly as CH-6 §S.2 defines it.
- **MD0-PF** (`build-sheet-MD-0.md` §14):
  - Q1 (a): one authored-fixture registry line;
  - Q3: the pre-ruled split applies, and MD-0b carries verification and the close variant;
  - Q4: Cold days.json entries are local days (CH5a1-R Q8 amended);
  - Q5 and Q6: defaults.
- **`build-sheet-CH-5c.md`:** 3 units, CH5c-R row. Plan §2.1, §3, the gates (G5/G6 = 76) and the totals (about 78 overall, about 73 on the lanes) are updated.
- **`brief-DS-1.md`:** the script's structure, sources, honest-state table and the ST-7 live step.
- **Away log:** D-AW-9 (EV "Low"), D-AW-10 (withheld Finding shown, with a stop), D-AW-11 (CH-5c at 3), and a "Mode ended" note.

### 2. Waiting on the owner (recommendations sent to the coordinator)

- **MD-0 Q2, build cost.** Recommended: two tiers.
  - L2m uses a minimal "states" day set, about 3–5 min, cached per code revision.
  - The full 14-day L3m is built once per main merge, in the background.
  - Batches of up to 256 envelopes in every case.
- **The DD-1 lever.** Deliver the baseline in max-legal batches (no B/ change). Optionally add a set-based insert inside `submit` on the one product path, with a parity test (a B/ evidence-path change, so an owner decision). A demo-only fast path is recommended against.
- **D-AW-3.** Recommended: record the recurrence while the change is under check, as a visible self-transition (`RECURRED_DURING_CHECK`, "Happened again on {day}, after the change on {day} · still being checked"). About 0.5 unit in CH-6a. The alternative is to reopen as "Came back". The silent skip is ruled out.
- **D-AW-2** (OD-P11/OD-P12): waits on DD-0b.

### 3. Remaining

- **`build-sheet-DD-1.md`** (6 units, scope as in the Architect 4 update §3 item 1). It is not written: its size and ingestion design depend on D-AW-2 and on the owner's answer to the MD-0 Q2 lever (batch size, set-based insert).
- Fold into DD-1:
  - the publication `recorded_at` clock seam (MD0-PF Q1, R4);
  - MG-1 `recorded_at` (Q5);
  - DS-1 §4's steady kind and its day.
- After DD-1: update §2.1 and the gates again.

- **MD0-S2 (later in this run):** MD-0 is Kobo-only at 3.5 units (about 2 remaining), with the D-AW-3 record taken on Kobo. Cold and EV move to the polish clone and the DD-1 baseline. CH-5a1 may start now. Owner to confirm. See `build-sheet-MD-0.md` §15.

- **Owner review of D-AW-1..8:** revised positions are in the away log (D-AW-5, 6, 7 and 8 changed). If the owner accepts them, rewrite CH-9 R1–R3 and R6, add a CH-9b sheet, and update CH-6b R10. Lane 2 grows by about 3.75 (CH-9 +1, CH-9b 2.5, CH-6b +0.25 on lane 1).

### Architect 5, final: after the owner's "all as recommended" (OWN-1104)

- **Written:**
  - the plan's OWN-1104 Agreed row and the CH9b-R / DD1-R row;
  - away log closed;
  - `brief-DD-0c-levers-probe.md`;
  - CH-9 §9 (supersedes R1–R3 and R6; adds R9, full-day MG-5; 5 units);
  - `build-sheet-CH-9b.md` (2.5);
  - CH-6 "Revision OWN-1104" (R10 sum; R16 RECURRED_DURING_CHECK in **CH-6b**, 5.75, because CH-6a is at 6);
  - `build-sheet-DD-1.md` (split DD-1a 3.5 / DD-1b 3).
- **Plan sizes:**
  - CH-9 5, CH-9b 2.5, CH-6b 5.75, MD-0 3.5 + MD-0b 1, DD-1 6.5;
  - gates G4 ≈ 73, G5/G6 ≈ 82.5; total ≈ 84 (lanes ≈ 79).
- **Lane 2 order:** CH-4 → MD-0 (Kobo) → MD-0b → CH-9 → CH-9b → DD-1a → DD-1b → CH-5c. The CH5a-R S2 text in the plan still shows the older lane string; update it on the next plan pass.
- **Next:**
  - run DD-0c, then confirm B-22 under 3 h (or B-16 to the owner);
  - CH-9b P1 may need an owner-declared pass margin (CH9b-R R3).

## Update 2026-11-04 (Architect 6)

Architect: Claude. Nothing is committed; the coordinator commits.

- **Not recorded earlier:** MD0-S3 (template DB, `build-sheet-MD-0.md` §16). MD-0 reached review at `5452abe29`: template about 485 s, clone 0.4 s, derive about 41 s, L2m 29 passed and 3 xfailed.
- **Written:** `build-sheet-MD-0.md` §17 (MD0-S4, R1–R6) and the plan row MD0-S4.
- **Result:**
  - F2 is fixture fidelity: point power, against the producer's interval means.
  - F5 is the harness clock on the late path.
  - Fix round of about 1 unit; MD-0 does not merge as-is.
  - CH-5a1 builds on, with its review after the fixed MD-0.
  - Product note (Medium) for SWEEP-DS: V3 accepts point power, and dispatch uses it while coverage ignores it.
- **Next:** dispatch the MD-0 fix round. Its pre-flight lists the added channels and the readers that need them. Then a fresh-Claude re-review, merge, and main merged into CH-5a1.
- **MD0-S5** (`build-sheet-MD-0.md` §18):
  - M2 (A): channels from producer identities, plus a busy noon by charge request (the CHARGE_OBLIGATION_ACTIVE exclusion) on every delivered day except D12/D13;
  - M1: import-traced fingerprint plus data directories, `chain/` excluded;
  - Lows L1–L5 in the same round;
  - receipt reasons logged to SWEEP-DS.
- **CH5a1-R2** (`build-sheet-CH-5a.md` §A13; plan rows CH5a1-R2 and CH5c-R2):
  - R-1: transaction time against transaction time;
  - COH-7a: adapt the check to `summary_day`, which closes the MD-0 ×2 (owner is now CH-5a1);
  - the extra E1 Low is accepted;
  - ledger reads keyed by Site.
  - **Performance trajectory misses the budgets.** Recommended: CH-5c grows to 5 units with stored route payloads, moves to lane 1 after CH-5a2 and before CH-5b; owner to decide (A/B/C).
- **OWN-CH5c (owner, verbatim: "go with option A"): done.** `build-sheet-CH-5c.md` rewritten (5 units, CH5c-R3 R1–R9, lane 1 CH-5a2 → CH-5c → CH-5b). `build-sheet-CH-5d.md` is new (1 unit, lane 2 last, the evidence cell and the Optimize card). CH-5b has Revision OWN-CH5c (its ETag is the stored copy`s etag; 5.5 units). The plan has rows CH5c-R2 (agreed) and CH5c-R3, plus sizes, gates (G4 ≈ 77.5, G5/G6 ≈ 85) and the total (≈ 86.5, lanes ≈ 81.5). Still to do on the next plan pass: the CH5a-R S2 lane text.
- **CH5a1-R3 / FIX-MAIN-1: written** (§A14 and the plan row). The FIX-MAIN-1 sheet is the plan row itself. The cause of the demo self-check failure is still open: FIX-MAIN-1 finds it first. This Architect`s context is heavy: start a fresh Architect for the next items.

## Update 2026-11-04 (Architect 7)

Architect: Claude. Nothing is committed; the coordinator commits. Read-only on the evidence DB `assetops_demo3_fixmainone_test` (SELECTs only).

- **FIX-MAIN-1 R1 (plan row, after CH5a1-R3 / FIX-MAIN-1).** The CO-1 self-check failure is a stale expectation, not a product defect.
  - Since CH-3, "applied" is the thread state on the board day. The change took effect on 3 Nov (`action_policy_change.effective_from`), so day S = 2 Nov reads NEEDS_ATTENTION / PRIMARY_FINDING_OPEN, as CH-3 §0/§5 and line 186 expected.
  - Ruling (a): the expectation moves, with owner CH-3. Option (b) is rejected (I-12, DS-R1 item 3).
- **CO-1 now asserts:**
  - the effective day e is after S;
  - `mg2 == ('NEEDS_ATTENTION','PRIMARY_FINDING_OPEN')` and the cost row state is NEEDS_ATTENTION;
  - the subline contains `THREAD_BEFORE` for e plus one of the two after-forms.
- **New CO-1b (S+1):** no PRIMARY_FINDING_OPEN, and "Fix verified, monitoring (ACT-001)". A failure here is a product finding: report it and stop.
- **Other rows:** no other CO-*/WK-* row shares the old assumption.
- **Same-day CHANGE_APPLIED and RESOLVED_MONITORING:** this is the A5 rule (VERIFIED is valid from the change day and known at the outcome's `recorded_at`), plus the demo's one-hour next-day trial window. It is not an artefact.
  - Low, recorded for CH-6b R16: CLEAN_DAYS counts from the valid day.
- **Day-S wording** is honest and needs no copy change. One reading risk: "not judged yet" sits beside the trial line "after: met · checked over 09:00–10:00". This goes to PC-1, DD-1 and DS-1.
- **Still open in FIX-MAIN-1:** items (2)–(4) and M4 of CH5a1-R3 are unchanged. Re-run the prepare self-check after the CO-1 edit and expect all 24 rows to pass (the 23 existing rows plus CO-1b).

### Architect 7, second item: CH5a2-R (CH-5a2 pre-flight)

- **Written:**
  - `build-sheet-CH-5a.md` §B13 (S1, R1–R8);
  - the plan row CH5a2-R;
  - plan updates: §2.1 CH-5a2 at 9, §3 rows CH-5a2a (5) and CH-5a2b (4), CH-5c deps, total ≈ 90.5 / lanes ≈ 84.5, G4 ≈ 80.5, G5/G6 ≈ 88, and the CH5a-R S2 current-lanes note (done).
- **Lane 1:** CH-5a2a → CH-5a2b → CH-5c → CH-5b → CH-6a → CH-6b. CH-6a P3 checks the Claim shape that CH-5a2b builds.
- **R4 changes B2.** The rendered link is a sibling `link_ref`; the existing identity `ref`s stay byte-identical.
- **R3 fixes the count-claim literals.** They are MOCK DEVIATION candidates and go through guard V.
- **Waiting on the owner: R7, the summary card day.** Recommended: one day rule shared by the board and the summary (a UTC-midnight day = the calendar date picked, as that Site's local day).
  - Today the 31 Oct card shows Kobo's 1 Nov board.
  - CO-6 is expected to fail on main `01133225a` because of CH-5a1's `summary_day`. Tell FIX-MAIN-1 not to move CO-6's expectation; it waits on R7.

### Architect 7, third item: MD0b-R (MD-0b packet)

- **Written:**
  - plan row MD0b-R;
  - `build-sheet-MD-0.md` §19;
  - CH-6 sheet "R16 revision MD0b-R" (own L0 and L2-synthetic case; MD-0 D14 is now the negative case).
- **A1 (COH-8):** resolved by CH-5a2a B6. It is an owned entry until CH-5a2a deletes it. MD-0b does not wait.
- **A2 (COH-6, close):** a real eligibility-vs-study disagreement (CH4-R R7 keep). An owned entry, owner CH-6a. The days stay.
- **Cost:** close template on demand (the lifecycle file list, E1/E4, post-merge job); the fingerprint is not narrowed; Known deviation 5 is folded into the same fix round; tiering is a measured proposal later.
- **Context:** this Architect is now moderately heavy. Start a fresh Architect after the next item.

## Update 2026-11-05 (Architect 8)

Architect: Claude. Nothing is committed; no database touched.

- **CH5a2b-R written:** `build-sheet-CH-5a.md` §B14 and the plan row CH5a2b-R (after MD0b-R). CH-5a2b stays at 4 units; no plan size or gate change.
- **Rulings:** Q1, Q2, Q3, Q5, Q6, Q8, Q9, Q10, Q11 defaults accepted (Q3 with a pre-declared UTC-day vs Site-local-day A/B class; Q1 with an L0 test pinning F1). Q4 default except the diagnostic is renamed `ACTION_ROW_MISSING`. **Q7 overridden:** one `B/chain/` function builds all three count claims from the chain thread set for all three bodies; `thread_progress` legacy fields stay on the Finding-row set until CH-6b; differences are listed in the packet, not a stop.
- **Q9 needs no owner input:** the checked-days wording change follows from PC-1's one basis rule (BASE-1, plan §2.5.3, AG-28/AG-29), already owner-agreed.
- **For CH-6b:** retire `verified_resolution_count` / `priority_site_count` in favour of the claims, using CH-5a2b's difference list.
- **Still open from Architect 7:** R7 (summary card day) waits on the owner.

**Coordinator correction (2026-11-05):** R7 (summary card day) is NOT open. The owner approved it 2026-11-04 ("fix the summary now as recommended"); it was built as `window_day` in CH-5a2a and merged at ab890f695.

### Architect 8, second item: CH9-R2 (CH-9 pre-flight)

- **Written:** `build-sheet-CH-9.md` §10 and the plan row CH9-R2 (after CH5a2b-R). CH-9 stays at 5 units.
- **Rulings:** Q1 default (MD-0 busy request over the solar block; labelled fixture change; L0 per-hour proof). **Q2 overridden:** the expected hours are the declared operating hours (one helper shared with `critical_served`); an uncovered hour is missing, so today's 8 h Kobo story days become missing study days and MG-5 is PARTIAL on them (reported, not adapted). Q3 default, clarified (clipped intervals). Q4 default with one shared `daylight_hours`. Q5–Q8 defaults.
- **New DD-1 pre-flight item:** a story day is the full declared day (story run plus steady scenario), following the already-agreed "extend story days to declared hours, existing scenarios only". The DD-1 Architect sizes it. Without it, Kobo story days stay "not checked over the whole day" for the opportunity and MG-5.
- **Context:** this Architect is now moderately heavy after two pre-flights. Start a fresh Architect after one more small item.

## Update 2026-11-05 (Architect 9)

Architect: Claude. Nothing is committed; no database touched.

- **CH5a2b-R2 written:** `build-sheet-CH-5a.md` §B15 and the plan row CH5a2b-R2 (after CH9-R2). CH-5a2b stays at 4 units; no plan size or gate change.
- **D2 ruling: (a), the target is restated.**
  - The MD-0 estate day windows are the collector's enclosing two-UTC-date windows. By D14 they name two days, one of them `no_data`, so the grade is honest. A client-picked date names one day.
  - Polish never grades `complete` until DD-1. That is honest.
  - The new target: the text follows `count_basis(days)`, and on MD-0 every non-complete named day is a declared gap or outside the built set. The packet adds a grade table; no code changes and nothing is re-run.
- **Assigned to CH-6b (about +0.25 unit):**
  - COH-18: claim `days` = the sum of per-day grades over `window_days`, plus `gap_days` in `expected-mechanism.json`, plus an L0 planted-mapping test.
  - When CH-6b retires the legacy fields, the clone's S/week Portfolio text changes from "1 confirmed" to "1 open". CH-6b lists that change and confirms its cause from the thread events.
- **Owner:** nothing to decide. The polish "on the days checked" wording is the already-known DD-1 risk.

### Architect 9, second item: CH9-R3 (CH-9 build, u5 blocked)

- **Written:**
  - `build-sheet-CH-9.md` §11;
  - `build-sheet-CH-9b.md` Revision CH9-R3;
  - plan row CH9-R3 (after CH5a2b-R2), size rows CH-9 = 4.5 and CH-9b = 4.5, total ≈ 92 / lanes ≈ 86, and G5/G6 ≈ 89.5.
- **Q1: (b).** The mill Action needs an opportunity origin. Every Action store requires an origin Finding, and `verification_plan` references `action`. So CH-9b gets R0, "Actions from an opportunity" (2 units):
  - an exactly-one-of origin on `action` and `chain_action_thread`;
  - one `link_action`;
  - a reader audit plus a guard test;
  - byte-equal L2 proofs for Finding-origin Actions;
  - CH-4 R6 with a linked Action;
  - the ACCEPTED → APPLIED proof moved from CH-9 u5.
  
  (c) is rejected: no honest Finding exists. CH-9 has no stub.
- **Q2:** the Portfolio "kW at midday" fix stays in CH-9 (DS-R1). **Q3:** v2 is confirmed. **Q4:** SCENARIO_BASIS_MISMATCH is shown in plain words if demo-visible, never hidden. Multi-hour scenario pins go to post-demo, or to DS-1 if the demo script needs a Kobo what-if.
- **Owner:** nothing to decide. Lane 2 grows by 1.5 units for the agreed Grow mill story. Tell the owner as a size change.
- **Context:** this Architect is now moderately heavy. Start a fresh Architect after one more small item.

## Update 2026-11-05 (Architect 10)

Architect: Claude. Nothing is committed and no database was touched.

- **CH5c-R4 written:**
  - `build-sheet-CH-5c.md` §8;
  - plan row CH5c-R4 (after CH9-R3);
  - size rows: CH-5c 5 → 5.75, total ≈ 92.75, lanes ≈ 86.75, G4 ≈ 81.25, G5/G6 ≈ 90.25.
- **Q3 overridden.** max(xmin) and the R7 max-outbox term are not commit-order monotone, so a stored body could go stale.
  - New rule W1–W6: count-only terms on DB-enforced append-only tables.
  - Every other input table goes through the statement-trigger change log `chain_input_change`, counted, never filtered by `k`.
  - The watermark is read as the first statement of the compose snapshot.
  - Historical bodies are re-checked on every request.
  - The response store and the change log are reset together.
  - The guard resolves views to base tables and checks the triggers from `pg_trigger`.
- **Q9 overridden.** After the trim, `selected_revision_ids` (81.6 KB, shown only in the closed technical disclosure) is loaded when the disclosure opens, from a stored sub-route. That gives about 55 KB against an unchanged 100 KB budget, with nothing rendered removed.
- **Accepted:** Q1, Q2, Q4, Q6, Q7, Q11 as proposed. Q5, Q8 and Q10 are accepted with additions:
  - Q5: the alembic head and environment settings are part of `code_version`;
  - Q8: the pre-build uses the request path, holds no lease and does the pruning;
  - Q10: the write engine is used and the served bytes are the stored bytes.
- **Owner:** nothing to decide. Tell the owner two things: the size change (+0.75), and that the Portfolio's technical id list now loads when it is opened.
- **Context:** this Architect is light. One more item is fine.

### Architect 10, second item: CH5c-R5 (CH-5c build questions at `134f04941`)

- **Written:** `build-sheet-CH-5c.md` §8.4. Size stays 5.75. Not yet in the plan; add a CH5c-R5 row next to CH5c-R4 if the coordinator wants it.
- **R5-1:** W3 is replaced by a before/after check:
  - read the watermark and do the lookup in one short transaction, before any compose read;
  - the memo is created after that read;
  - on a miss, re-read the watermark after compose, and store only if it is unchanged; otherwise serve and do not store;
  - an L2 race test proves this.
  
  The result is never stale, and nothing torn is stored.
- **R5-2:** coverage stays complete:
  - `event_consumption` is excluded only if the listener proves no stored route reads it; otherwise it is Site-scoped through `event_outbox.site_id`;
  - `site` is scoped by its own id; `tenant` and TRUNCATE stay tenant-wide;
  - an idle-tick stability test must show the watermark does not move, otherwise stop and the Architect rules on column-listed triggers;
  - live-demo misses after real changes are accepted as honest, and the pre-build re-warms the routes.
- **Owner:** nothing to decide.

## Update 2026-11-05 (Architect 11)

Architect: Claude. Nothing is committed and no database was touched.

- **CH9-R4 written:**
  - `build-sheet-CH-9.md` §12;
  - plan row CH9-R4 (after CH5c-R4);
  - size rows: CH-9 4.5 → 5.75 (cap 6, no split), total ≈ 94, lanes ≈ 88, G4 ≈ 84, G5/G6 ≈ 91.5.
  - G4 had been missing CH9-R3's +1.5, and G6 still read 89.5. Both are corrected.
- **F1: (a), in CH-9 (+1).** `critical_served` reads the one CRITICAL row:
  - served is that row's delivered energy;
  - unserved is that row's `unserved_kwh`, which the rule already computed but the projection dropped;
  - the hour counts only when that row is SUPPORTED.
  
  Two more parts of the fix:
  - The stored row figure is added under `mini-service/2`. The bump is needed because revision reuse is keyed on the model version and the input hash.
  - 0047 re-enqueues the stored `/1` service hours through `mini_enqueue_hour`. It is enqueue only, and its downgrade is a no-op.
  
  The old adapter also added critical served to all-load unserved. The mandatory L0 is a real-shape truth table, with an unclassified load and no request. (b) is rejected (a second derivation); (c) is rejected (ships without R9).
- **F2: the study is authoritative (+0.25).** The summary GROW headline and its headroom signal read the study through the Portfolio's read, so there is one source.
- **F3: accepted.** It is folded into CH-5c/CH-5b, after the builder checks the 4 `read.mini_depth` calls for same-argument repeats (R1).
- **Polish:** honest (CH9-R2 Q2). **DD-1 full-day story days are now a hard G5 requirement.** If the DD-1 pre-flight measures them above the +50% prepare budget, it goes to the owner then.
- **Owner: inform, nothing to decide.** Suggested text:
  - "On today's demo data the 'daytime solar unused' line for Kobo has disappeared, because the demo story days only cover 8 hours of a 24-hour site and the solar check now honestly needs the whole day.
  - Making the story days full days is now a must-have in the demo-data step (DD-1); it brings the line back with measured figures.
  - The CH-9 slice also grows by 1.25 units (to 5.75) to fix a measurement gap found in review."
- **Context:** light. One more item is fine.

### Architect 11, second item: CH5c-R6 (CH-5c open item: the tick's pre-build was never served)

- **Written:** `build-sheet-CH-5c.md` §8.5 and plan row CH5c-R6. CH-5c 5.75 → 6.0 (at the cap). Totals: ≈ 94.25, lanes ≈ 88.25, G4 ≈ 84.25, G5/G6 ≈ 91.75.
- **The fix:**
  - The tick runs in the serve env (one env function), and `report.prebuild` carries `code_version`.
  - New guard: the pre-build stores nothing and reports `SKIPPED_NO_SERVE_ENV` when the cursor keys are absent.
  - Prune keeps the latest 3 per (route, request_key, code_version), and never deletes by "not my version".
- **Tests:** an env-parity L0/L1 test (proved to fail once), an L2 skip test, and an L2 per-version prune test. Acceptance: a real `demo_combined` run returns a `hit` on the first Portfolio and summary request after a tick.
- **Factory:** unify with `lab_app` only if that is seam-legal. Otherwise re-run the `fresh` parity on L3; injection is post-demo.
- **Owner:** nothing to decide. This fix is what makes "fast first request after a tick" true in the real demo run.
- **Context:** moderate after two items. Start a fresh Architect for the next one.

## Update 2026-11-05 (Architect 12)

Architect: Claude (binding checked in the plan2/ch5c `.ai/ROLE_CONFIG.md`: Claude since 2026-10-27). Nothing is committed and no database was touched.

- **CH5c-R7 written:**
  - `build-sheet-CH-5c.md` §8.6;
  - plan row CH5c-R7 (after CH5c-R6);
  - a new size row and a schedule row for CH-5c2;
  - the lanes now read CH-5c → CH-5c2 → CH-5b.
  - Totals: ≈ 96.75, lanes ≈ 90.75, G4 ≈ 86.75, G5/G6 ≈ 94.25.
- **Split.** The fix is about 2.5 units on a slice at the 6.0 cap.
  - CH-5c stays 6.0 and merges with the response store **off by default**: a pre-build with the store off stores nothing and reports `SKIPPED_STORE_OFF`. Its merge chores are M3 (a single-alembic-head L0 test, W6 and `fresh` on a merged-tree clone, re-point to 0048 if second) and L7 (the per-day loop moves into the tests, and the 279-day parity is re-run once).
  - **CH-5c2** (2.5 units, lane 1) does H1, H2, M1, L1–L4 and `host/`+`contracts/` in `code_version`, turns the store on, and owns the E4 hit check.
- **H1:** a file-state term `F` (declared roots in `config/chain/file-inputs-v1.json`: path, size, `mtime_ns`) is appended to W, and re-checked at (c).
  - The gate-result-in-key option is rejected because it costs lineage reads on the hit path.
  - Guard: a test-only `sys.addaudithook` fails on any unlisted file or network read during compose.
  - The demo loop order becomes tick (no pre-build) → comparison → pre-build.
- **H2:** `valid_until` per live row.
  - It is the min of the registered clock boundaries (helpers `read_scope.within` / `since` over one `read_scope.clock()`), capped at the next local midnight, minus 1 s.
  - The lookup treats `now >= valid_until` as a miss.
  - Static and listener guards cover clock reads. There is a moved-clock test, and a sweep test as the completeness proof on data. The pre-build runs every tick.
- **M2:** an open acceptance item owned by DD-1b, with a stop rule of `wmtime` > 50 ms or trigger cost > 10% of settle. No change-log prune before the demo.
- **L5** is folded into the H1/H2 tests. **L6** is a packet note.
- **Owner:** nothing to decide. Tell the owner that the fast first page after a tick arrives with CH-5c2 (+2.5 units), not CH-5c. No stale page can be served in between, because the store is off.
- **Context:** light. One more item is fine.

### Architect 12, second item: CH5c2-R1 (CH-5c2 pre-flight at `55219fd1f`)

- **Written:**
  - `build-sheet-CH-5c.md` §8.7;
  - plan row CH5c2-R1 (after CH5c-R7);
  - the CH-5c2 size and schedule rows.
  - CH-5c2 2.5 → 3.0. Totals: ≈ 97.25, lanes ≈ 91.25, G4 ≈ 87.25, G5/G6 ≈ 94.75.
- **Forced:** `valid_until` and the L4 TRUNCATE refusal go in `0048_chain_response_expiry`, because 0047 is merged. Whichever of CH-5c2 and CH-9 merges second re-points and runs W6 and `fresh` on a merged-tree clone.
- **Q1–Q7 accepted as defaulted.** Additions:
  - Every clock output field in a stored body is either Q4-masked (named in the packet) or proved absent. An unmasked one is High.
  - The rest of the §3 clock reads are each classified in the packet.
  - An objective-head parity test, live and historical.
  - The module list changes only by a reviewed diff.
  - Beyond-§3 sites are Known Deviations, and go to the Architect before merge if they reach a stored body.
- **Owner:** nothing to decide.
- **Context:** moderate after two items. Start a fresh Architect for the next one.

## Update 2026-11-05 (Architect 13)

Architect: Claude (binding checked in the plan2 `.ai/ROLE_CONFIG.md`: Claude since 2026-10-27). Nothing is committed and no database was touched.

- **SPLIT-1 written** (owner efficiency rule, 2026-11-05):
  - a "Build units (split 2026-11-05)" section at the end of `build-sheet-CH-5b.md`, `-CH-6.md`, `-CH-9b.md`, `-DD-1.md`, `-CH-5d.md`; each unit has scope, a reading budget, acceptance checks and a review rule;
  - plan row SPLIT-1 (after CH5c2-R1); the DD-1 size and schedule rows; the totals and G5/G6 rows; lane notes on the CH-5b and CH-6b schedule rows.
- **Units.** CH-5b 5.5 = 5b1 1.5 + 5b2 2 + 5b3 2. CH-6a 6 = 6a1 2.5 + 6a2 2 + 6a3 1.5 (6a2/6a3 one review; R7 moved into 6a3 so all board-value changes land in one L3 table). CH-6b 5.75 = 6b0 0.5 + 6b1 1.75 + 6b2 2.25 + 6b3 1.25 (6b2/6b3 one review). CH-9b 4.5 = 9b1 2 + 9b2 1 + 9b3 1.5 (9b2 reviewed with 6b0). DD-1 = 1a1 2 + 1a2 2 + 1b1 1.5 + 1b2 1.75. CH-5d1 1, unchanged.
- **Sizes.** No split overhead counted. DD-1 6.5 → 7.25: the full-day story days (CH9-R4 hard G5 requirement, 0.5) and the M2 trigger-cost measurement (CH5c-R7, 0.25) were never sized. Totals ≈ 98.0, lanes ≈ 92.0, G4 ≈ 87.25, G5/G6 ≈ 95.5.
- **Lane moves.** CH-5b1 (guards and tools) and CH-6b0 (R16 recurrence during a check) go to lane 2; both read only merged code. CH-5b1 must merge before CH-5b3 and CH-6a1; CH-6b0 before CH-9b3.
- **Lane-2 order (conditional).** Only CH-9b3 needs CH-6a3. If CH-6a3 is not on main when CH-6b0 merges, lane 2 runs DD-1a1 → DD-1a2 → DD-1b1 before CH-9b3; DD-1b2 always follows CH-9b3 (F-THREADS expects the mill verification). Remaining after CH-5c2 and CH-9: lane 1 ≈ 15.25, lane 2 ≈ 14.75.
- **Pre-flight placement.** CH-9b P1 (pass margin, possible owner OD) is asked in CH-9b1. DD-1 P1–P6 are answered once by DD-1a1; `.agent/DD-0c-probe-results.md` must exist first.
- **Owner:** nothing to decide.
- **Context:** light. One more item is fine.

### Architect 13, second item: CH5c2-R2 (CH-5c2 packet ruling list at `bc2ba7c35`)

- **Written:** `build-sheet-CH-5c.md` §8.8. All seven accepted; the size stays 3.0. Owner: nothing to decide.
- **CH-5b amended (item 5).** A 304 needs the watermark plus one indexed live-row lookup, because the ETag includes `valid_until`. There is still no composition, and a route that is not stored saves only bytes. The CH-5b2 builder must read §8.8 item 5 along with Revision OWN-CH5c.
- **Item 3:** the E4 hit check must show hits in the serve environment.
- **Context:** moderate after two items. Start a fresh Architect for the next one.

## Update 2026-11-05 (Architect 14): CH5b1-R (CH-5b1 pre-flight at `4479b6ce2`)

- Written: `build-sheet-CH-5b.md` "CH5b1-R" section; plan row CH5b1-R (after SPLIT-1). Size 1.5 unchanged; nothing committed; no DB touched. Q1 partly overridden: a declared NOT_CHAIN_SOURCED table with verified producers. `WARNING:CHARGERS_MOSTLY_IDLE` has no producer, so it is the one known-gap row, owner CH-6a1, which adds a detector or removes the key; the Architect rules on that choice. Q2–Q7 accepted, with additions. Owner: nothing to decide. Context: light.

### Architect 14, second item: CH5b2-R (CH-5b2 pre-flight at `c3cf85409`)

- Written: `build-sheet-CH-5b.md` "CH5b2-R" section; plan row CH5b2-R (after CH5b1-R). Size 2 unchanged; nothing committed. Q1 accepted: all five routes are stored, with every query parameter in the key. Q6 and Q9 partly overridden, with wording from the MA-1 mock (`v70/index.html:411-438`). New copy beyond the mock is labelled MOCK DEVIATION. The price suffix is a Known Deviation owned by CH-6. Q5 is interim until CH-6a1. Owner: nothing to decide. Context: moderate after two items; start a fresh Architect next.

### Architect 15: CH5b1-R2 (CH-5b1 packet D1 at `d54476ce2`)

- Written: `build-sheet-CH-5b.md` CH5b1-R2 line, at the end of the CH5b1-R section. Ruled (b): the producer of `SIGNAL:EVIDENCE_READINESS` is `outcomes/status.py:86-87`, the readiness status path that is already live. Owner CH-5b1, in its fix round. The test is behavioural (`outcome_state` on the `@EVIDENCE` alias per domain), and `KNOWN_GAPS` goes back to `CHARGERS_MOSTLY_IDLE` only. Nothing committed; no DB touched; owner: nothing to decide.

### Architect 15, second item: CH9b1-R (CH-9b1 pre-flight at `641c34e0d`)

- Written: `build-sheet-CH-9b.md` CH9b1-R section; plan row CH9b1-R (after CH5b2-R). Q1 overridden to B: the mill Action goes on `domain_action` (domain + MINI, exactly-one-of Finding/opportunity origin). APPLIED is the work-case completion, as CH-9 Q8 says. `action` is untouched. Q2 and Q3 overridden to match (no new table and no `apply_schedule`); Q4–Q7 accepted (Q5 classes swapped, Q6 extended to a Cold/EV domain action). Sizes: CH-9b1 3, CH-9b2 2.5 (it gains the `verification_plan` exactly-one-of action/domain_action, and the applied anchor and origin widening), CH-9b3 1.5; total 7, no split. Migration 0051. P1 owner-decided 2026-11-05 (`.agent/owner-mill-pass-margin-2026-11-05.md`): the catalogue target is `"10*mean(later) >= 11*mean(baseline) productive_kwh[midday]"`. Nothing committed.

## Update 2026-11-05 (Architect 16): SCOPE-1, scope cut to a defensible first-client presentation

Architect: Claude (binding checked: `.ai/ROLE_CONFIG.md`, Claude since 2026-10-27). Nothing committed; no DB touched. Owner, verbatim: `.agent/owner-scope-backlog-2026-11-05.md` (both lines).

- **Written:** `.agent/backlog-post-demo.md` (BL-01 to BL-12, 4.25 units, plus the "present less" list); a "Scope cut (SCOPE-1)" section at the end of `build-sheet-CH-5b.md`, `-CH-6.md`, `-CH-9b.md`, `-DD-1.md`, `-CH-5d.md`; plan row SCOPE-1 (after CH9b1-R), the totals, gates, §2.1, §2.2 and schedule rows.
- **Build list (remaining 27.0).** Lane 1 (13.0): CH-5b2 2 (in build) → CH-5b3 1.25 → CH-6a1 1.25 → CH-6a2 2 + CH-6a3 1.5 → CH-6b1 1.75 → CH-6b2 2.25 + CH-6b3 1.0. Lane 2 (14.0): CH-9b1 3 (in build) → CH-9b2 2.5 → CH-9b3 1.0 → DD-1a1 2 → DD-1a2 1.75 → DD-1b1 1.25 → DD-1b2 1.5 → CH-5d1 1. CH-9b3 no longer waits for CH-6a3; CH-6b0 is dropped.
- **Totals:** ≈ 96.5 (100.5 − 4.25 + 0.25); lanes ≈ 90.5; G4 ≈ 86.5; G5/G6 ≈ 94.0. The earlier total rows had not carried CH9b1-R's +2.5; they do now.
- **One addition (+0.25, CH-6a3), stated as defensibility-critical:** "Why?" on every money figure names the declared price ("{kWh} kWh × {price}"), closing CH5b2-R Q7's Known Deviation. Reason: a figure the client cannot trace through "Why?" is not defensible.
- **Owner to confirm (unsure):**
  1. BL-09: the mill check is shown without MG-5/MG-4 guardrails ("rose by at least the declared 10%"); a critical-load question is answered from the MG-5 row. Keep in backlog, or put back (+0.5)?
  2. BL-07: RECURRED_DURING_CHECK. No story day needs it after MD0b-R, but if a headroom occurrence falls in the mill's later window it is not recorded as "during the check". Backlog, or put back (+0.5)?
  3. The +0.25 price line in "Why?".
- **Standing rule for every future Architect (SCOPE-1).** Any new work, whether from a ruling, a pre-flight answer, a review finding or a fix round, must be stated in the ruling as **defensibility-critical, with its reason**: which shown number, label, claim or "Why?" line would be untrue, untraceable or unable to hold up under questioning without it, or why the build would not run. Anything not stated that way goes to `.agent/backlog-post-demo.md` with an id, source, reason and size, and adds nothing to the plan. Prefer presenting less over building more. A size increase on a build unit must name the SCOPE-1 reason in the plan row.
- **Context:** moderate. Start a fresh Architect for the next item.

## Update 2026-11-05 (Architect 17): CH5b2-R2

- Binding checked: Claude, set 2026-10-27 in the plan2/ch5b2 `.ai/ROLE_CONFIG.md`. Nothing committed. CH5b2-R2 is recorded at the end of the CH5b2-R section in `build-sheet-CH-5b.md`. All four packet items are confirmed: KD-6 `threads_through`; "Critical supply served"; the estate `say` fallback as a MOCK DEVIATION; the 304 running admission and the Site-set read. No new work, and no change to size or plan.
- CH9b1-R2 is recorded at the end of the CH9b1-R section in `build-sheet-CH-9b.md`, covering the mill Action link latency. The fix is option (b): DD-1 R8's prepare backfill step c. DD-1b2 owns it at +0. It records the mill Action before R8, and F-THREADS asserts that the Action is linked. (a) is rejected. (c) is not built because Q2 left no live create path.
- CH5b3-R is recorded at the end of `build-sheet-CH-5b.md`. All five builder defaults are accepted: `chainClient` with a per-URL ETag; the days line in the dialog only (MD-CH5b-4, new backlog item BL-13 at an estimated 0.25, outside the plan); the mock's card markup; `Dialog.tsx`, a modal or a sheet at 600 px, with Close at every width (MD-CH5b-5); "Why?" on every row except NOT_MEASURED and on the four cards, with a loading line and an error line. Size stays 1.25.
- CH9b2-R is recorded at the end of `build-sheet-CH-9b.md`.
  - Unit change: **CH-9b2 2.5 → 3.0.** The +0.5 is Q8, where 0052 widens `verification_outcome` and `verification_evaluation_request`, stated as defensibility-critical. That makes CH-9b 7.0 and lane 2 14.5. The plan file's lane-2 rows and totals still need the +0.5.
  - Q2 is overridden: the effective day is in neither window.
  - Q4 SHORT is accepted. The screen shows "Not judged yet: only {n} of 3 fully checked days before the change", and F-THREADS asserts that the plan is not SHORT.
  - All other defaults are accepted.
- CH6a1-R is recorded at the end of `build-sheet-CH-6.md`. Q1 is overridden: the `MEASURE:` records are data only in CH-6a1. Their wiring into "Why?" moves to CH-6a3 at +0, in the same body change and clone run as the price line, and it closes CH5b2-R Q5's Known Deviation. Q2 to Q5 are accepted. No unit change: 6a1 is 1.25 and 6a3 is 1.5. Context is now moderately heavy; a fresh Architect is advised after this item.

## Update 2026-11-05 (Architect 18): CH6a2-R

- Binding checked: Claude (main `.ai/ROLE_CONFIG.md`, 2026-10-27). Nothing committed. CH6a2-R is recorded at the end of `build-sheet-CH-6.md`.
- Q1, Q3 and Q5 are accepted.
- Q2 is overridden for the potential. Its basis comes from the study's own days, and is NOT_KNOWN when the item has none (MD-CH6-4). MG-5 and MG-2 take their basis from the days of their source measure, and only when the packet cites that those rows produced the figure.
- Q4 is overridden. The study shows for OPEN, RECURRED, REOPENED and CHANGE_APPLIED. RESOLVED_MONITORING, CLOSED and WITHDRAWN show "No potential found yet".
- Q6: the copy equals the mock, but the basis is NOT_KNOWN with `days=None`.
- CH-6a2 stays 2. There is no new work and no backlog item.

## Update 2026-11-05 (Architect 18): CH6a3-R

- CH6a3-R is recorded at the end of `build-sheet-CH-6.md`. Nothing committed.
- **CH-6a2 deviations:** all eight are confirmed. ACTION_IN_HAND corrects my CH6a2-R Q4 omission. `POTENTIAL_STATES` is now defined by exclusion, as every state except RESOLVED_MONITORING, CLOSED and WITHDRAWN.
- **Q3, price line in "Why?":**
  - Several prices give the line "{kwh} kWh at {n} declared prices"; it is not omitted.
  - MG-2 gets "{lo}–{hi} L × {price} {cur}/L" from the stored consequence. This is +0.25 and defensibility-critical.
- **Q4:** must show "Not known yet", never a blank.
- **Q5:** the headroom words follow `POTENTIAL_STATES`.
- **Q1, Q2 and Q6** are accepted.
- **Sizing:** BL-13 stays in the backlog. CH-6a3 goes from 1.75 to 2.0, and the plan row needs that +0.25 with the SCOPE-1 reason.

## Update 2026-11-06 (Architect 19): CH9b3-R

- Binding checked: Claude. Nothing committed. CH9b3-R is recorded at the end of `build-sheet-CH-9b.md`. All 12 defaults are accepted. **CH-9b3 goes from 1.0 to 1.5**, making CH-9b 7.5 and lane 2 15.0; the plan rows still need this. SCOPE-1 reason: the mill verdict page is the only place the R7 before/after line and the metrics table can show, and without it the Grow row's "verified" claim is untraceable. There is no overlap with CH-6a3. For the owner: Q3, a zero baseline, is read as INCONCLUSIVE BASELINE_ZERO, so no rise is claimed.

## Update 2026-11-06 (Architect 20): DD0c-R

- Binding checked: Claude. Nothing committed. DD0c-R is recorded at the end of `build-sheet-DD-1.md`; plan row DD0c-R; backlog BL-14 added. L1 approved as an opt-in host `seal_once` in DD-1a1 at R3's +0.25; all three parity differences acceptable; L2 not built (SCOPE-1), B-22 kept with B-16 only on an over-3 h DD-1b2 rehearsal (R1); earlier-day Cold fill backlogged as BL-14 (only forward Cold days can be added). Sizes unchanged, DD-1 6.5. No owner question. DD-1a1 may start.
- DD1a1-R (Architect 20, same day): recorded at the end of `build-sheet-DD-1.md`. Q1–Q8 accepted. Q2 (Kobo night repeats the 18–20 h no-sun evening window unchanged) is accepted with a "steady night" label, and with an L2 stop gate if the night opens a generator run, fuel use, a Finding, a thread or a money change. Q5 corrects DD0c-R's ~22 Cold runs per day to 24. DD-1a1 stays 2 and DD-1 stays 6.5. The owner is informed of the night-data choice but it does not block.
- DD1a1-R2 (Architect 20, same day; owner `.agent/owner-kobo-nights-2026-11-06.md`): the Kobo night profile is recorded in `build-sheet-DD-1.md` and the plan row DD1a1-R2. It replaces DD1a1-R Q2.
  - Grounded night loads with a stated basis per value: residential 9/5/3/5 kW and clinic 4/2 kW, no sun, mill 0. Start states come from measured probe runs, never chosen.
  - The steady night is carried by the battery with no generator. One story night follows the overcast day, before the trial; its generator run comes from the physics, not from a declared result.
  - Gates protect ACT-K1, the mill verification and the spare-solar study.
  - DD-1a1 goes from 2 to 2.5 and DD-1a2 from 1.75 to 2.0, so DD-1 is 7.25. The plan's lane-2 totals still need +0.75.

## Update 2026-11-06 (Architect 21): CH6a3-R2

- Binding checked: Claude. Nothing committed. CH6a3-R2 is recorded at the end of `build-sheet-CH-6.md`. No owner question.
- **H3, the ONE-SOURCE rule:** the Grow money, the subline and the kWh/price contributor all come from the snapshot earnings claim, or all read "Not known yet".
- **H1:** the test fixture is stale, but its money expectations stand.
- **H2:** the cause of the all-NOT_KNOWN real data is unproven. R2a must settle it with clone row counts (closes M1). The full §A8 L2m runs on `mechanism_db()`, and the real-data end-to-end check is added to DD-1b2 F-THREADS.
- **H4:** a days line per part, three parts always shown, the v70 grid, and MD-CH6-1/2/3 plus MD-CH6-7 registered (renumbered from the colliding -4).
- **Medium and Low:** M1–M5 are fixed now. L3 becomes BL-15.
- **Sizing:** CH-6a3 goes from 2.0 to 4.25, in two rounds: R2a backend (1.5), then R2b wire and layout (0.75), with one re-review after both. The plan rows, BL-15 and the DD-1 F-THREADS line still need updating.
- DD1a1-R3 (Architect 22, 2026-11-06; binding checked, Claude; nothing committed): recorded at the end of `build-sheet-DD-1.md`.
  - The steady night's 05:00 generator start is accepted as physics. R2's "41 %" was an arithmetic slip, and the loads match their stated bases.
  - The 0 L over 55 min RUNNING is the specified model: battery-first order and no idle fuel. It is disclosed in the night label and the "Why?" line, and backlogged as BL-16.
  - The gate is replaced by five L2 checks: night shape and MG-5; MG-2 and ACT-K1; mill and spare solar; Findings, threads and money; the 06:00 seam.
  - Q2: `kobo-steady-day` declares 300 L / STOPPED with a source line. The builder drafts every Kobo file on the registered Site and re-runs probes S and O there.
  - DD-1a1 2.5 → 2.75 and DD-1 7.5; the plan rows need it. The owner is informed, with a recommendation to accept.
- DD1a1-R4 (Architect 22, same day; nothing committed): `mill-midday` is BLOCKED on v6. The fix is a derived `kobo-mill-midday`: the `kobo-daytime@2` windows verbatim, plus 300 L / STOPPED with R3's source line, used by the v2 kind. The manifest override and reusing `kobo-steady-day` are both rejected. Checks: windows equal the parent, READY on KOBO-001, 0 generator starts, and the CH-9b mill verdict unchanged. Size +0; DD-1a1 stays 2.75.
- DD1a1-R5 (Architect 22, same day; nothing committed): option (a), which amends Q6.
  - One sequence epoch per Site-day stream, with the sequence continuing across runs. Story runs are emitted unchanged; complements leave out shared instants and end exclusive. Cold uses the same rule ([start, covers_end)).
  - (b), (c) and (d) are rejected.
  - A gateway probe comes first: continuation across sealed runs, out-of-order complement receipt, and a `late` offset. Stop if any is refused.
  - Acceptance: the same 3 Findings with and without complements, 0 AMBIGUOUS, and Q6 trial metrics equal.
  - DD-1a1 2.75 → 3.25, DD-1 8.0; the plan rows need it. No owner question.
- DD1a1-R6 (Architect 23, same day; binding checked, Claude; nothing committed): on the Kobo `degraded` day, the outage lasts the rest of the local day, and post-outage complements deliver 0. The reset epoch is rejected because it invents a reset and goes AMBIGUOUS. Required: clear `_OUTAGE` per build, and add a note line. The L2 check is a test-calendar degraded day: night-early full, half the story, 0 after, no S2 row after the last delivered sample, the outbox keeps the rest, the next day is clean, 0 AMBIGUOUS, and the grade equals v1. The v2 calendar has no Kobo degraded day (add-day only). Size +0; DD-1a1 3.25.
- DD1a1-R7 (Architect 23, same day; nothing committed): split trial-after's `night-early` at ACT-K1's 00:00Z `effective_from`.
  - Part A is [21:00Z, 00:00Z) on v16. Part B is a derived `kobo-night-early-from-0300` on [00:00Z, 03:00Z) on v17, with its start state measured from a probe of Part A at 00:00Z.
  - Both parts are on the same Site-day epoch and gateway state, with the sequence continuing, so R5 holds.
  - Moving the boundary and moving the night elsewhere are both rejected. The rule is general: split any complement that crosses a revision boundary.
  - Checks: L0 instant-once with one epoch; L2 READY on v16 and v17, no seam jump, one epoch with the sequence 1..N, ACT-K1 equal with and without, and R5's acceptance.
  - Size +0.25: DD-1a1 3.5, DD-1 8.25; the plan rows need it.
- CH6b1-R (Architect 24, 2026-11-06; binding checked, Claude; nothing committed): CH-6b1 pre-flight Q1–Q8 ruled in `build-sheet-CH-6.md` CH6b1-R. Q1–Q4 and Q6–Q8 are accepted, Q2 with a no-reach-back condition. Q5 is accepted with two overrides: the "At least" form also applies when a Site is NOT_KNOWN, and the total is the sum of the rounded Site values. CH-6b1 owns the CO-6/CO-6b LATEST_EVENT → PERIOD lines in `tools/demo_combined_finish.py`, and DD-1a1 does not touch them. The size stays 1.75.
- CH6b1-R2 (Architect 24, 2026-11-06; nothing committed): KD-2 MG-5 one-day verdict kept but its days line must name the day (single-day node window), all no-kpi reading verdicts; +0.25 → CH-6b1 2.0; window-wide MG-5 → BL-16. KD-3 (states template 4/7, L2m recomputes) and KD-1 (Cold/EV L0 only) confirmed.
- CH6b1-R3 (Architect 24, 2026-11-06; nothing committed): KD-4 rejected; PERIOD stays but cold/EV evidence-bound reads cover each selected evidence window inside [lo,hi) (latest contained event shown, its window named in the days line, repeats counted, nothing outside read); c3 test back to NEEDS_ATTENTION+REPEATED; +0.75 → CH-6b1 2.75.
