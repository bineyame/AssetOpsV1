# 3B4 reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake round 1 answered, D-3B4.16 to D-3B4.26). Discovery review (W5): a new mechanism on today's Finding store, a migration,
and a name added to a writer's table list. Read `spec.md`, `rulings.md`, then the diff. Done means every question of
spec §9 answers yes with evidence and every plant below fails its named test. Cite the builder's gate run at the same
commit; run nothing heavy unless a finding needs it (`.ai/ROLE_CONFIG.md`).

## What to check, and how

1. **Independent checks (W2).** Tests 1, 2, 4 and 5 write their expected tables and figures as literals from the pack
   (`derived-values.json`), never from `OBSERVED`, `signs` or `observe`.
2. **The rule.** `observe` follows spec §2.2's order exactly; strict `>`; band from the actual `of_factor`; the
   un-carried actual; no `Decimal` quantised; no float.
3. **Unknown is not zero.** No path turns a `None` side or band into 0 (grep `or Decimal(0)`, `or 0` in
   `structure/observe/`).
4. **The store.** No bounds CHECK (D-3B4.24); `input_evidence_sha256` is the Site row's digest read through `store.get` (D-3B4.21); The migration's CHECKs equal 0056's plus the arms (test 10); every INSERT is in the two stores; the
   lifecycle table of spec §4.3 is implemented first-match (test 11); the claim's key set is exactly spec §4.3's 25 keys; money-unit actual, target, gap and band are conditions and stay, a bridge value or effect does not (D-3B4.18).
5. **The sweep (W6).** Re-run spec §4.4's grep on the branch; every reader is class A or in the table; the four
   reader predicates are present, `rows()` filtering all five of its selects (D-3B4.23); `chain/threads.py` is unchanged.
6. **Seams.** `git diff main...HEAD --stat`: no `structure_snapshot/` edit, no `registry.py`, row file, `sources.py`, `i18n/` or `outcome_map.py`
   change; the guard diff is the one `$findingTables` name; check-all and `check-architecture.ps1` pass.
6b. **Imports and seams (D-3B4.20, D-3B4.25).** `observe/rules.py` imports only `registry`, `expressions`, `attribution.rules`; `observe/__init__.py` is a docstring; `check.py` imports `observe.rules` and reads `TARGET_RULE` by a function-local import; the `check.py` commit is after 4a and 3B6 (`git merge-base --is-ancestor`); the actual side is chosen only in `observe_site` (`site.actual`).
7. **Roles.** A Site manager's grant admits only on its own Site; money leaves need the finance lead (test 15); the person is read by `onboard_person` (no `AccountService.tenant_by_slug`, no 3A6/3A7 dependency); `pct` 0 is accepted and gives band 0 (D-3B4.19).

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Must fail |
|---|---|---|
| P1 | `outstanding` declared `DOWN` | tests 1 and 3 and start-up (`STRUCTURE_OBSERVE_DIRECTION`) |
| P2 | `billed_kwh` (a node) added to `OBSERVED` | test 3 and start-up (`STRUCTURE_OBSERVE_LEAF`; never `COVER`, D-3B4.16) |
| P3 | `technical_loss_kwh` moved to `OBSERVED` | test 3 and start-up (`STRUCTURE_OBSERVE_SOURCE`) |
| P4 | `field_visits` moved to `OBSERVED` as UP | test 3 and start-up (`STRUCTURE_OBSERVE_KIND`) |
| P5 | `dawn_days_below` removed from both tables | test 3 and start-up (`STRUCTURE_OBSERVE_COVER`) |
| P6 | `abs(gap) < band` instead of `<=` for inside | test 5 (band equals gap) |
| P7 | band computed from the target's `of_factor` | test 4 (Kobo band 23.6 becomes 14.0) |
| P8 | a `None` band treated as 0 | test 5 (`TOLERANCE_NOT_AVAILABLE`) |
| P9 | `observe_site` reads the carried actual (`site_bridge(...).actual`) | test 6b (Kisiwa `om`) |
| P10 | the service computes the basis over the claim (so `snapshot_as_of` enters it); `basis()` cannot see a snapshot | test 11 (rebuilt snapshot writes) |
| P11 | `UNCONFIRMED` written for an `INSIDE_TOLERANCE` observation | test 11 |
| P12 | the thread-sources predicate removed | test 13 |
| P13 | `finding_detail` predicate removed | test 13 |
| P14 | a SITE_MANAGER grant on another Site admitted | test 15 |
| P15 | a `money` or `effect` key (a bridge value) added to the claim | test 11 (claim key set, literal) |
| P16 | `MONTH_OPEN` check removed | test 14 |
| P17 | `_fence` counts structure revisions | test 13 (fence assertion) |
| P18 | `rows()` `finding` or `finding_revision` select unfiltered | test 13 (`findings` and `revisions` lists) |
| P19 | `rows()` assessment, evidence or merge select unfiltered | test 13 (`assessments`, `evidence`, `merges` lists) |
| P20 | `PCT_INVALID` refuses 0, or band 0 reads the `of_factor` actual | tests 5 and 15 (`pct` 0 cases) |
| P21 | `observe/rules.py` imports `targets.rules` at the top | test 1b (fresh-interpreter imports) |
| P22 | `basis` drops one listed field (for example `target_evidence`) | test 7 (one field at a time) |
| P23 | `input_evidence_sha256` taken from the portfolio row | test 11 (Site row digest) |

## Not findings

- Snapshots served with reason `RULES` after merge (the code digest moves when `check.py` changes).
- The fence still counting fuel, cold and EV revisions (`R-FENCE-FUEL`, D-3B4.9).
- A COLD or EV Site excluded with `STRUCTURE_NOT_OBSERVED` once 3B6 merges (D-3B4.25); `REGISTRIES` keys `OBSERVED` does not name (spec §10).
- No opportunity Findings (D-3B4.4); no words or screen (D-3B4.13); `liability` not observed (spec §11 Q6).
