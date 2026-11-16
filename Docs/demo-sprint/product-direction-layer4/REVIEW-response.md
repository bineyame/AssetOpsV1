# Layer 4 pack: response to the independent review

## Author response (rev 2)

**AssetOps Architect (Claude) · 16 Nov 2026 · branch `task/product-direction-layer4-design`, edits on top of `f1f6d9bf9`, nothing committed.** `REVIEW.md` is unchanged. All edits are inside `Docs/demo-sprint/product-direction-layer4/`.

**Checks after the fixes:**
- `python3 check_manifest.py` gives **126 checks passed, 0 failed**. It had 73; it was extended for M1, M3, L2, L3 and L10.
- `node build.mjs` rebuilt the mock-up, and `tools/run-audit.sh` passes everything:
  - 146/146 routes render with no errors.
  - 0 broken links.
  - 0 routes overflow at 390 px.
  - 0 internal-vocabulary hits on the 36 added screens and their drawers. The forbidden list is now wider.
  - Drawer focus, trap, Escape and return all pass.
  - Focus visible 6/6; contrast 14/14.
  - The role toggle keeps the same numbers in 4/4 roles.
  - All 4 budget × letter-of-intent cases pass.
  - The pilot form only shows the example toast.
- The main HTML re-renders: 5/5 diagrams, no script errors, no overflow at 390 px.

| Finding | Outcome | What changed |
|---|---|---|
| **M1** The "cheapest" EV schedule was not the cheapest bill | **Fixed** | Tariff C-114 gains a 00:00–05:00 tier at 0.09; October is unaffected, because charging on arrival ends around 23:10. EMB-CHEAPEST is now costed at 12,975/month, the lowest bill, and is still rejected because 3 buses are short. EMB-DEADLINE is 13,356/month (saving 8,788.80; 12-month net 103,965.60). Ruiru is given its own older tariff C-117 (no tier), so its October figures stand. The checker asserts cheapest < deadline and checks every component. Updated: manifest; main document §6, §8.3; contracts §4.4 and new E7; models §4.1, EV-T1/T2 and C3 row 6; integration trace E; Q6; mock-up comparator and drawer. |
| **M2** `evidence_class` name collision | **Fixed** | The new axis is now `money_class`. Main document §5 now states that 0042:50 is a column named `evidence_class`, used as a source basis, and gives its readers. Also updated: §3.3(b), §4, §13, contracts §6.2, models, the matrix row, the manifest's R2 wording and new ruling A11. "Evidence class" appears nowhere on screen. |
| **M3** Budget switch mixed two assumptions; "or/and" wording | **Fixed** | The mock-up has a separate letter-of-intent control. All four cases show both inverter paths side by side, with the line "More budget never lowers the result". The checker enumerates the four cases by brute force: 6,096 / 2,556 / 6,096 / 3,546 at spend 6,430. The wording is "and" everywhere: main document §2.2 and §7.3, integration line 299, models §7.3. The manifest now states why the claim path loses the huller: restore on 28 Nov, connection needs 5 working days, lapse on 30 Nov. |
| **M4** Measured build cost absent | **Owner decision** | Q10 now records Deliverable 7 as "met except measurement". The options are to authorise one re-benchmark on an allowed `*_test` or `_audit` database, or to accept the gap. The cost plan's status line and the "could not be completed" table say the same. |
| **L1** Internal vocabulary on client screens | **Fixed** | The method and meter-check sentences are rewritten in plain language. "fixture" and "manifest" are removed from client text. The audit's forbidden list is extended and now also scans evidence drawers. |
| **L2** Coverage only for Lakeside | **Fixed** | Harvest coverage is 97.8% (Thika maintenance 80 estimated). Metro coverage is 99.28% (Kasarani maintenance 300 estimated). The checker verifies both. All three operators render coverage. |
| **L3** "[test-confirmed by checker]" overstated | **Fixed** | Relabelled "[derived, arithmetic checked]". The checker now covers the option economics (STOPSOC, huller, welding, billing, MWEA-AGG, KIRI repair and replace, EMB), the inverter residuals and allocation optimality. |
| **L4** Stale cross-references | **Fixed** | The C3 rows cite OR-ENT-2, OR-ENT-3, OR-ALLOC-1 and OR-VER-1. The link count is updated to 335 (after L6). |
| **L5** Kasarani stopgap basis ambiguous | **Fixed** | The manifest, main document, contracts and mock-up now say: 90 in total for the 3 nights to the 9 Nov restore, against about 240 of penalties and 2 broken departures if we wait. |
| **L6** X8 missing | **Fixed** | X8 rows link O2, P1 and A3 to S6 and S8. X8 is also tagged on crew-dependent levers (MG-L3, MG-L6, MG-L10, CC-L5, CC-L6, CC-L7, CC-L9, EV-L3, EV-L9). |
| **L7** Mock-up details | **Fixed** | Every do-nothing row has a reason. The Mto inverter "do nothing" path shows "$0 now; cover lost after 27 Nov 2026". Checklist B9 now says the budget switch is Lakeside only. |
| **L8** Replay figures read as results | **Fixed** | Main document §2.1 marks them at first use as design values that the slice 3 adapter must reproduce. The mock-up labels 210 L, 20 L and 68 L "Design value: to be reproduced from your data". |
| **L9** v72 characterisation thin | **Fixed** | Main document §9 names v72 as the v7.2 design foundation (tokens, Inter, light and dark) that UQ-FI builds on, says vNEXT has not adopted it yet, and refers to Q4. |
| **L10** Mixed EV cost bases | **Fixed** | Maintenance is now included at every depot (Embakasi 600, Ruiru 500). Plan is 38,520.80, actual 41,705.12, 32.03 per departure; the variance is unchanged at −3,184.32. |
| **L11** Oracle shipped in the bundle | **Fixed** | `tools/gen_fixtures.py` strips `oracle:`, and the bundle contains no oracle ids. Recorded as ruling A12. No owner decision is needed. |
| Residual risks 1–3 | **Recorded** | RR1 (replay calibration on clipped days) and RR2 (protected-seam port change) are now in slice 3 of the phase plan. RR3 (two demo estates side by side) is an owner decision before any client demo. All three are in `design-questions-and-decisions.md`. |

None of the findings is disputed.

## Author response (rev 3)

**AssetOps Architect (Claude) · 16 Nov 2026 · on top of `d30ef6af4`, nothing committed, `REVIEW.md` unchanged.**

**Checks after the fixes:**
- `check_manifest.py`: **127 passed, 0 failed**. One check was added for N3 (cost per kWh).
- The mock-up was rebuilt: `fixtures.js` regenerated with no oracle ids, then `node build.mjs`.
- The audit now runs through the portable `tools/run-audit.sh --shots`:
  - 146/146 routes render with no errors.
  - 0 broken links; 0 routes overflow at 390 px.
  - 0 vocabulary hits.
  - Focus 6/6; contrast 14/14.
  - Drawer, role and budget × letter-of-intent checks all pass.
- I spot-checked the edited screens in the browser.

| Finding | Outcome | What changed |
|---|---|---|
| **N1** M2 rename incomplete, and the wrong column cited | **Fixed** | Changed `money_class` in: matrix row 61 (and row 79's "money class"), phase plan slice 2b, A4, integration §App 6, and the contracts §3.1 header. The main document §5, A11, the matrix and the manifest now cite **both** existing source-basis columns: `finding_thread_occurrence.evidence_class` (0042:50, written by `chain/threads.py:205`) and the snapshot column (`0043_chain_snapshots.py:37`, `chain/measures.py:37`, read in `chain/ports.py`, `chain/builder.py` and `chain/outcomes.py`). |
| **N2** October rationale impossible | **Fixed** | The 00:00–05:00 tier is now a contract term effective 1 Nov 2026, so October is billed at 0.12 in all non-peak hours. Updated the manifest tariff and note, the models §4.1, the main document §6, and the mock-up's "what happened" text. |
| **N3** Cheapest bill only because it buys less | **Fixed** | The models §4.1, contracts E7, main document §6, manifest note and walkthrough now say that the cheapest schedule is lowest only because it buys 9,300 kWh less, and that per kWh delivered it costs 0.167 against 0.154. The checker asserts the per-kWh ordering. |
| **N4** Stale 6,928.80 | **Fixed** | `fixture-mapping.md` now reads $8,788.80, with the new verification target. |
| **N5** Metro proof target weaker than the model | **Fixed** | The target is now near-zero peak-price charging, about 62,000 kWh a month at the 00:00–05:00 rate, peak ≤ 400 kW, and every departure met. |
| **N6** Kasarani "wait" path shown as $0 | **Fixed** | The path now reads "$0 now; about $240 in likely penalties and 2 broken departures". |
| **N7** Crew meter ignores the letter-of-intent case | **Disputed, with an explanation added on screen** | 3 of 3 is correct even when the huller is lost. The Mto visit is still needed to fit the restored inverter and check the meters; the huller connection only shared that visit (manifest: Mto inverter + huller + audit combined into one visit). The plan page now shows this explanation under the meter in that case. |
| **N8** Pre-existing UI issues | **Fixed (cheap)** | Thika now reads "Within the occupancy model" when occupancy is at plan. Bridge driver amounts on cost operators use one sign convention (negative = worse), so −$2,604 matches the cost lines. The energy-model formula on client screens is replaced by plain words. |
| **N9** Audit wrapper not reproducible | **Fixed** | `tools/run-audit.sh` now reads `CHROME` and `PW` (required) and the optional `AUDIT_LD_LIBRARY_PATH` / `FONTCONFIG_FILE` from the environment, with clear errors when they are missing. The README documents the setup for any machine. |

Residual risks from the re-review are unchanged and already recorded: screenshots were spot-checked rather than compared in full, and RR1 still governs the replay design values.
