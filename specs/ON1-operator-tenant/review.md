# ON1 review r1 (discovery, W5): operator tenant from one onboarding file

Reviewer: fresh Claude, 2026-11-20. Branch `task/ON1-operator-tenant`, head `837af9aaf`, worktree
`/opt/assetecon/AssetOpsV1-on1` (read only). Judged against spec rev 3, rulings D-ON1.1-16, reviewer guide rev 3,
runbook.md, and the two owner files (option A; "the approval step can wait").

## Summary (verdict: ACCEPT WITH FINDINGS FIXED ON THE BRANCH)

- Rights: no way found for a real file to write or grant anything. Step 3a is reached only after steps 0-3. It raises
  before any store read beyond `tenant_slugs` and before any write. Service 3 and 8 cover it, and my plant C
  (3a only on an empty database) failed service 8.
- Submit/accept separation holds in the file rule (plant B failed) and in the store backstop, both the memory store
  and the adapter (Postgres p3). The grant API path is the accepted Q5 residual.
- RC4: the command calls `commercial_upload_settings` (through `database_target`) before it composes anything.
  An emulated file is refused on `assetops_op_*`. Every RC4 URL in the tests uses `rc4.invalid:1`, and the
  no-connect fixture is autouse in the service, keys and settings files.
- Demo isolation: `Demo.env()` pins `demo` and drops the real-data switch and the key directory, so `serve_env()` and
  the API on 8990 behind the 5490 web demo both inherit the pin (settings 4).
- Key erasure: final. `_tombstoned` fails closed, and the tombstone is written before the key is unlinked. Tombstones
  block `create_key_file`, `FileKeyStore.key` and `key_state`. One fail-closed branch is untested (F2).
- Runbook test: it can fail (five built-in plants, plus V11/V22).
- Blocking: F1 (Q2, check-all red). Also to fix: F2 (a test). F3 and F4 are Low and go to the Architect.

## Findings

**F1 Medium (acceptance gap: check-all must pass). `backend/assetops_backend/accounts/service.py:234`.** `def
onboarding_open(` matches the persistence guard's bare `open\(` pattern
(`tools/checks/configuration-persistence.ps1:318`), so `check-architecture.ps1` fails. I reproduced it: "Storage
technology above the adapter layer in .../accounts/service.py:234". The guard is right not to be worked around.
**Q2 view: rename** (e.g. `onboarding_grants_open`, 5 references). Reasons:
- The same bare pattern appears twice (lines 318 and 412). Narrowing one leaves the guard inconsistent, and narrowing
  both changes a safety guard outside §4 to fit one method name.
- The lookbehind narrowing is a reasonable guard-hygiene item on its own merits; queue it separately if wanted.

The Architect rules. Until then the branch cannot merge on a red check-all.

**F2 Low (test gap). `backend/tests/test_on1_key_erasure.py`; code `file_key_store.py` `_tombstoned`.** The spec
(§3.5) says `PermissionError` and any other `OSError` mean "erased", and the code does that. No test reaches the
branch: the "mode 000 tombstone" case does not make `os.lstat` fail, because lstat needs no file permission.
- My plant A (`except OSError: return False`, fail open) passed all 86 no-database ON1 tests.
- Fix: one keys test that monkeypatches `os.lstat`, for the tombstone path only, to raise `PermissionError`. It should
  assert that `key()` raises `PseudonymKeyErased`, that `create_key_file` raises `KeyErased`, and that `key_state` is
  `ERASED`.
- This is also a spec-template note: the mode-000 case was meant to prove this branch and cannot.

**F3 Low (spec text, Architect's `runbook.md`; the build copied it verbatim, as required).** Step 4 of the runbook is
one block. Followed top to bottom, `apply` runs with `$DIGEST` still unset, because the digest is printed two lines
earlier in the same block. It is refused (`ONBOARD_DIGEST_DIFFERS`, exit 2, no write: it fails safe). `set-password`
then runs once with an unset `$EMAIL`, but the text says to run it for three people. The parser test cannot see this
(R5's class, the guide's "runbook as a person" probe). Fix in `specs/ON1-operator-tenant/runbook.md`, then recopy:
1. Put `digest` in its own block, then `DIGEST=<the printed value>`.
2. Put `check` and `apply` in a second block.
3. Make `set-password` a per-person block with `EMAIL=...`.

**F4 Low (Q1, preference with a reason).** `ONBOARD_FORMAT` at the object's path is workable: the `where` points at
the right place. Its sentence, "This is not an onboarding file of version 1.", is misleading for `people[2].roles`
with six entries or for a missing `people` key: the file *is* version 1. Plain words (RULES §10, the guide's "Words"
probe) favour a separate `ONBOARD_STRUCTURE`, for example "This part of the file has a missing or unknown field, or
too many or too few entries." It is one code in `_strict`/`_list` plus a row in §5. If the Architect keeps
`ONBOARD_FORMAT`, nothing else changes.

No other finding. Scope matches §4 and §6 plus the bookkeeping. There is no migration. `accounts_api.py`,
`model.py`, sign-in and the guard are untouched. `database_name` appears nowhere.

## Checks run (by me, on `837af9aaf`)

- Module paths: with `PYTHONPATH` set to the worktree's `backend:backend/tests:contracts:simulator:gateway:field:host:tools`,
  `assetops_backend`, `assetops_contracts` and `assetops_simulator` resolve under `/opt/assetecon/AssetOpsV1-on1/`.
- `heavy-slot.sh -- pytest` the four ON1 no-database files + `test_3c0a_accounts_service.py`: **124 passed** (30 s).
- `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_on1_onboarding_postgres.py`: **5
  passed** (11.9 s), routed `*_test` (`test_url_is_a_test_database` passes). No `assetops_op*` database was touched.
- `check-architecture.ps1`: **fails** on F1 only. `check-agent-workflow.ps1`: passed.
- My plants, in the scratch copy
  `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/on1-r1-plants-2199340`
  (a `git archive` of the head; the baseline there is 86 passed):
  - A: `_tombstoned` fails open on `OSError`. **Survived** (F2).
  - B: the file separation rule ignores `OPERATOR_EXECUTIVE`. **Failed**
    `test_the_analyst_is_never_the_executive`.
  - C: step 3a only when `tenant_slugs()` is empty, so a real file on its own existing tenant proceeds. **Failed**
    `test_8_rc4_matrix`.

## Cited, not rerun

- The builder's 657 passed (Postgres included), V1-V22 (23 runs), the 3 guard plants and fast check-all 39/40. All of
  these are at `f2a7970b6`. `git diff f2a7970b6 837af9aaf` touches only `.ai/state`, `specs/INDEX.md`, the spec status
  line, `mid-build-questions.md` and `packet.md`, so no code changed after those runs.

## Could not verify

- The real runbook database steps (coordinator only, by design).
- The `fsync` durability of the tombstone across a crash. It is untestable here; the order (tombstone, then unlink) is
  right by reading.

## Residual risk not named in the packet

- `tools/s*_walkthrough.py` and other ad hoc app launchers inherit the shell, unlike `demo_combined`. An
  `ASSETOPS_TENANT_SLUG` exported by mistake would make them serve that tenant. They are not the 5490 demo, and the
  runbook's subshell rule is the guard.
- `create_key_file` checks for a tombstone and then runs `O_EXCL` create. A concurrent `erase` can leave a stray key
  beside a tombstone. It fails closed (`key()` and `key_state` say erased), but the file stays on disk. Coordinator
  only, one operator: negligible.
- Exit-3 refusals (`AccountRefused`, the key errors) print the code with no sentence (packet notes this; §5 gives none).
