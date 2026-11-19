## 9j2. Ruling DIESEL-1-R3j2: K4b pre-flight stop S-a (the chain graph refuses `FINDING:UNEXPLAINED_FUEL`)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). READ on main at `c1324273b` (the K4b worktree base; K4a, K6a, K6b merged) and on `task/DIESEL-K5-fuel-screens` (not merged). Nothing was run.
- **This ruling amends §9j.11–§9j.13 and §9l.4's K4b bullets.** Everything not named here stands.

### 9j2.1 The stop (READ, confirmed)

- `chain/graph.py:159-160` rejects an `ENTRIES` key `FINDING:<m>` unless `<m>` is a key of the thread-lifecycle `clean_day_measures` (`chain_keys`, `:107-111`, through `thread_signal_key`). The check runs at app start (`main.py:644`), in `test_ch5b_graph.py::test_main_config_passes` and in `chain_graph_render`.
- `config/chain/thread-lifecycle-v1.json` has no `UNEXPLAINED_FUEL` key, and `parse_thread_lifecycle` (`chain/lifecycle.py:101-103`) rejects an empty list.
- §9j.11 adds the map entry and never names the lifecycle side. That was an Architect miss in R3j, not a builder error. It is recorded as D3 (structural oversight).

### 9j2.2 Decision: route (b), an explicit empty clean-day list

**Options weighed:**
- **(a) A real fuel clean-day measure** (a chain measure such as "night accounted for within the margin", register input, adapter, snapshot rows, lifecycle entry). **Rejected for the demo.** It is about 0.6–0.9 of new chain work. It would also change how the fuel thread closes (after N clean nights), and nothing in K6b's verdict or K7's story depends on that. It goes on the after-the-demo list: "fuel clean-night measure, so a verified fuel thread can close".
- **(b) An empty list is a valid declaration. Chosen.**
  - Runtime is unchanged. `measures_for` already returns `()` for a missing mechanism (`lifecycle.py:74-75`), `complete_days` returns `set()` for no measures (`:293-294`), `used_measures` uses `.get` (`why.py:91`), and `postgres_thread_sources.py:192`/`:269` take a union in which an empty list adds nothing. The fuel thread behaves exactly as it does today on main.
  - It is honest. It says in configuration what is true: this mechanism has no clean-day measure, so its thread never closes on clean days.
  - It is consistent with how a fuel thread is meant to end. K4a's lifecycle withdraws an Action-less thread when support is lost (`OPEN` + `SUPPORT_LOST` → `WITHDRAWN`, `lifecycle.py:57`). K6b's verdict drives `CHANGE_APPLIED` → `RESOLVED_MONITORING` on VERIFIED, or `REOPENED` on INEFFECTIVE / expired INCONCLUSIVE. A later UNEXPLAINED night is a new occurrence on the same thread, so `RESOLVED_MONITORING` → `RECURRED`. None of these needs a clean-day measure. The only transition the fuel thread cannot take is `RESOLVED_MONITORING` → `CLOSED` (`CLEAN_DAYS`), and with (b) that is a declared fact rather than an accident.
- **(c) Let the graph accept a `FINDING:` key with a `NOT_CHAIN_SOURCED` row.** **Rejected.** It widens a guard whose purpose is that every Finding mechanism has a lifecycle. A `FINDING:` key that the threads step does handle (it does, through `SUBJECT_COLUMN`) would be mislabelled "not chain-sourced".

**The policy version stays `thread-lifecycle/1`.** The effective policy is identical for every mechanism, including `UNEXPLAINED_FUEL` (empty before by default, empty now by declaration). No stored event changes meaning.

### 9j2.3 Exact changes for S-a (K4b)

1. `B/chain/lifecycle.py` `parse_thread_lifecycle`, the per-mechanism check (`:102`):
   - becomes `if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names):` (the `or not names` term is removed). The error message is unchanged.
   - Comment above the loop, verbatim: `# DIESEL-1-R3j2: an empty list declares a mechanism with no clean-day measure; its thread never closes on clean days (it stays RESOLVED_MONITORING until a recurrence).`
   - The top-level "must be a non-empty object" check (`:98-99`) is unchanged.
2. `config/chain/thread-lifecycle-v1.json`: `"UNEXPLAINED_FUEL": []` added as the **last** key of `clean_day_measures`. No other byte changes.
3. `B/outcomes/outcome_map.py` `ENTRIES`: `"FINDING:UNEXPLAINED_FUEL": (("MG-8",), ()),  # DIESEL-1-R3j: no mock F-id (MD-FUEL-K4-1)` placed **directly after** `"FINDING:EV_INTERRUPTION"`. The group comment `# stored Finding mechanisms (the four that exist)` becomes `(the five that exist)`.
4. `Docs/demo-sprint/chain-graph.dot` and `.svg` regenerated with `chain_graph_render` (no hand edit). The mechanism node has no measure edge; that is correct.
5. Tests:
   - `test_ch5b_graph.py:31` becomes `"chain graph OK: 7 measures, 6 lifecycle mechanisms, 16 outcome-map entries"`. The mutation table is unchanged (its "Finding without lifecycle mechanism" case still fires).
   - `test_ch6_contributions.py` `ENTRIES_TODAY` gains the same line in the same position.
   - **New L0, in `test_k4b_protect_fuel.py`:**
     - `parse_thread_lifecycle` accepts `{"X": []}` and gives `measures_for("X") == ()`; it still raises `ChainConfigError` for `{"X": "a"}`, `{"X": [""]}` and `{}` (must fail if the list-type check is dropped too).
     - `load_thread_lifecycle().measures_for("UNEXPLAINED_FUEL") == ()` and `"UNEXPLAINED_FUEL" in load_thread_lifecycle().clean_day_measures` (must fail if the config line is removed: the graph check then raises `entry_source`).
     - `check(chain_graph_inputs())` passes (the app-start check).
   - `test_ch3_lifecycle.py`, `test_ch2_threads.py`, `test_md0b_ensure.py` and the CH-5a2 contract goldens stay green unchanged. The goldens hold no fuel thread, so the new key cannot reach them. Any change there is stop S-b.

### 9j2.4 The fuel thread line after a verdict (honesty guard)

- After K6b's VERIFIED, the fuel thread sits in `RESOLVED_MONITORING` and never closes. `THREAD_MONITORING` ("… · {k} more fully checked days to close") would then promise a countdown that never moves.
- Today that line cannot appear for the fuel thread: `_thread_action` (`board.py:725-732`) looks only at W1 `ActionFact`s, and the fuel Action is a domain Action. The verdict reaches the board as the Assure contributor (`FuelVerdictFact`, K6b). K4b keeps it that way with a guard, so a later change cannot produce the false countdown:
  - `B/site_outcomes/mini.py`: a fuel `FindingFact`'s `lifecycle_view` is `{**view, "close_measured": False}` when `ct.policy.measures_for(mechanism) == ()`. Dispatch views do not get the key.
  - `B/site_outcomes/board.py` `thread_line_item`, first line of the `if f.thread.get("verified"):` branch: `if view.get("close_measured") is False: return None  # DIESEL-1-R3j2: no clean-day measure, so no countdown; the verdict is the Assure contributor`.
  - L0 test: a fuel `FindingFact` with a verified thread **and** an `ActionFact` on that thread gives `thread_line_item(...) is None`; the same fact without `close_measured` gives a `MONITORING` item (non-vacuous). Must fail if the guard is removed.
  - Every dispatch, Cold and EV thread line stays byte-equal (no `close_measured` key).

### 9j2.5 Answers to the builder's other questions

1. **`site_outcomes/composition.py`: approved.**
   - `build_outcome_board_service` builds `fuel_balance = build_fuel_balance_store(database_url) if database_url else None`, with a function-local import from `assetops_backend.fuel_balance.composition` (this avoids an import cycle through `work.composition`). It passes `fuel_balance=fuel_balance` to `BoardServices`, and `dispose()` calls `fuel_balance.dispose()` when it is not None.
   - `BoardServices` (`read.py:87`) gains `fuel_balance: Any = None` as its **last** field, with the comment `# PostgresFuelBalanceStore (DIESEL-1-R3j2; K4b's fuel_windows/fuel_findings/has_windows)`.
   - `read.py` `mini_ports` binds `fuel_windows`, `fuel_findings` and the applicability read (`has_windows`) from it. If it is None, the port raises `PortUnavailable` as every other `BoardServices` port does, and `Reads` records PARTIAL. It is never a "0" or "not applicable" claim. **Exception, so Kobo stays byte-equal:** MG-8's `not_applicable` comes from `has_windows`. If that read fails, MG-8 is `UNKNOWN` (`findings_ok` rule), never N/A.
   - `test_out_b4_imports.py` stays unchanged and green (only `composition.py` imports another composition).
2. **The K5 code (store methods, `night_text.py`, `fuel_finding_ref`): no byte-for-byte copies.**
   - **Why:** K4b needs more of K5 than the builder listed. §9l.4 also requires `refs.fuel_finding_ref` and the `FUEL_FINDING` ref kind, which on K5's branch come with frontend counterparts (`linkRefs`, the client href builder). K5's `FUEL_REASON_WORDS` is already amended against §9j.11 (the guard-V-safe "no-load" wording), and K5 still has captures pending. Copies of a moving branch drift, and a partial copy of the store file (two of K5's three methods plus its import) is a real conflict, not a trivial one.
   - **Order:**
     - **Now:** K4b builds everything that does not need K5: §9j2.3, §9j2.4, MG-8 and applicability plumbing, the composition and ports (with `night_context`/`has_windows` calls written against K5's signatures as read above), the claims exclusion (§9j2.5 item 4), the Portfolio card keys and frontend, UF1 and KIS-8a, and their tests with fake ports.
     - **Preferred:** K5 merges to main, and K4b runs `git merge main` at its next commit boundary. It then imports `night_context`, `has_windows`, `FUEL_REASON_WORDS` (from `fuel_balance/night_text.py`) and `fuel_finding_ref` as they stand on main.
     - **Fallback**, only if K5 has not merged when K4b's K5-independent work is committed: the coordinator may tell K4b to `git merge task/DIESEL-K5-fuel-screens` (a real merge at K5's accepted head). K4b then **must not merge to main before K5 does**, and it merges main again before its packet.
     - In neither case does K4b edit a K5 file.
   - **New stop S-f:** K4b needs a change inside a K5 file (signature, literal or ref kind). Report it; K5's owner fixes it on main.
3. **The Protect category count: intended in K4b.** It does not wait for K8.
   - Once mapped, the fuel thread's primary category is Protect everywhere `outcome_roles` is read: `estate/portfolio.py:297` `category_counts` (`open_findings` and `sites_with_primary_finding`), the Findings lens chips (`lens_flags`) and thread `categories`. Kisiwa's Portfolio Protect count rises by one while an unexplained-fuel Finding is open.
   - That is true, and it is the purpose of the mapping. Holding it back would need a mechanism filter in `category_counts`, which is a special case that hides a real Protect finding.
   - **Goldens:** no Kobo, Cold or EV golden holds a fuel Finding, so §9j.13's golden acceptance stands unchanged. The Kisiwa effect first appears in K7's data. **K8** re-expects it in its COH rows and the all-26 recapture. The K8 card gains one line: "Kisiwa Protect `open_findings` +1 while the night-4 thread is open (R3j2)".
4. **`claims.disrupting`: exclude `UNEXPLAINED_FUEL`. Confirmed.** Unexplained fuel is a loss-of-stock finding, not a service disruption. `SITES_DISRUPTED` must not count it.
   - `B/chain/claims.py`: `NOT_DISRUPTION_MECHANISMS = frozenset({"UNEXPLAINED_FUEL"})  # DIESEL-1-R3j2: a stock finding, not a service disruption` beside `DISRUPTED_STATES` (`:41`). `disrupting` (`:112-114`) gains `and t.get("mechanism") not in NOT_DISRUPTION_MECHANISMS`. The thread wire carries `mechanism` (`site_chain.py:81`). Both callers (`claims.py:148`, `chain_api.py:379`) take the exclusion with no edit.
   - L0 test: an `OPEN` primary-Protect thread with `mechanism` `UNEXPLAINED_FUEL` is not in `disrupting(...)`; the same thread with `COLD_EXCURSION` is (must fail if the predicate is removed).
   - `threads.classify` (open/in-hand/verified counts) still includes the fuel thread, as §9j.11 says.

### 9j2.6 Approved files (added to §9j.13)

- `B/chain/lifecycle.py` (the `:102` predicate and its comment only)
- `config/chain/thread-lifecycle-v1.json` (one key)
- `Docs/demo-sprint/chain-graph.dot`, `Docs/demo-sprint/chain-graph.svg` (regenerated)
- `B/site_outcomes/composition.py` (the store, the field and the dispose)
- `B/chain/claims.py` (now required, no longer conditional)
- `backend/tests/test_ch5b_graph.py` (the count line), `backend/tests/test_ch6_contributions.py` (`ENTRIES_TODAY`)
- `B/site_outcomes/board.py` and `mini.py` were already on the list; the §9j2.4 guard is in scope.
- **Removed from §9l.4:** "K4b starts after K5's phase B build" is replaced by the order in §9j2.5 item 2.

### 9j2.7 Size, stops, critical path

- **K4b: 1.0 → 1.1** (range 0.95–1.3). That is +0.1: the S-a route and its tests 0.04, the thread-line guard 0.02, the claims exclusion 0.02, the composition field and dispose 0.02. **Stop S-e's ceiling becomes 1.3.** The increase is reported, not absorbed: **Kisiwa total +0.1.**
- **Critical path:** K4b stays off it. Lane 1 (K5 merge → K4b 1.1 → K8 → captures) was about 8.15–8.4; with +0.1 and a short wait for K5's merge it is about 8.3–8.6. That is still below the main path of **about 9.0**, which is unchanged. **Headroom to the 9.75 tripwire: about 0.75.** No cut is needed and the demo date does not move.
- **After-the-demo list (coordinator):** "fuel clean-night measure, so a verified fuel thread can close".
- **Plan HTML rows (coordinator):** K4b becomes 1.1. The rulings table gains "DIESEL-1-R3j2: `UNEXPLAINED_FUEL` declared with no clean-day measure (thread never closes on clean days); fuel thread excluded from `SITES_DISRUPTED`; Kisiwa Protect count +1 while open; K4b imports K5 after K5 merges (no copies); K4b 1.1".

### 9j2.8 Owner questions

None. For the owner's information, in plain words: the system has a rule that every kind of finding must say how it is closed. The unexplained-fuel finding had no such rule yet, so the system would have refused to start. It now states openly how this finding ends. It is withdrawn when a later check no longer supports it. Once a fix is verified, it stays under watch and comes back if fuel goes missing again. It does not yet close by itself after a run of clean nights. While the finding is open, Kisiwa's "Protect" count shows one more item, which is true. That count is not presented as a service outage. The work grows by a tenth of a unit, and the demo date does not move.

---

## 9o. Ruling DIESEL-1-R3n: after K7-D's scratch prepare (E3 timing, the KOBO-001 404s, KIS-3's evidence, K7-F start)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. READ on main at `c5b25066c` and on `task/DIESEL-K7-kisiwa-story` at `63f60f986` (packet `.agent/review-packet-K7.md`; `tools/demo_combined.py:404-633`; `tools/demo_combined_rows.py:526-590`). Nothing was run.
- **This ruling amends §9l.3 (K7-F, the scratch prepare, `EXPECTED_SECONDS`), §9l.5's E3 lines and §9m.6's path.** Everything not named here stands.

### 9o.1 E3 timing, restated from measured figures

- **Measured:**
  - three-Site whole-list prepare: 3585 s (DD-1b2b);
  - Kisiwa build step (Kisiwa-only scratch): 3568 s (10 days at 315–382 s, mean about 353 s; register 2 s);
  - Kisiwa-only total: 4199.5 s, so the shared tree, finish, ticks and prebuild cost about 630 s, and they are already inside the 3585 s.
- **Four-Site estimate:**

  | Part | Seconds |
  |---|---|
  | Three-Site prepare as measured | 3585 |
  | Slack for K4b/K5/K6 reads in the ticks and prebuild since DD-1b2b | 0–300 |
  | Kisiwa build, as measured | 3568 |
  | Slack for Kisiwa days built last, on a database that already holds Kobo, Cold and EV (up to +15%) | 0–535 |
  | Kisiwa's share of the shared steps: mini-depth drain, two ticks and prebuild with a fourth Site, KIS rows in the self-check | 150–400 |
  | **Total** | **about 7300–8390 s, 2.0–2.35 h** |

- **Margin against the 3 h cap (10800 s): about 2400–3500 s (0.65–0.95 h, 22–32%).** The top of the range is about 600 s under the 2.5 h (9000 s) re-ruling trigger. **It fits. It is not close to 3 h, so there is no owner question.**
- **Parallel: no.** Kisiwa installs after all three core Sites (§9l.3 install order), every step writes one database at story instants, and the K7-D run's lowest free RAM was 1.91 GB with a single job against the 1.0 GB floor. A second concurrent child would break the "one heavy job" gate and risk the floor.
- **Trim: none.** Every per-day step is a guard or a product write (publish and accept, the physics and dip checks, assess, raise). None is cut to save time. If K9's rehearsal exceeds 2.5 h, the first lever the Architect will weigh is profiling the per-day cost (where the 353 s go against K1/K3's 180–300 s). It is not parallelism and not a cap raise.
- **`EXPECTED_SECONDS["kisiwa"]` becomes 3600** in K7-F (10 × about 353 s, plus register, assess and raise; replaces 2520). Comment: `# DIESEL-1-R3n: measured in K7-D's scratch prepare (3568 s build step)`. This only feeds the default 2× cap; E3 and the rehearsal pass `--cap-seconds 10800` explicitly.
- **K9's rehearsal, restated:** a four-Site whole-list prepare on its own `*_test` database with `--cap-seconds 10800`, keep-awake on, about **2.0–2.35 h** of machine time (was about 1.5 h). It is machine time outside K9's 1.0 lane-units, as before. K9 restates E3 from the rehearsal's measured wall time. **Stops stand:** above 9000 s, the Architect rules before E3. If the run reaches the 10800 s cap, the cap is never raised silently: a higher cap or a cut goes to the owner.
- **The first four-Site run is K9's rehearsal.** It is also the first run in which Kisiwa sits beside the core Sites in the full self-check. A non-KIS row that fails only because Kisiwa is present (estate or Portfolio counts, COH rows, for example Protect `open_findings` +1, §9j2.5 item 3) is K8's re-expectation, reported as a stop to the Architect. K7-F does not edit those rows.

### 9o.2 The KOBO-001 404s in a Kisiwa-only prepare: expected, not a defect. Leave them alone.

- **Cause (READ):** `performance_and_prebuild` (`tools/demo_combined.py:626-633`) hard-codes `("KOBO-001",)` for the Performance comparison. That call and the prebuild both run with `check=False`. The prebuild warms pages that include Kobo's. Any partial prepare without Kobo (Cold-only, EV-only or Kisiwa-only) prints the same lines. This predates K7, and neither line can fail the prepare.
- **Decision: no `--sites` skip.** E3, K9's rehearsal and the default prepare after K7-F always include Kobo. A skip would edit a shared step for a scratch-only cosmetic gain, and the three-Site path must stay byte-equal in behaviour (S-9).
- **K7-F's scratch packet** lists these two lines as "expected in a Kisiwa-only prepare (R3n)". It also **records the prepare's exit code**: it must be 0, and a non-zero exit is stop S-6.

### 9o.3 KIS-3: it already asserts the tolerance; K7-F adds the printed evidence

- `kis3` (`tools/demo_combined_rows.py:555-571`) already asserts every one of the five terms against `Fraction("1/100000")` and fails the row beyond it. A pass therefore means "within 1/100000 L". No new assertion is needed.
- **What is missing is the evidence.** K7-F adds to KIS-3's pass body `"tolerance_l": "1/100000"` and `"max_diff_l": {term: str(<largest |stored − handover| over the ten nights>)}` for the five terms. The values are exact `Fraction` text. The L0 pass self-test asserts both keys, and every `max_diff_l` is ≤ the tolerance.
- **Owner: K7-F** (it already edits `T/demo_combined_rows.py` for KIS-9 (e)). Its second scratch packet quotes the printed line.
- **K7-D's ASSIGN deviation (packet "Deviation") is ratified.** The ASSIGN is recorded at `assign_at` (`S−5d 13:20`) on its own clock, because the Work API refuses an occurred-at more than 5 min after the recorded-at (`B/work/model.py:36`). It is at its story instant, and the calendar is unchanged.

### 9o.4 K7-F starts now, branched from K7-D; the two merge to main together

- **Start now.** K6a and K6b are merged, which was K7-F's dependency.
- **Branch:** `task/DIESEL-K7F-kisiwa-freeze` in `C:\Users\assef\Bineyame\AssetOpsV1-k7f`, **from `task/DIESEL-K7-kisiwa-story` at `63f60f986`** (this replaces §9l.3's "from main after K6 merges"). Then `git merge main` to bring in K6b. Never rebase.
- **Scope:** §9l.3 "The freeze step" as fixed by §9m.5, plus this ruling: `EXPECTED_SECONDS` (§9o.1), KIS-3 evidence (§9o.3), the default `--sites` flip, the verification link form and KIS-9 (e).
- **K7-D's review runs in parallel** on its own branch, against the K7-D diff. Any K7-D fix commits land on `task/DIESEL-K7-kisiwa-story`, and K7-F runs `git merge task/DIESEL-K7-kisiwa-story` before its packet. K7-F's review covers only the K7-F delta (`git diff <K7-D accepted head>...K7-F head`).
- **Merge:** after **both** reviews ACCEPT, the coordinator merges `task/DIESEL-K7F-kisiwa-freeze` into main **once**. It carries K7-D, and the merge message names both. K7-D is never merged alone, because the R3k2 L2 carry makes a three-Site default fail the KIS rows until the default flips.
- **Second scratch prepare (K7-F), same command and database as K7-D's:** `python tools/demo_combined.py --db assetops_demo3_kisiwa_test --work var/demo3_kisiwa prepare --sites kisiwa --cap-seconds 5400`.
  - **When:** after K7-F's L0 tests are green and committed, with main (K6b) merged in.
  - **Gate (all required):**
    - only one heavy job on the machine, which the coordinator confirms;
    - no K5 capture or `serve` reading `assetops_demo3_kisiwa_test` during the run, because the tool drops and recreates it;
    - free RAM ≥ 2.5 GB for 2 consecutive minutes, sampled every 30 s, with the samples in the packet;
    - `tools/keep-awake-during-tests.ps1` running (no `-ExecutionPolicy`).
  - **Cap 5400 s.** Measured 4199.5 s, plus seconds for the freeze and evaluation, is about 1.29×. The worst measured day ×10 gives about 4450 s. Stop at the free-RAM floor of 1.0 GB (S-8). A stall with no output for 10 min is reported, not retried.
  - **Run with `PYTHONUNBUFFERED=1`**, set in the environment, so the stall rule can actually see output: K7-D's log was blind for about 60 min. Also sample the prepare's peak working set every 60 s (K7-D missed it).
  - **Reads:**
    - `demo_combined_kisiwa.py check`: KIS-3 (with `max_diff_l`), KIS-4 and KIS-9 including (e). Every row must pass.
    - §9m.5's freeze and evaluate assertions, and the verdict as computed.
    - Seconds per day, the wall time and the exit code.
  - **Afterwards:** keep the database and work folder until the coordinator confirms K5's captures no longer need them, then `drop`. The K7-F data are a superset of K7-D's, so K5 can capture from them.
- **K7-F size: 0.5 → 0.65** (range 0.6–0.75):
  - the second scratch prepare runs about 70 min, not 45, so +0.1;
  - `EXPECTED_SECONDS`, KIS-3 evidence and the branch merges, +0.05.

  **S-11's K7-F ceiling becomes 0.8.** The increase is reported, not absorbed: **Kisiwa total +0.15.**

### 9o.5 Critical path against the 9.75 tripwire

- R3k2's **9.0**, with K7-F 0.5 → 0.65, gives **about 9.15 lane-units**: spent 3.65 → K4a 1.6 → K6a 0.6 → K6b 1.4 → K7-F 0.65 → K8 captures 0.25 → K9 1.0.
- **Headroom: about 0.6. No cut, and no owner question.** The cut candidates in §9m.6 stay named if a later stop eats the headroom.
- K7-D's review runs beside K7-F's build. It joins the path only if a K7-D fix round outlasts K7-F's build and scratch prepare, which take about 0.65 together.
- K9's rehearsal grows by about 0.5–0.85 h of machine time, outside lane-units. **Demo date:** about +0.1 working day on R3m's +3.4, so about **+3.5** (range 3.0–5.5).
- **Plan HTML rows (coordinator):**
  - K7 becomes 2.55, with "K7-D 1.9, K7-F 0.65".
  - The E3 row becomes "Kisiwa build measured 3568 s (about 353 s per day); four-Site E3 ≈ 2.0–2.35 h of the 3 h cap".
  - The machine-time note becomes "K7-F scratch about 70 min; rehearsal about 2.0–2.35 h".
  - The rulings table gains "DIESEL-1-R3n: E3 restated from measured Kisiwa days (2.0–2.35 h, fits the 3 h cap); KOBO-001 lines in a Kisiwa-only scratch expected, no skip; KIS-3 prints `max_diff_l`; K7-F from K7-D, one merge carrying both; K7-F 0.65; path about 9.15".

### 9o.6 Owner questions

None. For the owner's information, in plain words: each Kisiwa example day takes about twice as long to prepare as we estimated, about 6 minutes instead of 3. Preparing the full four-Site demo should now take about 2 to 2⅓ hours, still inside the 3-hour limit you set, with at least 40 minutes to spare. The full practice run will confirm the figure first. If that run takes more than 2½ hours, we will look at it again before the real one. If it ever needs more than 3 hours, we will ask you rather than raise the limit. The work grows by about 0.15 unit, and the demo date moves by about a tenth of a working day.

---

## 9j3. Ruling DIESEL-1-R3j3: K4b review FIX, H1 (two untracked fuel tables on stored routes) and L1–L3

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. READ on main at `58e401900` (K3, K4a, K6a, K6b, K5 merged) and on `task/DIESEL-K4b-protect-fuel` at `9331a094e` (review `.agent/review-K4b.md`). Read: migrations 0047, 0050–0057; `config/chain/watermark-inputs-v1.json`; `config/chain/stored-composer-modules-v1.json`; `tools/chain_watermark_guard.py`; `backend/tests/test_ch5c_watermark_postgres.py`; every `responses.serve` caller; every backend reader of `fuel_balance_window`, `fuel_residual_consequence_revision` and `operational_record`. Nothing was run.
- **This ruling amends §9j.13 and §9j2.6 (K4b's approved files) and §9j2.5 item 1, which approved the store injection without naming watermark coverage. That was an Architect miss in R3j2, recorded as D3 (structural oversight).** Everything not named here stands.
- **H1 is confirmed. Its fix is required before K4b merges.** No exemption: these tables change the stored board, summary and Portfolio bodies, and the guard contract has no exemption path except the store's own tables.

### 9j3.1 The fix: migration `0058_fuel_watermark_inputs`

**Is the gap already covered by Finding triggers? (READ)**
- `finding` and `finding_revision` are in 0047's `INPUT_TABLES` and carry the four `_cic_` triggers.
- **`fuel_residual_consequence_revision`: covered by accident, not by contract.** Its only writer is `fuel_residual_append` (`financials/adapters/postgres_consequence_store.py:405`). The raise calls it from `fuel_balance/findings_service.py:89-91` on the raise's connection, in the same transaction as `fuel_apply`'s `finding_revision` insert. So today every consequence row commits together with a `finding_revision` row, and that moves `W` for the Site. This holds only while there is one writer that shares the transaction. A later re-price or backfill would break it silently. The W6 guard reads `pg_trigger`, not co-commit habits, so it would still report the table `untracked`. **It gets its own triggers.**
- **`fuel_balance_window`: not covered.** K3's assess writes windows in their own transactions (0055: not a chain-event producer, no outbox, and no Finding or assessment write). The K4a raise reads the window later, in a separate transaction. A WITHIN_MARGIN, BELOW_MATERIALITY, EXCESS or NOT_ASSESSED night, or a Site's first window, never touches a tracked table. Even an UNEXPLAINED night leaves stale bodies between the K3 commit and the raise commit. **It needs triggers.**

**New file `backend/migrations/versions/0058_fuel_watermark_inputs.py`** (0058 is free on main, in K4b, and in K7-F):
- `revision = "0058_fuel_watermark_inputs"`, `down_revision = "0057_fuel_verification"`.
- The docstring says this migration extends the CH-5c W2 change log to the two fuel tables that the stored board, summary and Portfolio read since K4b (DIESEL-1-R3j3). The tables are append-only (`ledger_append_only`), so in practice only the INSERT trigger fires. All four are created because the W6 guard requires them.
- `INPUT_TABLES = ("fuel_balance_window", "fuel_residual_consequence_revision")`
- **Reuse 0047's generator. Do not copy it.** Load `0047_chain_response.py` through `importlib.util.spec_from_file_location("_m0047_chain_response", Path(__file__).with_name("0047_chain_response.py"))`, exactly as 0048 loads 0029 (`0048_daylight_enqueue.py:29-35`).
- `upgrade()`: for each table, `cols = _M._columns(bind, table)`. Raise `RuntimeError(f"watermark input table {table!r} does not exist")` when the table is empty. Then:
  - `tenant = _M._TENANT_COLUMN.get(table, "tenant_id" if "tenant_id" in cols else None)`
  - `site = _M._SITE_COLUMN.get(table, "site_id" if "site_id" in cols else None)`
  - `op.execute(_M._trigger_sql(table, tenant, site))`

  Both tables carry `tenant_id` and `site_id`, so the change rows are Site-scoped. A Kisiwa window write does not move Kobo's board watermark. It does move the estate summary and Portfolio, which is correct.
- **Created objects:** functions `chain_input_change_fuel_balance_window()` and `chain_input_change_fuel_residual_consequence_revision()`, plus the triggers `<table>_cic_ins`, `_cic_upd`, `_cic_del` and `_cic_trunc` on each table. Every name is under 63 characters.
- `downgrade()`, for each table in reverse order: `DROP TRIGGER IF EXISTS <table>_cic_trunc|_cic_del|_cic_upd|_cic_ins ON <table>`, then `DROP FUNCTION IF EXISTS chain_input_change_<table>()`. `chain_input_change` rows already written stay, because the log is append-only. That is the safe direction.
- **No backfill row.** The new alembic head changes `code_version` (the `file_code_version` head hash). Every stored body is therefore rebuilt once after the upgrade, and the demo's prebuild runs after prepare.
- **0047 is not edited.** It is an applied migration, and its frozen tuple stays as it is.

**Config:** `config/chain/watermark-inputs-v1.json` `tables` gains `"fuel_balance_window"` and `"fuel_residual_consequence_revision"`, in alphabetical position: after `"foundation_revision"` and before `"ingestion_batch"`. No other byte changes. `version` stays `watermark-inputs-v1`: the change adds coverage only, and over-invalidation is the safe direction.

**Tests (in `backend/tests/test_ch5c_watermark_postgres.py`, `assetops_k4b_test` only):**
1. Add `_migration_0058_tables()`, the same loader pattern as `_migration_tables()`. `test_declared_inputs_equal_the_frozen_migration_list` becomes `set(declared) - {"chain_action"} == set(_migration_tables()) | set(_migration_0058_tables())`. This must fail if either JSON line is removed, or if 0058 lists a table the JSON does not.
2. `test_every_declared_input_has_the_four_change_triggers` checks `_migration_tables() + _migration_0058_tables()`. This must fail if 0058's `upgrade` is skipped for either table.
3. **New `test_fuel_window_insert_flips_only_its_site(engine)`:** insert one `fuel_balance_window` row for Site A, using the existing real-table helpers' tenant, Site and asset setup or the K4a Postgres fixture pattern; the builder picks whichever is smaller. Then `read_watermark(A)` changes and `read_watermark(B)` does not. This must fail if the trigger is dropped. The consequence table is covered by test 2. Its insert needs the full Finding chain (FKs to `finding`, `finding_revision`, `fuel_balance_window`), which K4a's Postgres tests already exercise.

**Guard CLI evidence (W6), in the packet:**
- **Required in the fix round,** only if the coordinator names a kept, Kobo-bearing prepared `*_test` database and its work folder. Clone it to a producer scratch database `assetops_k4b_audit_guard` (`CREATE DATABASE … TEMPLATE …`, with no open connections to the template). Upgrade the clone to head at the K4b fix commit, then run:

  `python tools/chain_watermark_guard.py --database-url <clone> --work <work dir> --out var/k4b-guard.json`

  The packet quotes the printed summary line. Acceptance:
  - `untracked []` and `unresolved []`;
  - `fuel_balance_window` appears in `all.read` (it proves the Kobo `has_windows` path was listened to);
  - `unlisted_modules []`;
  - exit 0.

  Drop the clone afterwards.
- **If no such database is kept,** do not run a prepare (about 1 h) only for this evidence. Tests 1–3 are the contract, because the guard's `untracked` predicate is the same `pg_trigger` four-event check as test 2. **The CLI then moves to K9's rehearsal** (four-Site prepare, with a Kisiwa fuel Finding present, so `_fuel_findings` also reads the consequence table). K9's packet gets the same acceptance as above, plus `fuel_residual_consequence_revision` in `all.read`. The K9 card gains the line: "W6 guard CLI on the rehearsal database: `untracked []`, both fuel tables read (R3j3)".
- Either way, add **one row to the after-the-demo list**: "F4 checks modules, not tables: add a table-level W6 check to a Postgres test so a new stored read of an untriggered table fails in CI, not only in the CLI".

### 9j3.2 Scope across merged units: the gap is K4b's alone (READ)

The stored routes are exactly the `responses.serve` callers:
- `outcome_api.py:220` (board) and `:252` (outcome summary);
- `estate_portfolio_api.py:75` (Portfolio);
- `estate_api.py:64` (Findings index);
- `chain_api.py:165` and `:308` (the chain and "Why?" routes).

None of them reads a fuel table on main:

| Merged surface | Fuel table read | Stored composer? | Gap on main? |
|---|---|---|---|
| K3 `fuel_balance_window` (0055) | The table itself. Writers: K3 assess, K4a raise | Written only, never read by a stored route on main | No |
| K4a raise and `fuel_residual_consequence_revision` (0056) | Writes. `analytics/adapters/postgres_finding_store.py:740` and `actions/adapters/postgres_action_store.py:812` read only `finding_revision.claim->>'fuel_balance_window_id'` (JSON text, not the table) | Those modules are listed, but the reads are claim JSON on tracked tables | No |
| K5 Fuel page nights, night detail, fuel Finding list and page (`fuel_balance_api.py:98-142`) | `fuel_balance_window`, consequence, K2 records | **No.** Plain `served(...)`, with no `ResponseStore` | No |
| K6b verdict page (`action_api.py:322`, `actions/verification.py`, `fuel_verification.py`) | `fuel_balance_window` (night choice), `operational_record` (site visits through `case_operational_records`) | **No.** `action_api` never calls `responses.serve` | No |
| K6b board entry (`FuelVerdictFact`, `mini.py:458`, `site_chain.fuel_verdict_actions`) | Chain snapshot rows from `domain_action` and `verification_*`, all tracked | Yes, stored | No (tracked tables only) |
| K2 fuel records on `operational_record` (0054) | `work/adapters/postgres_fuel_records.py`, `postgres_global_read.py` | Read by work detail, the verdict page and K5 night detail. None of them is stored | No. **Residual:** `operational_record` is untracked. Any future stored read of it needs the same treatment |

- K4b's own board binding reads `site` and `asset` (`night_context`), and `finding` and `finding_revision` (`_fuel_findings`). All of these are tracked. The two fuel tables are the only untracked reads. K4b does **not** bind `night_records_and_provenance` (K2 records) into the board, so `operational_record` stays off stored routes.
- **Conclusion:** the gap opens with K4b's injection (§9j2.5 item 1). It is not a pre-existing hole, and no merged unit needs a fix.

### 9j3.3 Who does it, and the order with K7-F

- **K4b's fix round does it,** on `task/DIESEL-K4b-protect-fuel`, with a Sonnet builder (fix-round rule). There is no separate unit: the gap is K4b's alone, and the migration is what makes K4b's reads lawful.
- **Re-review:** a fresh Claude reviewer checks H1 and L1–L3 only, plus the 0058 file and the JSON diff. Merge on ACCEPT.
- **Order with K7-F: independent, either may merge first.** Whichever merges second runs `git merge main` first. Never rebase. K7-F adds no migration, so there is no number clash, and neither branch touches the other's files.
- **K7-F's scratch database without the triggers does not matter:**
  - On K7-F's tree no stored route reads a fuel table, because K4b's board binding is absent. Its stored bodies are therefore correct without them, and none of its KIS evidence depends on the change log.
  - `demo_combined.py prepare` drops, recreates and upgrades to head. The first database built on a main holding both K4b and K7-F carries 0058, and its K7 backdated writes then log change rows. The watermark is a count, not a time, so a backdated write still expires the historical (`known_at`) bodies. That closes the reviewer's K7 concern.
  - **No K7-F scratch re-run** and no edit to K7-F.
  - The extra cost per prepared window write is one statement-level insert into `chain_input_change`, which is negligible against the measured 353 s per day.
- **Test template:** the new head makes the `pg_harness` templates stale. They rebuild once at the first Postgres test run, at about the cost of minutes. This is expected and not a defect.

### 9j3.4 K4b's Lows: all three in the same round

- **L1, fix.** In `read.py` `mini_ports` → `fuel_findings`: `_tank, k = fuel_context()` and pass `k` (not `known_at`) to `.fuel_findings(t, sid, lo, hi, k)`. Now one board reads the window, applicability and Finding at one cutoff (§9j.11 "as known at the board cutoff"). Stored and historical composes are unchanged, because `k == known_at` when `known_at` is given.
  - L0 test in `test_k4b_protect_fuel.py`: with `known_at=None`, a fake store records the instant that `has_windows`, `windows` and `fuel_findings` receive. All three are equal to `night_context`'s instant. This must fail if `fuel_findings` reverts to `known_at`.
- **L2, fix (one token, safe direction).** In `mini.py` `_fuel_findings`: `no_close = policy is None or tuple(policy.measures_for(FUEL_MECHANISM)) == ()`.
  - With no policy (a failed `chain_threads` read, or `thread_policy` not injected), a fuel Finding never shows a countdown. The fuel mechanism's lifecycle is declared empty in configuration (§9j2.3 item 2), so "unknown policy" can only mean "no countdown we can stand behind".
  - L0 test: a fuel `FindingFact` composed with `policy=None` carries `close_measured: False`. This must fail on the old `policy is not None and …` form.
  - Dispatch, Cold and EV views are unchanged (still no key).
- **L3, fix.** Restore the space at `mini.py:504`: `plan_facts = tuple(...)`.

### 9j3.5 Approved files (added to §9j.13 and §9j2.6)

- `backend/migrations/versions/0058_fuel_watermark_inputs.py` (new)
- `config/chain/watermark-inputs-v1.json` (two lines)
- `backend/tests/test_ch5c_watermark_postgres.py` (tests 1–3 of §9j3.1)
- `B/site_outcomes/read.py` and `mini.py` (already approved: L1–L3), and `backend/tests/test_k4b_protect_fuel.py` (L1 and L2 tests)
- `.agent/review-packet-K4b.md` (a fix-round section, plus the guard CLI line or the note "CLI moved to K9 (R3j3)")

**New stops:**
- **S-g:** `_trigger_sql` from 0047 cannot be reused unchanged (signature or behaviour). Report it; do not copy or fork the generator.
- **S-h:** the guard CLI, when run, reports any `untracked` or `unresolved` table other than these two, or any `non_200`. Report it with the JSON; do not fix outside these files.

**Focused runs only:**
- `test_ch5c_watermark_postgres.py` and `test_k4b_protect_fuel.py`;
- the L0 files the review listed for `mini.py` and `read.py` (`test_ch5a1_board_contract.py`, `test_ch5a2_contract.py`, `test_ch2_threads.py`, `test_pv1_value_lines.py`);
- `test_out_b4_board_postgres.py -k kobo`.

No full suite.

### 9j3.6 Size and critical path

- **K4b: 1.1 → 1.25** (range 1.2–1.3). That is +0.15:
  - migration and JSON 0.04;
  - the three watermark tests 0.04;
  - L1 and L2 with their tests, plus L3, 0.03;
  - the guard CLI clone run or the K9 note 0.02;
  - re-review 0.02.

  This is inside stop S-e's ceiling of 1.3. The increase is reported, not absorbed: **Kisiwa total +0.15.** If K9 takes over the CLI, K9 absorbs it inside its 1.0, because the guard is about 10 min on the already-built rehearsal database.
- **Critical path: about 9.15, unchanged. Headroom to the 9.75 tripwire: about 0.6.** The path is spent 3.65 → K4a 1.6 → K6a 0.6 → K6b 1.4 → K7-F 0.65 → K8 captures 0.25 → K9 1.0.
  - K4b's fix round (about 0.15) runs beside K7-F's remaining review and merge, and K8 waits for both.
  - K4b joins the path only if its fix round and re-review outlast K7-F's merge. Then the path grows by at most the overlap, which is ≤ 0.15, giving ≤ 9.3, still about 0.45 under the tripwire.
- No cut, and the demo date does not move.
- **Plan HTML rows (coordinator):** K4b becomes 1.25. The rulings table gains "DIESEL-1-R3j3: 0058 adds W2 change triggers on `fuel_balance_window` and `fuel_residual_consequence_revision` (watermark-inputs +2); gap is K4b's alone (no merged stored route reads fuel tables); K4b fix round, independent of K7-F's merge; L1 one cutoff, L2 no countdown without a policy, L3 whitespace; K4b 1.25".

### 9j3.7 Owner questions

None. For the owner's information, in plain words: some pages are saved after they are first built, so they open quickly. A saved page is rebuilt when the data behind it changes. The new Protect fuel line reads two fuel records the system was not yet watching for changes, so a saved page could have kept showing an old fuel status. This fix makes the system watch both records. Any new fuel check now refreshes the saved pages straight away, including the ones for earlier days. It also tidies three small points. The work grows by about 0.15 unit and does not move the demo date.

---

