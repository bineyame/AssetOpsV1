# 6a handshake (rev 1 spec; reviewer and implementer pre-flight)

Fresh Claude reviewer, 2026-11-22, on `main` at `19c3e7cb8` (the 6a/6c rev 1 merge). Read: `spec.md`, `reviewer-guide.md`,
D-P6.1 to D-P6.19 (`specs/6-decision-valued/rulings.md`), the IA-P spec's decisions list def, 3C2's code and tests, and
the code below. Not re-raised: Q1 (Kobo's fuel saved "Not available yet" until 0K4f), Q2, Q3 (6f1/6f2).

**Checked and found as the spec says.** Migration head `0071_person_on_actions` (so `0072`); 0070's raw `UPGRADE`
string, the `WS` check text, `REFUSE_IF_USED` and the reverse-order `DOWNGRADE` (`0070_agreed_action.py:25-79`);
`ledger_append_only()` (0005, never dropped); `site_tenant_id_unique` (`0001:79`), `finding_site_unique UNIQUE
(tenant_id, site_id, id)` and `finding.mechanism` (`0009:39, 54`), `operator_account UNIQUE (tenant_id, id)` (`0062:37`);
`agreed_action` has no `(tenant_id, id)` unique (`0070:26-45`), so 6a adds one; `NULLS NOT DISTINCT` is already in use
(`agreed_action_once`). `structure/check.py:21` holds the deferred-levers line; `check_all()` runs `check_pins()` then
`check_observed()` on the no-argument path only (`check.py:395-416`); `StructureError(code, structure_key, factor_id)`.
`FactorRow.levers` exists and no code reads it (`registry.py:72`). `PINS` and `pin_of` (`pins.py:37-56`):
`GENERATOR_SUPPORT_CANDIDATE` pins `candidate_l`, and `candidate_l` and `battery_throughput_kwh` are MINI_GRID leaves,
both home `OPTIMIZE_COST` O1 (`rows_mini_grid.py`). `KOBO_GRID` is `runs/replay_study.py:50-52` (`ReplaySettings` of
`Fraction`s, stop outermost), and it gives F-P1's 13 keys in order once 90/30 is removed. `SITE_TYPE_TO_STRUCTURE`
(`structure/read.py:27-31`) and `SiteRef` (`chain/ports.py:16-21`). `accounts/permissions.py`: `ANALYST`, `EXECUTIVE`
(`OPERATOR_EXECUTIVE`), `FINANCE` (`FINANCE_AND_COMMERCIAL_LEAD`), `SITE_MANAGER`, `COMMAND_ROLES`, `roles_of`.
`AccountService.tenant_by_slug` (one line, gate S) and `onboard_person` (`OnboardPerson.roles` holds `(role, site_id)`
pairs, `active`). 3C2's `clean_title` and `_now` (`actions/agreed.py:144-174`), the `agreed_action.refused` statement
shape (`i18n/statements/en/agreed_action.py`), the `count` slot with a noun (`Count(n, "character")`) and `bare`, the
`example` slot, and the nouns `character` and `month` (`vocabulary.py:106-118`). `ADOPTED` is
`tools/checks/statement_catalogue.py:41`. The persistence guard's 3C2 block (`configuration-persistence.ps1:1006-1013,
1618-1629`). The command output time format is `record_action.py:50` (`%Y-%m-%dT%H:%M:%SZ`).

## Reviewer questions (R)

**R1. Gate P's owner record is not on `main`** (spec:3-4, §0; rulings header). The spec and the rulings cite
`owner/owner-accept-p6-defaults-2026-11-22.md`, and the rulings cite `owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`.
Neither is tracked on `main` (`git log -- owner/owner-accept-p6-defaults-2026-11-22.md` is empty). Both sit untracked in
the main checkout. The packet cannot point to gate P's evidence, and guide check 1 cannot be met.
*Default:* the coordinator commits both owner files (verbatim) to `main` before 6a's first commit. The packet cites the
commit.

**R2. OD-25's start-up rule, as worded, passes a lever that disagrees with one pin** (spec §3.1, last rule; guide 6).
"a lever whose purpose factor's `home.category` differs from the home category of every pinned factor ... that lists
the lever" refuses only when it differs from all of them. A lever listed by one agreeing pin and one disagreeing pin
passes, and `home_category` (§3.5) then disagrees at run time, which is what the rule exists to stop. Test 2's single
plant (one disagreeing pin) cannot tell the two readings apart.
*Default:* refuse when the purpose factor's category differs from that of **any** pinned factor listing the lever. Test 2
adds a second case: two planted pins, one agreeing and one disagreeing, which must refuse.

**R3. No fixture prepares a decision with a Finding** (spec §5, §6 test 3; done question 5). P4's happy path, its two
refusals, and the `home_category` read from the pin have no fixture literal. The only Finding case is the plant
"read the heading from the lever when a Finding is set". So `FINDING_NOT_FOUND` and `FINDING_NOT_ON_LEVER` can be
"covered" by any input, and nothing shows that a decision with a Finding and one without, for the same period, are two
decisions (`decision_once` includes `finding_id`).
*Default:* add to §5:
- **F-P3:** Wanjiru prepares KOBO-001 2026-10 with a stored `GENERATOR_SUPPORT_CANDIDATE` Finding (memory store). It is
  a second decision beside F-P1, with `finding_id` set and `home_category` `OPTIMIZE_COST`.
- **F-P4:** the same with an `UNEXPLAINED_FUEL` Finding refuses `FINDING_NOT_ON_LEVER` (its pin `unexplained_l` lists
  no lever).
- **F-P5:** a random UUID refuses `FINDING_NOT_FOUND`.

The Postgres test (7) keeps `finding_id` null. Test 6's FK case needs no stored Finding.

**R4. Test 6 asserts "each violation by constraint name", but most checks have no name** (spec §2; guide 2). Postgres
names unnamed CHECKs after the table and the first column they reference, with `1`, `2` suffixes on collision. For
example, `decision_option` has a column check on `generator` and two table checks that start with `generator`. The
names then depend on declaration order, and a test written against generated names passes whichever check fired.
*Default:* the migration names every table-level CHECK and every multi-column CHECK (`CONSTRAINT <table>_<rule>
CHECK ...`), and test 6 asserts those names. Column checks keep Postgres's `<table>_<column>_check`, which is stable. The
names are listed in the packet.

**R5. Test 2's "ten rules" hide compound rules** (spec §3.1; §6 test 2). Three of the listed rules each hold two or
three refusals:
- "not a row of that registry, or whose row does not list the lever";
- "an axis name not `ID_RE`, or an empty or repeated `values`";
- "a template whose `{names}` differ ..., or a non-whole value".

"One planted lever per rule" can leave a branch untested.
*Default:* one case per refusal branch, about 14 in all, each asserting `StructureError("STRUCTURE_LEVER", key,
lever_id)` and the branch's plant. The packet lists them.

## Implementer questions (I)

**I1. The evaluator cannot find a decision's Site** (spec §3.2 `DecisionStore`; 6c §4 E3, E4). `decision()` returns
`(DecisionRow, options)`, and `DecisionRow` holds `site_id` only. 6c needs a `SiteRef` for
`structure_read.site_inputs(site_ref, …)` and the Site code for `STUDY_FRAME_MISMATCH`. The Protocol's only Site read is
`site(tenant_id, site_code)`. 6a merges first, so a gap here makes 6c edit 6a's Protocol, memory store and adapter.
*Default:* 6a adds `DecisionStore.site_by_id(tenant_id, site_id) -> SiteRef | None`, in the Protocol, the memory store
and the adapter (`SELECT id, site_code, site_type, timezone FROM site WHERE tenant_id = :t AND id = :s`), and tests it
in test 7. **High** (it crosses the two slices).

**I2. C3 needs the decision's Site before O1 has read it** (spec §3.3 C3, O1; fixture "David ... `PERSON_ROLE_REQUIRED`").
For `state_one_off`, C3 says "a SITE_MANAGER grant must cover the decision's Site", but the decision is read at O1,
after C3. The order is undefined for David on a missing decision (`PERSON_ROLE_REQUIRED` or `DECISION_NOT_FOUND`?), and
for a person who holds SITE_MANAGER elsewhere plus FINANCE.
*Default:*
- C3 checks that some role of `roles_of(command)` is held, at any Site. If none is, it refuses `PERSON_ROLE_REQUIRED`.
- After O1, the recorded role is the first role in `roles_of` order that covers the decision's Site: FINANCE covers
  every Site, and SITE_MANAGER covers only a granted Site. If none covers it, the step refuses `PERSON_ROLE_REQUIRED`.
- So David on a missing decision gets `DECISION_NOT_FOUND`, and on KOBO-001's decision `PERSON_ROLE_REQUIRED`.
- A test case covers a person holding SITE_MANAGER at MTO-001 and FINANCE: recorded role `FINANCE_AND_COMMERCIAL_LEAD`.
- prepare and choose are unaffected (single, Site-free roles).

**I3. P6 contradicts itself** (spec §3.3 P6). "the current settings are not compared; a re-run with other settings is
`ALREADY_PREPARED_OTHER` when they differ." `--horizon` on a re-run is not mentioned either.
*Default:* on the identity match, `current` is compared to the stored `current_settings` numerically, axis by axis
(`Decimal("90") == Decimal("90.0")`), and `horizon_months` is compared to the stored one. Equal: return the stored
decision, `already_prepared=True`. Different: `ALREADY_PREPARED_OTHER`. Test 3 covers both changes.

**I4. Adding `levers` to the `candidate_l` row: no version bump** (spec §3.1; `registry.py:175-180`). By the rows'
convention every row change bumped the registry version (v2 to v4). The version is checked against stored structure
snapshots (`evaluate.py:469`, `structure_snapshot/build.py:102`), so a bump to v5 would make every stored v4 snapshot
fail `STRUCTURE_COMPOSE` until it is rebuilt.
*Default:* no bump. `levers` changes no value, expression or source. The docstring of `rows_mini_grid.py` records "6a:
`candidate_l` lists its lever; version unchanged (no value changes)". The packet says so.

**I5. The jsonb shapes are left to the builder, and 6c depends on them** (spec §2 `missing`, `assumed`, `admission`,
`dawn`, `settings`; §4 "decimal strings"). Only `settings` has a shape (`{"stop_soc_pct": "70"}`).
*Default:*
- `missing`: a list of `[record_kind, source_family, factor_id_or_null]` triples, the same shape as 6c's JSON line.
- `assumed`: a list of factor ids.
- `admission`: 6c §3.5's object, fractions as `"n/d"`.
- `dawn`: 6c §3.5's object, fractions as `"n/d"` and integers as numbers (see 6c I4).
- `MissingInput` round-trips through the adapter exactly. Test 7 stores and reads back one row of each.

**I6. The persistence guard cannot pass a parenthesised value** (spec §4 guard; `configuration-persistence.ps1:1012`).
The 3C2 pattern is `VALUES\s*\([^()]*\)`. A `CAST(:settings AS jsonb)` inside `VALUES` breaks it, and so would any
function call. The guard also counts one INSERT per writer, but the 6a adapter has seven, one per table.
*Default:*
- Bind jsonb as `:settings::jsonb` (no parentheses), or as SQLAlchemy `bindparam(type_=JSONB)`.
- The new block holds seven per-table INSERT patterns and requires each to be seen at least once (anti-vacuity), as the
  event-store block does with its shapes.
- The advisory-lock `SELECT` and the reads are not writes.
- The two planted failures stay as the spec says.

**I7. The 3C2 people are a class in a test file, not a fixture file** (spec §5 "by the same fixture file and stores";
`tests/test_3c2_agreed_actions.py:101-140` `World`). Copying it would fork the people, and importing a test module from
another test module is fragile.
*Default:* move `World`'s people and Sites setup into `backend/tests/lakeside_people.py` (a plain helper module, not a
test). 3C2's two test files import it unchanged in behaviour, and they must still pass. 6a extends it with the decision
store. The Postgres people come from the same `onboarded` fixture 3C2's Postgres test uses.

**I8. Flag parse failures map to no code** (spec §4). Only `BAD_UUID` and the `--option`/`--none` argparse error are
named. Nothing says what happens on `--current stop_soc_pct` (no `=`), `--amount abc`, `--crew-visits x`, `--horizon x`,
or `--period 2026/10`.
*Default:* argparse takes every value as `str`, and the command maps each failure to the service's code before any
store call:
- a malformed `--current` → `BAD_CURRENT`;
- `--amount` → `BAD_AMOUNT`;
- `--crew-visits` → `BAD_CREW_VISITS`;
- `--horizon` → `BAD_HORIZON`;
- `--period` → `BAD_PERIOD`;
- a UUID flag → `BAD_UUID`;
- a missing `DATABASE_URL` → `NO_DATABASE`, exit 2, as 3C2's `REFUSAL_EXIT`.

Test 8 has one case each.

**I9. The JSON lines' value forms** (spec §4). Settings, amounts and times have no stated form.
*Default:*
- `settings` and `amount` are decimal strings (`"70"`, `"90.00"`, two places for money).
- Times are `%Y-%m-%dT%H:%M:%SZ` (`record_action.py:50`).
- `prepared_by`, `declared_by` and `chosen_by` are display names.
- `home_category` is the code (`OPTIMIZE_COST`).

**I10. An agreed Action with no Site, and `--none` with `--action`** (spec §3.3 H5, §3.5 `state`, plant 9). `agreed_action.site_id`
is nullable (`0070:30`), so `agreed_action_site` returns `None` for a tenant-wide Action. H5 does not say whether `None` is
a mismatch. Nothing refuses `--none --action`, yet plant 9 plants that choice "in the memory store", as though the
service could not make it.
*Default:*
- A Site-less Action is `ACTION_SITE_MISMATCH`.
- `--none --action` is allowed (keeping things as they are can still have an agreed Action) and reads `KEPT_AS_IS`. Plant 9
  goes through the service.

**I11. Words: the horizon sentence and one refusal fixture** (spec §3.4; §5; guide "Open").
- `BAD_HORIZON` "Write the horizon in months, from {least} to {most}." with `most` a `count` of noun `month` renders
  "from 1 to 60 months", repeating "months".
- "Zara reads ... Lakeside's decision → `PERSON_NOT_FOUND`": `for_tenant` takes no person (§3.5), so there is no read
  that can refuse her.

*Default:*
- The sentence becomes "Write the horizon as {least} to {most}." (`least` bare, `most` noun `month`), giving "as 1 to 60
  months".
- `BAD_BASIS` uses noun `character`, as 3C2 does.
- The fixture covers Zara choosing and stating a one-off. The read is tenant-scoped by its argument, and test 7 shows
  another tenant's decisions are absent.

**I12. IA-P's Decisions row shows the Site's name** (spec §3.5; IA-P spec "The list defs", decisions: "Site
(`site_name`)"). `DecisionView` carries `site_code` only.
*Default:* `DecisionView` gains `site_name` (the adapter reads `site.name`; the memory store keeps it). Due stays outside
6a ("Not available yet" in IA-P).

**I13. Where `check_levers` runs, and the key form** (spec §3.1).
- `check_all()` runs `check_pins()` then `check_observed()`. "after `check_pins`" leaves the slot open.
- No rule checks that a filled key matches the database's `option_key` form (`^[a-z0-9][a-z0-9-]{0,63}$`). A template
  such as `stop_{x}` passes start-up and fails only at insert.

*Default:*
- `check_levers()` runs between `check_pins()` and `check_observed()`, on the no-argument path only.
- The two-points-one-key rule also refuses a key outside the `option_key` form (same code). Test 2 adds that case.

## Pre-flight as run here

Code read only; no test was run (no 6a code exists yet). `study.json` sha256 `c52e4755…eccc78b61` confirmed, for 6c's K1.

## Answers (Architect)

*(to be filled)*
