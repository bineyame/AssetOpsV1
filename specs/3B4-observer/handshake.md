# 3B4 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main` (spec §0 (a) to (c)), write their questions here in one batch. Number them R1,
R2 ... and I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects,
and is marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Round 1, written 2026-11-21 against `main` at `12a0c6356`. Verified clean (no question): F1's expected table matches
`Docs/demo-sprint/product-direction-layer4/derived-values.json` for all three Sites (every other observed leaf is equal
on both sides; Kobo band 2 % of 1180 = 23.6, Kisiwa 48); no served text is added (the `title` is a code, no reader
reached by an observer Finding shows it once the four readers change; D-SC1.28 does not hold 3B4).

- **R1 (done), §2.3 `COVER` and `LEAF`; reviewer guide P2.** `COVER` refuses "an entry that is not a leaf ID of the
  registry", and runs before `LEAF` (code-major). `billed_kwh` is a node of the registry (`rows_mini_grid.py:106`), so
  P2 (`billed_kwh` added to `OBSERVED`) raises `COVER`, never `LEAF`, and `LEAF` cannot fire for any real node.
  Expected: `COVER` refuses only an entry that is no row of the registry; a node is `LEAF`'s; P2 and test 3 then name
  distinct codes. If `COVER` keeps both, `LEAF` is dead code and P2's "must fail" code is wrong.
- **R2 (done), reviewer guide plants P12/P13 and test 13.** Four readers change but only two have a plant (the threads
  predicate, `finding_detail`). Removing the `_fence` predicate or the `rows` predicates is caught by test 13 only if
  that test asserts each. Expected: plants P17 (`_fence` counts structure) and P18 (`rows` returns a structure row, in
  any of its selects, see I4) each fail a named assertion of test 13, so "each plant fails its named test" (§9 Q8) covers
  all four predicates.
- **R3 (done), §1, §4.3 claim, P15.** The spec says a Finding "never claims money" and P15 plants "a money gap
  written into the claim", yet the claim holds `actual`, `target`, `gap` and `band` for `outstanding`, `in_transit`,
  `om`, `staff`, `tariff` and `diesel_price` in their money units (278.00 USD), which §1 itself states. Expected: "no
  money" means no bridge value or effect of acting (no `money`/`effect` key, no priced line); a money-unit leaf's own
  figures in its own unit and currency are the condition and stay. Say so in §4.3 and P15, and have test 11 assert
  the claim's key set literally (not "no key containing money").
- **R4 (done), §5.3 `PCT_INVALID` against D-3B4.5/D-3B4.6.** `pct` must satisfy `0 < pct <= 100`, but `unexplained_l`
  carries a structure default of 2 % (`rows_mini_grid.py`, `Tolerance("diesel_l", 2.0)`), and `CLEARED` returns to that
  default. So no Site can declare zero tolerance on `unexplained_l` (raise every adverse deviation, the design's own
  default for an unset tolerance); the DB regex already admits `0`. Expected: `0 <= pct <= 100` accepted, a `SET`
  with pct 0 gives band 0, and test 5 adds that case; otherwise say it is deliberate.

## Implementer questions (pre-flight results first)

**Pre-flight (a), run on `main` (read only, no database).** Signs of §2.2 over `BRIDGE_ROOTS["MINI_GRID"]`
(`contribution`, `collected`), by a scratch walk of `registry.parsed_text` with the spec's rules: every one of the 19
`OBSERVED` leaves is reached, none with both signs, no `Call`, `/`, `Num` or `*` of a non-`Ref` below any root. UP
leaves all `{-1}`: `unexplained_loss_kwh`, `adjustments_kwh`, `unmapped_kwh`, `in_transit`, `outstanding`,
`necessary_l`, `candidate_l`, `unexplained_l`, `diesel_price`, `om`, `staff`. DOWN leaves all `{+1}`: `delivered_kwh`,
`tariff`, `productive_kwh`, `productive_tariff`. Not reached: the four Protect observed leaves (`reduced_days`,
`unserved_critical_kwh`, `customer_hours_interrupted`, `dawn_days_below`). The reached-but-not-observed leaves
(`technical_loss_kwh`, `extra_l`, `battery_throughput_kwh`, `wear_rate`, `collection_cost`) match §2.1's reasons by
`filled_by.family` (DECLARED) and `absent` (OPTION_ONLY); `period_days` is CALENDAR/NEVER_EMPTY. No disagreement. Note
the registry has no `family` attribute on a row: it is `row.filled_by.family` (and `home` may be `None`), which §2.3's
`SOURCE` and `KIND` must read that way.

**Pre-flight (b), the sweep on `main`.** The §4.4 grep, extended to aliases (`finding f`, `INTO/UPDATE finding`), finds
no unlisted reader that breaks on a `structure` row. Unlisted but harmless, classes: `thread_sources._FINDING_LIFECYCLE`
(whole-Site scan of `finding_revision`; consumed only through a thread's occurrences, `lifecycle_run.py:83`, which a
structure Finding never has: class unchanged, as the spec says); `work_read._FINDING_TITLES`, estate `_created` and
`_with_mechanism`, `finding_store.index_lineage_on`, `domain_action_index` (all by revision or Finding id: class A);
cold, EV and fuel readers filter their own domain (class A). `_FINDING_SOURCES_BY_ID` is built by `replace` on the
`ORDER BY`, so a predicate added before it is inherited, as §4.4 assumes. **One fifth reader, inside a listed
one:** I4. The `financial_consequence_dirty` trigger is narrowed to `mini_grid` by 0022 and not widened by 0056, so
it does not fire (the spec says "mini_grid and cold_chain"; the cold one is its own trigger, no change).

**Pre-flight (c).** Not run: F2's world (`test_5b_attribution._world()`, `READ_AT` from `test_3a4_commercial_months`)
may need a database; not touched in this round. Unit 3 prints it first. `READ_AT` is imported, not defined, in
`test_5b_attribution.py:40`; the spec should cite it that way.

**Guard (§4.5).** Confirmed: `$findingTables` (`configuration-persistence.ps1:753`) is the one list read at the two
sites (the writer's own-statement check at :1331 and the other-modules check at :1711); `structure_tolerance` joining
it needs no new block, provided `tolerance_append` is a plain `INSERT INTO structure_tolerance` in
`postgres_finding_store.py`. Every write line of that file must then be an INSERT into the list (:1331), so the
tolerance read must stay a `SELECT`. No question.

- **I1 (done), §2.3 imports.** `check.py` would import `observe.rules`, which reads `TARGET_RULE` from
  `structure/targets/rules.py`; that module imports `structure.evaluate` (line 15), and `evaluate.py:22` imports
  `StructureError` from `check`. A top-level import in `check.py` is a cycle. Expected: `check_observed` imports
  `observe.rules` inside the function (as the spec's "reads the real table at call time" allows), `observe/rules.py`
  never imports `check` at module level, and a test imports `structure.check` first in a fresh interpreter.
- **I2 (done), §4.3 `input_evidence_sha256` = "the snapshot's `payload_sha256`".** The decoded `SiteMonthSnapshot`,
  `PortfolioMonthSnapshot` and `Served` carry no payload digest; it is on `SnapshotRow` (`model.py:48`) inside the
  store. Which digest (a Site row's or the portfolio's), and how does the service obtain it without editing
  `structure_snapshot/`? Expected: the Site row's, taken through a public read of the store row; or recompute
  `codec.digest` of the decoded Site snapshot's canonical form and say so; the value must not enter `basis`.
- **I3 (done), §5.2 and §5.3 account calls.** `AccountService.tenant_by_slug` does not exist on `main`: `tenant_by_slug`
  is on the store (`accounts/store.py:37`) and the service calls `self._store.tenant_by_slug` privately; the spec cites
  it "from 3A6", which is unmerged. The `--as` precedent (3A7 Q1) is unmerged too, `declare_objective.py` takes no
  person, and `onboard_person(email)` returns an `OnboardPerson | None` whose active state and `(role, site_id)` pairs I
  could not confirm. Expected: name the exact public calls for tenant by slug and for an active person's grants by
  email, or list 3A6 and 3A7 as gates in §0 (units 2-3 start only after both merge).
- **I4 (done), §4.4 `rows`.** `rows()` runs five selects (`postgres_finding_store.py:263-277`), the spec changes two.
  `SELECT * FROM finding_revision_assessment` (the `cites` list) is Site-wide and would list every structure revision's
  assessment link, dangling against the `revisions` list the predicate removed; the evidence select is empty for the
  new domain. Expected: the assessment select joins `finding_revision` and takes the predicate too; test 13 asserts
  `rows()["assessments"]` holds no structure link.
- **I5 (done), §4.1 `finding_revision_structure_bounds`.** `episode_start` and `episode_end` are already `NOT NULL`
  (`0009_finding_store.py:82-83`), so `CHECK (domain <> 'structure' OR (... IS NOT NULL ...))` can never fail. Expected:
  drop it (less migration, a simpler downgrade, test 10 loses one assertion); say so in §4.1.
- **I6, §0 and D-3B4.14 sequencing.** `4a` (registry v4, nodes only: `metered_kwh`, `billed_kwh`) and `3B6` (cold and EV
  registries, `check_all` order) touch `check.py`, rows and sources; units 2 to 4 touch the Finding and assessment
  stores, `chain/adapters`, `permissions.py` and the guard, none of which either slice edits. Why must units 2-3 wait
  for them? Expected: they need not, apart from gate A's migration number and I3's gates; only the `check.py` edit is
  last. If so, state it, so the lane is not idle while 4a and 3B6 are open. Also state that with 3B6 merged
  `REGISTRIES` holds COLD and EV keys that `OBSERVED` does not name, and that this is intended (§10) and not a `KEY`
  fault.
