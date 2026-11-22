# Review: DD2.2 profile `bool` type (commit 0db0c72de, `task/DD2-books`)

## Round 1: discovery review (2026-11-22)

**Verdict: ACCEPT.** No High or Medium findings. Two Low findings, neither blocking; fix on the branch when convenient.
Judged against DD spec §7 DD2.2, D-DD.24 and handoff Q9. Every acceptance point holds: `bool` is in `TYPES`; a bool
path must carry a map whose values are exactly `{"true","false"}` (`ProfileInvalid columns.N.paths.M.map`, and
`NATIVE_LAYOUT` in `check_layout`); a bool path without a map is refused; a map on a non-bool, non-coded path is still
refused; the cell writes a JSON boolean; an unmapped cell is refused `NATIVE_VALUE` (Q9). The change is minimal and
backward compatible: before it, a map was allowed only with type `text`, so the new `bool` branches and the P5 skip
(`path in column.maps`) change nothing for any existing profile or layout (3A3 and 3A6 suites pass unchanged). It
follows the coded-path pattern (map declared on the path object, refused at `.map`, map miss is `NATIVE_VALUE`, probed
by P4), so it is consistent with how other native types are declared and refused. The 12 tests catch each mutation
tried (see Checks). No consumer outside `contracts/` has to learn about `bool`; see Consumers.
Counts: High 0, Medium 0, Low 2.

### Findings

**L1 (Low, contract tightness): `bool` is accepted on coded and identity paths.**
`contracts/assetops_contracts/native/profiles_v1.py:201` (`allowed = (type_ == "bool") or ...`) and
`contracts/assetops_contracts/native/layouts_v1.py:142` accept `type: "bool"` on any path. I probed this: a profile
with `kind` (a `CODED_PATHS` member) as `bool` compiles and reads `kind: True`, and `source_record_id` as `bool` reads
`source_record_id: True`. Before this change a coded path could only be `text`. The spec calls bool "the one exception
to 'a map sits only on a coded path'", which assumes a bool path is not a coded path. Today the envelope/records
parse at admission would refuse such a record, so nothing wrong gets in, but the refusal comes at a later layer with a
less precise code. It matters because this is a protected seam that every profile goes through.
Fix: at compile time refuse `bool` on a path in `CODED_PATHS` or on `source_record_id`, giving `ProfileInvalid
{pw}.type`, with the same rule in `check_layout`, plus one test for each. A preference, not an acceptance gap.

**L2 (Low, documentation drift): the 3A6 spec still lists the old type set.**
`specs/3A6-source-profiles/spec.md:83` lists the path-object types without `bool` and says "`map` only with type
`text`". This file is the reference for the profile format. Fix: add `bool` and the bool map rule there, citing
D-DD.24 (or add a one-line pointer to DD2.2).

### Consumers checked
- `backend/assetops_backend/commercial/profiles.py`: admission step 4b (`ADMIT_MAP_UNCOVERED`) iterates all maps, so a
  bool map's keys must both appear in the sample. That is the right behaviour, and nothing needs changing. Steps 4c
  (`_DATED`, `number`) ignore `bool`, which is correct.
- `layouts_v1.is_profile_shaped`: a bool column has `types`, so its layout is never rendered. `_cell`'s reverse-map
  path is therefore never reached with a boolean.
- I found no frontend, simulator or world-exporter code that branches on profile types (grepped for `month_of` and
  `types.get`).

### Checks run
- `PYTHONPATH=<wt>/contracts:<wt>/backend heavy-slot -- pytest contracts/tests/test_dd2_bool_type.py
  test_3a6_profiles.py test_3a3_native_layouts.py -q`: **169 passed** (66 s). Imports resolve to the worktree.
- `ASSETOPS_GUARD_PYTHON=... pwsh tools/check-architecture.ps1`: **Architecture check passed.**
- Mutations, each reverted with `git checkout`; the tree is clean afterwards:
  M1 write the text instead of the boolean: 1 failed. M2 drop the "bool needs a map" refusal: 1 failed.
  M3 drop the P5 skip of mapped paths: 1 failed. M4 drop the `check_layout` bool-needs-map rule: 1 failed.
  M5 drop the exact `{"true","false"}` check: 5 failed.

### Not verified / residual risk
- I did not run any full suite (none needed for a contracts-only diff, per §7).
- Downstream acceptance of a boolean `body.block_met` by the records/envelope parse for `DEPARTURE` is DD2.4's job.
  The first real bool profile (ev-departures) should be admitted end to end, with its expected file holding JSON
  booleans.
- `record_id_join` or `version_digest` over a bool column uses the mapped text (`"true"`/`"false"`), the same as coded
  maps. It is untested, but there is no current use.
