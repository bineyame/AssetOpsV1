# 3B2 review

## Round 1: discovery review (W5), 2026-11-21

Reviewer: fresh Claude (assetops-reviewer), not the author. Branch `task/3B2-findings-pinned`, head `9fa87a495`,
diff `git diff main...9fa87a495`. Judged against spec rev 2 and rulings D-3B2.1 to D-3B2.15.

**Summary.**
- **Verdict: ACCEPT.** No High or Medium finding. One Low (spec text for `STRUCTURE_PIN_MISSING`); it does not block.
- Scope is spec §7.5 plus bookkeeping. `outcomes/` diff is empty. No served text (D-3B2.8).
- The T4 literal matches the wire, regenerated on its own from `39e1682de`: all 18 key x domain pairs are equal.
  Edits to an outcome-map entry fail T4 (three planted edits).
- The pin check runs only on `check_all()` with no argument. Removing the guard fails P5's test, and removing the
  call fails the start-up tests. 3B1 has no `check_all(registries=X)` caller, so its tests cannot change.
- `parity()` compares within the pin's own domain only. Switching it to `cold_chain` fails T3.
- The `-/<mechanism>` placeholder for `STRUCTURE_PIN_MISSING` is acceptable (L1).

### Checks run (own output)

| Check | Result |
|---|---|
| Module paths (worktree PYTHONPATH) | `/opt/assetecon/AssetOpsV1-3b2/backend/assetops_backend/__init__.py`, `.../contracts/assetops_contracts/__init__.py` |
| `git diff main -- backend/assetops_backend/outcomes/` | empty (0 lines) |
| Files in diff | `structure/check.py`, `structure/pins.py`, `tests/test_3b2_findings_pinned.py`, packet, spec status, `specs/INDEX.md`, `.ai/state/data.md`, `index-2.md` |
| Served-text grep (`CATALOGUE`, `messages`) | only the docstring comment on `_NO_KEY` and test/packet prose; no `messages.CATALOGUE` key, sentence or word map |
| No DB, heavy slot: 3B2, 3B1, out_a1, health, 3B3 evaluate + window price, 3B7a seam + snapshot, 5b attribution, 4b1, 4d, 5a | **484 passed, 1 skipped**, 23.0 s |
| Postgres, `heavy-slot.sh --db`, `run-host-tests.ps1` (`assetops_test`): 3B3 read, 3B7a snapshot, 5b attribution | **14 passed**, 36.2 s |
| `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set) | Architecture check passed. |
| `tools/check-agent-workflow.ps1` | Agent workflow check passed. |

I did not rerun `check-all.ps1` (40 guards) or a selected or full suite. I rely on the implementer's run at the same
revision, recorded in the packet.

### Independent snapshot check (checklist item 2, D-3B2.6)

I exported `39e1682de`'s `backend` and `contracts` with `git archive`. From them I generated `categories_for` and
`lens_flags` for every `FINDING:` key plus `FINDING:UNMAPPED` over the three domains, and compared the result with
the test's `WIRE_SNAPSHOT` literal. Result: 18 pairs on each side, equal. The literal is not built from `ENTRIES`.
`test_t4_the_snapshot_covers_every_finding_key` also fails if someone adds a `FINDING:` key without extending the
literal.

### Probes and plants

Each plant went into a `git archive` copy of the head in the scratchpad (the worktree was not edited) and was
reverted after the run. The start-up line is `create_app()`.

| Plant | Start-up | 3B2 tests | Fails for the stated reason? |
|---|---|---|---|
| P1 `UNEXPLAINED_FUEL` -> `diesel_l` | `STRUCTURE_PIN_TOTAL MINI_GRID/diesel_l` | 9 failed | yes |
| P2 drop `EV_INTERRUPTION` from `PENDING_PINS` | `STRUCTURE_PIN_MISSING -/EV_INTERRUPTION` | 10 failed | yes |
| P3 `candidate_l` home -> Protect P1 (rows file) | passes | 4 failed (T1 manifest, T3 x2, T5) | yes: a new divergence |
| P5 remove `if registries is None:` (pins always checked) | passes | 1 failed (`..._runs_no_pin_check`) | yes |
| remove the `check_pins()` call from `check_all` | passes (no pin check) | 3 failed (start-up tests) | yes |
| P6 pin `cost_to_serve` | `STRUCTURE_PIN_TOTAL MINI_GRID/cost_to_serve` | 9 failed | yes |
| P6 pin `fuel_cost` (product) | passes | 3 failed (T1/T5 tables only) | yes: accepted by the check |
| P7 `parity()` reads `cold_chain` instead of the pin's domain | passes | 2 failed (T3) | yes |
| `_is_total`: bare `Ref` not a total | passes | 9 failed (T2 totals) | yes |
| T4: drop `MG-4` from the GSC CHECKED entry | passes | 1 failed (T4 mini_grid/GSC) | yes |
| T4: `COLD_EXCURSION` CC-1 -> CC-6 | passes | 1 failed (T4 cold_chain/COLD_EXCURSION) | yes |
| T4: `UNEXPLAINED_FUEL` MG-8 -> MG-2 | passes | 2 failed (T3, T4) | yes |
| P4 (registry read at call time) | covered by `test_t5_reads_the_registry_at_call_time`, which passes | | |

In the scratch copy the skipped test is the T4 git-diff test (no `.git` there). In the worktree run it executes.

### Against the acceptance questions (spec §7)

1. Two mechanisms are pinned (`candidate_l`, `unexplained_l`) and the three cold/EV ones are pending. All five match
   design §4 and D-3B2.2 (class sweep W6: both pins and all three pending entries checked against the table).
   `STRUCTURE_PIN_MISSING` refuses a mechanism left out of both.
2. A missing factor and a pure sum are both refused at start-up (`ConfigurationError`). Under D-3B2.12, `Call`, `*`
   and `/` keep a node pinnable. `_is_total` treats any node type other than `Ref`/`Num`/`Neg`/`Bin(+,-)` as not a
   total. That covers `Call` and matches the ruling.
3. `parity()` returns exactly D-3B2.4's one row, and T3 holds it as a test-owned literal.
4. The wire is unchanged: the literal snapshot was verified on its own, the `outcomes/` diff is empty, and
   `test_out_a1_outcome_map.py` passes unchanged.
5. Scope is clean. `PIN_CODES` is separate from `CODES`, and `__all__` gains only `check_pins` and `PIN_CODES`. Layering
   follows D-3B2.11: `outcome_map` is imported only in `pins.py` and `check.py`, as a module, and `pins.py` does not
   import `check`.

The independence checks (guide item 3) pass: `DESIGN_PINS`, `DESIGN_PENDING`, `OWN_DOMAIN_OF_STRUCTURE`,
`EXPECTED_DIVERGENCES` and `WIRE_SNAPSHOT` are all literals in the test, and none is imported from `pins.py`.

### Findings

**L1 (Low, spec text, not an acceptance gap): `STRUCTURE_PIN_MISSING` text is `-/<mechanism>`.**
`backend/assetops_backend/structure/check.py:256` and `:299`.
- Spec §3 says a mechanism-level fault is written `STRUCTURE_PIN <key>/<mechanism>`. An unpinned `ENTRIES` key has no
  structure key, though. `ENTRIES` is keyed by signal, not by structure, so any key put there would be invented.
- The `-` keeps `StructureError`'s fixed `<CODE> <a>/<b>` shape and signature, and it carries 3B1's meaning: "none at
  this position" (`STRUCTURE_CATALOGUE <key>/-`, `check.py:107`). The only difference is that 3B1 uses it in the
  factor position and this uses it in the key position.
- My judgment: it fits the spec's intent and 3B1's code format. Inventing a key would be worse.
- Fix (bookkeeping, not code): the Architect adds one line to spec §3 or `rulings.md` recording
  `STRUCTURE_PIN_MISSING -/<mechanism>`, so that 3B6 and later readers do not take it for a defect. The branch needs no
  change.

No other finding.

### Residual risk the packet does not name

- **P5 coverage.** The guarantee that `check_all(registries=X)` runs no pin check is held only by 3B2's own test.
  3B1's suite has no `check_all(registries=...)` caller, so "3B1 tests unaffected" is true trivially, not as evidence.
  The 3B2 test does fail when the guard is removed, so the coverage is real.
- **`pinned_category` outside start-up.** It raises `KeyError` when a pin's structure has no registry. Start-up
  prevents this for the real data, but a test that patches `REGISTRIES` without `MINI_GRID` and then calls
  `pinned_category` or `parity()` will raise instead of returning `None`. 3B5 and 3B6 consumers should know this.
- **No mechanism-key check.** `check_pins` does not check that `PINS[m].mechanism == m`. Only T1 asserts it, for the
  real table. This is harmless today; 3B6 will add three pins and should keep that assertion.
- **3B5 scope.** As the guide says, 3B5 must apply D-3B2.4 and nothing more when it switches the wire.

USER_REVIEW_REQUIRED: none (no screen, wire or served-text change).
