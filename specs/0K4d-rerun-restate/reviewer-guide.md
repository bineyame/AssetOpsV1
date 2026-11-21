# 0K4d reviewer guide

Architect (Claude), 2026-11-21, rev 2 (D-0K4.26 to D-0K4.29). Discovery review (W5): the figures that will reach the option card. Read
`spec.md`, D-0K4.7, D-0K4.9, D-0K4.11, D-0K4.12, D-0K4.16 and D-0K4.26 to D-0K4.29 in `specs/0K4-dispatch-model-review/rulings.md`, then the
diff and `/opt/assetecon/evidence/0K4d/`. Done means every question of spec §5 answers yes with evidence and every
plant fails its named test.

## What to check, and how

1. **The rule is the owner's.** `admission.py` against D-0K4.9 part by part; the dawn appears only in
   `DawnInformation`. Any use of a dawn figure in `admitted` is High.
2. **Nothing modelled in the study or the rule.** `admission.py` and the `replay_study.py` additions hold comparisons,
   counts and local-date framing only; no price, no fuel law, no threshold beyond the two rule defaults.
3. **Reproduce one case yourself.** Through the slot pool, run the 8-day v2 season on v8 and read `stop-70-reserve-30`'s
   avoided litres, most starts in a day, and longest run without full charge with your own loop. Equal to V2 and to
   the tool's output. Quote the `study.json` identity header (commit, season digest, trajectory digests) you reproduced
   against (D-0K4.28).
4. **Fault gone.** Read the per-step night table in the evidence for one post-overcast night: the generator starts at
   35 %, SOC rises while it runs, no battery discharge beside it. V3 holds on the 61-day baseline too.
5. **Labels and assumptions.** Every printed line starts with the four labels; `study.json` has `assumptions` equal
   to V4's four strings, each with its basis and derivation (D-0K4.27), and the Kobo header has `admission_rule`;
   nothing says observed. No design value is read or written: run `\b(210|2,?916|68)\b` and `\b(20|150) ?L\b` over
   the two tools, `admission.py` and the `replay_study.py` diff, and list each hit with its reason (a declared fact
   such as 150 kWh is not a design value). The statement-catalogue check shows no `HAND_BUILT_NEW`.
6. **One figure per quantity.** Check the packet's numeral list against the restated §4.2 text, numeral by numeral:
   each is one of D-0K4.29's four kinds, and each place D-0K4.29 names is restated as it says. "0 of 61", "dawn PASS",
   330, 120, 12.00, 2,916.00 and the sensitivities are gone; the value reads "Not available yet (`6c` values it)". The packet's reconciliation table is the only
   two-figure table and says why each figure moved.
7. **Reproducibility.** V5 (in-process, no flags, against `main`'s recorded literals), V6, and the 0K2 and 0M recorded commands still run on v7 and v1 (the defaults).

## Plants (each must fail the named test; revert after)

| # | Plant | Must fail |
|---|---|---|
| P1 | `admitted` also requires `dawn.days_below == 0` | AD4 |
| P2 | starts judged relative even when the baseline passes | AD2 |
| P3 | full-charge limit `every_days` instead of `every_days - 1` | AD3 |
| P4 | `reserve_breach_steps` counted against the baseline's reserve for every case | AD7 |
| P5 | the end SOC not counted for the last date | AD7 |
| P6 | `assumptions` not copied to `StudyResult` | V4 |
| P7 | the Kobo tool's default `--model-version 8` | V5 |
| P8 | the baseline judged against an absolute limit with no fallback | AD5 |
| P9 | Mto's derivation entry for the no-load rate deleted | V4 (`KeyError`) |
| P10 | the Kobo tool accepts `--model-version 8 --season v1` | V6 |

## What counts as done

All of spec §5 yes; P1-P10 each fail; the 61-day figures reproduced for one case by the reviewer; mid-build count 0.
