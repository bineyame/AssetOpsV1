# TEL-06 review (TEL-06a / TEL-06b)

Reviewer: fresh Claude reviewer (did not author the slice). Branch `task/TEL-06-csv-collector` at `f408a8f6`, diffed against main `caf22405`.
Authority: build spec TEL-06 body plus section M (Q1-Q9), `.agent/TEL-06-questions.md`, `.agent/telemetry-rulings-2026-10-27.md`, owner Q7 = (c).

## Verdict: ACCEPT

There are no High or Medium findings. The one Low below is optional and can be fixed on the branch or left as it is.

## Verified

- **Eight refusal codes, each before any gateway call.** `CSV_CODES` matches the spec tuple exactly (`field/assetops_field/export_csv.py:43-44`). `CsvRefused` rejects an unknown code (`:55-61`). `collect` runs the whole `_reports` validation before `publisher.admit` (`:177-179`), and `reports()` makes no IPC call. Every focused refusal goes through `_refused`, which asserts `link.calls == []` and that the profile SHA is in both the attribute and the message (`field/tests/test_field_export_csv.py:79-86`). Each code has a named test, and that is enforced at `:256-261`. In 06a step 3 the outbox, admission and hold counts are unchanged after the renamed-header and no-`Z` refusals.
- **Profile signals and units.** `field/profiles/generic-interval-csv-illustrative-1.json` matches the M Q1 table row for row: row IDs, device and signal IDs, roles, columns, point and sign text, `AS_EXPORTED`, `kW`, `INTERVAL_SIGNAL`, 900/900, `0.001`, and the confirmed `source_document` wording. The top-level keys are as ruled. There is no `battery_soc` or `generator_power` row. The freshness test checks spans, cadences, class and unit against the publication profile, and roles against the snapshot bindings.
- **Fixture.** It has 49 rows, 196 cells and 4 blank cells, all in the 03:00Z row. The header is exactly as ruled, with LF line ends and no BOM. I checked it **independently** with `Decimal` `ROUND_HALF_EVEN` at 0.001 from the `-1` JSONL, without the project helpers: all 196 cells match, and the only non-terminating value is `14586/361`, which becomes `40.404`. The CSV SHA-256 I computed is `8c886ba8…e9e9`, the same as the manifest. The manifest's key set is exactly the M Q2 (e) set.
- **Generator determinism and freshness.** The generator reads the checked-in JSONL after checking its SHA against the manifest. It uses no clock and no random source, and the CSV has a fixed column order and sorted instants. It raises on `DROPPED` or `SUPPRESSED_BY_GAP` and on a missing signal. The freshness test regenerates into `tmp_path` and compares the bytes of both files, so it is a real test and not a self-comparison.
- **Real path, no injection.** 06a goes from the in-process `CsvCollector`, through a real `GatewayLink` to the `tel4.Bench` gateway process, to FakeCentral over TLS. 06b uses the real gateway process, `_central` with real ingestion, and a fresh Postgres database. Nothing is written straight into the ledger. Envelopes are read back read-only from the gateway SQLite.
- **Provenance UNKNOWN and no consequence.** My 06b run showed `state: UNKNOWN`, `["NO_POSITIVE_BINDING"]`, and 0 rows in every consequence table.
- **No vendor naming.** A case-insensitive grep of the TEL-06 files (collector, field test, profile, fixture directory, 06a) for victron, vrm, sma, huawei, solaredge, monta, monnit, cerbo, gx, aggsoft, fronius, schneider, sunny and venus found nothing. The only hits for "modbus" are module names. Modbus is a protocol, not a vendor, and the imports are allowed by Q-T66.
- **Guards not loosened.** The diff does not touch `tools/`, `.ai/` or any `.ps1` file.
- **The Q7 return value.** `collect` returns exactly `{profile_sha256, file_sha256, session_ref, report_count, admissions, sealed}`. `file_sha256` is computed over the raw bytes that were validated (`export_csv.py:177-182`). The field test asserts the exact key set, the SHA and `session_ref` (`test_field_export_csv.py:150-153`).
- **Q5, Q6, Q8, Q9.** `collect` holds no session state, and the test asserts the operations `["admit","seal","release_run"]`. A wrong cell count, a blank line inside the file, or a trailing blank line gives `INVALID_VALUE` at `rows[i]`. `0.50` is normalised to `0.5`. `report_key` comes from `build_report`.

## Findings

| Sev | File:line | Finding | Fix |
|---|---|---|---|
| Low | `field/tests/test_field_export_csv.py:3-5` | The module docstring still says the profile's "content is an open question, see `.agent/TEL-06-questions.md` Q1". M Q1 has since ruled it. Only the comment is stale. | Reword to say the test profile is synthetic and independent of the ruled profile. |

There are no acceptance gaps.

## Checks I ran (at `f408a8f6`)

I used the Lane T PYTHONPATH with `AssetOpsV1-tel6`, with the plan2 venv as the interpreter. The import check resolved `AssetOpsV1-tel6\gateway` and `AssetOpsV1-tel6\field`.

- `pytest field/tests -q`: **197 passed** in 13.76 s.
- `pytest host/tests/test_field_observation_fixtures.py -q`: **3 passed** in 4.43 s.
- `pytest host/tests/test_field_export_csv_proof.py -q` (06a): **1 passed** in 4.94 s.
- 06b `-k test_generic_csv_lands_as_accepted_evidence`, run once:
  - I created a fresh `assetops_tel6rev_test` in `assetopsv1-postgres-1` (127.0.0.1:55432) with `DROP ... IF EXISTS WITH (FORCE)` followed by `CREATE`, and then `fresh_database()` reset it in place.
  - Result: **1 passed, 2 deselected in 10.82 s**, 12.2 s of wall time.
  - It produced 196 accepted rows, `{"feeder_demand": 147, "pv_power": 49}`, and 4 batches (`6463ce13…`, `661c9a8f…`, `88eb219c…`, `d7d52e06…`).
  - I dropped the database afterwards and confirmed that no `tel6` database remains. No other database was touched.
- I ran both guards directly with `ASSETOPS_GUARD_PYTHON` set and no policy override: "Architecture check passed." (exit 0) and "Agent workflow check passed." (exit 0).
- I ran no full suite and no frontend checks, because the slice touches no frontend.

## Not verified

- I did not repeat the packet's non-vacuous proofs (the reverted mutations). I checked by reading that the BOM, duplicate and unit-header tests would fail if the guarded behaviour were removed.
- I ran 06b once, not twice. The second consecutive green is the implementer's evidence: two runs at `5c6bb33e`, and the later commits change only the packet.

## Residual risk

- This is the packet's own risk: the 06a/06b oracle encodes the M Q2 rounding rule, so it shares the ruling's assumptions. My independent `Decimal` check above confirms the fixture against the JSONL, but not against the ruling.
- The span check is measured from the Unix epoch rather than from midnight. The two are equivalent only because 900 divides 86400. A future profile with a span that does not divide a day would need the rule restated. That is outside TEL-06 scope.
