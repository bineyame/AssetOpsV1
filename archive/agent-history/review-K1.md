# Review K1: the Kisiwa Site (DIESEL-1-R3c §9c.1)

- Reviewer: Claude (Opus), fresh context, independent first review. I did not author K1.
- Branch `task/DIESEL-K1-kisiwa-site` at `18b5bbcdc`, diff `f9d27116b...HEAD`. `git merge-tree` against current main `5d8ac9ee3` (K2 merged since) is clean.
- Read: the §9c.1 card, §9c.3, §9a, §9.2, the three owner decision files, the packet, and the full diff.

## Verdict: FIX

One Medium: K1's vocabulary edit breaks two existing tests that pin the full vocabulary tables. The card's localised test list does not name them, so the builder did not run them. The fix is a test-pin update, the same kind as the catalog pin K1 already made. Everything else matches the card, and parity is real (details below).

## Findings

### M1 (Medium, acceptance gap): two existing vocabulary pin tests fail on the branch

- **Where:** `backend/assetops_backend/sites/models.py:285-291, 316, 345-346` add the two keys. The tests that break are:
  - `backend/tests/test_w402_roles_properties.py:91` `TestTypedProperties::test_definitions_and_carriers`. It asserts `MINIGRID_PROPERTY_CARRIERS ==` an exact dict, and it asserts the units and kinds of those keys (`:92-105`).
  - `backend/tests/test_w205a_ev_vocabulary.py:118` `TestVocabulary::test_nine_ev_properties_with_exact_unit_and_carrier`. It asserts `STATE_PROPERTY_VALUES ==` an exact dict (`:131-137`).
- **Observed:** `pytest tests/test_w402_roles_properties.py tests/test_w205a_ev_vocabulary.py` gave 2 failed, 109 passed. Pytest's diff shows that the only extra items are `fuel-level-sensor-accuracy` and `fuel-level-sensor-accuracy-basis`. Neither test file is in the K1 diff, so both passed on `f9d27116b`. A1 updated these same pins when it added the no-load keys.
- **Why it matters:** these are regressions. The end-game E2 full suite will report them, and they will look like a broken main at that point, far from their cause.
- **Fix:** add the K1 entries to both exact-dict pins. That means `"fuel-level-sensor-accuracy": "FUEL_TANK"` and `"fuel-level-sensor-accuracy-basis": "FUEL_TANK"` in the carriers pin, the `("L","PHYSICAL")` and `("state","PHYSICAL")` units in the w402 pin, and the basis state set in the w205a pin.
  - This edits test assertions over the shared table. It does not change any EV template, fixture, config, digest or served byte, so in my reading it is not the "EV byte change" stop. The Architect should confirm that, because `test_w205a_ev_vocabulary.py` is an EV-named file outside the card's twelve.
  - After the fix, add both files to the K1 localised list.
- I ran a wider adjacent no-DB set to look for other pins. It covered `test_component_properties`, `test_site_parsing`, `test_site_templates_api`, `test_simulator_lab_gate`, `test_sites_api`, all non-Postgres `test_w402_*`, `test_s3_demo_configuration` and `test_md0*`. Result: 388 passed, 4 skipped, and the only failure is the w402 one above. I found no other pin.

### L1 (Low): the F0r reference mixes line endings; the proposed `.gitattributes` rule does not make it checkout-independent

Hashes I verified myself:

| File | Committed blob (`git show HEAD:`) | Working copy (CRLF) | Reference in `probe-result.json` |
|---|---|---|---|
| `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml` | `77777c82…b634` | `a9391175…911d` | `actions_sha256` = `77777c82…b634` (LF) |
| `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json` | `68a54ef8…1c33` | `6a4de5d7…55c4` | `registered_path.bindings_sha256` = `68a54ef8…1c33` (LF) |
| `.agent/DIESEL-D0/kisiwa-diesel-hybrid-60kw.draft.yaml` | `261b7e64…414b` | `d9a4107a…aa11` | `d0_template_sha256` = `d9a4107a…aa11` (**CRLF**) |

`tools/probe_kisiwa_fuel.py:698-708` hashes raw `read_bytes()`. The packet says the builder's two-file LF read reproduces F0r's values, and that is true. But the reference itself is mixed:
- two of its input hashes were taken on LF bytes, probably because F0r wrote those files fresh;
- the third (`d0_template_sha256`, which is compared because it is not a removed key) was taken on CRLF bytes.

**Is the normalisation fair?** Yes, and I accept it. It hides no parity difference, because nothing but those two hash strings depends on the files' line endings:
- the probe parses both files with `read_text` + `yaml.safe_load` and `json.loads` (`:150`, `:266`), which ignore line endings;
- the per-action `content_sha256` is taken over canonical JSON;
- the monkeypatch at `host/tests/test_k1_registered_kisiwa.py:97-101` is scoped to exactly `probe.ACTIONS` and `probe.BINDINGS`, and it restores their committed blob bytes, so it makes up no value.

It does not fall under the card's stop. The stop protects "every litre, band, state, gap, dip, count and gate value", and those all compared equal with no normalisation needed.

**The residual problem.** The test passes only on a checkout where the D0 draft is CRLF and the F0 files are forced to LF:
- **On an LF checkout** (a Linux clone, or `core.autocrlf=false`), K1's parity test fails on `assumptions.d0_template_sha256` (`261b…` against `d9a4…`).
- **With only the packet's suggested rule** (`.agent/DIESEL-F0/* eol=lf`), Windows becomes "current". An LF checkout still fails on the D0 hash.
- **With `eol=lf` on `.agent/DIESEL-D0/*` as well**, parity breaks here too.

So the packet's claim that the rule "makes F8's `--check` checkout-independent" is incorrect.

**My recommendation for the Architect.** Not in K1: the card forbids editing the probe and `probe-result.json`, and K1 cannot close this alone.

Make a small evidence-hygiene fix with three parts:
1. The probe hashes LF-normalised bytes for all three inputs.
2. Re-pin only `d0_template_sha256` to `261b7e642aa7e2f3a2d5175868cf7b2a406b2c89154b1229ca78424e65a6414b`, and record that as an F0 evidence correction (like R3b's F8 fix). No measured value moves.
3. Add `text eol=lf` for `.agent/DIESEL-F0/*` and `.agent/DIESEL-D0/*`.

After that, K1's monkeypatch becomes unnecessary and can be dropped.

**Placement:** fold it into K3. K3 reproduces F0r's per-night bands, so it already touches this evidence. Or make it a stand-alone 0.1 task before K7. It must land before the probe `--check` or K1 parity is run anywhere other than this Windows checkout. Until then, the card's "`probe_kisiwa_fuel.py --check` must still print 'probe result current'" item cannot pass on this checkout, on main as well.

### L2 (Low, preference): the L2 site test asserts less than the packet reports

`backend/tests/test_k1_kisiwa_site_postgres.py:126-127` asserts `fuel[0] > 0` and that some analytic id contains "dispatch". The run itself printed 94 records spanning 12:00Z to 12:00Z, and `dispatch` CANDIDATE_AVOIDABLE ×2 and COMPLETE ×2.

A regression that lost most of the day's tank readings would still pass. Two examples: a dropout or binding cut that leaves only a few accepted `fuel_level` rows, or a cadence change.

The card only asks that the readings "exist", so this is not an acceptance gap. Pinning `fuel == (94, 12:00Z, 12:00Z)` and `analytic_id == "dispatch"` would make the test catch it. Do it if the M1 round is open anyway.

### L3 (Low, information, routed correctly): template signal names say "clinic" and "mill"

`config/site-templates/kisiwa-diesel-hybrid-60kw.yaml:312` "Active power to the clinic" and `:320` "Active power to the mill" are Site data that can reach Foundation or readings screens. The card requires these bytes to equal the D0 draft, and its client-wording list did not anticipate them. So the builder was right not to change them and to route them to K8, which would need a template v2 and a new fingerprint pin.

I confirmed that no served board string in the L2 run contains clinic, mill, Kobo, theft, stolen, siphon or pilfer (case-insensitive grep over every printed row).

## Card checks (what I verified, not the packet's word)

- **Template:** the header equals the card literal. The bytes from `template_id:` to EOF are identical to the D0 draft (`diff` on `git show` blobs: equal). The fingerprint pin `013c3bbc…ca07c` passes, and the catalog lists four templates with the comment line.
- **Bindings:** `cmp` of the committed blobs against `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json` shows them equal: 12 rows, roles-2, `declare_signals: []`.
- **Roles-4 config:** it equals the card literal.
- **Vocabulary:** it is as the card specifies: two definitions, the basis set with SITE_CALIBRATION, FUEL_TANK carriers and strictly positive. `minigrid_foundation.py` is untouched.
- **Registration order and clocks:** import at `import_at`, convert at `install_at`, then as known at +30 min: supply uses and the no-load rate at +25, roles-4 at +27. `register` re-enables the Site's gateway and source (`disabled_at = NULL`, Kobo's statement) and publishes diesel v1 only, at +1 h.
- **Runs:** `RUN_PROFILE` and `KisiwaRegistered` pin product `MINI_GRID_V7_MODEL` and registered-kobo-publication v5. The probe's `build()` uses `reg.draft` and `reg.sim` (`probe_kisiwa_fuel.py:393`, `:400`, `:443`), so the physics ran on product v7. `d-verification-window-v3.json` still pins v6.
- **Product edits:** `models.py` is the only product edit. The changed files are the card's twelve plus the packet.
- **Kobo, Cold and EV:** no Kobo, Cold or EV template, fixture, config, conversion or scenario byte is in the diff. `test_scenario_execution_contract.py` and `test_execution_contract_alignment.py` pass. One side effect, not a stop: the new data files and `models.py` move `mechanism_dataset.input_fingerprint`. That is a test-cache key (`backend/tests/mechanism_dataset.py:1054`), not a product digest, so the next mechanism-template test run rebuilds its template DB once.
- **Lab:** the Lab template listing (`simulator_lab_api.py:2490`) will now list a fourth template. The packet's "no client screen changes" holds for the demo DB, but the Lab picker gains Kisiwa. This is inherent to card file 1 and not a finding.
- **MD-KIS-K1-1:** a data-only deviation. K1 ships no UI, so no screen can contradict it before K7 and K8.

## Do the tests fail if the code is broken?

- **Parity:** I reproduced the builder's mutation without editing any repo file. A scratch script set `kis.SITE_SOURCE` to a copy of the import record with stop-soc 80, re-registered on `assetops_k1_test` and ran the same comparison. It found **850 differences**, the first being `dips[0].dip_l` 683 against 706. So the probe really drafts from the Postgres-registered Site, and the comparison is not vacuous.
- **One vacuous field:** `runs[*].scenario_sha256` is `null` for all ten runs in both F0r's reference and the result, so the card's "scenario sha" element compares nothing. That is pre-existing in F0r. Physics equality is still covered by the exact-fraction end states, nights, dips, the 935 fuel-level reports and the gates.
- **L0:** the vocabulary tests exercise each of the following, and each would fail if its rule were removed:
  - the carrier (generator refused);
  - strict positivity (0 L refused);
  - the unit (L/h refused);
  - the state set (SITE_TEST, the lower-case value and the empty string refused).
  - `register_in` in memory asserts 15 roles-4 bindings and each fact's value.

## Checks run (by me, on `18b5bbcdc`)

- **Imports:** python from `AssetOpsV1-plan2\.venv`, PYTHONPATH absolute under the k1 worktree. `assetops_backend`, `demo_combined_kisiwa`, `kisiwa`, `probe_kisiwa_fuel`, `assetops_simulator` and `execution_adapter` all resolve into `AssetOpsV1-k1`.
- **Card no-DB list:** `test_k1_kisiwa_fixtures`, fingerprints, catalog, `test_s1_bindings`, `test_s2_registered_basis`, `test_fuel_cost_v2`, `test_scenario_execution_contract`, `test_execution_contract_alignment` and `host/tests/test_mini_grid_v7.py`: **249 passed** (32.7 s).
- **Adjacent no-DB:** 2 failed (M1), 109 passed for the two pin files. In the wider set, 388 passed, 4 skipped and 1 failed (the same w402 failure).
- **L2 parity** (`assetops_k1_test`; free RAM 4.55 GB): **1 passed** (41 s). Removed-key values are as the packet says. Foundation and binding-set versions are 9 against 1, and the snapshot differs (`d358aba3…` this run against `38a121ba…`), as expected. The report text differs only in `report_key`, at 699.5 L.
- **L2 site:** **3 passed** (433 s).
  - Price: UNPRICED/NO_PRICE, then PRICED 1.25 USD.
  - Published: 1828 batches and 3659 envelopes.
  - `fuel_level`: 94 records, from 2026-10-01T12:00Z to 2026-10-02T12:00Z.
  - Assessments: dispatch CANDIDATE_AVOIDABLE ×2 and COMPLETE ×2. The worker asserts DONE inside `LabRunner.step`.
  - Board: 200, PARTIAL.
  - The Foundation facts (10 L GENERIC_DEFAULT, 4.9 L/h GENERIC_DEFAULT, supply uses, roles-4 with 15 bindings) are asserted by the test and passed.
- **Mutation:** scratch parity mutation with stop 80 gave 850 differences (above).
- **Guards:** `tools\check-agent-workflow.ps1` passed. `tools\check-architecture.ps1` failed on its first run only because the worktree has no `.venv` (Rule 8 and chain-structure "no Python interpreter"). With `ASSETOPS_GUARD_PYTHON` set to the plan2 venv it **passed**. Both were run directly, with no `-ExecutionPolicy`.
- **Not run:** `check-all.ps1`, `check-navigation-truthfulness.ps1`, and the probe `--check` commands. For those I rely on the packet's report. The probe `--check` is analysed under L1.
- **Not run (out of scope or forbidden):** the frontend suite and build (no frontend change), the full suite, a prepare, `test_demo_combined_postgres`. `layout-evidence` does not apply, since there is no layout change.

## Residual risk not in the packet

- The F0r reference only verifies on a CRLF checkout of D0 (L1). This matters as soon as anything runs on Linux or on a fresh LF clone.
- The parity check of scenario identity is vacuous (`scenario_sha256` is null throughout).
- The first mechanism-dataset test after merge rebuilds its cached template, which costs time but is correct.
