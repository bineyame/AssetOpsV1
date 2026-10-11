# Dispatch analytic decision table (S3-01, model `dispatch-3.1`)

Authority: `D-2026-10-11-s3-dispatch-interval-assessment`, `D-2026-10-11-s3-phase-1-fixture-and-late-evidence`, task `tasks/S3-01-dispatch-assessment.md` ("`dispatch-3` comparison table"). Baseline: `backend/tests/dispatch_decision_table.md` (`dispatch-2`, kept unchanged and readable for historical file-backed revisions). Version bump: `D-2026-10-11-s3-phase-3a-version-and-cutover`.

Analytic: `backend/assetops_backend/analytics/dispatch_v3.py` (pure). Inputs: `analytics/assessment_inputs.py` (`EvidenceQuery`, `AnalyticInputSet`). Cohort: `analytics/cohort.py`. Tests: `backend/tests/test_s3_dispatch_v3_analytic.py`, `test_s3_dispatch_assessment_postgres.py`. Every threshold below is a named constant; changing one is a new model version and therefore new revisions.

## Model versions

| Version | Differs from the previous version | Status |
| --- | --- | --- |
| `dispatch-3` | first durable model (phase 2) | historical: stored runs, revisions and URLs stay unchanged and readable; a pinned run/revision carries `model_note: OLDER_RULE_RESULT ...`; never selected as CURRENT under `dispatch-3.1` |
| `dispatch-3.1` | (Q9) two or more sequence epochs of one source in a UTC window give a default `AMBIGUOUS` cohort even when the spans do not overlap ("Successive epochs"); (Q13) every interval limitation is lifted into the window list as `INTERVAL_LIMITED: ...`, so a `LIMITED` window always names its reason ("Claims") | current. The worker's reconcile pass enqueues every window whose last DEFAULT selection used another version and reassesses it through the normal job path; explicit cohort selections are point-in-time choices and are not remapped |

Every rule, threshold and branch below is the `dispatch-3.1` rule. The model version is in every `input_sha256` and `basis_sha256`, so a version change always appends new revisions under the same keys.

## Inputs (accepted public evidence and selected public configuration only)

| Input | Source in `dispatch-3` | `dispatch-2` source | Change |
| --- | --- | --- | --- |
| Generator state | role `generator_state` (instant) and `generator_power` (5-min mean, at interval end) | device/signal strings | re-keyed by canonical role and asset |
| Load | role `feeder_demand`, every asset bound to it at t (selected binding set) | three hard-coded meters | bound assets, not a fixed list; any missing asset makes load unusable |
| PV available power | role `pv_available_power` (`minigrid-roles-2`) | `pv-inverter-controller/available-power` | needs the roles-2 binding; observed `pv_power` never substitutes |
| PCS discharge capability | role `pcs_discharge_capability` (`minigrid-roles-2`) | `battery-pcs-controller/discharge-capability` | as above; rated or actual `battery_power` never substitutes |
| Battery SOC | role `battery_soc` (instant) | device/signal | re-keyed |
| Battery reserve | selected Foundation control `reserve-state-of-charge` effective at t, known at the run's cutoff | POLICY record or reserve override | changed: Foundation control only; no POLICY reading is invented |
| Minimum runtime | selected Foundation generator property `minimum-runtime` | POLICY record | changed (row 2 below) |
| Operator override | none (S2 V3 is measurement-only) | OPERATIONAL_RECORD | removed: alternative stated unavailable |
| Fuel level, SFC | not used | SFC for indicative fuel | removed: no fuel or money in S3 (Q6) |

Readings are placed by source time (an interval mean at its interval end), never by receipt or publication time. Each reading keeps its as-accepted Foundation and binding revision IDs. Its role is the one recorded at acceptance, not today's mapping. Controls and role coverage come from the Foundation and binding revisions selected for each instant at the run's knowledge cutoff. This is how a backdated publication changes a later run. The input hash covers both sets of revisions.

## Windows, cohort and series

| Rule | Value | Note |
| --- | --- | --- |
| Assessment window | UTC day `[00:00, 24:00)` | worker unit; an explicit window may be any half-open range |
| `BRACKET` | 6 h each side | bracketing evidence for bounds and continuity; also the neighbour-window reach of a recompute job |
| Interval ownership | an interval belongs to the window containing its first ON report | a neighbour window assesses intervals that start there |
| Default cohort | the streams `(gateway, source, sequence epoch)` with a reading inside the window | a stream seen only in the bracket is neither pulled in nor named (it would change the window's basis whenever a neighbour day receives evidence) |
| Ambiguous cohort | one source reports overlapping source-time spans under two or more epochs | window `INDETERMINATE`, `AMBIGUOUS_COHORT` names each epoch; no interval is assessed; an explicit cohort selection assesses one choice under a cohort-suffixed key |
| Successive epochs (phase-3 amendment, review F3) | non-overlapping epochs of one source inside one window | `AMBIGUOUS` like overlap: central evidence has no attested marker separating a reprovisioned gateway from a labelled fault fixture placed beside ordinary evidence, so the default cohort never blends epochs; an explicit selection may name several non-overlapping epochs |
| `REPORTS_OVERLAP` | two readings at one channel-time in one stream | span unusable (covers same-role contradictions and same-epoch run overlap) |
| `SEQUENCE_ORDER_INVERTED` | a reading sequenced after another of its channel but placed earlier | span `[earlier, later]` unusable; never re-sorted by receipt |

The cohort never uses an epoch name, a manifest label, a Lab run ID or receipt order. Same-epoch overlapping runs (Q3) show up as `SEQUENCE_ORDER_INVERTED` and `REPORTS_OVERLAP` over the overlapped span. A labelled fault-fixture epoch is a separate stream. If it shares a window with an ordinary epoch of the same source (overlapping or not), the cohort is `AMBIGUOUS`. If it stands alone, its readings are assessed with the same limits and are never blended into another stream.

## Interval reconstruction (carried from `dispatch-2`, re-keyed)

| `dispatch-2` portion | `dispatch-3` | Status |
| --- | --- | --- |
| ON = RUNNING, else mean > 0; OFF = STOPPED/STARTING/FAILED, else mean = 0; otherwise UNOBSERVED | same; contradictory statuses or a cohort limit at the report time give UNOBSERVED | carried, plus limit |
| `CONTINUITY_TOLERANCE` 20 min | same | carried |
| Lower bound = observed segment spans; upper bound = OFF before to OFF after, open if absent | same; also open when the OFF lies beyond the bracket | carried |
| A positive mean is not a whole interval of runtime | same | carried |

## Segment evaluation

Each point uses interval means ending at t, or the latest instant in `(t - INSTANT_TOLERANCE 10 min, t]`. Distinct GOOD values at one rank are `CONFLICTING`, and nothing uses them. A cohort limit touching the lookup range is `AMBIGUOUS_SERIES`. `SOC_HEADROOM_POINTS` = 10. `CAPABILITY_HEADROOM` = 10 %.

| Row | `dispatch-2` | `dispatch-3` | Status |
| --- | --- | --- | --- |
| 1 | operator override → Necessary | unavailable (no V3 command record). The alternative says "no command record observed", never "no command occurred" | removed |
| 2 | within the minimum-runtime POLICY of first ON → Necessary | uses the Foundation `minimum-runtime` value effective at the part's start. A point is possibly inside the minimum runtime if `t - first ON report < minimum runtime`; the first ON report is the latest possible start. A Candidate there becomes Indeterminate. No policy Necessary is claimed from a configured value. Physical rows 3 and 4 still apply | changed (fail-closed) |
| 3 | SOC <= reserve + 10 and load > PV available → Necessary `BATTERY_AT_RESERVE` / `BATTERY_NEAR_RESERVE` | same, with the reserve from the Foundation control | carried |
| 4 | load > PV available + discharge capability → Necessary `CAPABILITY_SHORTFALL` | same | carried |
| 5a | PV available >= load × 1.1 with discharge capability usable → Candidate | same; both capability roles must be bound and accepted | carried |
| 5b | SOC > reserve + 10 and PV + discharge >= load × 1.1 → Candidate; SOC inside headroom → Indeterminate | same | carried |
| 6 | otherwise Indeterminate, naming each missing, conflicting or headroom reason | same, plus `missing role` (unbound in the selected role set), `NOT_GOOD` (UNAVAILABLE quality, Q2) and `AMBIGUOUS_SERIES` | carried, extended |

Segments use the both-ends rule: Candidate only if both ends are Candidate; Necessary if either end is; otherwise Indeterminate. This is carried. A segment is split where the reserve or minimum-runtime control takes or leaves effect strictly inside it. The ends use the reports' own measurements and the part's control, as in `dispatch-2` (carried, now for Foundation controls). A segment touched by a cohort limit on a point role is Indeterminate and names the limit (new). A gap or unobserved segment is Indeterminate and counts only in the upper bound (carried).

## Claims

| Segments | Interval claim |
| --- | --- |
| all Necessary | `NECESSARY` |
| any Candidate | `CANDIDATE_AVOIDABLE`, bounded to the sum of Candidate segment durations; Necessary and Indeterminate portions listed separately; no edge allowance (changed: `dispatch-2` added edges for fuel) |
| otherwise | `INDETERMINATE` |

Confidence is carried: High, dropping one level each for an Indeterminate portion, a margin below `STRONG_MARGIN` (25 % of load), and transition uncertainty above `TRANSITION_LIMIT` (15 min) or an open bound. The open bound is a new drop reason. The window claim is `COMPLETE` with no limitation, `LIMITED` when any limitation is named (missing role, cohort limit, open bound, configuration, or an `EVIDENCE_GAP` for any segment left Indeterminate by missing, poor-quality or conflicting evidence or a generator-state gap; restores `dispatch-2`'s rule, which an earlier `dispatch-3` draft dropped), and `INDETERMINATE` when no cohort could be selected or the generator series itself carries a cohort limit (`GENERATOR_SERIES_AMBIGUOUS`: intervals cannot be reconstructed there). Every interval limitation (for example an open bound) is lifted into the window list as `INTERVAL_LIMITED: interval from <first_on>: <limitation>`, so a `LIMITED` window never carries an empty limitation list. A capability role unbound over part of the window is named with its span (`MISSING_ROLE ... over start..end`). No Finding, fuel quantity, saving or money is produced (S4).

## Basis, runs and revisions

- `input_sha256` covers the window, read range, cohort selection and limits, sorted evidence IDs with their envelope digests, as-accepted revision triples, selected controls (value and validity), selected bindings, role coverage, configuration limits and model version. It does not cover `knowledge_at`, so replaying the same basis at a later cutoff gives the same run.
- An interval `basis_sha256` covers the model version, the interval's evidence IDs and digests, the selected controls and its result. A window `basis_sha256` covers the model version, the input hash and the window result. A new revision is appended only when the basis differs from the latest revision under the same key.
- Keys: `dispatch:window:<window start>` and `dispatch:interval:<generator asset>:<first ON report>`. An explicitly selected cohort adds `:cohort:<identity prefix>`.

## Comparison with the file-backed `dispatch-2` claims (Performance cutover)

`analytics/performance_comparison.py`. A legacy claim is compared with the one selected `dispatch-3.1` interval overlapping its running span. A selected interval of another model version (`STALE_MODEL`) or one whose window has a PENDING, LEASED or FAILED recompute job (`STALE_PROJECTION`) is `UNPROVEN`, even when the claim levels match. `MATCH` also requires every cited record to be accepted and in the selected interval's evidence (a comparable basis; default built, `.agent/S3-01-questions-4.md`). A cited record not accepted centrally is `MISSING_SOURCE`, which keeps the gate closed; it is not parity. A claim change is `INTENTIONAL_DELTA` only through a documented, claim-specific rule difference below. The selected interval's own segments must name the limitation, and every record the legacy claim cites must be accepted and in that interval's evidence. A limitation elsewhere in the window does not qualify. Anything else is `UNPROVEN`. There is no catch-all.

| Rule | Legacy claim | `dispatch-3.1` claim | Interval limitation required | Table row and change |
| --- | --- | --- | --- | --- |
| `CAPABILITY_CHANNELS_REQUIRED` | `CANDIDATE_AVOIDABLE` | `INDETERMINATE` | a segment names `PV available power: ...` or `PCS discharge capability: ...` | rows 5a/5b: `dispatch-2` inferred available PV and discharge from observed `pv_power`/`battery_power`; `dispatch-3.1` requires the accepted `minigrid-roles-2` capability channels |

The gate also refuses if the report was made under another model version, or if any window is still selected under another model version (lineage `selected_heads_other_model`). An empty legacy-claim set passes only as a zero-inventory statement, not as claim parity.
