# W5-04a combined merge candidate re-review: V1a/V1b fix round, V2a fix round, V2b

Independent Reviewer (Claude), 2026-10-24. Branch `task/W5-04b-ev-work-ui` at `c8209474`. It contains the V1 fix branch
`task/W5-04a-fix` at `3a100f2f`, merged as `c3487ce3`. I read:

- the V1 diff `71e5cdc9..3a100f2f` and the V2 diff `9558a035..c8209474`. I separated the V2 diff into the V2a fix
  `35b01c25`, the V1 merge `c3487ce3` and V2b (`9bab4bfe`, `baae7c9f`, `c8209474`);
- the original reviews `.agent/W5-04a-review.md` and `.agent/W5-04-V2a-review.md`;
- readiness rulings 1–66 (mainly 25, 26, 39, 50–66), pre-flight rulings 23 and 34, and the build spec's fix lists and
  V2b card;
- the three handoffs, `.agent/W5-04-V2b-evidence/` (including `cold-k2-recapture/`), the v69 `ev-work` mock and
  `.ai/ROLE_CONFIG.md`.

I treated the handoff claims as claims to check. I did not edit review3, and I fixed nothing.

## Verdicts

| Unit | Verdict | High | Medium | Low |
| --- | --- | --- | --- | --- |
| **V1a** (schema, ports, selector; L5) | **ACCEPT** | 0 | 0 | 0 |
| **V1b** (index pin ruling 53, L1–L4, L6, portability) | **ACCEPT** | 0 | 0 | 0 |
| **V2a** (fix round Low-1 to Low-4, rulings 53/57) | **ACCEPT** | 0 | 0 | 0 |
| **V2b** (producer-backed `ev-work` captures) | **REVISE** | 0 | 1 | 2 |

V2b's one Medium (M1) concerns who seeds the worst-case data, not what the captures show. M1 closes in either of two
ways:

- move the seed into a V1b-owned walkthrough `worstcase` mode and recapture the two worst-case states, **or**
- get an explicit Architect ruling that waives pre-flight 23 for this seed (Architect item 1). With that waiver, V2b
  becomes ACCEPT with its two Lows.

The other merge gates still apply: the full backend suite now running on review3 must pass on this revision, and the
guards must pass on the merged head.

## Checks I ran (at `c8209474`, review3 read-only unless noted)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | Passed. |
| `tools/check-agent-workflow.ps1` | Passed. |
| `npx.cmd tsc --noEmit` (frontend) | Clean, rc 0. |
| Targeted vitest `--maxWorkers=1 --minWorkers=1`: `evWorkActions`, `coldWorkActions`, `siteWorkActions`, `w1f4ChangesWorkStructure` | 4 files, **102/102 passed**, 42.9 s. On this machine vitest started normally; the known esbuild sandbox failure did not happen. |
| DB-free pytest: `test_w504_ev_work_cases.py`, `test_w504_ev_intent_model.py` | **28 passed**. |
| Postgres, private base `assetops_w504rr_test`, PYTHONPATH set to review3's packages, `-n 2`: `test_w504_ev_intent_postgres.py`, `test_w504_ev_intent_api.py` | **20 passed**. JUnit tests=20, skipped=0, failures=0, errors=0. 530.6 s (8:53 wall), run while the full suite was also running. The DB was dropped afterwards; a `LIKE '%w504rr%'` query returns nothing. |
| Non-vacuity of the ruling-53 model test (in a throwaway worktree; reverted, tree clean) | Restoring the old `lineage = _Lineage(rx, known_at).resolve(actions)` makes `test_index_ev_intent_row_resolves_at_the_intent_pin_not_the_read_known_at` **fail**. |
| Walkthrough URL derivation (import only) | With `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:p%40ss@pg:5432/..._test`: `PG_ADMIN` is `postgresql://assetops:p%40ss@pg:5432/postgres` and the per-mode URL is `postgresql+psycopg://assetops:p%40ss@pg:5432/w504a_positive_x_test`. The password escaping is preserved. On Windows, `pid_alive(4)` is True and `pid_alive(999999)` is False. |
| V2b evidence (offline) | `w504b-evidence.log`: 199 PASS, 0 FAIL, 11 INFO; `failed: 0` in `w504b-measurements.json`. I read every capture's measurements and looked at four PNGs. I also diffed the cold recapture numerically against the last pre-rename baselines (see Focus 3). |

**What I did not run:**

- the full backend suite. The coordinator's run on review3 is the merge evidence, and **no same-revision full-suite
  result is cited in any handoff**;
- the full vitest suite and `vite build`. The implementer reports 2907 tests and a green build at `baae7c9f`;
- `test_w504_ev_work_producer_postgres.py` and the walkthrough CLI. I had a two-file limit, and this test creates
  `w504a_fx_*` DBs and live PIDs;
- the Linux-container run of the producer tests. The implementer reports 21 passed there;
- the browser captures. They need Chrome, the walkthrough APIs and a Vite server per API.

## Focus 1: V1 fix round (`71e5cdc9..3a100f2f`)

### V1 item 1 / ruling 53, the index row at the intent pin: closed exactly

`work/domain_action_index.py:450–463` now reads intents first. An EV row whose `_head` intent exists gets the cutoff
`min(head.recorded_at, known_at)`. Every other row, cold included, keeps `known_at`. `_Lineage` resolves once per
distinct cutoff. The source href, `_source_state`, and the fence entry (`frev if selected`, so also the selection
token) all come from that pin. The envelope `known_at`, the historical flag, membership, the cursor and the fence
shape are unchanged.

The tests cover the following:

- **Model test.** A later head displaces revision `R` for the no-intent EV row and the cold row, but not for the EV
  row with an intent. The test asserts the hrefs, the state counts, both requested cutoffs and the exact fence token.
  It also shows that a read before the intent uses only its own `known_at`. It is non-vacuous (see above).
- **Postgres test `test_ev_index_row_uses_the_intent_pin_and_no_intent_row_reads_known_at`.** After a real later head:
  - the row with an intent keeps the live href and its summary;
  - the no-intent row has a null href, and the envelope is UNKNOWN only because of that row;
  - the detail hrefs agree with the index hrefs;
  - historical reads before the intent, at it, and between the intent and the head are all HISTORICAL with live hrefs;
  - two `limit=1` pages succeed over the displaced snapshot and share the token.
- **API test.** With only the intent row, both the index and the detail read `CURRENT` after the later head, with the
  same non-null href. This isolates that row's status contribution.

The index takes its status from the pin, while the detail additionally re-checks `ev_basis`/`ev_selects_finding`.
Because an Action can only be raised on a SUPPORTED exact revision, and a revision's status is immutable, the two
agree whenever the pin exists. I found no reachable disagreement.

### L1, the EV conflict 409s: closed, and the declared_at body really hits the key/body 409 path

`domain_intent.py:146–150` takes the advisory lock and calls `intent_by_key` **before** the declared_at bound, basis,
root and supersedes checks. Same key with a different `declared_at` means a different `command_sha256` while `prior`
exists, so it is refused at line 150 and nothing later is reached. This is the key/body `DOMAIN_INTENT_CONFLICT`, not
the second-root conflict at line 162, even though both carry the same literal. The new body
(`now − 2 min`) is still inside the command window, so it is a valid body that differs only in hash.

The handoff's reason for the change is correct: reversed criteria are a 422 shape error and would never reach the key
lookup. The test also covers:

- Action key/body (line 88);
- second root (line 162);
- stale `supersedes_id` and supersedes of a non-head (line 164);
- a repeated exact case link under another key (line 246);
- the case-link basis change (409 `BASIS_CHANGED`).

Each case asserts `counts()` afterwards. The API test repeats the Action key/body and second-root 409s over HTTP.

### L2 / ruling 55, the backdated vector and the DB-time vector: closed, and ruling 55 is not weakened

The existing vector is labelled BACKDATED in its docstring and inline. The new
`test_ev_db_time_disposition_after_the_intent_leaves_the_pin_fixed` does the following:

- stamps `decided_at = clock_timestamp()` (new `db_time` keyword in `ev_depth_cases.add_import`);
- asserts `decided > intent.recorded_at`;
- compares the pin at `recorded` before and after with only the `state` key removed: revision, run window, seqs and
  `evidence_cutoff` are equal, and `evidence_cutoff <= recorded`;
- asserts the shared cutoff did advance (`pin_at(now).evidence_cutoff == decided`);
- checks that the detail `status`, `selection_token`, `intent`, `results`, `source_provenance` and `links` are equal.

**Decision on removing `state`:** this does not weaken ruling 55. The status that ruling 55 fixes is the Action's
status, which is the **detail** `status`. The test asserts it unchanged. The pin's own `state` word is currentness
relative to the site-wide watermark. Reading a fixed cutoff after the watermark has advanced makes that word
HISTORICAL by definition. The test does not hide this: it asserts it explicitly as `("CURRENT", "HISTORICAL")`, so a
regression in either direction would fail. `link_state` maps HISTORICAL to CURRENT for a non-historical read
(`link_coverage.py:71–80`), which is why the detail status holds.

One possible tightening, which is a preference and not counted as a finding: assert `detail0["status"] == "CURRENT"`
literally rather than only through equality.

### L3, cold-Site vectors: closed

Both `test_w502_domain_intent_postgres.py` and `test_w502_domain_intent_api.py` post two full otherwise-valid bodies to
the **cold** Site:

- an `EV_CHARGING` body is refused 422 `DOMAIN_INTENT_LINK_INVALID` with the EV literal;
- a `MINIGRID` body is refused 422 with `NEUTRAL_DOMAIN_INVALID`.

Both assert `counts == [0,0,0]`.

### L4, complete zero: closed

`zero_reads_complete` now requires empty rows, an integer `total_count == 0` that is not a bool and not absent, and
`next_cursor is None` on both reads. The unit test covers each bad shape on either side.

### L5, cold half of the ruling-32 cutoff: closed by disclosure

The fix list allowed either disclosure or a new test. The handoff states the limit exactly: no cold pin or link is
read, there is no `link_coverage` read, the cold and EV paths share `_ReadTx._cold_ev`, and the builder's mutation
failed the test.

### L6 and portability: closed. The new code works on Windows and in Linux, and kills only recorded, verified PIDs

**`_stop_owned`** (`tools/w504_ev_work_walkthrough.py:652–658`) kills only when all of the following hold:

- the recorded entry has a `port`;
- the live PID's command line still contains `uvicorn`, `serve_entry:app` and `--port <recorded>`, with a word
  boundary after the port.

`serve` records `{pid, port}` for every server (line 530), and its command line is
`python -m uvicorn serve_entry:app --host 127.0.0.1 --port N`. So our servers match, and a reused PID does not.

**Windows:**

- liveness uses `tasklist /FI "PID eq n"`;
- the command line comes from CIM;
- the kill is `taskkill /PID n /T /F`. A venv launcher's child dies with its tree.

**POSIX:**

- liveness uses `kill 0` plus a zombie check in `/proc/<pid>/stat`;
- the command line comes from `/proc/<pid>/cmdline`;
- the kill walks `/proc` parent links for descendants of the verified PID only, deepest first, with SIGKILL. No
  `pkill` or image-name match is used.

`drop` drops a stale entry without killing it and logs it. `attest` records `stopped_pid: null` if it did not stop the
unavailable API, and V2b's tool then **fails** its "unavailable stopped by attest" claim, so the gate is not vacuous.

**Database URLs.** `PG_ADMIN` and the per-mode URLs derive from `ASSETOPS_TEST_DATABASE_URL` when it is set, using
that server, port and credentials with the admin database `postgres`. Otherwise they use the compose defaults. The
admin connection still only CREATEs/DROPs marker-listed `w504a_*_test` names.

**Tests.** The unit test covers `is_recorded_server`, and it checks that `_stop_owned` skips a non-matching line and a
missing port. The Postgres drop test records one process that looks like ours (killed) and one unrelated live PID
(it must survive). That is stronger than the original test.

**Residual risk.** A URL with a query string, such as `?sslmode=`, would break the `_PG_URL_PREFIX + name`
concatenation. Neither the harness nor compose uses one.

### Rulings 54 and 56

- **54:** the V2b packet names pending, stale and unknown as unavailable, with the producer limits.
- **56:** the port is left bound and unused, with no cleanup.

Both are satisfied.

## Focus 2: V2a fix round (`35b01c25`): every Low is closed

### Low-1: closed exactly

`workAttrs(..., value?)` now renders the cold `data-cold-work-*` attribute as `"true"` when no value is passed, and
the domain attribute as `""`. The notice passes an explicit `""`.

I checked this against base `a0883773`:

- K2's notice was the only explicit `""`: `data={{ "data-cold-work-notice": "" }}`.
- Every other presence-only cold attribute was a bare boolean prop, so it rendered `="true"`.
- No current call passes `""` except the notice.

`coldWorkActions` asserts ten names as `"true"`, each domain twin as `""`, and the notice as `""`. Under the
pre-fix code these assertions would read `""` and fail.

### Low-2 and Low-3: closed

- **Low-2.** `EV_WORK_PRESENTATION.domainActionLink = EV_ACTION_LINK_LIVE`.
- **Low-3, pager.** The test shows Next pins the response `known_at` and the cursor, and First drops the cursor and
  keeps `from` and `to`.
- **Low-3, 409 restart.** The 409 `WORK_BASIS_CHANGED` panel shows `EV work unavailable` with the server message, and
  Retry drops the cursor and keeps `known_at`.
- **Low-3, ruling 57 interim.** The EV case tab has no `data-domain-work-window` and exactly one `form`.
- **`siteDetailRoute`.** It remains a regression run with no new vector, as the fix list says.

### Low-4: closed by the Architect

R75 and R77 are amended in the register exactly as rulings 59 and 60 say (`mock-departure-register.md:130,132`).

### Ruling 53 on the UI side

The fixture doc records the intent pin. `evPinUnavailableRow()` adds the honest `href: null` row. The new test shows
the Source as supplied, either pinned (CURRENT, no notice) or unavailable (UNKNOWN, with a notice). Neither case
renders an anchor or any list/detail disagreement copy.

### Scope

`9558a035..c8209474` touches only these four frontend files. V2b changes no product code.

## Focus 3: V2b

### Mock fidelity at 1440/390 and the final caps

I read every capture from `w504b-measurements.json` and looked at the 1440 positive, 390 worst-folded and 1440
`unavailable-503` PNGs. The structure matches v69 `ev-work` (`index.html:337–343`) and the labelled departures:

- breadcrumb, stored name, R78 subtitle and the Work subtabs;
- the page-local Window after the subtabs (R112). It has the UTC labels (R77), is right-aligned at 1440 and full
  width at 390;
- `Scoped to EV · n actions` with the EV gap text and no link (R79/R111/R04);
- `Actions at this site` with `Due dates are not yet set` (R76) and the six mock columns;
- the plain EV code (R113) and `Finding {id8}` with `Finding version` (R74/R75);
- the amber `Open` badge, the mock criterion and the closing notice (R03).

All closed-state heights (1440 / 390) are under the ruling 25/50 caps:

| State | main | strip | Actions panel | notice |
| --- | --- | --- | --- | --- |
| positive | 568 / 722 | 39 / 61 | 184 / 199 (mock 183 / 230) | ≤ 60 |
| historical | 628 / 782 | | 184 / 199 | currentness 42 / 42 |
| zero | 646 / 805 | | 262 / 282 (cap 460 / 560) | |
| forbidden-403 | 582 / 721 | | 198 / 198 | |
| worst-folded, 5 rows | 864 / 1003 | | 480 / 480 | |

There is no document horizontal overflow at either width. At 390, the table scrolls inside its panel (821 px in
318 px) with a sticky first column.

The expanded states are measured and reported but not gated, as rulings 26 and 51 require:

- worst-expanded: 1200 / 1409;
- window-error.

### Honest unavailable vectors

- **Pending, stale and unknown.** Each appears as an INFO line ("browser capture unavailable (ruling 54; pure
  component vector)") with the manifest's reason. They are pure vectors in
  `evWorkActions.test.tsx:305` (PENDING_RECOMPUTE / STALE_SOURCE tones, plus HISTORICAL and UNKNOWN), and UNKNOWN
  also appears in the new ruling-53 test.
- **In-panel EV 503.** It is a pure vector (`evWorkActions.test.tsx:327`, 403/503).
- **The `unavailable-503` capture** is the Site-level `Site unavailable` page. It is labelled that way in its INFO line
  ("Site-level refusal, not an in-panel EV 503"), in the tool header and in the handoff. Its only claims are no rows,
  no zero and no overflow.
- **Backdated vector.** None is used or presented as a late decision (ruling 55).
- **160-character error text.** It is disclosed as not producible.

### Cold K2 recapture after the CSS rename (ruling 62)

The handoff reports 461 PASS and 934 PASS, the same totals as the earlier runs. Matching totals do not prove "changed
nothing", so I diffed the measurements numerically:

- **Cases (`w502b-k3-measurements.json`) against the post-K4 baseline `W5-02c-K4-evidence/cases-recheck`**
  (`de57ee51`, after K4 and before the rename): **0 numeric differences** across all states and both widths. This is
  strong evidence that the rename left the shared case surfaces unchanged.
- **Actions (`w502b-measurements.json`) against the last pre-rename Actions run `W5-03b-ui-evidence/cold-actions-recheck`**
  (`d7397e36`): 19 numeric differences.
  - 13 are `scrollerScrollWidth` changes of 2–8 px at 390, where random UUIDs and Finding IDs differ per run.
  - 3 are `action-positive` main/docHeight (340→755 and 455→1115). They come from K4's Action detail, which merged
    after `d7397e36`.
  - 4 are `worstcase-expanded-open` at **1440 only**: every row is +18 px, the panel goes 731→819 and main 1115→1203.
    These are not explained in the packet (Low-2).

### Are the capture claims non-vacuous?

Yes:

- Row claims require `rows.length > 0` and `cells.length > 0`.
- The badge claim requires `badgeCount > 0`.
- The preview and summary claims fire on non-empty sets: worst-folded has 8 previews at two lines each and 12
  summaries at one line each.
- The full-text claim requires `full.length > 0` (values 160 and 173).
- The seed claims require 201/200 for each POST: four Actions and four intents, all 201, IDs recorded.
- The "unavailable stopped" claim requires a non-null `stopped_pid`.

### Findings

**M1 (Medium, contract/ownership departure): the evidence tool writes producer data, which pre-flight 23 forbids.**
`tools/w504-ev-work-evidence.mjs:322–364` (`SEED`, `seedWorstCase`), called at line 437.

- **What is wrong.** Between its two phases, the tool spawns a Python child. The child imports
  `w504_ev_work_walkthrough`, sets `DATABASE_URL` and posts four Actions and four intents into the walkthrough's
  positive DB with the SERVICE principal.
- **The rule.** Pre-flight ruling 23 says: "V1b owns `tools/w504_ev_work_walkthrough.py` … `prepare` emits positive and
  zero fixtures …; V2b/V3b/V4b consume its manifest; **`.mjs` only captures**." Readiness 1–66 do not supersede this:
  - ruling 25 gives V2b/V3b/V4b "capture scripts";
  - ruling 31 keeps the producer in V1b;
  - ruling 39 makes V2b consume V1b's manifests.
- **Precedent.** The W5-02 cold walkthrough has `worstcase` as its own DB mode
  (`tools/w502_cold_work_walkthrough.py:25,71`).
- **Why it matters:**
  - After the seed, the positive DB no longer matches the walkthrough manifest (1 Action against 5 on the page).
  - The capture tool becomes a second producer, with a Windows-only interpreter path and a private `_clients` import.
  - V3b and V4b extend this same `.mjs` (their file lists name it), so they would inherit a write path, and their
    captures would depend on whether phase B had already run against the shared DB.
- **What is not wrong.** The data is genuine: it goes through the public sole writer, uses no SQL and no test import,
  every status and ID is recorded, phase A was captured before the seed, and the builder disclosed it as a judgment
  call.
- **Fix (recommended).** Add a V1b-owned `worstcase` mode to `tools/w504_ev_work_walkthrough.py`:
  - its own `w504a_worstcase_<tag>_test` DB and port;
  - the same native replay, then five Actions with intents through the same SERVICE path, with 160-code-point title
    and owner;
  - manifest entries with every ID.

  Drop `SEED`/`seedWorstCase` from the `.mjs`, point phase B at the `worstcase` process, and recapture worst-folded and
  worst-expanded at both widths. Phase A captures do not need to be redone.
- **Alternative.** An explicit Architect ruling waives pre-flight 23 for this V2b seed and says whether V3b/V4b may
  reuse it (Architect item 1).

**Low-1 (Low, cap labelling, ruling 50): the non-loaded refusal is measured against the positive-panel cap.**

- **What is wrong.** `tools/w504-ev-work-evidence.mjs:422` calls `caps(W, "forbidden-403", m, wi)` with the default
  `CAPS.panel` 650/850, and the handoff table reports it the same way. Ruling 50 and build spec line 82 cap the closed
  non-loaded state panel at **360/590** and say "V2b/V4b report these states at both widths".
- **Why it is Low.** The measured 198 / 198 is inside 360/590, so no cap is actually missed.
- **Fix.** Pass `panelCap: [360, 590]` for the refused state, or have the Architect confirm that the titled
  `Actions at this site` panel holding a refusal falls under 650/850 rather than ruling 50's "untitled" cap
  (Architect item 2). Either way, update the handoff table.

**Low-2 (Low, evidence claim): "the cold layout is unchanged" rests on equal PASS totals, and one Actions delta is
not explained.**

- **What is unexplained.** `cold-k2-recapture/w502b-measurements.json`, state `worstcase-expanded-open` at 1440,
  against `W5-03b-ui-evidence/cold-actions-recheck`:
  - every row is +18 px (119→137);
  - the panel goes 731→819;
  - main goes 1115→1203.
- **Why it is probably harmless:**
  - This is a ruling-24/26 expanded state, so it is not gated.
  - The same state at 390 is unchanged.
  - The recapture PNG's rendered rows match the baseline PNG. In the new PNG, about 140 px of blank space follows the
    closing notice, which suggests the measurement was taken mid-toggle rather than reflecting a CSS change.
- **Fix.** State the numeric diff in the packet: cases 0, Actions limited to the IDs, K4 and this one state. Then
  explain it, or rerun that one state to show it is timing.

## Focus 4: worst-case seeding decision

**Recommendation: move the seed into a V1b-owned `worstcase` walkthrough mode (M1).** It is not acceptable as built
without an Architect waiver, for three reasons:

1. Pre-flight 23 is an explicit binding rule ("`.mjs` only captures") that no later ruling supersedes.
2. The cold precedent (W5-02 `worstcase` mode) shows how the project does it.
3. V3b and V4b share this tool and need the same worst-case fixtures (five rows, 160-character case values). Putting
   them in the walkthrough serves all three units and keeps the manifest a full description of each DB.

The seeding is otherwise honest. A waiver would not hide a capture defect, so the Architect may reasonably choose that
route if speed matters more.

## Focus 5: implementer decisions and departures

- **V1 fix round:** no new decisions. The two second-pass test changes (L1 body, L2 `state`) are explained and
  correct.
- **V2a fix round:** none.
- **V2b:**
  - The seed (M1) is the one new implementer decision. It is labelled, but it contradicts pre-flight 23.
  - The zero capture uses the zero DB over `[W.from − 1 day, W.from)`. That is a genuine successful-zero read, and it is
    labelled in the handoff table. I accept it.
  - The Site-level `unavailable-503` capture is labelled.
- **Unlabelled visual departures:** none found.

## Items for the Architect

1. **M1:** either require the V1b `worstcase` walkthrough mode (recommended) or rule an explicit waiver of pre-flight
   23 for the V2b in-tool seed, and say whether V3b/V4b may reuse that seed.
2. **Ruling 50 scope:** does the Work list's in-panel refusal (inside the titled `Actions at this site` panel) take
   the 360/590 "untitled non-loaded state panel" cap or the 650/850 positive-panel cap? The measured 198/198 meets
   both.

## Residual risk the packets do not name

- No handoff cites a same-revision full backend suite for `c8209474`. The coordinator's run on review3 is the only
  such evidence, and I have not seen its result.
- `_server()` builds per-mode URLs by string concatenation. A harness URL with a query string would produce a broken
  DB name. Today's URLs have none.
- The V2b captures exercise only `Etc/UTC` (R77 defers non-UTC Sites), and only one Finding revision, which every
  seeded Action shares.

## Coordinator verification of V2b re-review closure (2026-10-24)
M1: seeding removed from tools/w504-ev-work-evidence.mjs (capture-only); walkthrough worstcase mode added with producer test. Low-1: 403 panel at ruling-50 360/590 (198/198). Low-2: cold worstcase-expanded-open 1440 back to baseline 119/731/1115 (INFO). EV recapture 195 PASS/0 FAIL; focused w504 Postgres 52; tsc clean; targeted vitest 247; check-all 11/11. Verdicts: V1a, V1b, V2a, V2b ACCEPT. Full backend suite on c8209474: 4040 passed + 1 known schedule-tick flake (passes alone); the closure touches only tools and one test.
