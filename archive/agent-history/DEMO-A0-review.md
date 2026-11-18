# DEMO-A0 review: assumption-store recorded clock seam (R1)

Reviewer: fresh Claude reviewer. Branch `task/DEMO-A0-assumption-clock-seam` at 7be6feae7, against main e19bb687.
Judged against Addendum 1 R1 of `AssetOpsV1-plan2/.agent/build-sheet-DEMO-COMBINED.md`.

## Verdict: ACCEPT

No High or Medium findings. The two Low findings below are optional hardening, not acceptance gaps.

## What was checked

**The diff (3 files, +125/-2).** Only the publication instant `at` changes
(`backend/assetops_backend/financials/adapters/postgres_assumption_store.py:138-139`). When there is no override,
the expression still evaluates `c.execute(text("SELECT clock_timestamp()")).scalar_one()` on the same connection, at
the same point (after the advisory lock and the head check). The `RECORDED_TIME_NOT_LATER` check, `plan_assignments`,
validation, idempotency, the SYSTEM-principal rule and every insert and update are unchanged. The override value also
flows into `recorded_at`, `recorded_from` and the `recorded_to` closures, which is the intended "one instant" contract.
The keyword is keyword-only, so it cannot be passed by position. `composition.py` (lines 39, 43, 58, 72, 148), `main.py`,
`publish_assumption.py` and `tools/s602b_test_scoped_cases.py:222` construct the store without it. This matches R1.

**The guard.** The AST test (`backend/tests/test_demo_a0_assumption_clock_seam.py:22-34`) flags a call keyword or an
attribute access named `test_recorded_clock_override` anywhere under `assetops_backend/` except the store. The text check
covers `composition.py` and `main.py`. I ran the guard's logic over probe snippets in scratch:

| Bypass | Caught |
|---|---|
| `functools.partial(S, test_recorded_clock_override=f)` | yes (Call keyword) |
| `s.test_recorded_clock_override = f` | yes (Attribute) |
| `S(url, **dict(test_recorded_clock_override=f))` | yes (inner Call keyword) |
| `S(url, **{"test_recorded_clock_override": f})` | **no** |
| `kw = {"test_recorded_clock_override": f}; S(url, **kw)` | **no** |
| `setattr(s, "test_recorded_clock_override", f)` | **no** |

Of these, only the text check on `composition.py`/`main.py` catches the string-literal forms, and only in those two
files. The existing evidence seam `test_decision_clock_override` has **no** guard at all (`grep` finds no check in
`backend/tests` or `tools/checks`), so this is already stronger than the precedent R1 cites. See L1.

**The tests.** They are meaningful:
- With the override at X, `recorded_at == recorded_from == X`, `snapshot(known_at=X-1s)` is empty and
  `snapshot(known_at=X)` selects the row.
- With a constant override, a second publication is refused `RECORDED_TIME_NOT_LATER`. This proves the check still runs
  against an overridden instant.
- Without the override, the attribute is None and `recorded_at` falls within now ±30 s.

**Planted break (in memory, via a scratch pytest plugin; the worktree was not edited).** I made `__init__` swallow the
override so the server clock was always used. Result: 2 failed, 3 passed.
`test_override_sets_recorded_instant_and_snapshot_visibility` failed, and so did `test_override_keeps_recorded_time_not_later`
(DID NOT RAISE). The packet's own non-vacuity check (a keyword planted in `composition.py` fails the AST test) is
consistent with the AST logic I probed. `git status` was clean afterwards.

**Security and honesty.** The seam can only be reached by Python code that constructs the store. No CLI flag, env var,
HTTP route or configuration exposes it: `publish_assumption.main` accepts an injected `store=` object, but argparse
has no clock option. Back-dating real data in production would need a code change to composition, and the guard
would catch the obvious form of that change. The append-only rule still holds: an override can never record at or
before the series' latest instant, so a demo cannot rewrite an existing history. It can only start or extend one at
a past instant. The residual honesty cost is the one R1 already names as the owner's veto: the price's recorded time
reads as onboarding, not as build day. This is the same pattern as the accepted evidence ledger seam, in the same layer.

**"Byte-identical without override".** Showing this by behaviour is sufficient here. The no-override branch is the
original expression, textually unchanged, evaluated in the same place on the same connection. A golden diff would add
nothing. The unchanged s402/s408/out_e3/out_e4 and s4 assumption suites passing is adequate evidence.

## Findings

- **L1 (Low, hardening, not an acceptance gap).** `backend/tests/test_demo_a0_assumption_clock_seam.py:22-34`: the AST
  guard misses the string-literal forms (`**{"test_recorded_clock_override": ...}`, a kwargs variable, and `setattr`/`getattr`
  with the name as a string) in any product module other than `composition.py`/`main.py`.
  *Why it matters:* these are deliberate evasions, not accidental wiring, so the risk is small, and the guard already
  exceeds the evidence seam's protection. *Fix if wanted:* also flag any `ast.Constant` whose value equals `KW`, or
  simply make the text check `KW not in source` for every file under `PKG` except the store. The current AST test
  would then become a subset of it.
- **L2 (Low, scope).** The guard scans `backend/assetops_backend/` only, not the other runtime roots (`host/`, `gateway/`,
  `field/`) or `tools/`. Today nothing there constructs `PostgresAssumptionStore` except the test-scoped
  `tools/s602b_test_scoped_cases.py:222`, which does not pass the keyword. R1 scoped the guard to `assetops_backend/`, so
  this matches the ruling. Note it only if product composition ever moves outside that package.

No other findings. The message at `postgres_assumption_store.py:145` still says "The server clock is not later...", even
when an override supplied the instant. That is cosmetic and only reachable in tests, so it is not raised as a finding.

## Checks run (by me, on 7be6feae7)

- Focused pytest (plan2 venv, `assetops_test`): `test_demo_a0_assumption_clock_seam.py` plus the four
  `test_s4_assumption*` files: **88 passed** (26 s).
- R1 scoped set, `-k "s402 or s408 or out_e3 or out_e4"`: **24 passed**, 4501 deselected (99 s).
- Planted break (in-memory): **2 failed, 3 passed**, as expected.
- `tools\check-all.ps1` with `ASSETOPS_GUARD_PYTHON` = plan2 venv: **All 11 guards passed**.
- Not run: the full backend suite. Per R1 it is folded into DEMO-A's `-Tier all`, which must run on a tree containing
  A0. No frontend checks apply, because there is no frontend change.

## Residual risk

- The full-suite evidence for this change does not exist yet. It depends on DEMO-A's `-Tier all` running on a tree that
  includes A0.
- The override callable is not checked for timezone-awareness. A naive datetime would be interpreted by the
  timestamptz column using the session time zone. This is test-only, and the R1 caller will pass aware instants.
