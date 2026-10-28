# TEL-06 builder questions (Lane T, 2026-10-28)

Branch `task/TEL-06-csv-collector`, worktree `AssetOpsV1-tel6`. To: Architect (Claude).
Owner rule: no isolated design decisions. Owner Q7 = (c): no vendor naming; the format is illustrative.

What I built: `field/assetops_field/export_csv.py` and `field/tests/test_field_export_csv.py` (41 passed), from TEL-06 and 0.6 alone.
I stopped on the items below. The items marked **blocking** decide the content of the checked-in profile, the fixture, the 06a proof and the 06b Postgres test, so none of those files exists yet.

## Blocking

**Q1. Content of `field/profiles/generic-interval-csv-illustrative-1.json`.** The spec names the file and the 0.6 `EXPORT_CSV` rules, but not its rows. Its rows need `row_id`, `device_id`/`signal_id`, `role`, `source_unit`, the `quantity` texts, `span_seconds`/`cadence_seconds`, `output_resolution`, `csv.column` and a vendor-free `source_document`.
- The `-1` JSONL (`kobo-public-observations-v1`) has 5 interval signals: `pv-inverter-controller/ac-power`, `battery-pcs-controller/ac-power`, and `clinic-meter`, `mill-meter` and `residential-meter` `/active-power`. It also has 1 state signal, `battery-pcs-controller/state-of-charge`. All of them have 49 samples at 15 min.
- The plan card (§B1 "Essential measurements") asks for `pv_power`, `feeder_demand`, `generator_power` and `battery_soc` as state. But 0.6 says `EXPORT_CSV` rows are `INTERVAL_SIGNAL` only, so SoC cannot be a CSV row. The `-1` JSONL also has no generator signal and no single "feeder" signal.
- Please rule on: (a) which signals are rows, and the source JSONL (`-1` or `-2`); (b) the column names; (c) `output_resolution` per row; (d) the `profile_id`/`profile_version`; (e) the `source_document` and `quantity` texts. Is `"assetops-generic-interval-csv/1, an illustrative format defined by AssetOps; not a vendor format"` the right wording?

**Q2. Fixture `contract-fixtures/telemetry/generic-interval-csv-v1/{kobo-window.csv,manifest.json}`.**
- (a) The window. Is it the JSONL's full `03:00Z-15:00Z`?
- (b) The `-1` JSONL values are exact rationals from `simulator-lab-publication:3`, for example `1035/19`. A CSV cell must be a finite decimal and an exact multiple of `output_resolution`. Which quantization rule applies: half-even at `output_resolution` via `quantize_half_even`, as TEL-T1-Q7 rules for the emulator? Or another rule?
- (c) What do non-`REPORTED` outcomes write? `NO_PRECEDING_INTERVAL` at 03:00Z is an example. Is that a blank cell (`UNAVAILABLE`/`NO_MEASUREMENT`) or an omitted row? Omitting the row would leave the 03:00Z interval unpublished.
- (d) Where does the generator live, and is a freshness test required? The card asks for the "generating command" in the manifest. The obvious home is a new function in `host/tests/field_observation_fixtures.py` plus a case in `test_field_observation_fixtures.py`, but neither file is in the TEL-06 Files list.
- (e) What is the manifest shape? Is it the 0.6 JSONL manifest keys, plus the source JSONL SHA-256 and the CSV SHA-256?

**Q3. TEL-06a proof (`host/tests/test_field_export_csv_proof.py`).**
- Should it reuse the TEL-04 harness from `test_field_modbus_tcp_proof.py`: the snapshot, `expect_identity_from_snapshot`, `GatewayProcess` and `FakeCentral`?
- "Identical message IDs and no new sequence": I read this as the second `collect` of the same file returning `ALREADY_ADMITTED` with the same `message_id` per report. The gateway's queue sequence should not advance, which I would check through `diagnostics`. Is that right?
- Does the second `collect` use the same session ref or a new one?
- Is the plan card's extra fault test, "a row after the gateway's now gives `SOURCE_TIME_IN_FUTURE`", in scope? The spec's gate list omits it.
- 0.3 classes this file as heavy, so it waits for a queue slot either way.

**Q4. TEL-06b (the third test in `test_field_modbus_tcp_acceptance_postgres.py`).** It is blocked on Q1 and Q2. The card says "with its own Site". Does that mean the TEL-05 `KOBO-001` setup on its own fresh database, or a different Site? It is written to be run only when the coordinator sends a go.

## Non-blocking (built provisionally; please confirm or correct)

**Q5. `release_previous` "on start likewise".** `CsvCollector(profile, publisher)` has no state directory and no previous session ref. The module map lists no CLI, but the plan card says "a CLI over one file". I have not implemented `release_previous` for CSV. Options:
- (a) a CLI with `--state-dir` and `session.json`, as the poller does;
- (b) a `previous_ref` argument to `collect`;
- (c) the caller calls `publisher.release_previous` itself.

**Q6. A data row whose cell count differs from the header.** No code is assigned to this case. Provisionally it raises `INVALID_VALUE` at `rows[i]` (`export_csv.py`, marked in the code). A blank line in the middle of a file falls into the same case. Should it be `INVALID_VALUE` or `HEADER_MISMATCH`?

**Q7. The `collect()` return.** The keys are not defined. Provisionally it returns `{"profile_sha256", "report_count", "admissions", "sealed"}`, where `sealed` is the `seal_and_release()` dict. The card's "raw file SHA-256 is recorded" is not in the spec. Should the return add `file_sha256`?

**Q8. The value text.** A cell goes through `Fraction(cell)` and the existing `build_report` → `exact_decimal_text`, so `0.50` reaches the gateway as `0.5`. The alternative is to send the cell text verbatim. Which is right?

**Q9. The `report_key`.** The spec's `report_key` (profile id, version, device, signal, source time) is used. The card's "format, Site, column and interval start" key is not used, and I read the spec as overriding it. The same file therefore deduplicates. An *overlapping* file with the same profile also deduplicates per interval end.
