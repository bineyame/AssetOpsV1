# TEL-06 review packet (TEL-06a / TEL-06b): partial, stopped on questions

Status: in_review (partial: collector core only; profile, fixture, 06a and 06b are blocked on `.agent/TEL-06-questions.md`)

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel6\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel6\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel6\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel6\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel6\host;C:\Users\assef\Bineyame\AssetOpsV1-tel6\field;C:\Users\assef\Bineyame\AssetOpsV1-tel6"
```
Interpreter: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`. The import check names `AssetOpsV1-tel6\gateway` and `AssetOpsV1-tel6\field`.

Branch `task/TEL-06-csv-collector`, from main `caf22405` (plus `205d3062`, TEL-05b Lows). Build commit `b43283ca`.

## Task
TEL-06 in `.agent/build-spec-telemetry-2026-10-27.md`: the illustrative generic interval CSV collector `assetops-generic-interval-csv/1` (owner Q7 = (c), no vendor naming).

## Outcome delivered
- `field/assetops_field/export_csv.py` contains `CSV_CODES` (the eight codes), `CsvRefused(code, field, detail, profile_sha256)` and `CsvCollector(profile, publisher)`.
  - `.reports(path)` validates the whole file with no IPC and raises `CsvRefused`.
  - `.collect(path)` runs `reports()`, then `admit`, then `seal_and_release`.
- The grammar is exactly as TEL-06 states it:
  - BOM or non-UTF-8 → `ENCODING`; no data rows → `EMPTY_FILE`.
  - The header is `timestamp_utc` plus `<column> [<unit>]` in any order. The unit passes through verbatim to the report `unit`.
  - Timestamp format → `INVALID_TIMING`, span grid → `SPAN_MISMATCH`, repeat → `DUPLICATE_ROW`, order → `UNSORTED_ROWS`.
  - Each cell is matched against `-?[0-9]+(\.[0-9]+)?` and must be an exact multiple of `output_resolution` → `INVALID_VALUE`. A blank cell gives `UNAVAILABLE`/`NO_MEASUREMENT`.
  - Each row is one interval `[t - span, t)`. Reports are built through the existing `build_report`, with only `unit` replaced.
- Imports: stdlib, `assetops_contracts`, and `assetops_field` only (D4).
- **Not delivered (blocked):**
  - `field/profiles/generic-interval-csv-illustrative-1.json` (Q1);
  - `contract-fixtures/telemetry/generic-interval-csv-v1/*` and its generator (Q2);
  - `host/tests/test_field_export_csv_proof.py`, TEL-06a (Q3);
  - the TEL-06b third Postgres test (Q4);
  - `release_previous` on start (Q5).

## Files materially changed
- `field/assetops_field/export_csv.py` (new)
- `field/tests/test_field_export_csv.py` (new, 41 tests; it uses a profile built in the test, not the checked-in profile)
- `.agent/TEL-06-questions.md` (new, Q1-Q9)

## Acceptance criteria (TEL-06 gates)
| Gate | Status |
|---|---|
| Same file twice → identical message IDs, no new sequence | Partial. The focused test shows byte-identical admit bodies. The gateway-side check needs 06a, which is blocked (Q3). |
| Renamed header refuses whole file, 0 IPC admissions, names profile SHA | Met (focused): `test_header_mismatch_refuses_the_whole_file_with_no_ipc[*]` asserts `link.calls == []` and the SHA in both the attribute and the message. Not yet shown through a real gateway (06a). |
| Timestamp without `Z` → `INVALID_TIMING` | Met (focused). |
| Blank cell → `UNAVAILABLE` | Met (focused), with `NO_MEASUREMENT` and the span carried. |
| Header unit `W` → `UNIT_INCOMPATIBLE` holds | Partial. The focused test shows `[W]` passes to the report unit verbatim. The hold itself is gateway behaviour and needs 06a (blocked). |
| 06b: accepted IDs listed, provenance `UNKNOWN`, no money row | Not built (Q4). |
| No vendor name in TEL-06 code, profile, fixture, UI text | Met for the files that exist: a case-insensitive grep of `export_csv.py` and `test_field_export_csv.py` for vendor names (victron, vrm, sma, huawei, solaredge, monta, monnit, cerbo, gx, aggsoft) returns nothing. The test imports `FakeLink` and `profile_document` from the shared `field_fixtures.py`, which names its `-1` source by design (Q-T66). No UI text is touched. |
| Every `CSV_CODES` entry has one focused test | Met. `test_every_csv_code_has_a_focused_test` enforces it by name. |

## Checks run (at `b43283ca`)
- `pytest field/tests/test_field_export_csv.py` → 41 passed.
- `pytest field/tests` → 193 passed in 14.2 s.
- Non-vacuous proof (committed first, reverted with `git checkout`): with the BOM check and the duplicate check disabled, 2 failed (`test_encoding_a_byte_order_mark_is_refused`, `test_duplicate_row_a_repeated_timestamp_is_refused`). `git status` was clean after the revert.
- Guards: see "Guards" below.
- No heavy job was run, no Postgres was run, and no server was started.

## Guards
`toolseck-architecture.ps1` → "Architecture check passed."; `toolseck-agent-workflow.ps1` → "Agent workflow check passed." (run directly, no policy override, ASSETOPS_GUARD_PYTHON set to the plan2 venv). Vendor-name grep: exit 1 (no match).

## Known deviations
- Q6: a row whose cell count is wrong raises `INVALID_VALUE` provisionally.
- Q7: the `collect()` return keys are provisional.
- Q8: the value text is normalised through `exact_decimal_text` (`0.50` → `0.5`).
- Q9: the spec's `report_key` is used, not the card's.

## Residual risk
- The gateway's handling (dedupe, `UNIT_INCOMPATIBLE`) is untested until 06a exists.
- `release_previous` is absent, so a crash between `admit` and `seal` in a CSV session would leave an unsealed group until another session seals.

## User-review focus
Answer Q1-Q4 (blocking). Then the profile, the fixture and generator, 06a and 06b get built. 06a and 06b are heavy, and 06b is Postgres. Both need a queue slot.
