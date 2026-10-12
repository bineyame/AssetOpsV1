# S4-01 phase 1 questions (fail-closed defaults shipped)

For one Architect batch; none blocks phase 1. Each names the default the build uses and where it lives.
Authority: `tasks/S4-01-finding-identity.md`, `D-2026-10-12-finding-episode-and-revisions`,
`.agent/architect-A-finding-episode-answers.md`.

1. **Revision idempotency key.** Technical design names `UNIQUE(finding_id, assessment_revision_id)`. A cross-window
   episode can keep its primary interval revision while another supporting interval changes, so that key would refuse a
   real support change. Default: `UNIQUE(finding_id, revision_no)` and `UNIQUE(finding_id, basis_sha256, transition)`
   (`backend/migrations/versions/0009_finding_store.py`); the primary `assessment_revision_id` FK is kept, not unique.
   Retry of one basis still adds nothing (F08, replay in `tools/s4_finding_cases.py verify`).
2. **Indeterminate segments as a bridge.** Default: a gap of at most 20 minutes is bridged only through observed
   Necessary segments or Indeterminate segments whose reason is a modelling reason (`dispatch_v3._NOT_EVIDENCE_GAPS`);
   an evidence gap, contradiction or ambiguous cohort never bridges (`analytics/finding_episode.py`). Stricter
   alternative: only Necessary bridges.
3. **Recurrence link.** Default: `recurs_after_finding_id` is set only when an observed generator OFF separates the two
   episodes by more than 20 minutes; an unobserved separation opens an unlinked Finding (F06 `13:00` expects
   `recurs_after: null`). Alternative: link on any >20-minute separation.
4. **Window revision in the basis.** Default: the selected window AssessmentRevision is cited
   (`finding_revision_assessment`, scope WINDOW) but excluded from `basis_sha256`, so a window-only re-selection with
   identical interval support appends nothing. Alternative: include it (more revisions, each a no-op to the claim).
5. **Collateral revisions after a backdated control.** A backdated control splits the open Foundation revision, so every
   later window re-selects new control revision IDs and new interval AssessmentRevisions. Default: unchanged episodes
   on those days append `SUPPORT_CHANGED` with identical bounds and minutes and the new interval revision (F05 steps,
   `collateral` in the spec). Alternative: a quieter `BASIS_REFRESHED` transition, or suppress when only control IDs
   changed (would leave the Finding citing a non-selected revision).
6. **Fixture provenance.** The task asks for assessments produced through the S2 registered simulated gateway. No Lab
   scenario authors the exact late/held/contradicting/bridging reports the cases need. Default: every case is a
   LABELLED AUTHENTICATED FIXTURE Batch V2 (authored public content sealed against the registered binding snapshot and
   posted with the registered gateway credential over TLS; S2 step-8b / S3 Q1 precedent), never described as
   gateway-sealed; F01 is not additionally produced as a gateway-sealed Lab run (S3 case 02 already proves the
   gateway-sealed path to a CANDIDATE interval). Alternative: a gateway-side labelled fixture op, or F01 duplicated
   through a Lab run.
7. **No mutable `closed_at`.** Default: lifecycle and closure are derived from the latest revision
   (`NO_LONGER_SUPPORTED`, `MERGED`); `finding` has no mutable column, so every table stays append-only.
8. **Minimum-runtime control route (producer).** No product route publishes generator minimum-runtime in this release
   (`foundation_api.py` accepts only the battery reserve). Default: the producer publishes reserve through
   `POST /api/sites/KOBO-001/foundation/revisions` and minimum-runtime through `FoundationService` in the copied tree,
   labelled as a fixture control. Alternative: add a product route (out of S4-01 scope).
9. **Spec `decided` instants.** Over HTTP, central acceptance and publication use the server's real clock; the spec's
   `decided` values are ordering labels only (the Postgres test applies them exactly). Default: keep both; the run
   artifact records real IDs, not the labels.
