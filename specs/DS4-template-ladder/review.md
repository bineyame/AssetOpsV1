# DS4 review: units 1 and 2

## Round 1 (discovery, W5): units 1 and 2 at `af27201d2`

Reviewer: Claude (fresh; not the author), 2026-11-21. Diff `git diff main...af27201d2` (15 files, +2696/-6).
Read: spec rev 3 (amended §2.1), `rulings.md` D-DS4.1 to D-DS4.27, `reviewer-guide.md` P1 to P34, `packet.md`,
`mid-build-questions.md`, and every changed line of code and tests.

**Summary.**
- **Verdict: ACCEPT WITH FIXES.** Fix M1 and M2 on the branch; a verification re-review of those two closes it.
- Safety holds: names go through `check_name`/`permitted_database` before every statement; admin host `127.0.0.1`;
  no `FORCE`; `walk`/`serve`/`assetops_op*`/`assetops_test` refused; C5 runs under its own
  `assetops_wc5_pt<hex>_base_test`; `/opt/assetecon/keys` and `/opt/assetecon/worlds` still do not exist; no key file
  name or content reaches stdout, the manifests or the packet.
- Honesty holds: `C4_CONTRACT` equals §2.1 cell for cell (read by hand, 47 + 47); `C4_SITE_CLASSES` is D-DS4.26's
  literal; `C4_KNOWN_FINDINGS` is exactly the 12 D-DS4.27 lines; nothing missing reads 0 (`None` never equals; `B`
  needs a `missing` or non-empty `missing_leaves`).
- The cover rule is right on 16 envelopes of my own (local midnight both ends, multi-day, DST, Kiritimati, unsorted,
  reversed); unreadable and naive times are their own code.
- **M1 (Medium):** C4 does not check which Sites it judged: two Sites, or one Site twice, PASS.
- **M2 (Medium):** `harness_run`'s built environment is not tested against inheritance (my plant passes every test).
- Lows L1 to L6: the missing `ALL` line, three untested rules, the known-finding mark, two edge paths.
- Deviations: all three accepted.
- Follow-up (coordinator: 5a F1 merged on `main` at `a8a30426a`): after DS4 merges `main`, empty `C4_KNOWN_FINDINGS`,
  rerun T12, and expect C4 PASS and exit 0. Reviewed as the branch stands.

### Checks I ran

| Command (worktree; PYTHONPATH backend, contracts, simulator, tools) | Result |
|---|---|
| `heavy-slot.sh -- python -m pytest test_ds4_world.py test_ds4_batch_days.py test_ds3_bulk_load.py -q` | 95 passed in 5.44 s |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set) | Architecture check passed |
| `check-agent-workflow.ps1` | Agent workflow check passed |
| `heavy-slot.sh --db -- pwsh run-host-tests.ps1 -- test_ds4_world_postgres.py test_ds4_batch_days_postgres.py -s` | 8 passed in 40.5 s (T12-T17). T12's check: C1 5 files, C2 136 tables, C3 1 snapshot matches, C5 injected 0, C6 `0 batches (telemetry none)`, C7 7 steps PASS; C4 FAIL with 12 `known D-DS4.27` lines, 0 `new`. Afterwards no `assetops_ds4t*`, `assetops_wc5_*` or `ds4g*` database is left |
| My cover-rule probe (16 span sets, 15 `envelope_span` inputs) | below, in "Cover rule" |
| My C4 probe (`c4_oracle` on payloads built from `derived-values.json`) | M1, L3 |
| 12 plants of my own in a `git archive` copy (scratch, deleted) | 8 caught, 4 not (M2, L2) |

Not rerun: the DS3/ON1/3A3/3B4/3B7a regression set and fast check-all (packet: 69 passed and "All 40 guards passed"
at `9eff83776`; `af27201d2` adds only the packet, handoff, spec status and state entry, so the same code revision).
The builder's plants P1 to P34 I did not repeat one by one; I read each named test and ran my own plants instead.

### Findings

**M1 (Medium, acceptance gap against D-DS4.16's totality). C4 does not check the set of Sites.**
`tools/world.py:925-944` (`c4_oracle`) judges whatever rows `_c4` (`:1021-1044`) gets from the manifest's
`snapshots[...]["sites"]` ids through `store.get`. It FAILs only when there are no rows at all. My probe: rows for
Kisiwa and Kobo only give `PASS`; Kobo's row twice gives `PASS`. So a world whose snapshot build excluded a Site, or
whose `store.get` returned fewer rows than ids, passes `check` and is reported "clean, good" (`check_passed: true`).
C2 and C3 compare the world with its own build record, so they do not catch it either. T12 would notice on today's world
(its blank list is computed over all three codes), but `check` itself, which WK and the walkthrough rely on, does not.
D-DS4.16 and §2.1 say the contract covers "all 47 mini-grid factors in each Site snapshot of this world"; §3.6's text
says "for each Site row" and does not name the set, so this is partly a spec gap. **Fix:** in `c4_oracle` (or `_c4`),
FAIL when the multiset of `(slug, site_code)` rows differs from the definition's `tenants[*].sites` keys for each month:
`site_missing <slug>/<code>`, `site_duplicate <slug>/<code>`, and a row whose code is not in the definition (today a
`KeyError` that `_guard` turns into a FAIL, so it is safe but unnamed). Add T9 cases (two Sites; one Site twice) and a
plant (drop the check). Tell the Architect, since it adds a FAIL line form to §3.6.

**M2 (Medium, missing test on a protected seam). `harness_run`'s environment is only tested for the keys it removes.**
`backend/tests/test_ds4_world.py:786-822` checks that the runner sees the base URL, the heavy-slot markers and none of
`DATABASE_URL`, `ASSETOPS_TENANT_SLUG`, `ASSETOPS_PSEUDONYM_KEY_DIR`. My plant `env = dict(world.environ)` at
`tools/world.py:949` (inherit the parent) passes all 95 tests, because the fixture's parent has none of those keys and
the base URL is overwritten after. The code is right today (`world.env(None)` builds from scratch). It matters because
an inherited `ASSETOPS_TEST_DATABASE_BASE_URL` plus the harness run variable makes `pg_harness.py:99` route to the
parent's base, which is how `assetops_test` would be touched (D-DS4.20), and an inherited `PGDATABASE` or
`ASSETOPS_REAL_OPERATOR_DATA` is what T5 forbids for product steps. **Fix:** in that test, give the parent
`DATABASE_URL`, `PGDATABASE`, `ASSETOPS_TEST_DATABASE_BASE_URL`, `ASSETOPS_REAL_OPERATOR_DATA=on` and an unrelated
variable, and assert the runner's environment has exactly the keys §3.5 lists for `harness_run`.

**L1 (Low, acceptance gap: output contract).** `cmd_check` (`tools/world.py:1095-1124`) prints one line per check but
not the closing `{"check": "ALL", "state"}` line §3.4's table names. The exit code carries the state, so nothing is
lost today; unit 3 or WK may read the line. Fix: emit it after the seven lines; one assertion in T9.

**L2 (Low, missing tests).** Three of my plants pass every test: (a) C4 `E` equality with a 0.01 tolerance
(`_equal`, `:886-893`; §3.6 says "no tolerance"); (b) `check_state` without the `manifest` part (`:627-638`;
D-DS4.21 names it); (c) C6 never reporting a gap (`:1075-1076`). (c) is unreachable while telemetry is none and its
functions are tested by T8 and T15-T17; (a) and (b) are one assertion each (an `E` value off by 0.001 fails; a new
blob id for the manifest YAML gives `check_stale: "manifest"`).

**L3 (Low, preference).** `C4_KNOWN_FINDINGS` marks every FAIL line at a named cell `known`, whatever the failure
(`:928`, `:940`). My probe: Kobo plan `tariff` at 9.99 against 0.4 is marked `known D-DS4.27`. D-DS4.27 accepts the
lines because "the cells are blank, never a wrong number"; a wrong number there would still FAIL C4 (state is safe),
but T12's "no `new` line" would not flag it. Consider marking `known` only when the product value is `None`.

**L4 (Low).** `current_l2` (`:606-620`): when the current-key L2 manifest exists but its database does not, the
refusal is `WORLD_TEMPLATE_STALE key` (no part differs), where `WORLD_NO_TEMPLATE` or a named "database missing"
reads better. Diagnostic text only.

**L5 (Low).** `cmd_check`'s `finally` (`:1113-1115`) calls `drop_db` even when `wait_idle` timed out; the server's
error then escapes as a traceback (not a code) and the L2 `check` block is not written. Safe (nothing forced), but not
a coded exit.

**L6 (Low, residual).** A partial L1 that failed after `onboard apply` (for example at `load`) is dropped and rebuilt
without erasing the tenant key it created (`_rung`, `:647-660`), so its key file stays live in the shared
`<key-root>/<L1>/` and a later `drop` reports `keys_left` 1. It is reported, never named or read, and only the
coordinator removes key directories; the spec does not ask for an erase here. Worth one line in the unit 3 runbook, or
an erase of the partial's tenants before its drop.

### Cover rule (step 7a), my own envelopes

At `Africa/Addis_Ababa` unless named: two points one local day: None. Last reading exactly at local midnight:
`local cover 2026-10-06..2026-10-06 differs at 2026-10-07` (as D-DS4.17 rules). First reading exactly at local
midnight: None. A single point at midnight: None. An interval ending exactly at local midnight (exclusive): None. That
interval plus a point the next day: None. A three-day interval alone: None. An interval over days 6-7 and a point on
day 9: `differs at 2026-10-08`. Mixed `+03:00`/`Z` offsets: None. Los Angeles across the 1 Nov DST change with a real
gap day: `differs at 2026-11-01`. Kiritimati: `utc ... differs at 2026-10-06`. Unsorted contiguous: None; unsorted
with a gap: refused. `envelope_span`: naive, `None`, int, bytes, list, bad text, a bare date, `+25:00`, `ZZ`,
non-ASCII digits each raise `BatchTimeUnreadable` naming the field; nothing else escapes. Step 7a sits after step 7
and before step 8 (`bulk_load.py:186-198`); the days come from `chain.events.local_days` and `S3_BRACKET`, imported.
Residual: year 0001 or 9999 instants raise `OverflowError` in `cover_gap` (the bracket leaves the calendar). The
contract's instant regex admits those years; the real path's consumer uses the same arithmetic, so this is not a new
hole, but it is a traceback, not a code.

### Plants of my own (scratch copy, each alone, reverted)

Caught: cover rule as subset only (T8 a); `B` passes on `None` without `missing` (T9 oracle); Kisiwa override applied
to the plan side (T9b); local grain only (T8 g); clean tree without the check code (T3); known marks never `new` (T9
known); `envelope_span` ignoring `interval_end` (T8 d); L2 not frozen (T5). Not caught: M2's inheritance plant and
L2's (a), (b), (c).

### Deviations (packet), judged

- T8 in `test_ds4_batch_days.py`: accepted. Pure, same cases (a)-(g) and the unreadable inputs; the file list in
  §0 does not name it, which is wording.
- The check block named `check_inputs` per §3.3: accepted. D-DS4.21 is the later ruling; §3.6's
  `derived_values_sha256` is stale text for the Architect to fix.
- T6's `tools/world.py` case through `list`: accepted. `tools/world.py` is a `code` key part (§3.2), so `clone`
  refuses the template first; the test shows the clone path with `pg_harness.py` and `code.tools/world.py` through
  `list` (`test_ds4_world.py:629-664`). The spec's T6 sentence cannot hold as written.
- The others (C4's detail an object, C6's SQL shape, a raising check as its FAIL, `site_timezone` not on the
  Protocol): fine.

### Follow-up after 5a F1 (`main` `a8a30426a`)

The branch was reviewed as it stands, with the 12 D-DS4.27 lines. Once DS4 merges `main`, the commit that brings
F1 in empties `C4_KNOWN_FINDINGS` (D-DS4.27: "removed in the DS4 commit that first merges `main` after F1") and
reruns T12 through `heavy-slot.sh --db`. Expected: C4 PASS, exit 0, `check.passed` true, and a blank list of exactly
the 123 §2.1 `B` cells. Any `new` line then (for example plan `necessary_l` not 2300 / 700 / 300) goes to the
Architect. The verification re-review checks this together with M1 and M2.

### What I could not verify

C5's real `pwsh` path (injected in T12; unit 3). C6's parse path on real batches (none exist). The builder's 34 plant
runs (I read the named tests and ran my own). Unit 3 is not built.

### Residual risk the packet does not name

M1 until fixed. L6's orphan key. The world check passes only while the definition's Sites are what `build` built;
the C2 and C3 checks are self-referential by design (they catch drift, not a wrong build).
