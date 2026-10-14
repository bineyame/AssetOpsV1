# Planner notes — S4-02c (2026-10-14)

- Packet name: `tasks/S4-02c-evidence-consequence-work.md`. It owns only registry node `I-evidence-acceptance-consequence-work`; S4-02a/b and S4-02 closeout are unchanged.
- Q6 carry: **yes**, S4-02c owns a run/scheduling plan, bounded drain, scoped concurrency and persisted retry eligibility. The S4-02b one-shot CLI alone is not sufficient for S5 current money eligibility.
- The S2-02 ledger commits `accepted_evidence`, `ingestion_disposition` and dispatch recompute job in `decide_chunk`. Migration 0012's accepted-disposition trigger enqueues consequence work in that transaction, with no ledger-adapter write to the consequence table; rollback is atomic. Migration 0011's assumption/FindingRevision work causes stay valid.
- The owner's analysis-input-data item in `.ai/MILESTONE_REVIEW_BACKLOG.md` is referenced only. This packet does not change simulated publication cadence or real-Site readiness.
- No owner question is needed for this non-UI packet. The false review flag requires a typed no-work discrepancy without new copy and use of the existing reviewed `POWER_NOT_IN_ASSESSMENT_INPUTS` text in Leg A. If implementation requires owner-facing copy, reopen the flag and checkpoint.
- Registry `queue_baseline_nodes` already contains `I-evidence-acceptance-consequence-work`; it remains unchanged and mapped to S4-02c.
- The checker parses `S1`–`S7` milestone rows as umbrella task gates (`I-<task>`). This follow-on uses the `Financial consequence follow-on` queue label so its existing producer node remains the only registry gate; no synthetic `I-S4-02c` task node was added.
- Plan fix round 1 validation: `node frontend/docs/architecture/check_v69_dependency_registry.cjs`, `--next-work --out .agent/next-work-2026-10-14g.json`, and `--verify-report .agent/next-work-2026-10-14g.json` all passed. The report's generic `stop_owner` near-tie remains a scorer output; `.agent/architect-contest-2026-10-14d-answers.md` already selected this Planner refinement under the owner's delegation. The generated report is an output artifact, not a source edit.

## For the Architect batch

- R1: S3 `assess_dispatch process-jobs` and S4 `match-findings` remain one-shot and unscheduled. S4-02c schedules the consequence drain only. After late evidence, S5 honestly shows `PENDING`/`STALE`, but current priced money waits for those two commands. Decide whether S3/S4 scheduling is a separate follow-on before W1 exit; this does not block this packet.

## Plan fix round 1

- The two-leg walkthrough uses a new versioned authored variant with a withheld 07:00–07:05 mean. Leg A drains the unchanged FindingRevision to current quantity-unavailable; Leg B re-evaluates the Finding, then derives current priced money.
- Migration 0012 uses a stored-role accepted-disposition trigger, shared Site enqueue lock with the 0011 FindingRevision trigger, partial unique indexes and a three-arm cause CHECK. The one-shot runner uses a Site advisory claim and attempt-derived retry time; no guard amendment is needed.
- R2: a backfill can create many evidence work rows. The packet requires a bounded-batch test across multiple Findings.
