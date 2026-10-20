# W3-01 pending rulings (q3, Lane A compatibility run, 2026-10-20)

q1 and q2 are answered in `.agent/W3-01-build-spec.md` ("Run 1 rulings (q1)", "Run 2 rulings (q2)"). Lane A
merged main (`1f731005`) and dry-read every ruling-1 call site before editing. Nothing below was built on an
assumed answer; **no Lane A code is committed**. Items 1-3 block the cold/EV envelope part of the one
compatibility commit; items 4-6 are readings to confirm.

1. **EV no-head read with a non-empty accepted window (r9 M1-a).** `EvReadService._snapshot`
   (`postgres_assessment_store.py:2128-2144`) runs the `recompute_job` query only when a selected revision
   exists, so a no-head read is never "pending". Under ruling 5 + q2 ruling 1 that read has neither block and
   `source_provenance` becomes the empty UNKNOWN/`EMPTY_CITATION_SET` DTO with `evidence_ids:[]`, while its
   limitation still says the source is mixed or unverified. Today it publishes the window set's own class/IDs
   with null basis, and `test_w206_ev_reads_postgres.py::test_unassessable_source_has_unknown_status_and_limitation`
   (`_unassessable`, lines 512-524) asserts non-empty `evidence_ids`/`source_ids` and `MIXED`/`UNKNOWN` from the
   set. Which? (a) empty DTO, and that test is rewritten; (b) the window's `_ev_rows` set as
   `pending_source_provenance` (`cited_set(ids,[])`, null digest) whenever no head exists and the set is
   non-empty; (c) also run the `recompute_job` query without a selection, so (b) applies only when a pending job
   overlaps, else (a); (d) other. Same question for cold: confirm a no-selection cold read with a `pending_since`
   job gets a pending block per q2 ruling 2, and without a job the empty DTO (today `classification:null`).

2. **Detail reads: top-level `source_provenance`.** `ColdReadService.finding` returns `{**envelope, **item}`
   (line 1893); EV `session`/`finding` details likewise spread the envelope. Ruling 2 gives the detail row its
   own set (`cold_finding_row_selection`, `ev_session_row_selection`, `ev_finding_row_selection`). Is the
   detail's top-level `source_provenance` (a) the row DTO, with the envelope's `selected_source_provenance` /
   `pending_source_provenance` siblings kept beside it, or (b) the envelope alias unchanged, with the row DTO
   under its own key (which name?). The q2 dry-read ("never overwrite the newly computed public
   `source_provenance.basis_sha256`") fits (b) but names no key.

3. **Row DTO key and EV session cited set.** Contract items 4-5 give cold Finding, cold consequence, EV session
   and EV Finding rows their own DTOs. (a) Is the per-item key `source_provenance` on each list item (cold
   `/cold/findings` items, `cold_site_reads` consequence rows, EV `/sessions` and `/findings` items)? (b) Ruling
   2's EV session row cites "that session revision's exact accepted uses": `ev_session_evidence.evidence_id`
   only, or its union with `ev_meter_interval.evidence_id` for the same `revision_id` (both are the uses
   `_sessions` reads, lines 2263-2280)?

## Readings to confirm (not blocking)

4. **Wiring.** `PublicProvenance.finding_revision/consequence_revision` match `SourceProvenanceResolver`'s
   signatures and return the W1-compatible dict or `None`, so the W1 call sites (`finding_read`,
   `consequence_read`, `consequence_history`, and through them `site_overview`, `actions/service`,
   `finding_api`) get the new values by composing `PublicProvenance(PostgresEvidenceLedger(url))` where
   `build_source_provenance` is injected today (`analytics/composition.py:build_finding_read_service`, the two
   `financials/composition.py` builders), via a new `evidence/composition.py:build_public_provenance`.
   `build_source_provenance` stays for `actions/composition.verification_ports` (`resolve`). `ColdReadService`
   gains a `link_rows` kwarg wired from `build_link_rows_reader()` in `build_cold_read_service`. These three
   composition files are outside ruling 1's file list.
5. **Fail-closed W1 blocks.** `evidence/provenance_read.py:unresolved` (not wired / unreadable / not found)
   keeps its current shape without the public keys; Lane A does not fabricate them, and the frontend reads
   `classification ?? state`. Confirm, or name the public projection for these blocks.
6. **Empty envelope helper.** q2 ruling 1 has Lane B change `dual_blocks(None, None)`; at `2951b66c` it still
   raises. Lane A waits for that Lane B change (or an equivalent Lane B helper) rather than composing the three
   keys itself.
