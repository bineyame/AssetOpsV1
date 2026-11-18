# W2 cold technical design review - D-2026-10-17-w2-techdesign-cold

Reviewer: fresh Claude reviewer (independent, not the author). Targets: `.agent/W2-technical-design-cold.md` and the amended `.agent/architect-W2-design.md` at 04170b25, judged against `.agent/architect-W2-techdesign-cold-request.md` (B1-B9) and `.agent/W2-design-review.md`. I made read-only spot checks against the code and ran no suites.

## Verdict: RETURN (targeted amendment)

The design is substantially concrete. It has an exact v4 kind/outcome allowlist, typed event columns, the thermal update equation with default values, excursion bounds and hysteresis, claim levels, money gates, routes and fixtures. M1 and M2 are closed. Five Medium findings remain. Three contradict existing schema or guards, and two leave choices to the implementer that the owner's bar excludes. All five are fixable in place. W2-01 can still start, because none of them touch its scope except the Low on roles and bindings.

## Findings

**M1 - Generalising the Finding store stops at `finding`. `finding_revision` is still dispatch-shaped, and the domain value is wrong.** (B2/B5, acceptance gap)
- `0009_finding_store.py:80-84,102`: `episode_start`, `episode_end`, `candidate_minutes`, `necessary_minutes` and `indeterminate_minutes` are NOT NULL, with CHECK `episode_start <= episode_end`. A cold open episode or an unknown-start episode (design §5) has no value for these columns. The design never says how cold fills or relaxes them, nor what fills `support_sha256`/`cited_evidence_sha256`. `analytic_run.cohort*` (`0007:48-50`) is likewise unmapped for cold.
- Design §2 adds a CHECK "retaining `generator_asset_id` for `domain='DISPATCH'`". The stored value is `'mini_grid'` (`analytics/finding_episode.py:78`, written at `postgres_finding_store.py:159`), and recompute uses `'dispatch'` (`assessment_worker.py:56`). As written, the CHECK protects no existing row. The cold domain strings (`COLDCHAIN` for Finding, `cold` for recompute) are also inconsistent.
- Fix: give the exact cold mapping or the nullable relaxation, with CHECKs keyed on `'mini_grid'`, for every NOT NULL dispatch column of `finding_revision` and `analytic_run`. Name one domain literal for each table.

**M2 - The S2 conflict codes contradict the existing ledger, and "quarantine" is undefined.** (B1)
- The design names `MESSAGE_ID_CONFLICT`, but the existing kind is `MESSAGE_CONFLICT` (`0005:239`, `ledger_reads.py:232,376`). Renaming it would change Receipt V2 bytes, which the design says stay stable.
- For `EVENT_ID_CONFLICT`, the design does not specify:
  - which `ingestion_disposition.decision` value is written (`REJECTED` or `CONFLICT`);
  - whether `conflicts_with_evidence_id` is set (CHECK `evidence_rejection_conflict_kind`, `0005:240`, forbids it for any kind but `MESSAGE_CONFLICT`);
  - how receipt counts classify it (`ledger_reads.py` puts any other kind under "rejected").
- "`evidence_rejection.kind` accepts event conflict codes": `kind` has no allowlist. The CHECK at line 240 is the constraint that matters. "Recompute domain check includes cold (if constrained)": it is not constrained. That hedge should be resolved.
- Fix: keep `MESSAGE_CONFLICT`, and state the decision value, the conflict reference and the CHECK change for `EVENT_ID_CONFLICT`.

**M3 - New writers and new tables are not placed under architecture guard rule 8.** (B2)
- `tools/checks/configuration-persistence.ps1:601-660,700,710` pins a closed list of Postgres writers, each confined to its own tables, plus an `ON CONFLICT` allowlist.
- The design adds `cold_episode*` (0022) and `cold_consequence*` (0023), and an event-uniqueness race whose loser "receives a conflict disposition". It does not name the writer modules (new writers, or extensions of the assessment, Finding and consequence stores), the rule 8 table lists, or the `ON CONFLICT ON CONSTRAINT <event unique>` allowlist entry. That is an architectural choice left to the implementer.
- Fix: name the owning adapter for each new table and the exact guard edits.

**M4 - The scenario forcing is unspecified, and the defaults cannot produce the excursion demo in the window.** (B4)
- §4 gives only scenario file names and "explicit forcing list". It gives no times, assets, door schedule or initial thermostat phase.
- With the stated defaults, passive warming is 0.08*(20-T)/1.2, about 0.019 degC/min. From 3 degC the chamber needs about 53 min to exceed 4 degC. A 19:00-20:00 window therefore cannot yield the 15-minute lower-bound exposure Finding (§5) unless the implementer tunes the forcing, door heat or initial T. That is a modelling choice, and close to "forcing to the mock".
- Further open points:
  - `cold-contradictory` is "a second incompatible state ... **or** an invalid role/kind mapping".
  - The ">0.4 degC between two primary probes" rule cannot arise, because `cold-roles-1` allows one calibrated chamber probe per room (§3).
  - "If composing with mini-grid" leaves standalone-versus-composed open.
- Fix: per scenario, give a forcing table (time, kind, asset, value), the initial state, and which demo claim each case must produce. Pick one contradiction mechanism, and either allow a second chamber probe role or drop the probe-disagreement rule. State standalone or composed for W2-02.

**M5 - Several response fields are named but have no shape, and the capability vocabulary is open.** (B7)
- These fields have no field-level shape:
  - overview `objective`, `temperature_summary`, `backup_summary`, `causal_strip`, `needs_attention`, `consequence_summary`;
  - temperature `gaps`;
  - evidence `capabilities[].claim`, with no enumerated claim list;
  - the `currentness.state` vocabulary;
  - `source_provenance` and `limitations`, which are only referenced.
- Fix: enumerate the claim IDs and currentness states, and give the inner fields of each summary object, or cite the exact W1 read model each one reuses by path.

## Low (non-blocking)
- L1 `binding_roles.py:43-46`: `Role.value_kind` is `NUMBER|STATE`. `cold-roles-1` needs EVENT and FOUNDATION_CONTROL policy roles, and the binding `conversion` for an EVENT role is unspecified. "ONE per attempt" is not a binding cardinality.
- L2 `host/lab_execution.py:1075`: persisted discrete validation is the generator lifecycle (`_LIFECYCLE`). Cold states such as compressor, door and transfer need a per-model vocabulary. The kernel catches fuel's `PhysicallyUnacceptable` (`execute.py:97`), and the cold failure guards should name it. Model selection is already an identity registry (`execution_adapter.py:127`), and mapping selection is already per profile (`mappings.py:138-143`), so "closed registry" means extending these.
- L3 The derivation of `overlap_group` is unstated. `cold-door-heat` is kWh per minute but is labelled kWh.

## Checks against the questions
1. Concreteness, B1-B9:
   - Concrete enough: B1 (except M2), B3, B6, B8, B9.
   - Open choices remain: B2 (M1, M3), B4 (M4), B5 (one detail inside M1/M4), B7 (M5).
2. Correctness against the code:
   - The 0020 change is safe for existing MEASUREMENT rows: the new columns are nullable, the family CHECK matches the rows already present, and the `accepted_evidence_append_only` trigger already covers added columns. Rule 8 is the gap (M3).
   - SourceEnvelopeV3 is correctly identified as the active path (`ledger.py:279` refuses non-MEASUREMENT).
   - For `models.py`, L1 from the earlier review is handled: `SITE_TYPES`, the component types and `degC` are all named.
   - The `financial_consequence_revision` fuel-only CHECK is correctly avoided.
3. Fail-closed rules and W1 reuse are sound:
   - No interpolation or gap bridging.
   - Missing steps are UNKNOWN.
   - Temperature never means spoilage.
   - Amount is null unless RECORDED.
   - There is no overlap summing.
   - LR and S4-05 gates and plain copy apply by reference.
4. M1 is closed: v4, typed storage, mapping allowlist and migration 0020. M2 is closed: W2-05a/b, and W2-02 names pack selection. The L2 owner questions were added as decisions 4 and 5.

## Not verified
I did not run any suites or the registry checker. I did not check the v69 panel numbering line by line, and I did not trace the 0014 clock-attestation join.
