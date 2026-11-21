# 0K4d handshake (rev 1 spec; reviewer and implementer pre-flight)

Fresh Claude reviewer, 2026-11-21, on `main` at `e39a5d2fa`. Read: `spec.md`, `reviewer-guide.md`, D-0K4.7, D-0K4.9,
D-0K4.11, D-0K4.12, D-0K4.16 and D-0K4.19 to D-0K4.25 in `specs/0K4-dispatch-model-review/rulings.md`,
`one-figure-change-list.md`, the 0K2 spec and rulings (D-0K2.23), and the code below.

**Commit 1 needs only `main`: it holds.** §2.1, §2.2 and AD1-AD8 touch `runs/replay_study.py` and new files only.
None of `task/0K4a-dispatch-v8` (commits 1-2 and the handoff, `3baf2fa63`), `task/0K4b-fuel-curve` or
`task/0K4e-candidate-energy` touches `replay_study.py`, `headroom_replay.py`, the two tools, `mto.py` or
`kobo_season.py`. Nothing outside `replay_study.py` constructs `CaseOutcome` or `StudyResult`, so the four new required
fields break no caller. `headroom_replay.py` has its own outcome types. The seam test
(`backend/tests/test_0k1_replay_port_seam.py:38-61`) flags only files whose text holds `forward_replay`, so
`admission.py` needs the allow-list only if it names that word. Commits 2-3 need 0K4a (v8 in `kobo_draft`,
D-0K4.22 R1) and 0K4c. No database is used anywhere, so the `*_test` rule is not engaged.

**Checked and found as the spec says:** `CaseOutcome` (`replay_study.py:182-211`; `clipped_steps` then `input_class`);
`StudyFrame` :122-147; `StudyResult` :219-239; `dawn_verdict` :206; `_outcome` :466-497; the B13 adopting-word scan
(`backend/tests/test_0k2_replay_study.py:518-538`; "replace" is on its list, so docstrings are exempt but string
literals are not); T11 (`host/tests/test_0k2_kobo_season.py:408`); `GRID = (S(90, 30), S(70, 30), S(90, 25))` (:66);
`check_manifest.py`, `tools/select-tests.py`, `tools/heavy-slot.sh --label`. Plants P1, P2, P3, P5, P6 and P8 each
fail their named test as written.

## Reviewer questions (R)

**R1. P7 cannot fail V5** (`reviewer-guide.md:37`; `spec.md:150-151`). V5 passes `--model-version 7 --season v1`
explicitly, so changing the default to 8 leaves V5 green. "Equal to `main`'s tool" has no source, because the test
cannot run `main`.
*Default:* the pre-flight runs `main`'s `tools/kobo_replay_study.py --days 8` and records each case's `avoided_l`
exact. V5 calls the tool's `main([...])` in-process with **no** model or season flag and compares to those literals. It
also asserts that the header reads `model=mini-grid/7 season=v1`, so P7 fails twice.

**R2. Places in §4.2 that would keep a design value or a dawn gate beside the restated figures** (`spec.md:110-124`;
`domain-and-decision-models.md:399-415`; D-0K4.9, D-0K4.11). §2.5 does not cover these, and the change list assigns
some of them to 0K4d (items 9, 14):
- :407 "of the 330 candidate L (120 L of candidate running remain needed)", "lowest charge 30% ≥ warranty floor 10%"
  and "wear costed 12.00";
- :406 the reserve-25 row's value cell "REJECTED";
- :399 `dawn_ok(π) ... → bound`;
- :410 "the worst replayed day at least 2 points above the dawn limit" (a dawn gate in the selection);
- :415 "Sensitivity / break-even" (2,286.00, 2,166.00, 15.6 L/month, 1.70/kWh) and "Minimum sample: 61 days for the
  dawn bound".

*Default:* 330 and 120 read "Not available yet (Kobo's October telemetry through `dispatch-3.3`)". Lowest charge
becomes the study's `min_soc_pct`, SIMULATED, with the floor as information. Wear and the reserve-25 value read "Not
available yet (`6c` values it)". `dawn_ok` is restated as information. :410's rule reads "admitted by
`runs/admission.py`; `6c` chooses among the admitted". The sensitivities read "Not available yet (`6c`)", and the
minimum sample is restated as the dawn information's sample.

**R3. The 61-day figures carry no identity a later run can be checked against** (`spec.md:153-155, 168-173`;
D-0K4.20). They reach the option card, but `study.json` records no commit, no site-run digest and no season digest.
A later edit would move them under the same label.
*Default:* each `study.json` header records `git rev-parse HEAD`, the model id and version, the season, the v2
inputs digest (0K4c R1), and `trajectory_digest` of each site run (0K4a's `host/tests/trajectory_digest.py`). The
packet prints them, and the reviewer's own reproduction (guide check 3) quotes the same digests.

**R4. Values that may be missing must not show as 0 or blank.** These are the reconciliation table and the
non-calibrated path (`spec.md:170-173`). The v7 studies have no admission and none of the four new measures. A
NOT_CALIBRATED or SAMPLE_TOO_SHORT result has `baseline=None` and `cases=()`, so `admit` never runs. "The cause:
dispatch, fuel curve, taper or season" cannot be told apart from two runs that change the model and the season
together.
*Default:* v7 cells with no measure read "not computed on v7". A non-calibrated study prints `admission not
available (<status>)`, and the MG-T cells read "Not available yet (replay not calibrated)". The cause column reads
"model v7→v8 and season v1→v2 together (not separated)" unless a separating run exists. No extra run is added.

**R5. Guide check 5's grep cannot be decided as written** (`reviewer-guide.md:20-21`). "20" and "150" match declared
facts and dates: Mto's battery is 150 kWh (`host/tests/mto.py:28, 73`), the tank is 20,000 L, and every date holds
"2026".
*Default:* the check is the regex `\b(210|2,?916|68)\b` together with `\b(20|150) ?L\b`, run over the two tools,
`admission.py` and the `replay_study.py` diff. Each hit is listed with its reason, so a declared fact such as 150 kWh
is shown as not a design value.

**R6. SC-1 evidence for the backend files** (D-0K4.19; `tools/checks/statement_catalogue.py:985-996`).
`admission.py` sits inside the scanned package. `replay_study.py` already carries 15 baselined fingerprints
(`StudyRefused` details, `tools/checks/statement-handbuilt-baseline.json`). A new `StudyRefused` or other custom
exception with an English detail would be `HAND_BUILT_NEW`. A built-in `ValueError` or `TypeError` is the negative
class (N2).
*Default:* `admission.py` and the additions raise only built-in exceptions and hold codes. The packet records the
statement-catalogue check's output (no `HAND_BUILT_NEW`), and the diff leaves both baseline files untouched.

## Implementer questions (I)

**I1. The pre-flight cannot run where §0 places it, and the Mto tool has no `--time-one`** (`spec.md:22-24`;
`tools/mto_headroom_study.py:194-199`). v8, season v2 and the §2.4 flags do not exist on `main`.
*Default:* the pre-flight print moves to the start of commit 2, after `main` is merged. Commit 2 gives the Mto tool
`--time-one` in D-0K2.24's form (site run plus one baseline replay, exit 0). Mto's cap is
`max(25, ceil(2 x (site + 6 x replay) / 60))` minutes. Commit 1 has no pre-flight beyond B1-B13 green on `main`.

**I2. Two start rules** (D-0K4.16 says "STOPPED/FAILED to STARTING/RUNNING ... (0K2's start rule, D-0K2.23)").
`start_steps` (`replay_study.py:369-376`) counts only `previous == "STOPPED"`, and 0K2's B6 asserts "a FAILED then
RUNNING gives 0".
*Default:* `max_starts_in_a_day` reuses `start_steps(states, start.generator_state)` unchanged, grouped by the local
date of each step's start. "/FAILED" in D-0K4.16 is a slip to correct in the rulings.

**I3. AD7 needs a public entry point, and P4 needs two reserves** (`spec.md:84-87, 137-139`; guide P4).
§2.2 computes the measures inside the private `_outcome` (`:466`), which needs `ObservedSeries`, the frame and the
baseline. `ReplayStep` carries no per-step reserve (`contracts/assetops_contracts/forward_replay.py:123-130`), so
"its own reserve in effect" can only be the projection's `reserve_soc_pct`.
*Default:* add a public pure helper
`admission_measures(p, local_times, first_previous) -> (reserve_breach_steps, max_starts_in_a_day, full_charge_dates, longest)` to
`replay_study.py` and its `__all__`. It reads `p.reserve_soc_pct`, and `_outcome` calls it. AD7's stubs give the
baseline reserve 30 and the case 25, with one step at SOC 27. The case counts 0 and the baseline 1, so P4 fails.

**I4. Which are "the five" assumption strings, and where are they read from?** (`spec.md:102-104, 149`; D-0K4.7
says "the five properties of D-0K4.4 to D-0K4.6", but those name three new values plus SFC.) The run freezes only
`model_needs` (`runs/models.py:809-839`): the authored value and unit, with no basis. Basis rows are not needs and are
never frozen, and the run holds no Foundation document (`FrozenSiteBinding`, `:339-355`). Mto's 2.4 L/h is said to be
"the same generic rule as Kobo's (0.08 L/h per kW)", but Kobo's 3.3 is not 0.08 x 40 = 3.2
(`tools/demo_combined_kobo.py:144`, "about 0.08"). Scaled from Kobo's own value it would be 3.3 x 30 / 40 = 2.475,
or 2.5. No ruling names Mto's value.
*Default:* four strings, in this order:
- `generator-no-load-fuel-rate 3.3 L/h (GENERIC_DEFAULT)`
- `generator-minimum-load 30 % (GENERIC_DEFAULT)`
- `battery-charge-taper-start 95 % (GENERIC_DEFAULT)`
- `specific-fuel-consumption 0.3 L/kWh (TEMPLATE)`

The SFC slot carries the property's `source` when it has no basis row. Values come from the frozen `model_needs`
(authored form) and bases from the site record the tool rendered (`host/tests/kobo.py:66`). Each tool has one helper,
which V4 calls. Mto's value is 2.4 L/h, logged as an Architect-declared assumed value. The Mto JSON header carries
`assumptions`, and `HeadroomResult` does not change.

**I5. How the flags combine, and the v7-only code they leave** (`spec.md:93-97, 101-108`). Three gaps:
- What does `--model-version 8 --season v1` (or `7` with `v2`) run?
- `dawn_class` reads `overcast_v1` (`tools/kobo_replay_study.py:70-73`), which is wrong on v2.
- `mto_base_run` and `mto_season` (`host/tests/mto.py:61-66`) take no `version`, `site` or `season`.

*Default:*
- A mixed pair exits 2 with `STUDY_GRID_INVALID`-style text on stderr. A v8-on-v1 figure would be a second figure for
  the quantity.
- v8 with v2 uses `season_site_v2` (Kobo) and `mto_site_v2`, the reduced Mto run included.
- `dawn_class` takes the season's overcast function.
- `mto_base_run(days, *, inverter_limit_kw, version=7, site=mto_site)` and `mto_season(run, days, season="v1")`.
- Every printed line and header carries `model=` and `season=`. On v7 and v1 that adds the two labels and changes no
  figure.

**I6. The §2.5 anchors and figure definitions** (`spec.md:110-121`). The anchors are off by two lines on `main`:
- the table rows are :406-407 (not 403-404);
- "Design values as calibration-spike inputs" is :412 (not 410);
- the sensitivities and the vectors share :415.

The figure definitions are not fixed. "The mean of September and October scaled to 30 days" could mean
(Sep + Oct) x 30 / 61 or the mean of per-month rates, and the two differ. "Starts", the case behind each row, and
the Mto figures are not named.
*Default:* anchor by text, not by line. The defaults for each figure:
- **A month** is the tool's `scaled_to_30_days` (window x 30 / 61, `tools/kobo_replay_study.py:115-120`).
- **Starts** is `added_starts` scaled the same way, with `max_starts_in_a_day` in the admission cell.
- **Stop 70** is `stop-70-reserve-30`. **Reserve 25** is `stop-90-reserve-25` (the template's stop is 90).
- **Dawn margin** is `worst - 35`.
- **Huller** is `mto-huller` `extra_fuel_l` x 30 / 61.
- **Reduced inverter** is `extra_fuel_l_per_day`.

**Answered** (Architect, 2026-11-21): every question by a D-ID or its default, in the table "Handshake answers (rev 2 of 0K4c and 0K4d)" of `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.26 to D-0K4.30); the spec is rev 2.
