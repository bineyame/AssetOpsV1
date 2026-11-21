# 3C2 handshake

Reviewer questions and builder pre-flight, one combined round (`.ai/RULES.md` §4). Round 1 below; answers go under "Handshake answers (round 1)" in `rulings.md`.

## Reviewer questions

Round 1, on spec rev 1 (main b8b812f23). Severity: High blocks the build; Medium wants an answer in spec rev 2.

### High

- **R1 §2.3 steps 7 and 8, D-3C2.3: a retry after the due day is refused, not recognised.** `DUE_IN_PAST` (step 7)
  runs before `add` finds the stored row. A command retried after a lost connection, on the due date's next UTC day
  (or when `--due` is today and the retry crosses midnight UTC), prints `DUE_IN_PAST` and exit 2 instead of
  `already_recorded` true. The gate question "does a re-run of the same command record nothing new" is then false at
  the boundary. Expected: say whether the identity read (step 8's lookup) precedes step 7, or that a re-run past due
  is a refusal by design; add the case to §4 and test 2 either way (clock 2026-12-16, R1 with `--due 2026-12-15`).
- **R2 §2.3 steps 3 and 6, the rights: "the signed-in person is recorded" has no sign-in.** `--as EMAIL` is checked
  against `onboard_person` (active, same tenant, holds `OPERATOR_EXECUTIVE`), but nothing proves the typist is Amina;
  Q2's default accepts that (`created_by_script` true). Expected: the spec says in one sentence that the command is
  the analyst's trusted act and that no password or session is read, and the packet reports it as residual risk (not
  silently as "authenticated"); and test 2 has the case "`--as` is an inactive executive" (PERSON_NOT_FOUND), which §4
  lacks (the only inactive case is not listed at all, for creator or owner).
- **R3 §2.3 step 8 and `add`: the unique-index backstop has no stated behaviour.** The lock serialises writers, but if
  the lookup misses and the index still raises (a writer that skipped the lock, or `hashtextextended` collision
  across tenants only widens waits, not rows), the spec does not say whether the adapter catches the violation and
  returns the stored row or lets it become `ACTIONS_UNAVAILABLE` (exit 3). Test 7's two-thread case cannot tell the
  lock from the index. Expected: the adapter catches `UniqueViolation` on this index and returns `(stored, True)`;
  test 7 gains a plant "lock removed" that still passes only because of that catch, and a second test that inserts
  past the lock to prove the catch.

### Medium

- **R4 §2.3 step 5: a factor of the wrong Site type is accepted.** `FACTOR_UNKNOWN` tests membership in any registry
  of `REGISTRIES`, so `--site KISIWA-001 --factor` naming a mini-grid-only factor on a cold-chain Site records. 5c's
  row shows "Site and factor". Expected: the factor must belong to the registry of the Site's type (and §4 gains one
  refusal), or the spec states that the factor is a label only and 5c shows it as such.
- **R5 §2.3 step 6, owner scope: tenant-wide roles own everything.** Only SITE_MANAGER is site-scoped in `role_grant`
  (0062 `CHECK ((role = 'SITE_MANAGER') = (site_id IS NOT NULL))`), so Wanjiru (ANALYST) and Joseph (FINANCE) pass as
  owners of a Kobo change, and a FIELD_TECHNICIAN too. D-3C2.2 says "any tenant-wide role", so this is the ruling, but
  §4 tests only Joseph (tenant-wide) and Peter and Halima. Expected: §4 accepts Wanjiru as owner of R1 (or the ruling
  names who may not own), so P2/P3's plants cannot be satisfied by a rule that is too narrow as well as too wide.
- **R6 §2.3 step 1 and the DB check: the two title rules differ.** Python `strip()` removes every Unicode space (NBSP,
  U+2003, U+0085); Postgres `btrim` removes only spaces. The stored title is the stripped one so the check passes, but
  an internal control character such as U+0085 or U+2028 is above U+0020 and kept, and the identity key is raw text.
  Expected: state NFC normalisation or none; add `"Title\twith tab"` (below U+0020, BAD_TITLE) and a title of exactly
  200 characters (accepted) to §4; the 201 case is there already.
- **R7 §2.5 `created_at` format and `clock` reads.** "ISO with Z" is given for `09:30:00Z` only; a real clock has
  microseconds. Also `clock()` is read in steps 7 and 8 and for `state`, so three reads can straddle midnight.
  Expected: one clock read per `record`, `created_at` printed as `YYYY-MM-DDTHH:MM:SSZ` with microseconds truncated
  (stored value truncated the same way, so the printed and stored values agree), and the already-recorded line shows
  the stored `created_at` (R1 again at 10:00Z prints 09:30Z; add it to §4).
- **R8 §6 done 3 and §5 test 2: the exact stderr form is untested as a whole.** "`<CODE> <sentence>`" is checked per
  case but not that nothing else prints, that stdout is empty on refusal and that stderr holds no email. Expected:
  each refusal case asserts stdout `""`, stderr exactly `"CODE sentence\n"`, and no `@` in either.
- **R9 the read, §2.4: newest first is tested on three distinct times only.** P5 fails, but the `id DESC` tie-break
  (same `created_at`) is not exercised, and in memory `UUID(int=n)` ordering equals insertion order so a wrong tie
  rule passes. Expected: §4's read gains two Actions at the same `created_at` with ids 4 and 5, expected 5 before 4,
  in tests 3 and 8.
- **R10 the value rule (RC9) has no failing test.** Nothing asserts that nothing is valued. Expected: test 1 asserts
  the JSON has exactly the twelve keys of §2.5 (no money or "value" key), and test 5 greps the table's columns and the
  adapter's SQL for no `commercial_*`, `value`, `amount` or currency reference. Add plant P11 "a `value` key in the
  line" failing test 1.
- **R11 plants that cannot fail or are missing.** P7 (trigger left out) fails test 6 only if the test also proves
  DELETE; say both. P10 fails the guard only if the guard scratch copy runs the whole script (the `UPDATE` shape is
  caught as "not the one INSERT"); state the guard's exit and message in the packet. No plant covers: the role check
  using the owner's rather than the creator's role (P12: `created_role` from the owner), the owner scope checked
  against `creator` instead of `owner` (P13), step order (an owner refusal before a site refusal; P14: swap steps 4
  and 6, fails the case "`--site NOPE-001 --owner zara@…`" which §4 lacks), and the S6-01a separation beyond the SQL
  grep (P15: the service imports `actions.service`). Expected: add P12 to P15 and the two-fault case to §4.
- **R12 test 5's SQL grep.** "Names no table but `agreed_action`, `operator_account` and `site`" is a substring risk:
  `agreed_action` contains `action`, so a grep for the S6-01a `action` table must be word-bounded (`\baction\b`) and
  the allowed list must be matched whole. Expected: the regex is stated; a planted `FROM action` fails it.
- **R13 separation on the screen side (unit 2).** `StoreAgreedActions` reads only `service.for_tenant`; 5c test 9(d)
  should also have an S6-01a Action open on the same tenant (via the existing test helper) and assert `actions.rows`
  still holds only R1. Without it P8 is proved at the adapter, not at the screen. Expected: add that to test 9(d).
- **R14 Q4 and the Site timezone.** Overdue is by UTC date; Kobo's clock is Africa/Nairobi (UTC+3), so from 21:00Z the
  day before the due date a Kobo change reads Open though the due day has begun there. Accepted by Q4 for this
  fortnight; the runbook sentence ("Overdue by UTC date") is not in the spec's deliverables. Expected: say where the
  sentence lives, or confirm it is only in D-3C2.4.
- **R15 ordering inside the fortnight (see P1).** The spec starts "after 3A6 and 3A7 have merged", but the unit table
  says only "3A6 and 3A7 merged"; 3B7a's 0066 is also unmerged. Expected: §0 and §8 name the revision the migration
  revises as the live head at merge time, not a fixed name (see P1).

## Implementer pre-flight

Checked on main b8b812f23 in `/opt/assetecon/AssetOpsV1-3c2hs`; read-only. Nothing built, nothing run against a
database.

- **P1 (High, ordering) migration 0069 and its parent.** Main's head is `0065_commercial_upload`
  (`down_revision` "0064_person_on_work"); 0066 (3B7a, guard approval pending), 0067 (3A6) and 0068 (3A7) are not on
  main. The spec's `revises 0068_commercial_reconciliation` and test 6's chain pair
  `("0069_agreed_action", "0068_commercial_reconciliation")` are right only if all three merge first and in that
  order. Risks: (a) if 3B7a merges after 3C2 or 3A7 changes its revision name, Alembic has two heads or the test
  names a revision that does not exist; (b) 3B7a awaits the owner's guard approval, so 0066 may slip behind 0069's
  readiness; (c) if 0069 is committed before 0068's file exists, `alembic heads` is broken on the branch. Mitigation:
  the build does not start until `ls backend/migrations/versions | grep 0068` shows the file on main (spec §0 already
  says so; keep it a hard gate, not a note); the revision string is read from the file on main at that moment, and the
  chain test is derived from `down_revision` of 0069 equalling the previous head (`script.get_current_head()` before
  the add), with the literal pair kept as the hand value. If 3C2 is ready first, the Architect renumbers; a 0069 that
  skips a number is wrong, as Alembic order is by `down_revision` but the repo's naming rule is sequential.
- **P2 (High) `AccountService.tenant_by_slug` does not exist.** Main has `AccountStore.tenant_by_slug`
  (`accounts/store.py:37`, adapter `postgres_account_store.py:173`) and private uses inside `service.py` (lines 182,
  209, 237, 242), but no public `AccountService.tenant_by_slug`; the spec (§2.3 step 2, "Builds on 3A6, D-3A6.17")
  expects it from 3A6, which is unmerged. If 3A6 names it differently, `record` fails on import. Mitigation: confirm
  the exact public signature in 3A6's branch before starting; if absent, 3C2 needs one two-line service method and
  the spec's file list must include `accounts/service.py` (it does not: "Edited" names only `permissions.py` and the
  guard), which would also break reviewer check 5 (diff lists only §0's files).
- **P3 (verified) the cited main code.** `AccountService.onboard_person` (`service.py:255`) returns `OnboardPerson`
  (`model.py:80`) with `tenant_slug`, `active` and `roles: frozenset[(role, site_id)]`, so steps 3 and 6 can read held
  grants as the guide asks. `COMMAND_ROLES` and `roles_of` are at `permissions.py:39` and `:71`; adding
  `"action.agree": (EXECUTIVE,)` is one line and `roles_of` raises `KeyError` for a missing key, so test 4 is
  meaningful. `ledger_append_only()` is created in 0005 (`:310`) and raises `restrict_violation`; 0062's
  `operator_account` has `UNIQUE (tenant_id, id)` (`:37`) and `site` has `site_tenant_id_unique` (0001), so all three
  composite foreign keys in §2.1 are valid. `site.site_code_key` is lower-cased, matching `lower(:c)`. `REGISTRIES`
  is `structure/registry.py:154`, `candidate_l` is in `rows_mini_grid.py:63`. `configuration-persistence.ps1` has the
  3C0a writer block (`$accountWriter`, shapes by regex) that the new block copies; `pwsh` is installed.
- **P4 (verified) the rights rule against the data.** `role_grant` has `CHECK ((role = 'SITE_MANAGER') = (site_id IS NOT
  NULL))`, so only SITE_MANAGER is Site-scoped; "any role other than SITE_MANAGER" is therefore exactly "tenant-wide"
  and §2.3 step 6 is consistent with 0062 (see R5). The executive check (`created_role`) takes the first of one role,
  so "first of" is vacuous for now and cannot fail; I will keep it as the literal list read from `roles_of`.
- **P5 (verified) the appending.** `ledger_append_only()` on `BEFORE UPDATE OR DELETE` does not stop `TRUNCATE` (0062
  and 0063 add no truncate trigger either). The spec matches house style; the guard forbids a runtime TRUNCATE; I
  note it as known residual risk in the packet, not a change.
- **P6 (verified) separation.** `actions/` on main holds the S6-01a modules (`service.py`, `lifecycle.py`,
  `verification*.py`, `ports.py`, `composition.py`); `agreed.py`, `agreed_composition.py` and the adapter are new
  names with no collision. `actions/composition.py` exists, `agreed_composition.py` is a different file; I will not
  import from it. A second `build_*` composition does not clash.
- **P7 (verified) no value.** The migration has no money columns and the adapter reads only `agreed_action`,
  `operator_account` and `site`; nothing from `commercial_*`. RC9's text ("recorded as an Action, not valued") is in
  `owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`, accepted by "accept all defaults for RC1 to RC9".
- **P8 (missing on main, as expected) unit 2's ground.** `backend/assetops_backend/deep_dive/` does not exist on main,
  nor `5c`'s test file; 5c unit 2 is unmerged, so unit 2 cannot start and test 9 cannot run; DDR's G10 (DDR spec
  line 70) calls `build_agreed_actions(url).service.for_tenant(tenant)[0]`, which fixes the name, return type and
  newest-first order I must keep. G10 also needs the stored `factor_id` and Site code in `AgreedActionView`, which §2.2
  provides.
- **P9 (clock) `due_on` check in SQL.** `CHECK (due_on >= (created_at AT TIME ZONE 'UTC')::date)` is immutable and
  allowed in a CHECK; with a microsecond `created_at` the truncation rule of R7 must hold on both sides, or the
  printed and stored values differ by microseconds and test 7's "every key but `action_id`" fails on `created_at`.
- **P10 (clarify) what the tests need that the spec does not give.** (a) How test 7 reads "ids from the database row":
  a `SELECT id` in the test, not the command's output. (b) ON1's fixture names (`lakeside-power.onboarding.json`):
  I will confirm Peter, Halima, Wanjiru, Joseph and Amina are all in it, and that Mto exists as a site (D-3C2.2's
  "not a Mto one" is not in §4's refusals: Halima/KISIWA and the no-Site case cover it, so I will add a `--site
  MTO-001` refusal only if the fixture has that code). (c) `tools/heavy-slot.sh --db` for the two-thread case needs
  two connections from one pooled DB; the adapter's engine pool size must be at least 2.
- **P11 (what I will do on the R-items).** R1 to R3 change the spec text, so I wait for rev 2 before coding; R4 to R15
  I will take as stated unless the Architect rules otherwise. Mid-build count stays 0 only if rev 2 answers P1 and P2;
  otherwise the first two commits are blocked, not guessed.
