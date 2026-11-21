# 0K4e handshake, implementer side

Implementer (Claude), 2026-11-21, pre-flight against `main` `0ead104e9` (spec base `fa13f254f`). No product code
written.

Checked and as the spec says:
- The `dispatch_v3.py` anchors `_Index` 152-211, `_evaluate` 253-316 (branch 298-300) and `_control_changes` 333-341.
- `index.control` returns `(value, control, problem)`, and `point(...)` takes the margin third.
- `assessment_inputs.py:183-184` and `BRACKET` 6 h (:32). `postgres_assessment_store._configuration` (:309-340) and
  `_property`.
- The Kobo template's `battery-energy-capacity` sits on BATTERY and `pcs-conversion-efficiency` on
  POWER_CONVERSION_SYSTEM.
- `claim_limit_read.SUPPORTED_MODELS` (:39). `_CANDIDATE_ROLES` matches by prefix (:56, :202), so the longer 3.3
  Candidate reason still maps.
- The worker's reconcile marks a head stale by `head.model_version != MODEL_VERSION` (`assessment_worker.py:193`), as
  E11 needs.
- E1-E3 arithmetic recomputed: need 120, held 95 and 133, 133 >= 132.

## Implementer questions (I)

**I1. The two sections give `energy_to_cover` different signatures.** §2.2 has
`_Index.energy_to_cover(t, feeders_at_t)`; §2.3 calls `index.energy_to_cover(t_meas)`. **Default:** one argument.
The walk reads the feeders at each slot `s` (`self.assets(LOAD, s)`), as §2.2's body already says.

**I2. The module's formatter does not give E1's figures.** The module has a decimal formatter, `_num`
(`dispatch_v3.py:74-77`), and §2.3 says to use it. It normalizes, so E1 reads "95" and "120", not "95.000" and
"120.000". **Default:** use `_num` and no new formatter. E1-E3 assert "95", "120", "133" and "132".

**I3. The new reason and missing texts fail the SC-1 ratchet.** §2.3 treats this as a possible mid-build question,
but it is certain. I ran `ratchet_hits` on §2.3's f-strings and they give rule-a fingerprints, each a `HAND_BUILT_NEW`
(`tools/checks/statement_catalogue.py:385-386`, `:965-970`). The allow classes are SQL, HASH and CODE only (:56).
D-SC1.34 (`specs/SC-1-statement-composer/rulings.md:524-526`) admits a served string to the baseline only when the
spec names the text and a D-ID. These texts are served: segment reasons and missing lists reach the dispatch reads.
**Default:** a ruling (D-0K4.x) that names §2.3's four new texts as baselined, in the same class as the 46
`dispatch_v3.py` fingerprints already there. Moving `dispatch_v3`'s texts to SC-1 statements stays a later unit of
its own. If you rule the texts must be statements now, the unit grows by about 0.5.

**I4. The walk multiplies the assessment's cost.** `lookup_asset` scans a channel's rows linearly on every call
(`dispatch_v3.py:179-181`). §2.2's walk does that for each feeder and for PV at every 5-minute slot, up to the read
range's end, for every evaluated ON point. A 30-day reassessment then grows by roughly the night's slot count, which
matters for the reconcile job. **Default:** keep a per-`_Index` memo of each slot's `(load - pv)` or its problem,
keyed by the slot instant, so each slot is looked up once per assessment. The results are identical (E1-E8
unchanged). The packet records `assess()` wall time for one window on 3.2 against 3.3.

**I5. The fixture E9-E11 and pre-flight item 3 name does not exist.** "The DS1 Kobo history producer" is not a test
fixture. DS1 is the CLI `tools/world_history.py`; `test_3a1_commercial_service.py:513-520` runs it over
`view_v1.json`, which gives 7 record files. The dispatch Postgres tests use the S4 case-runner world
(`test_4d_litre_split_postgres.py:17`, `CaseRunner`). Nothing loads October Kobo telemetry with dispatch assessments
into a `*_test` database. **Default:**
- E9-E11 use the `CaseRunner` world plus one planted night of battery-support Candidates.
- Precondition: on 3.2, at least one Candidate segment reaches the battery-support branch, so E9's "at most" is
  proved on a non-empty set.
- Pre-flight item 3's counts are taken over that fixture's days and labelled as such, not as "1-31 Oct".

**I6. §5 and §2.4 miss four downstream effects.**
- (a) `actions/verification.py:258-262` refuses a baseline whose days mix model versions
  (`VERIFICATION_MODEL_NOT_COMPARABLE`). On a telemetry database, verifications refuse between deploy and the end of
  the reconcile pass.
- (b) The S3 lineage and performance reads are keyed on `MODEL_VERSION` (`main.py:462`, `performance_migration.py:30`).
- (c) `structure/rows_mini_grid.py:62-67` serves source texts that say "dispatch-3.2 (...)". These are baselined
  fingerprints, and editing them makes new ones.
- (d) `claim_limit_read._role_of` (:88-92) maps none of the new missing texts to a role, so a 3.3 Indeterminate
  energy segment shows every role COVERED.

**Default:** no code change for (a), (b) and (d). §5 and the packet state (a) and (d), and E10 asserts (d). (c) stays
as it is (it names the rule family) and is classed "history" in the sweep.
