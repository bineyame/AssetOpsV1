# W3-02 `0a` independent review

Reviewed: commit `7a4d06ef` (code and tests) and handoff `2d36689a` on `task/W3-02-estate-evidence-money-basis`. Base is `c50ea24b`. I read them only through git objects and ran nothing in the review2 worktree.
Authority: `main:.agent/W3-02-build-spec.md`, Review closure 4 (the `0a` row, "Shared parser, 3- and 5-part cursor, refusals", and the D index) and Review closure 5.

## Verdict: ACCEPT

There are no High or Medium findings. The three Low items below can be fixed on the branch, or carried as notes for the phase 1/3 reviews.

## Contract check

- **`KEYS` gains the new kinds.** `evidence` and `financials` are each exactly `("from","to","known_at","limit","cursor")` (`estate/scope.py`). The existing roots are unchanged. Met.
- **Typed refusal, never a 500.** `parse_request` raises `EstateRefusal("INVALID_CURSOR")` (422) for a kind outside `KEYS`. `decode_cursor` does the same for an unknown kind, for `scope`, and for a non-string value. The test covers `money`, `""` and `Evidence`, asserting status 422 and `rows:None`. The parser ordering is preserved: window first, then known_at, limit and cursor shape. Met.
- **Cursor key set.** The new cursors use `_ACTION_CURSOR_KEYS` = `{v,kind,tenant_id,authorized_site_ids,access_basis,from,to,known_at,selection_token,after,page_one_mode}`, with `kind == route` and no `limit`, `lens` or `state_filter`. `page_one_mode` is required to be `live|historical`. Met.
- **The 3- and 5-part markers.**
  - Evidence takes 3 nonempty strings, with `after[1]` a UUID.
  - Financials takes 5: `after[0]` is null or a canonical six-digit instant (`token_time` round-trip), the other four are nonempty strings, and `after[2]` is a UUID.
  - For both new kinds, `from/to/known_at` must also be canonical.
  - `cursor_after` and `cursor_marker` invert each other, and the null-first form round-trips.
  - Met.
- **Old Finding/Action bytes unchanged.** The two-part path in `_marker_ok` matches the old check: length 2, all strings, `after[0]` an instant. `cursor_marker` emits `[token_time(at), row_id]`, and `kind` is still `"actions"` for Actions. Both existing `_cursor` call sites (`index.py:213,267`) keep the positional `(at, row_id)`. `test_finding_and_action_cursor_bytes_unchanged` compares against independently built bytes. Met.
- **Fence before marker.** `_fence` compares grant, window and selection token, then returns `cursor_after`. A changed cutoff is refused 409 in `_scope`. Closure 4 says `_scope` keeps cutoff normalization, so that is consistent. An old `/1` digest reaches 409. Met.
- **No HMAC.** The docstring states that cursors are unsigned and that no tamper claim is made. Met.

## Tests (non-vacuous)

I ran the tests on an exported copy of `7a4d06ef` (`git archive`) in my scratch directory, using the main repo's venv.

- `tests/test_w302_estate_cursor.py` gave **26 passed** in 0.5s. The handoff says 31. See L1.
- I ran 8 mutations; each one was applied, run, then restored. Seven were killed:
  - removing the unknown-kind guard: 1 test failed;
  - removing the canonical `from/to/known_at` check: 1 failed;
  - removing the Financials instant check: 2 failed;
  - letting Evidence accept a 2-part marker: 4 failed;
  - dropping the Evidence UUID check: 1 failed;
  - dropping the Financials UUID check: 1 failed;
  - adding an extra key to emitted cursors: 5 failed (the byte pin);
  - making `resume_after` lenient: 1 failed;
  - removing the `kind == route` match: 2 failed.
- The one mutation that survived defaulted `page_one_mode` to `live`. It is equivalent behaviour, not a test gap: the exact key-set equality still refuses a cursor missing `page_one_mode`.
- `test_w301_estate_api.py` on the export gave 5 passed and 3 failed. The **same 3 fail on the base `c50ea24b` export**, with `ImportError: V4_EV_MAPPING_PROFILE_ID` from `assetops_contracts`. My export picks up the main checkout's `contracts` package, so this is an environment artifact and not caused by this commit.

## Builder readings

1. **Canonical `from/to/known_at` on the new cursors.** Mechanical. The spec says "Validate ... canonical time", and the encoder only ever emits `token_time`, so no cursor the server issued can be refused.
2. **`site_id` validated as a UUID, case not normalized.** Mechanical, with a Low gap (L2). The spec asks only that `site_id` be validated as a UUID, and the emitter writes lowercase `str(UUID)`.
3. **The extra `resume_after` helper.** Mechanical, not an unruled design choice. Closure 4 B1 assigns this exact rule to the cursor section that `0a` owns: "only after this fence check whether its marker exists in the full ordered row set, with an absent marker 422 INVALID_CURSOR".
   - The helper implements that membership rule literally, with no seek or nearest-row semantics.
   - Placing it in the Lane-A-owned `scope.py` follows the ownership rule. Lane B cannot edit shared files, so without it phases 1 and 3 would need another Lane A prerequisite.
   - Nothing calls it yet, and nothing enforces the "call after `_fence`" order (see L3).
4. **A changed cutoff is refused 409 in `_scope`, before `_fence`.** Mechanical. This is W3-01 behaviour that closure 4 keeps ("`_scope` retains ... cutoff normalization"), and it still fires before any marker lookup.

## Findings

- **L1 (Low, packet accuracy).** `.agent/W3-02-phase-handoff.md` says "31 tests", but `test_w302_estate_cursor.py` collects 26: 6 plain tests plus 20 parametrized cases. The coverage it lists is present. Fix: correct the count in the handoff.
- **L2 (Low, preference-adjacent).** `scope.py:_uuid` accepts any form `uuid.UUID()` parses: uppercase, braces, `urn:uuid:` and unhyphenated hex. A crafted cursor in one of those forms passes `decode_cursor`. The request still ends in 422, because `resume_after` finds no exact match, but the refusal comes after the fence instead of at parse time. Fix: check `str(UUID(v)) == v`.
- **L3 (Low, residual risk for phases 1 and 3).** `resume_after` compares `tuple(marker) == tuple(after)` exactly. Phase 1/3 row markers must therefore use the `cursor_after` shapes: `site_id` as a lowercase `str` (not a `UUID`), and the Financials `window_start` as an aware `datetime` or `None`. The call must come after `_fence`, on the full unpaged ordered set. If a row builder emits `UUID` objects, every page two is refused 422 and no test catches it. The phase 1 and phase 3 reviewers should check that the page-two round-trip goes through the real adapter.

## Not verified

- The handoff's Postgres run (6 estate files, 66 passed, on `w302a_test`, 9m31s). I ran no Postgres suite.
- `tools/check-all.ps1` (11 guards). I was told to run nothing in the worktree, and my export lacks the matching `contracts` package.
- Duplicate JSON keys inside a cursor payload are silently last-wins (`json.loads`). This is not required by the spec, and the cursors are unsigned anyway.
