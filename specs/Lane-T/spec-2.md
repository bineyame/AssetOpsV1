## TEL-05 · Postgres acceptance, profile `-1` · 0.5 d · run alone

**Files.** `host/tests/test_field_modbus_tcp_acceptance_postgres.py` (**card correction:** `host/tests`, not `backend/tests`; feasibility §2.4), test `test_gx_profile_1_lands_as_accepted_evidence`. Skipped without `ASSETOPS_TEST_DATABASE_URL`.

**Approach (reuses the proven central pattern in `host/tests/test_s6_verification_publication.py:233-300`).**
1. `pg_harness.fresh_database()`; `PostgresFoundationStore(URL)`; KOBO-001 converted with `test_s1_bindings_postgres.converted(store)`; enable gateway and sources by the two `UPDATE ... disabled_at = NULL` statements of that test (stand-in for provisioning); registered daytime draft from that store gives the snapshot. Snapshot validity (Q-T48): the existing registered tests admit 2026-09-30 source times through the same conversion clocks without `OUTSIDE_VALIDITY`, and central `decide` checks the same Foundation/binding periods (`backend/assetops_backend/evidence/ledger.py:386-392`).
2. Central: `BatchIngestionService(PostgresEvidenceLedger(URL), clock)` behind `FakeCentral(respond)`, with the **real** UTC clock and no `test_decision_clock_override` (Q-T47: verified by reading that the decision clock only stamps `decided_at` and recompute-job times, `postgres_evidence_ledger.py:14-21`, `:525-528`, and that `submit`/`decide` have no age or received-time rule, `ledger_service.py:99-170`; not yet run).
3. Gateway process, activation, in-process emulator and poller subprocess as TEL-04 (upload `interval_seconds` 3600), replay rate 60 over 2026-09-30T03:00Z-15:00Z, then harness `deliver` until nothing is attempted.
4. Reads, all in-process with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` both set to `URL`:
   - accepted evidence: `SELECT id, role, device_id, signal_id, source_time, quality FROM accepted_evidence WHERE site_id = :s`, printed;
   - provenance (Q-T49): `build_source_provenance(URL).resolve(tenant_id, site_id, ids)` (`backend/assetops_backend/evidence/composition.py:36`, `source_provenance.py:250-253`);
   - assessment (Q-T50): `assess_dispatch.main(["assess", "--tenant-id", T, "--site-id", S, "--start", "2026-09-30T03:00:00Z", "--end", "2026-09-30T15:00:00Z", "--cohort", *field_bench.cohort_members(expect)])` with pytest `capsys`; stdout is one JSON `{"run_id", "created", "revision_ids", "new_revision_ids"}`; then `build_dispatch_read_service(URL).run(T, S, UUID(run_id))`.

**Gates.** Receipts COMPLETED; accepted evidence for both bound roles (`pv_power`, `battery_soc`), IDs printed; `resolve(...)["state"] == "UNKNOWN"` and its reason codes are exactly `["NO_POSITIVE_BINDING"]`; the assess run's `evidence[].evidence_id` set is a subset of this test's accepted IDs, and `"NO_GENERATOR_STATE"` appears in the serialized run detail; no `consequence` row for the Site; green on two consecutive invocations, each on a fresh database (Q-T56).

**Stop.** As the card; plus any central refusal for timing (report the refusal row; do not add a clock override).

---

## TEL-08 · BeagleBone Black repeat (stage 2, TCP only) · 0.75 d (+ owner 30 min) · October scope

**Preconditions (owner, physical, by 29 Oct 12:00).** microSD 8 GB or larger and a 5 V 2 A barrel supply on hand (buy only these if missing, about $16); flash Debian 13 IoT (kernel 6.12) to the microSD and boot from it; connect the board to the laptop's LAN by Ethernet, with internet access through that LAN for `apt`; give the builder SSH access with a key; allow inbound TCP 8443 and 5020 on the laptop's Windows firewall for the LAN profile (admin action). The coordinator flags these to the owner.

**Design choices (settled).**
- Boot from microSD; no eMMC flash. **Rejected:** eMMC flashing (slower, irreversible, not needed to prove the path).
- Ethernet on the LAN. **Rejected:** USB gadget networking (Windows RNDIS driver risk on Windows 11).
- Deploy by copying `contracts/assetops_contracts`, `gateway/assetops_gateway`, `field/assetops_field`, `field/profiles` and `host/tests/field_bench.py` to `/opt/assetops/src` with `scp -r` as user `assetops` (Q-T58), and setting `PYTHONPATH=/opt/assetops/src/contracts:/opt/assetops/src/gateway:/opt/assetops/src/field` and `PYTHONDONTWRITEBYTECODE=1` for every board process. Record `git rev-parse HEAD` and the tree hash, computed identically on the laptop (Git Bash, over the same copied set) and on the board (Q-T62): `cd /opt/assetops/src && find contracts gateway field host -type f ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum | sha256sum`; both must match. **Rejected:** building wheels (field packaging untested; adds a step that proves nothing about the path).
- Run gateway and poller as two `nohup` processes under a non-root `assetops` user; no systemd units in October. **Rejected:** systemd hardening (§7.9 step 8-10 is post-October).
- Emulator and `serve_tls` stay on the laptop. Python 3.13 from Debian, run as `/usr/bin/python3` directly: stdlib only, so no venv and nothing is pip-installed on the board (Q-T61). No test suite runs on the board; the TEL-08 run is the 3.13 evidence (Q-T7).
- Board clock must be NTP-synchronised (`timedatectl show -p NTPSynchronized` = `yes`; if `systemd-timesyncd` is missing, `sudo apt install systemd-timesyncd`) before the gateway starts. **Clock offset gate (Q-T27):** board `timedatectl timesync-status` `Offset` and laptop `w32tm /stripchart /computer:<the board's NTP server> /samples:3 /dataonly` both within ±50 ms, recorded in the claim record. At rate 12 the emulator's state lead and the 1 s send offset tolerate a relative offset up to 167 ms.
- Credential files on the board: `gateway.credential` (the gateway creates and protects it) and `upload-credential.<selector>` copied by `scp`, then `chmod 600` and owned by `assetops` (Q-T61).

**Laptop bench helper `host/tests/field_bench.py`.**
- `setup --database-url <postgresql://.../assetops_tel_bbb_test> --laptop-ip <ip> --board-state-dir /opt/assetops/state --out <dir>` (Q-T58, Q-T59): migrates the named database to head, converts KOBO-001, applies the same enabling as TEL-05, creates the daytime registered draft, runs `python -m assetops_backend.evidence.provision_gateway issue --tenant demo --site KOBO-001 --gateway <snapshot gateway.gateway_external_id> --enable-source <source_external_id>` (one per snapshot `sources[]` entry) `--credential-out <out>/board/upload-credential` with `DATABASE_URL` set, creates the TLS material, and writes `<out>/board/{snapshot.json (text), activation.json ({snapshot_text, claimed}), expect-identity.json (epoch "bbb-epoch-1"), gateway.json, upload-credential.<selector>, bench-cert.pem}` and `<out>/laptop/bench-key.pem`. `gateway.json`: `{"database": "gateway.sqlite3", "credential_file": "gateway.credential", "address": "/opt/assetops/state/gw.sock", "provisioning": provisioning_from_snapshot(..., epoch="bbb-epoch-1"), "upload": {"server_url": "https://<laptop-ip>:8443", "upload_credential_file": "upload-credential.<selector>", "ca_file": "bench-cert.pem", "interval_seconds": 30}}`. Backend imports are inside `setup` only.
- TLS (Q-T60): `C:\Program Files\Git\usr\bin\openssl.exe req -x509 -newkey rsa:2048 -nodes -days 7 -subj "/CN=assetops-bench" -addext "subjectAltName=IP:<laptop-ip>" -keyout bench-key.pem -out bench-cert.pem` (the precedent is `tools/s2_demo_walkthrough.py:142`); the self-signed certificate is its own CA, so `ca_file` is the certificate. `python -m assetops_backend.serve_tls --cert bench-cert.pem --key bench-key.pem --host 0.0.0.0 --port 8443` with `DATABASE_URL` = the bench database.
- `activate --address <ipc> --credential <file> --activation <activation.json>`: stdlib plus `assetops_gateway.ipc` only, so it runs on the board; sends one `activate`.
- `read --database-url <url> --what evidence|provenance|assess|findings|consequences [--start --end]`: in-process reads printing one JSON document each (backend imports inside): accepted evidence rows; `build_source_provenance(url).resolve(...)`; the `assess` call of TEL-05; `finding-rows`; consequence reads. Used by the TEL-08 gates and the TEL-07 runbook (Q-T63).
- Evidence API read through `serve_tls` (Q-T60): `GET https://<laptop-ip>:8443/api/sites/KOBO-001/evidence/records?limit=200` with Python `urllib` and `ssl.create_default_context(cafile="bench-cert.pem")`, no `Authorization` header (that header is the gateway upload principal, `backend/assetops_backend/evidence_api.py:195-214`; the read route takes none).

**Run.** Emulator CLI on the laptop (`--host 0.0.0.0 --port 5020`, replay rate 12, 2026-09-30T08:00Z-12:00Z, `--stop-at 2026-09-30T12:00:00Z`, wall epoch = now + 60 s, the same values passed to the board); on the board: gateway `serve`, `field_bench.py activate`, poller CLI pointing at `<laptop IP>:5020` with the same replay arguments; background uploader `interval_seconds 30`. Then on the laptop: `field_bench.py read --what assess` for the window, and the evidence API read.

**Gates.** The TEL-05 gates (COMPLETED receipts, accepted evidence per role, provenance UNKNOWN, assess completes, no consequence), now with real `serve_tls` and the board's gateway. **One uplink fault (Q-T57, card correction):** at about one third of the window the builder stops `serve_tls` on the laptop for 5 min of wall time, then starts it again. The poller keeps reading and publishing to the local gateway, so a real backlog forms: `diagnostics` (read over SSH with a one-line `GatewayLink(...).call("diagnostics")`) shows `queue_count` and `sealed_pending_batches` rising during the stop and back to 0 after recovery; no `BATCH_ID_CONFLICT` refusal appears; every gateway batch reaches a COMPLETED receipt; the accepted evidence has no gap across the stop. The SSH session stays up (the cable is not pulled). Clock offsets recorded. BBB claim record names "BeagleBone Black · Debian 13 IoT · kernel <uname -r> · Python <version> · commit <sha> · tree <sha256>". R2.

**Stop.** Any change to gateway or field code needed for Linux (report the traceback); NTP not synchronisable or offset above 50 ms; the board cannot reach the laptop after the firewall rule; any central refusal. **Slip rule:** if the board is not reachable by 30 Oct 09:00, TEL-08 moves to 31 Oct and the 30 Oct showing uses the laptop result.

**Stretch (only if TEL-05b is green first).** Repeat with profile `-2` and the prolonged JSONL.

---

## TEL-05b · Finding proof, profile `-2` · 0.75 d (focused parts can be built while the board is prepared)

**Files.** `field/profiles/gx-system-illustrative-2.json`, `contract-fixtures/telemetry/kobo-prolonged-public-observations-v1/`, additions to `host/tests/field_observation_fixtures.py` and its freshness test, `field/tests/test_field_gx_emulator.py` cases for unit 101, second test `test_gx_profile_2_raises_a_finding_with_no_money_shown` in the TEL-05 file. TEL-01 `decode.py` already supports `ENUM`.

**Profile `-2`.** Status `ILLUSTRATIVE`. Unit 100: the `pv-ac-output` row of `-1`, unchanged (V4 still publishes PV AC power at 15 min, so span 900, cadence 900, period 300). Unit 101, AssetOps illustrative block (row status `ILLUSTRATIVE`, `source_document` "AssetOps illustrative block; not a vendor register map"), FC 3, all numeric rows `int32`, `word_order BIG`, `scale_exponent −6`, `unit_exponent 0`, `register_unit` = `source_unit`, `register_quantum "1"`, `output_resolution "0.000001"`, sentinel `[2147483647]`; every interval row span 300, cadence 300, **poll period 60** (N = 5, Q-T12); every state row cadence 300. `quantity.point` for every unit-101 row: "AssetOps illustrative block; not a vendor register"; `phase_aggregation` `SINGLE_REGISTER`.

| Address | device_id / signal_id | role | unit | reading class | `quantity.kind` / `sign` |
|---|---|---|---|---|---|
| 1000 | `generator-controller/status` | `generator_state` | `state` | STATE, `ENUM` uint16 `{0: STOPPED, 1: STARTING, 2: RUNNING, 3: FAILED}`, sentinel 65535 | `OPERATING_STATE` / `not applicable` |
| 1002 | `generator-controller/ac-power` | `generator_power` | kW | INTERVAL | `AC_POWER` / `positive = power delivered to the AC bus` |
| 1004 | `residential-meter/active-power` | `feeder_demand` | kW | INTERVAL | `AC_POWER` / `positive = power drawn by the feeder` |
| 1006 | `clinic-meter/active-power` | `feeder_demand` | kW | INTERVAL | same |
| 1008 | `mill-meter/active-power` | `feeder_demand` | kW | INTERVAL | same |
| 1010 | `pv-inverter-controller/available-power` | `pv_available_power` | kW | INTERVAL | `AVAILABLE_AC_POWER` / `positive = power the PV could deliver` |
| 1012 | `battery-pcs-controller/discharge-capability` | `pcs_discharge_capability` | kW | INTERVAL | `DISCHARGE_CAPABILITY` / `positive = power the PCS could discharge` |
| 1014 | `battery-pcs-controller/state-of-charge` | `battery_soc` | % | STATE | `STATE_OF_CHARGE` / `not applicable` |

Spans, cadences and reading classes equal the V4 publication profile (`cadence_minutes` 5 for these signals, 15 for PV AC power) and the freshness test asserts it; it also asserts the `enum_map` texts are labels of the snapshot's `generator-controller/status` binding (the gateway holds any other value `INVALID_ENUM`, `service.py:864-869`). SoC is on unit 101 at full resolution, so 843 is omitted from `-2`: a 1 % register could move a point across the dispatch reserve headroom (`dispatch_v3.py:47` `SOC_HEADROOM_POINTS`). Device and signal IDs are the Kobo bindings (`backend/conversions/kobo-001-bindings.json`, plus the S3/S6 demo configs). The roles dispatch-3.2 reads (`dispatch_v3.py:51-58`: generator state and power, feeder demand, PV available, discharge capability, SoC) are all present; the critical-load channels are verification (S6) inputs, not dispatch inputs (Q-T54).

**JSONL.** `generate_prolonged_fixture(out_dir)` uses the in-memory converted store (`registered.converted()`), applies `kobo-001-s3-dispatch-demo-config.json` then `kobo-001-s6-verification-demo-config.json` exactly as `configure()` (`test_s6_verification_publication.py:82-87`), creates the registered `kobo-mini-grid-prolonged` draft over 2026-10-13T03:00Z-11:00Z with timestep 5 and `REGISTERED_KOBO_PUBLICATION_PROFILE_V4` as `draft()` (`:90-112`), executes it with `gateway=None` as in TEL-03, and writes the public observations. Same freshness test pattern.

**Postgres test.** As TEL-05, but configure the Postgres store with the same two demo configs and build the same prolonged draft for the snapshot; replay rate 60 over the window; then in-process, in this order, failing fast (Q-T51, Q-T52, Q-T53, Q-T55):
1. `assess_dispatch.main(["process-jobs"])` (the jobs ingestion created; default cohort selection), asserting every outcome `status == "DONE"`, then `assess_dispatch.main(["match-findings", "--tenant-id", T, "--site-id", S])`. This is the path the S4-01 `F01-gateway` case proved on the same scenario through a gateway (`tools/s4_finding_cases.py:446-449`); the matcher reads the default selection, which an explicit `assess` does not feed.
2. Finding: `build_finding_store(URL).rows(T, S)["findings"]` non-empty, else stop immediately (report `match-findings`' `window_statuses`); `frid = build_finding_read_service(URL).finding(T, S, fid)["selection"]["latest_revision_id"]`; `build_source_provenance(URL).finding_revision(T, S, frid)`: `cited_accepted_evidence_ids` ⊆ this test's accepted IDs, `state == "UNKNOWN"`, reason codes `["NO_POSITIVE_BINDING"]`.
3. Price: `publish_assumption.main(["fixture", "--site", "KOBO-001", "--file", "backend/conversions/demo-diesel-price-publications.json"])` with **no `--step`**, which publishes v1, v2, v3, v4 in order (each step's `expected_prior_step` must already be published, `publish_assumption.py:79-86`; `--step v4` alone refuses `PRIOR_STEP_NOT_PUBLISHED`). v4 gives 1.28 USD/L for October 2026. This is the same CLI the S4 Postgres tests use (`backend/tests/test_s4_assumptions_postgres.py:68-75`), so it is the "existing seeding" of amendment 2 item 5. Tenant default `demo` (`config.py:105`); `DATABASE_URL` = `URL`.
4. `recompute_consequences.main(["run", "--tenant", "demo", "--site", "KOBO-001"])`, exit 0.
5. API reads over `with TestClient(main.create_app()) as client:` with `DATABASE_URL` set by `monkeypatch.setenv` (the production composition, as `backend/tests/test_s5_overview_postgres.py:259-261`): `GET /api/sites/KOBO-001/finding-index`; `GET /api/sites/KOBO-001/findings/{fid}?revision_id={frid}`; `GET /api/sites/KOBO-001/findings/{fid}/financial-consequences?revision_id={frid}` (`backend/assetops_backend/finding_api.py:245-262`; `revision_id` is passed so a closed performance gate cannot hide the read).

**Gates (amendment 2, N1 replaced).** A dispatch Finding exists for the window citing only this test's accepted evidence IDs; its provenance is UNKNOWN / `NO_POSITIVE_BINDING`; every consequence read has `currentness.current_amount_shown == false` and `"MIXED_OR_UNKNOWN_SOURCE"` in `currentness.withheld_reasons`; the Finding read and the finding index show no current amount; green twice, each on a fresh database.

**Rejected.** Mixing a field-sourced generator with the other roles from the simulated publisher (two gateways on one Site would split the cohort and blur what the proof shows). Placing the extension rows at real GX addresses (would imply a vendor claim). Attaching a publication to get a figure (D5(d)). A separate "probe" heavy run before the real one (Q-T54): the test itself fails fast at step 2, so the probe would only spend a second slot.

**Stop.** No Finding arises (report the window assessment; do not tune values or window; the Architect decides the next step); a current amount is shown anywhere (stop immediately; that is a money-gate defect, report to the Architect); any 4xx from ingestion; the price fixture cannot be applied without new code.

---

## TEL-07 · Claim records and demo runbook · 0.25 d

**Files.** `.agent/TEL-05-review-packet.md`, `.agent/TEL-08-review-packet.md`, `.agent/TEL-05b-review-packet.md`, `.agent/TEL-demo-runbook-2026-10-30.md`.

**Claim records (Q-T64)** use the §10.0 template, whose fields are complete: R-level, Interface, Format / profile, Source model / firmware, Data origin and clock, Environment, Evidence, Not claimed. Values:
- R-level: TEL-05 "R2 (adapter lab-tested, emulator on one laptop)"; TEL-08 "R2 (adapter lab-tested on BeagleBone Black, emulator on the laptop)"; TEL-05b "R2 (adapter lab-tested, emulator on one laptop)". R3 is not claimed in October.
- Source model / firmware (card correction, Q-T37): "Emulator: stdlib Modbus TCP server in `field/tests/field_emulators/gx_server.py`, framing cross-checked with the pymodbus 3.16.1 client. No real device."
- Data origin and clock: the run's scenario and window, "values presented at the register's resolution (1 W, 1 %)" for GX rows, "the whole PV value on register 808, zero on 809 and 810", the clock mode, rate and wall epoch.
- Environment: as §10.0, plus the measured clock offsets for TEL-08.
- Evidence: accepted-evidence IDs, receipt batch IDs, the provenance result, test node IDs and pass counts, profile ID/version/SHA-256, JSONL SHA-256, commit, and (TEL-05b) the Finding ID and revision ID.
- TEL-05 statement: "Readings travelled emulator → Modbus TCP poller → real gateway → central ledger and were accepted as evidence. Source: not established. No Finding is claimed and no money is shown."
- TEL-05b statement: the exact text of amendment 2 item 6.
- Not claimed: "Victron GX, Cerbo or VRM compatibility; any real device or vendor register map; real wire faults; any money figure; any field performance" (TEL-05 and TEL-05b add "BBB").

**Runbook (Q-T63).** Exact commands for the live showing, terminal only, against `assetops_tel_show_test` (a `*_test` database built that morning by `field_bench.py setup`; never touched by pytest, whose `fresh_database()` uses `assetops_tel_test`): bench `setup`, `serve_tls`, emulator, gateway, `activate`, poller, then `field_bench.py read --what evidence`, `--what provenance`, `--what findings` (only after a TEL-05b-profile run) and `--what consequences`, each printing JSON. The runbook may cite the existing screen labels ("Source unverified", "No current cost is shown", `frontend/src/sites/sourceProvenance.tsx:101-104`) but adds no UI and starts no dev server.

**Gate.** A reviewer reruns the showing from the runbook alone.

**Stop.** The showing needs the demo database or a UI change.

---

## TEL-06 · Minimal generic CSV collector (B1) · 0.5 d + 0.25 d · after TEL-07, may move to 31 Oct

**Files.** `field/assetops_field/export_csv.py`, `field/profiles/generic-interval-csv-illustrative-1.json`, `contract-fixtures/telemetry/generic-interval-csv-v1/{kobo-window.csv,manifest.json}`, `field/tests/test_field_export_csv.py`, `host/tests/test_field_export_csv_proof.py` (06a), a third test in the TEL-05 file (06b).

**Interfaces (Q-T65).**
```python
class CsvRefused(ValueError):
    def __init__(self, code: str, field: str, detail: str, profile_sha256: str) -> None: ...
CSV_CODES = ("ENCODING", "EMPTY_FILE", "HEADER_MISMATCH", "INVALID_TIMING", "SPAN_MISMATCH",
             "DUPLICATE_ROW", "UNSORTED_ROWS", "INVALID_VALUE")
class CsvCollector:
    def __init__(self, profile: FieldProfile, publisher: GatewayPublisher) -> None: ...
    def reports(self, path: Path) -> list[DeviceReport]: ...     # whole-file validation first; raises CsvRefused
    def collect(self, path: Path) -> dict[str, Any]: ...          # reports(), then admit, seal_and_release
```
- File: UTF-8 (BOM refused, `ENCODING`), comma delimiter, LF or CRLF, parsed with stdlib `csv`. First line is the header; no data rows → `EMPTY_FILE`.
- Header: first column exactly `timestamp_utc`; then one column per profile row, in any order, each written `<column> [<unit>]` (one space, unit in square brackets, unit text `[^\]]+`). A missing, extra, renamed or malformed column → `HEADER_MISMATCH` before any IPC call. The bracket unit becomes the report `unit` verbatim; it is **not** compared with the profile, so a `[W]` header reaches the gateway and is held `UNIT_INCOMPATIBLE` (card gate). The profile row carries only `{"column": ...}`; the planned `unit_header` key is dropped.
- `timestamp_utc`: exactly `YYYY-MM-DDTHH:MM:SSZ`, else `INVALID_TIMING`; each value a multiple of the profile's `span_seconds` from 00:00:00Z, else `SPAN_MISMATCH` (D10: refused, not resampled). Each row is one interval `[t − span, t)`. Timestamps strictly increasing (`UNSORTED_ROWS`); a repeated timestamp → `DUPLICATE_ROW`. Gaps between rows are allowed (nothing is published for them).
- Cells: blank → `UNAVAILABLE`/`NO_MEASUREMENT`; otherwise `^-?\d+(\.\d+)?$` with `.` as the decimal separator and no thousands separator, and an exact multiple of the row's `output_resolution`, else `INVALID_VALUE`.
- Same op set and session-ref rule as the poller; `release_previous` on start likewise. The collector is not an aggregator. No vendor name in any TEL-06 file (code, profile, fixture, test, UI text); the rule does not apply to profiles `-1`/`-2`, which name their third-party source by design (Q-T66).

**Gates (card list quoted, Q-T6).** The same file admitted twice gives identical message IDs and no new sequence; a renamed header refuses the whole file with 0 IPC admissions, and the refusal names the profile SHA; a timestamp without `Z` is refused `INVALID_TIMING`; a blank cell becomes `UNAVAILABLE`; a header unit `W` produces `UNIT_INCOMPATIBLE` holds; for TEL-06b, accepted IDs are listed, provenance is `UNKNOWN`, and no money row exists; nothing in the code, profile, fixture or UI text names a vendor. Every `CSV_CODES` entry has one focused test.

**Stop.** Any request to name a vendor format.

**Rulings (2026-10-28).** Section M below is the current TEL-06 card (profile rows, fixture, 06a and 06b gates, Q5-Q9). Where it is more specific than this section, it wins.

---

