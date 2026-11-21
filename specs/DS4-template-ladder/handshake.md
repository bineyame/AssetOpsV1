# DS4 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

Pre-flight points the Implementer confirms against `main` (answer each in I-questions only if it does not hold):
the billing reader accepts a one-row file at `Revision` 2 as a late revision (spec §4 B3); `observe_structure run`
exits 0 on the built October snapshot; the DS3 parity v4 batch's envelopes fall on contiguous Site-local days; the
`scheduling.run tick` perf line carries per-stage `elapsed_ms` for the enrolled Site; `pseudonym_key erase` and
`key_state` behave as spec T13 states.

## Reviewer questions

Read against `main` at `54ee700e1`. Checked and holding: the world names (`assetops_world_audit_l0|l1|l2_<12 hex>`,
`..._audit_c_<label>`, prefix `assetops_worldbench`) match `permitted_database`'s `_AUDIT_NAME`, none contains
`walk` or `serve`, none starts `assetops_op`, all are at most 63 bytes (prefix 24 + label 20 gives 62); a walk or serve
name, or a label such as `reserve` or `observe` (substring `serve`), is refused by the same function. `exports` is
deterministic (two runs into scratch dirs were byte-identical), so C1 can hold. DS3's `pg_harness.drop_database` uses
`FORCE`; the tool's own drop does not, so P3 stands. No database was connected to.

**R1 (done). §2, D-DS4.1, §3.6 C4, §7 Q4: which figures go blank is named for one line only.** The spec says "every
telemetry-fed leaf reads Not available yet" and names Kobo's fuel split. On `main` the telemetry-fed leaves of the
mini-grid structure are `delivered_kwh` (READING `feeder_demand`), `unexplained_loss_kwh` (OBSERVER), `necessary_l`,
`candidate_l`, `unexplained_l` (litre source, dips and slots), `dawn_days_below` (`battery_soc`),
`unserved_critical_kwh`, and the nodes built on them (`diesel_l`, and through it `cost_to_serve`, `contribution`; the
loss, obligation-hours and replayed-dawn nodes), at all three Sites, both for the walkthrough and for
`derived-values.json`, which holds numbers for each. Unnamed, a silent extra blank passes C4 as `not_available`, and
a number that the product shows from an `ASSUMED` or declared fallback with no reading behind it also passes if it
happens to be `unchecked`. Expected: §2 gains a table (Site by factor, with the screen or leaf that reads blank and the
record it names), and C4 compares the product's `not_available` set with that table: a factor blank that is not in the
table, or a table factor with a value, is a FAIL. The honesty claim is then testable instead of asserted.

**R2 (done). §3.6 C4 pass bar, T12, §7 Q4: "at least one equal value" is too weak, and T12 is unproven on `main`.**
With telemetry absent most expected nodes are `not_available`; one equal leaf (a tariff) passes C4. Expected: the rule
names the must-equal set per Site and side (those the commercial files state: `revenue`, `collected`, `billed_kwh`,
`metered_kwh` where stated, `fuel_cost`, `om`, `staff`, `tariff`, `in_transit`, `outstanding`, the plan side's
`billed_kwh`, `revenue`, `fuel_cost`) and fails if any of them is not `equal`. Also: T12 asserts C4 PASS on a world
nothing on `main` has run (no test builds a snapshot over an ON1-only tenant; see I2). Say what a C4 mismatch at T12
does to "done": unit 2 cannot close while the real world fails, so the ruling is either an Architect call before the
unit ends (state the turnaround) or the must-equal set is the contract and everything else is reported only.

**R3 (done). §3.7, D-DS4.9, T8: does the gap rule really close D-DS3.21's gap?** D-DS3.21 is about the outbox cover
(least start to greatest end over `span`/`window`). The rule looks at one Site-local day per envelope (interval start,
else source time). Cases it does not settle: (a) an envelope whose interval spans days (start day 6, end day 9) with
another on day 8: the rule says gap (7), the cover is contiguous (false refusal); (b) an interval that crosses local
midnight (`21:00Z` to `21:15Z` at +03:00) counts the start day only, though the cover reaches the next day; (c) an
envelope the loader will reject at step 7 (`BULK_REJECTED_ORDINAL`) still counts a day at 3a; (d) step 3a runs before
step 6, so a batch already COMPLETED with a gap (real path) is now refused instead of `already_loaded`. Expected: a
day set per envelope (every local day from start to end, end exclusive), T8 cases for (a) and (b), and (d) stated as
accepted. If the cover is wider than the days (D-DS3.21 read once more against `chain/events.py`), the spec says so.

**R4 (done). §0 Unit 3, §3.4 `--key-root`, D-DS4.10: the key root is not described.** The spec says the coordinator
creates `/opt/assetecon/keys/world` (mode 700) but not what is in it, whether it is secret, or what leaves it. Neither
`/opt/assetecon/keys` nor `/opt/assetecon/worlds` exists on this machine today. Expected: it holds, per L1 database,
a directory (0700) of one pseudonym key file per tenant (the keyed-hash secret that turns customer identifiers into
pseudonyms; `pseudonym_key create|erase`) and, after an erase, tombstones. The world's data is synthetic, so the
keys protect nothing real, but a key re-links pseudonyms to identifiers within that world, so it is treated as a
secret: never committed, never copied, never placed in a packet, manifest or evidence file (manifests hold the path
only; T5 should assert no key file content or path under it appears in stdout or the bench report beyond the
directory name), and the coordinator owns its lifecycle (bench and drop leave empty directories and tombstones, as
spec §3.4 says).

**R5 (done). §3.4 `clone`, D-DS4.8: `check_passed` can outlive what it checked.** A clone copies the L2 manifest's
`check.passed`. The `check` block records `commit` and `derived_values_sha256`, but `clone` never compares them: the
derived values are not in any key, so editing `derived-values.json` (the oracle) or merging a change to the check
itself after a passing check still hands out `check_passed: true`; and "clean, good" is defined as exactly that flag.
Expected: `clone` reports `check_passed` true only when the block's `derived_values_sha256` equals today's and its
`commit`'s `tools/world.py` tree equals today's (else `null` with `check_stale`); one test (T9 or T6) for each.

**R6. T4, §3.2: add the operator-prefix and substring cases.** T4 lists `assetops_walk1` and the label `walk1`; add
prefix `assetops_opx` (operator name, refused by `is_operator_name`) and label `observe` (contains `serve`) so the
deny list and the operator rule are each exercised, not only the pattern. Not a gap in the spec's behaviour.

## Implementer questions

Pre-flight of the spec against `main` (read only; no database touched). Confirmed holding: `onboard_operator`
`digest|check|apply` flags and `ASSETOPS_TENANT_SLUG` as the served tenant; `load_world_inputs` flags;
`build_structure_snapshot build|verify` flags and its output keys (`portfolio_snapshot_id`, `sites`, `matches`,
`differences`), `verify` exit 4; `observe_structure run`; `pseudonym_key erase --dir --tenant-id`;
`scheduling.run enrol|tick --no-prebuild`; `heavy_slot_check.require(tool, db=)`; `world_history exports` and
`unwritten.json`; the fixture's accepters (Wanjiru ANALYST submits, Joseph FINANCE lead accepts); `site.timezone`
exists (migration 0001). Not confirmable without a database (pre-flight list in the head of this file): B3's late
revision, `observe_structure` exit 0, the v4 batch's contiguity, the perf line's `elapsed_ms` per stage
(`scheduling/tick.py:163` carries it per stage result), `key_state`; each is a day-one check inside unit 1 or 3.

**I1 (done). §3.7 step 3a: what `local_days` does with an envelope it cannot read.** Step 1's strict parse checks the
batch, not each envelope; envelopes are judged at step 7 (`decide`). 3a does `json.loads(text)`, `timing[...]`,
`datetime.fromisoformat(...).astimezone(...)`: a missing key, a bad string raises `KeyError` or `ValueError`
(uncaught: a traceback, not a refusal), and a naive timestamp is read in the host's zone. Expected: an envelope with no
readable, offset-bearing timestamp contributes no day at 3a (step 7 refuses it as `BULK_REJECTED_ORDINAL`, as today);
a batch of zero readable days passes 3a; T8 gains a malformed and a naive case. (Or: refuse at 3a with a named code; say
which, since DS3's refusal list is closed.)

**I2 (done). §3.5 L2, T12: a snapshot over a Site with no gateway, sources or binding set has never been built on
`main`.** The only tests using the Lakeside file are ON1's (`test_on1_operator_file.py`, `test_on1_served_tenant.py`);
none builds a snapshot or runs the observer on it, and `SnapshotBuilder.build` reads `site_inputs` for each Site. T12
expects `structure_snapshot` 4 and an observe exit 0. Expected: unit 1 starts with a spike on a scratch
`assetops_ds4t<hex>_audit_*` database (build L1 by hand through the three commands, then snapshot and observe), and if
`build` raises or `observe` exits non-zero the Implementer stops and asks the Architect rather than adapt the L2
steps. Say so in §6 unit 1.

**I3 (done). §0, §3.3, §3.4: who creates `--state` and its subdirectories, and what an L1 key directory does on
rebuild.** `/opt/assetecon/worlds` does not exist. The spec makes the coordinator create only the key root (unit 3).
Expected: the tool creates `<state>/{manifests,inputs,tmp}` (0700) under an existing, outside-the-repository `--state`
and refuses a missing one (`WORLD_STATE_INVALID`), and the coordinator creates `/opt/assetecon/worlds` with the key
root; tests use temporary directories. For the L1 key directory: after `drop` the directory and tombstones stay, so a
rebuilt L1 of the same key finds `<key-root>/<L1 database>/` present; expected the tool accepts an existing directory
that is mode 0700 and owned by the user (tenant ids are new, so no key collides), else `WORLD_KEY_ROOT_INVALID`.

**I4. §3.6 C5: `run-host-tests.ps1` run from inside the tool.** The wrapper resolves its own interpreter and
database (`ASSETOPS_TEST_DATABASE_URL`, else the shared `assetops_test`; its header), makes harness clones on the
test container, and checks package paths against this worktree. Spec §3.6 runs it with `DATABASE_URL` removed. It
carries no slot check, so the nested run is not a second slot, but it is a second DB job inside the first: confirm
the same `heavy-slot` marker covers it and that `pwsh` is on the PATH of the built environment (the C5 child gets the
tool's environment, but §3.5's `E` omits `PATH`-only wrappers' variables such as `ASSETOPS_TEST_PYTHON`). Expected:
C5's child environment is `E` plus `ASSETOPS_TEST_DATABASE_URL`, `ASSETOPS_TEST_PYTHON` when set, and the slot
marker; T9 records the environment passed.

**I5. §3.5 `drop` and `check` clones need the key directory.** Check clones and `verify` (C3) read tenant data through
`build_structure_snapshot`; the pseudonym key is only read by commercial paths, but a clone's `ASSETOPS_PSEUDONYM_KEY_DIR`
must be the L1 directory for any step that decrypts or recomputes identities. The spec sets it for L1 and L2 steps; say
the same for every `verify`, `observe` and C-check subprocess on a clone (expected: yes, always the L1 directory from
the clone's manifest).

**I6. §3.7 / T15: DS3's refusal for `site_timezone` None.** `BULK_UNKNOWN_GATEWAY` is already raised at step 3 when no
gateway row exists, so a `None` timezone after step 3 cannot occur for an existing Site (`site.timezone` is NOT NULL).
Expected: drop the `None` branch and the cache, or keep it as a one-line defensive assertion with no test; either is
fine. Not a done-changing question.
