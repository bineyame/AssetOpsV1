# DS1 handshake (one combined round, RULES §4 items 6-7)

Status: **open**. Code waits until this round is closed.

How the round works:
- The Reviewer (after reading `spec.md`, `reviewer-guide.md` and `rulings.md`) and the Implementer (after a pre-flight
  of `spec.md` against `main`, against the pack at `d9329b582` and against the mock-up at `task/uiux-guide` head) write
  their questions here in one batch, numbered R1… and I1….
- Each question cites the spec section, says what is unclear, and says what answer the writer expects.
- The Architect answers every question once, in `rulings.md` under "Handshake answers (round 1)", and folds the answers
  into `spec.md`.

## Questions the Architect expects (answer these first if you raise them)

1. **§8.1 extraction.** Does extracting `observe_side` change dict insertion order or the `money()` path for October?
   (Expected answer: no. P8 proves it.)
2. **§6.1 `share` on an `anchor` whose October whole is 0.** None exists in the world today. Should it be refused?
   (Expected default: refuse with `HISTORY_BOUND`.)
3. **§4.3 `scope_input`.** Does it include October's `bridge`? (No: the view drops `bridge`.)
4. **§6.1 jitter for `fixed`, `plan_value`, `per_day`.** These use no `R(f)`, so they have no jitter. Confirm.
5. **§7.1 `period_end`.** Is it a date only, or a story-clock instant? (A date, as October's `period_end`.)
6. **§9.4 G3.** Is the Portfolio overview alone the changed screen, or are the Site pages too? (Only the Portfolio
   overview; the Site tiles are unchanged, D5.)
7. **§3 DS1p's `history.json`.** It is produced from the DS1a worktree. Is DS1a merged first? (No: built and reviewed
   first, not necessarily merged.)
8. **§4.5 the fixture `view_v1.json`.** It lives on `main` and is derived from a pack file not on `main`. Is that
   acceptable? (Yes: it is a test fixture under `fixtures/`, regenerated only through `view`, with the pack commit
   named in its packet.)
9. **§8.3 P3 node list.** Which nodes exist per vertical? (Compare those present on both sides; a node absent on one side
   is a failure.)
10. **§10 test location.** Does `simulator/tests/world/` run under the existing `simulator` pytest configuration, or does
    it need a `conftest.py` for `--update-golden`? (Add `simulator/tests/world/conftest.py` with the option.)

## Reviewer questions

(none yet)

## Implementer pre-flight questions

(none yet)

## Implementer pre-flight

Implementer (Claude), 2026-11-20. I checked the spec against `main` at `c4b5df739`, the pack at `d9329b582`
(`/opt/assetecon/AssetOpsV1-pack-int`) and the mock-up at `task/uiux-guide` `31ba2d304` (read only). I wrote no code.
The numbers P1 to P16 below are pre-flight questions. They are not the §8.3 checks P1 to P10, which I write as
"check P2" and so on. `M:` is `P/demo-site-scenario-manifest.yaml` at `d9329b582`.

**I checked these and have no question about them.** Every file and function the spec cites exists:
- `evaluate_structure.py`: `main`, `money`, `num`, `as_date`, the M2 `for k, record in sides:` at :187, `__main__` at :623.
- `independent_model.py`: `Model.side_records` :470, `base_ctx` :484, `eval_leaves` :509.
- `check_manifest.py`: `main` :947, `evaluator` :98.
- `gen_fixtures.py` embeds the whole `derived` as `DERIVED` (:161), and `build.mjs:13` refuses `"oracle":`.
- In the mock-up: `uxHistory`, `uxTrend` and `uxTrendNA` at `loop-ux.js:370-377`, the tiles at :290, :292-293 and
  :330-331, and `opTotals` at `loop-core.js:207`. Each `OPS[op].sites` holds the same three Sites as the manifest.

Other things I confirmed:
- The evaluator reproduces `derived-values.json` byte for byte in a scratch copy (SHA-256 `bfe2cbc5…813a`, 0.7 s), so
  check P8's constant is sound.
- `check_manifest.py` in a scratch copy reports 4429 passed and 5 failed. All 5 failures are paths outside the copy, so
  check P9's baseline must be taken in place.
- The dependency-direction guard scans `simulator/**` for backend imports and `backend/**` for simulator imports. It
  does not scan `tools/`. No guard keeps an allowlist of simulator subpackages.
- `simulator/tests/conftest.py`'s session-finish guard skips when a path is named, so `pytest simulator/tests/world`
  does not trip it. `--update-golden` in `simulator/tests/world/conftest.py` registers only when that folder is a named
  path, so tests must read it with `getoption(..., default=False)`.
- July 2026 has 23 weekdays, 4 Saturdays and 4 Sundays (T7). `fleet_kwh` reproduces October for all three depots (20×140×31,
  8×150×31, 14×140×31).
- The private block is named `oracle` (M:1607). §4.1's own phrase "oracle-free" must therefore not appear in
  `world/**` docstrings (T3b).

**My probe of the evaluator.** I ran the M2 code on October's records, cut to the leaf sets the §5 rules would generate
(`obs = incident = entitlement = {}`), for all nine Sites and both sides. Every status equals October's (Ruiru plan:
"not decomposed", missing `kwh`), and no exception is raised. With those leaves held at October's values, every outcome
equals October's to the cent, so the M2 path itself is sound for history.

### P1 (High). The mini-grid actual rules omit `billed_kwh` and `diesel_l`, but checks P2 and P5 need them
- **Evidence.** October's actual sides hold `billed_kwh` and `diesel_l` (Kobo 8645 and 1180). Both are `record.*` names
  in the factor map, as fallbacks: `delivered_kwh: "record.delivered_kwh | record.billed_kwh"` (M:870) and
  `necessary_l: "record.necessary_l | record.diesel_l"` (M:880). The §5 `MINI_GRID.actual` rules (spec :219-222) have
  no rule for either, so check P2's set "October keys ∩ factor-map `record.*` names" fails at all three mini-grid Sites.
  Check P5 tests `unexplained_l <= 0.02 * diesel_l`, which needs a `diesel_l` the history does not hold. The evaluator
  never reads either leaf here, because the first alternative is always present. The node `diesel_l` evaluates to
  necessary + candidate + unexplained (probe: 1180, 2400, 320).
- **Proposed answer.**
  - Check P2 counts only the factor-map alternative the evaluator actually reads: the first present name of each
    `a | b` chain.
  - Check P5 uses the **evaluated node** `diesel_l` from `derived["history"]…periods`.
  - No new rule.
  - (Alternative: a quantity `sum` over three leaves plus a `billed_kwh` rule. That needs new grammar.)

### P2 (High). How the view represents YAML floats; this fixes every digest
- **Evidence.** §4.5: `canonical_bytes` refuses `float`. But the allowlisted view carries 139 YAML floats. Some
  examples:
  - `prices.diesel_usd_per_l.Kobo: 1.25`
  - `period.plan.revenue: 3420.0`
  - `physical.sfc_l_per_kwh: 0.3`
  - `energy_model.k_kwh_per_crate_day: 0.25`
  - `tariff.prices.peak: 0.24`

  `view_digest`, `scope_digest`, `view_v1.json` and the golden all depend on how these are written. The manifest holds
  no YAML dates or booleans in the allowlisted paths today.
- **Proposed answer.**
  - `ManifestView.from_document` turns each `float` into the decimal string `repr(x)` (Python's shortest round trip:
    `"3420.0"`, `"0.25"`). `int` stays `int`.
  - Numeric reads go through `Fraction(Decimal(str(x)))`, which treats int and string alike.
  - Any other non-JSON type (date, bool) is refused with a named code, for example `VIEW_TYPE`. The Architect names it.

### P3 (High). Allowlisted keys that a tenant or Site lacks
- **Evidence.**
  - `metro-bus` has no `prices`, `energy_model` or `capacity_crates_per_room`.
  - `lakeside-power` has no `energy_model` or `capacity_crates_per_room`.
  - The cold Sites have no `physical` or `tariff`, and the mini-grid Sites have no `tariff`.

  T3(c) says "the view's key sets equal the allowlist exactly", and §4.3 lists fixed keys for `scope_input.tenant` and
  `.site`. Writing these keys as absent or as `null` gives different digests.
- **Proposed answer.**
  - Omit an absent key in both the view and `scope_input`; never write it as `null`.
  - T3(c) then reads: each key set equals the allowlist ∩ the source's keys, and no key outside the allowlist appears.

### P4 (High). The EV rules key does not match the tenant's `vertical`
- **Evidence.** The tenant says `vertical: EV_DEPOT` (M:590). §5 keys the rules by `EV_DEPOT_CAPTIVE` (spec :227). The
  evaluator and the checks map `EV_DEPOT` to `EV_DEPOT_CAPTIVE` in code (`evaluate_structure.py:167`,
  `check_manifest.py:634`). The view drops `chain_model`, so the generator cannot look the name up.
- **Proposed answer.**
  - Key `history.rules` by the tenant's own `vertical` (`EV_DEPOT`), so the generator holds no mapping.
  - A vertical with no rules table is refused (`HISTORY_RULE_UNKNOWN`).
  - Or, if the Architect keeps `EV_DEPOT_CAPTIVE`, state that the mapping sits in `leaves.py`.

### P5 (High). `R(f)` carries the month's length, which bends intensive leaves and `cold_kwh`
- **Evidence.** §6.2 sums `W` over the month's dates, so `R(f)` ∝ days. That is right for volume leaves (`scale`), but
  not for two others:
  - **Embakasi `max_kw`** (a peak, not a volume), `trend flat 0.92 0.95 0.98`, gives 460, 475 and then **474**
    (500 × 0.98 × 30/31). The declared "creeping" story falls in September.
  - **`cold_kwh`** multiplies `H[crate_days]`, which is already × d, by `R(cooling)`, which is also ∝ d. So September
    counts 30/31 twice on the `k` term. Meanwhile the monthly `base_kwh` (M energy_model `form: "kWh_month = 1550 +
    0.25 x crate_days"`) is evaluated unscaled in `excess_kwh` for a 30-day month. Check P5's 5% band absorbs this
    today (about −1.3% in September), but `excess_kwh` feeds Optimize.
- **Proposed answer.**
  - Define a length-free shape `S(f) = (W(f,m)/d_m) / (W(f,anchor)/d_anchor) × (1 + jitter·u)`.
  - Use `S` in `cold_kwh`.
  - Add a rule `level f a b c` = `O[leaf] × a × S(f)` for intensive leaves, and set Embakasi to
    `max_kw: level flat 0.92 0.95 0.98`.
  - `scale` and `trend` keep `R`.
  - The Architect decides whether history `kwh_model` (check P5) scales `base_kwh` by d/31.

### P6 (Medium). Extracting `observe_side` has side effects the §8.1 signature does not carry
- **Evidence.** The try block (`evaluate_structure.py:187-205`) also sets `site_ctx`, `site_struct`, `site_base`,
  `site_vert` and `site_tenant`, plus `site_ctx[n]["_rights"] = rights`, when `k == "actual"`. M3 and M4 read these.
  `ctx["as_of"]` is `doc["as_of"]`. The §8.1 signature has no `k`, no `rights` and no `doc`.
- **Proposed answer.**
  - `observe_side(...)` returns `(result, ctx, factors)`.
  - The October loop does the `k == "actual"` assignments itself, unchanged. History discards `ctx` and `factors`.
  - Check P8 proves no drift.

### P7 (Medium). T9 cannot run through `generate_history`
- **Evidence.** T9 generates month `2026-10`, but §6.1 refuses `HISTORY_MONTHS` when the anchor is inside `months`. §4.1
  and §4.6 name only `generate_history(view)` as public.
- **Proposed answer.**
  - Add a public `generate_scope(view, tenant, site, month) -> block` to `history.py`. It validates rules but not
    months membership.
  - `generate_history` calls it for each scope, and T9 calls it with month `2026-10` and zero jitter.

### P8 (Medium). The CLI tests (T1, T10) have no manifest on `main`
- **Evidence.** T1 and T10 run `generate` and `check --manifest M` in separate processes. `M` is the pack manifest,
  which is not on `main`. The tests hold only `fixtures/view_v1.json`.
- **Proposed answer.**
  - `--manifest` also accepts a `.json` view, chosen by suffix. `from_document` is idempotent on a view, given P2's
    representation.
  - The tests pass the fixture.

### P9 (Medium). DS1a's fixture depends on DS1p's manifest, but DS1a is built first
- **Evidence.** §4.5 says `view_v1.json` is written "from DS1p's manifest". §3's Order says DS1p starts after DS1a's
  tests pass.
- **Proposed answer.**
  - DS1a builds the fixture from a scratch copy of `M` at `d9329b582`, with the §5 block appended verbatim.
  - DS1p appends the same bytes.
  - `meta.view_digest` in `history.json` equals the fixture's digest. The `check` command and check P10 prove it.

### P10 (Medium). Worktree runs import `main`'s simulator
- **Evidence.**
  - `/opt/assetecon/AssetOpsV1/.venv` has an editable install (`__editable___assetops_simulator_0_0_0_finder`) that
    resolves `assetops_simulator` to `/opt/assetecon/AssetOpsV1/simulator`. I verified this by import.
  - System `python3` has no pytest.
  - In the DS1a worktree, `python -m pytest simulator/tests/world` and `python tools/world_history.py` would therefore
    import `main`'s package. It has no `world/` before the merge, and an old one after.
- **Proposed answer.**
  - The commands become `PYTHONPATH=simulator:contracts /opt/assetecon/AssetOpsV1/.venv/bin/python -m pytest
    simulator/tests/world -q`.
  - `tools/world_history.py` puts its own repo's `simulator/` at `sys.path[0]` (from `__file__`) before importing. That
    makes DS1p's "from the DS1a worktree" command import the right code unmerged.

### P11 (Medium). The tooling and file list for DS1m's G3 and the register row
- **Evidence.**
  - `tools/heavy-slot.sh` exists on `main` (`d29f1a36f`) but not on `task/uiux-guide`.
  - §9.4 names no capture command for the 18 shots. The mock-up has `tools/run-audit.sh` / `audit.mjs --shots`, and
    there is `/opt/assetecon/tools/pw`.
  - The §9.3 register row lives in `.agent/mock-departure-register.md` (tracked), which §3's DS1m file list omits.
- **Proposed answer.**
  - Run `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh -- <capture>`, with the Architect naming `<capture>` (I propose
    the mock-up's `audit.mjs` screenshot path).
  - Add the register to DS1m's files on `task/uiux-guide`.

### P12 (Low). Which side the `<kind>` series reads
- **Evidence.** §8.1 defines a Site's outcome per side but not which side the `contribution` / `cost` series plots. Tile
  1 shows `T.actual` (`loop-ux.js:289-290`).
- **Proposed answer.** The `<kind>` series is the **actual** side's outcome, and `gap` is as stated.

### P13 (Low). Rule-engine details left open
- **(a) Units inside `H`.** Proposed: `H` holds the rounded values (integer units, money in integer cents), and money
  `O[x]` is ×100 before rounding.
- **(b) A rule naming a leaf this side does not generate** (`ratio`, `share`, `rest`, `sum`). Proposed: refuse with
  `HISTORY_RULE_ARITY`, or a new code the Architect names.
- **(c) An override key `tenant/site` that names no Site.** Proposed: refuse with `HISTORY_RULE_UNKNOWN`.
- **(d) `leaves.MONEY_LEAVES` against `history.money_leaves`.** Proposed: they must be equal, or refuse.
- **(e) `split_to_days`.** §4.1 writes `(total, days, weights)` and §4.4 writes `(total, days, day_weight)`. Proposed:
  `split_to_days(total: int, days: list[date], weight: Callable[[date], Fraction]) -> list[int]`. DS2 and DS3 build
  on it, so the Architect should fix it.

### P14 (Low). Non-incident facts that sit in `observations` evaluate as 0 in history
- **Evidence.** `major_assets` (Kobo 5, Kisiwa 4, Mto 5) and `field_visits` sit in `observations.october`, not in
  `period.actual`. History therefore has `asset_days_total = major_assets * period_days` (M:830) = 0, and the mini-grid
  O2 and Protect denominators are 0. Check P4 then passes trivially for mini-grids. Outcomes are unaffected (probe).
- **Proposed answer.** Accept, and say so in the packet. Or the Architect moves these two into the view's Site
  allowlist (`physical`-like facts). I recommend accepting for DS1.

### P15 (Low). Line numbers in a mock-up another agent is editing
- **Evidence.** The cited lines match `31ba2d304` today. The UI lane is editing the files.
- **Proposed answer.** DS1m re-resolves the lines by function name (`uxOverview`, `uxHistory`) at its base, and the
  packet records the head it used.

### P16 (estimate). DS1p at 1 unit looks low
- **Evidence.** DS1p holds a lot of work:
  - the `observe_side` extraction;
  - `load_history` and `evaluate_history`;
  - `history_side` in the independent model, with no shared code;
  - ten new checks;
  - the rule fixes from P1, P4 and P5, which land in its manifest block.
- **Proposed answer.**
  - DS1p is 1.5 units, and DS1 is 3.5 units (with DS1b, 4.5).
  - DS1a at 1.5 holds only if P2, P3, P7 and P8 are answered before code. DS1m at 0.5 holds.
