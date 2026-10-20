# W3-01 pending rulings (q4, Lane A compatibility run 2, 2026-10-20)

q1-q3 are answered in `.agent/W3-01-build-spec.md` (Run 1-3 rulings). Lane A resumed at `9239fb45` and built
the q3 map up to EV money, then stopped on item 1 below (no-decision rule). **No Lane A code is committed**;
the uncommitted diff is saved as `.agent/W3-01-lane-a-partial.patch` (see the phase handoff).

1. **EV money row: the stored row has no pinned Finding (blocking).** q3's EV money row says: select
   `ev_consequence_revision.finding_revision_id, assessment_revision_id`, cite money IDs union the pinned
   `finding_revision_evidence`, select `{ev_consequence_revision.id, finding_revision.id, ev_session_revision.id,
   assessment_revision.id}`, and "Missing pinned Finding/session/assessment for a stored row refuses the read
   through its existing unavailable path". In code, `ev_consequence_revision.finding_revision_id` is nullable
   (`migrations/versions/0026_w2_ev_money.py:50`) and the only writer always inserts `NULL`
   (`financials/adapters/postgres_consequence_store.py:997-1000`, `VALUES (:id, :t, :s, NULL, :ar, ...)`). An EV
   money row is window-level: it links N sessions through `ev_consequence_session` (`_with_links`, line 1115),
   not one session named by a Finding claim. Applied literally, every stored EV consequence (current or history)
   refuses `/ev/financials` (and the EV overview money summary), so `test_w207_ev_money_postgres.py` and the
   EV Site money reads would all become 503. Which applies?
   - (a) Row DTO cites `ev_consequence_evidence.evidence_id` only and selects
     `{ev_consequence_revision.id, assessment_revision_id, every ev_consequence_session.session_revision_id}`
     (no Finding member; needs a Lane B selection helper or an inline sorted set; Lane A would pass it to
     `cited_set`).
   - (b) As (a) but also union the `finding_revision_evidence` of every SUPPORTED EV Finding revision of that
     assessment whose claim names one of those sessions, selecting those Finding revisions too.
   - (c) Keep the literal ruling: a NULL pin refuses the read (EV money reads become unavailable until a later
     writer change pins a Finding; that writer change is outside Lane A's file list).
   - (d) No row block on EV money rows in this commit (envelope siblings only); defer to a later slice.

## Readings (built in the partial patch; confirm or correct with item 1)

2. **Cold Finding row pin.** `_REVISION` now also selects `er.id, er.assessment_revision_id` (episode revision
   joined by tenant/Site and the claim's `episode_revision_id`). A missing episode revision, or one whose
   `assessment_revision_id` differs from `fr.assessment_revision_id`, raises `ColdReadUnavailable` (503) for
   list, detail and Site reads, rather than an UNKNOWN row. Selection uses `fr.assessment_revision_id` (q3 text).
3. **Cold consequence pin.** `ColdReadService.consequence_provenance_on(c, snap, head)` requires the pinned
   `finding_revision` in tenant/Site with `assessment_revision_id = head.assessment_revision_id` and claim
   `episode_revision_id = head.episode_revision_id` (episode revision of the same assessment); else 503.
4. **EV Finding pin.** Exactly one `ev_session_revision` among the selected `result.session_revision_ids` whose
   `session_id` equals the claim's `session_id`; zero or more than one raises `EvReadUnavailable` (503).
5. **EV pending job vs currentness.** The `recompute_job` query now runs whenever `lo` exists; it gates only the
   public pending block. `currentness`/`pending` stay as before (`pending = selected is not None and job`), so
   no-head reads keep `UNKNOWN` currentness and the `_unassessable` limitation.
6. **Failed link reads.** Both cold and EV bind `link_rows` through one helper that maps any non-DB exception
   to the route's unavailable error (DB errors already map in `_read`); a missing reader is also unavailable.

**q4 answered** in `.agent/W3-01-build-spec.md` Run 4 rulings; built in the Lane A compatibility commit. No open Lane A question.
