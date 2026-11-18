# W4-01 / W3-01 closure check (2026-10-20, main e109f4f6)

Only items still open or vague are listed. Every other numbered item is closed with a literal artifact (JSON, DDL column, code, copy, test name or file:line).

Spot-checks that held on merged code:
- Finding lifecycle SUPPORTED / UNCONFIRMED / NO_LONGER_SUPPORTED / MERGED.
- Action reducer NONE_AT_CUTOFF / PENDING / APPLIED, with RESOLVED and RESOLUTION_WITHDRAWN as events.
- `/findings` and `/api/findings` are mounted (OperatorShellLayout.tsx:54, analytics_api.py:33).
- 21 non-test frontend files read `source_provenance`.
- Fixture codes KOBO-001, COLD-LAB-001 and EV-LAB-001 exist, and MG-DEMO-01 is refused (import_kobo.py:147).
- `docker-compose.yml:14` pins postgres:16.4-alpine.
- `SiteAnalyticsFrames.tsx:1013-1014` renders the Work subrow.
- `siteFindingHref` is at operatorSiteRoutes.ts:162.
- `test_s4_finding_index_*` files exist.

Labels: `Qn` is the W4 review question, `Wn` the W3 review question, `Dn` the provenance point.

## W3-01 open (8 items)

1. **W9 / closure B9 (High): `action_title` and `success_criterion` key paths do not exist in merged code.**
   - Spec: the closure says the "accepted recommendation snapshot's `title`" and "snapshot `success_criterion`".
   - Code: `action.snapshot` is jsonb (`0016_action_store.py:69`). `grep success_criterion` over `backend/` returns nothing, and no `title` key is written under `actions/`.
   - Missing: the real snapshot key names (rule id, field, percent unit and so on). Or state that the value is always null and the title is always `Action {action_code}`. The example criterion string is invented.
2. **D2 (High): the `detail` key list does not match the resolver.**
   - Spec: the decision says detail holds `accepted_evidence_ids,publications,fixtures,runs,evidence`.
   - Code: `source_provenance.py:211-226` returns `state,reasons,accepted_evidence_ids,problematic_accepted_evidence_ids,publication_ids,source_classes,fixtures,runs,evidence`.
   - Missing: `publications` is not a key. Name the exact keys, and say whether `reasons` is both top-level and in `detail`.
3. **D3 (High): `selected_revision_ids` is undefined for Actions.**
   - The closure says every selected row gets a digest, but not which IDs feed it for an Action row.
   - Missing: whether it is the event ID, the plan ID or the snapshot, and where the cited set is read (`action_basis_evidence` is per Action).
   - The W3 Action example still shows `EMPTY_CITATION_SET` as an "illustration", which is not a derivation.
4. **D6 (Medium): the typed extras list is incomplete.**
   - Closure lists `source_classes,fixtures,run_ids,details`.
   - The resolver also emits `run_id` and `run_identity_sha256` (`RUN_IDENTITY_CONFLICT`, lines 205-208).
   - Missing: the full extras set and the canonical sort for list-valued extras.
5. **W5 / B5 (Medium): per-Site coverage derivation is prose only.**
   - `job_state` is "from selected job/match work": no table or column mapping per domain.
   - `source_freshness` is "from the selected read envelope": no field or threshold.
   - `match_state` appears in the token but has no enum.
   - The "shared query helper" has no file, name, signature or `finding_index.py` line range to extract.
6. **W7 / B7 (Medium): `consequence` source columns are not named.**
   - Missing: the amount and currency columns of `financial_consequence_revision` and `cold_consequence_revision`. "Supported amount" and "acceptable source gate" are undefined.
   - EV money is deferred to the W2-07 merge gate, which is acknowledged. EV and the Cost lens are unbuildable until then.
7. **S19 / card predicates (Medium): `lens_flags` and card predicates are body prose only.**
   - Missing as columns: `High priority`, `Low confidence`, `Awaiting verification`. The cited code shows no priority or confidence column on the Finding revision. Say whether these are always null.
   - Missing: the "decision timestamp" for `Verified in 30 days`. `verification_outcome` has `recorded_at`, and the spec does not say that is the one.
8. **W20 (Medium): fixture inputs are deferred.**
   - `cold_replay_path`, `ev_manifest_paths` and the exact accepted IDs are "recorded in the packet".
   - The import entry point that creates KOBO-001 in a private test DB is not named.
   - Low: no single full literal estate Finding or Action page. The body JSON still mixes old keys (`lifecycle`, `source_finding_*`) with the closure's keys.

## W4-01 open (5 items)

1. **Q11 (High): provenance inputs for a case.**
   - The closure says the shared decision "applies" but never states `selected_revision_ids` for a case (the case revision alone, or plus linked Finding revisions and Action events). It also does not say how a pinned Action's cited set is read.
   - It does not say in which W4 commit the `public_provenance.py` patch lands if W3 has not merged.
   - Same root as W3 D3.
2. **Q7 / B7 (Medium): the positive fixture cannot obtain pinned IDs, and no link is exercised.**
   - The fixture input has `accepted_evidence_ids:[]` and `finding_links:[]`.
   - Missing: which public read supplies a KOBO-001 Finding revision and Action event, and the KOBO-001 import entry point in a test DB.
   - The `Finding {8}` label and `siteFindingHref` are covered by no named test.
3. **Q9 / B9 (Medium): status and coverage derivation has no joins.**
   - "As applicable to pinned domain" names three job tables with no key to the pinned Finding or Action link.
   - "Selected source read `source_freshness=STALE`" does not say which read.
   - The precedence list cannot be computed without the joins.
4. **Q8 / B8 (Low): the token fence has no content.**
   - `linked_selection_fences:[...]` is empty of definition. W3's token is per-Site and window-bound, and W4 does not say how a link's token is recomputed.
   - `selected_event_ids` does not say which events.
5. **Q6 and Q28 (Low): hash and refusal details.**
   - Does the canonical hash include the path parameters (`site_code`, `case_id`)?
   - The rejected `actor.kind=USER` is 403, but no code or message is given. Nothing says how the SERVICE `attestation` string is validated against `actor.id`.
   - The plan, record and operational POST responses are described as "adds id,recorded_at and the documented canonical ID/code/state", with no literal body.

## Counts

- W4-01: 5 open (1 High, 2 Medium, 2 Low).
- W3-01: 8 open (3 High, 5 Medium). The D1, D4, D5 and D7 provenance points are closed.

Worst three: (1) W3 W9: `title` and `success_criterion` snapshot keys do not exist in code. (2) D2: the `detail` list names `publications`, but the resolver emits `publication_ids` and other keys. (3) D3 / W4 Q11: `selected_revision_ids` for Actions and case revisions is undefined.
