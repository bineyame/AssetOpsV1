# S4-02d Planner notes (2026-10-14)

- Selected input: `.agent/next-work-2026-10-14i.json` selected `I-analytic-finding-worker-schedule` at 2.198 versus `I-action-store` at 2.016 (8.28%); this is the required 5–10% notice, not an owner stop.
- Packet: `tasks/S4-02d-analytic-finding-worker-schedule.md`; registry `task` is `S4-02d`. `queue_baseline_nodes` already contains the node, so its membership stays unchanged. `I-site-overview-read` already requires it and the separate `I-late-reading-series-and-money-limit` node.
- The existing S3 CLI drains up to 1000 jobs and reconciles all assessed Sites; the S4 CLI matches one explicit Site; S4-02c's consequence runner serves one named development Site. The packet therefore requires active persisted Site enumeration, fair bounds and a deployment-owned timer rather than assuming those current commands cover production tenants.
- USER_REVIEW_REQUIRED is false only for an operator/read-contract implementation with no new owner UI or copy. S5-01 retains its owner checkpoint. F1 run-1 numbering and amount withholding belong to `I-late-reading-series-and-money-limit`.
- Carry I1/I2 from the S4-02c backlog: uncapped failed consequence attempts and a hung runner masked by repeated skipped ticks must surface in health and recovery. The packet adds focused proof for both.
- Verification: `node frontend/docs/architecture/check_v69_dependency_registry.cjs` passed (224 nodes); `--next-work --out .agent/next-work-2026-10-14j.json` and `--verify-report .agent/next-work-2026-10-14j.json` passed. The verified report still selects `I-analytic-finding-worker-schedule` 2.198 over `I-action-store` 2.016, with the 8.28% notice. `git diff --check` passed. No commit made.

## Plan fix round 1 (RETURN review)

- H1/H2: S4 matches every selected Site tick after S3; only each affected window's currentness is held by live S3 work, unmatched selection or consequence work. Terminal FAILED jobs need typed operator requeue of the default window. Tick-only proof checks r1 `FINDING_REVISION_SUPERSEDED` and cites S4-02c for same-revision Leg A; first delivery and Leg B are tick-driven.
- M1/M2: migration 0013 and a new schedule writer own heartbeat, claims and fair cursor. `PLANNED` imported/enrolled Sites qualify; S3 leasing becomes Site-scoped. The built global `reconcile_all()` still runs every tick, with additional selected-Site coverage and cost measurement.
- M3/M4/M5: installing the environment timer retires the per-Site consequence timer; `STALE_NO_WORK` pre-0012 heads are reported with IDs and block CURRENT, without backfill. The walkthrough records F1 S3 limits but does not assert an S5 money decision; the source-ordered variant is its positive path.
- L1-L4: the Python S5 seam uses the existing S3 status, `match_state`/`finding_match_pass`, pending consequence work and DB time. DB statement/lock timeout and killable children are both exercised; S3/S4 are serial for each Site and a moved fence is `FENCE_MOVED`. Timer installation and runbook are phase 2.
- Risks: no owner-visible host installation before `I-late-reading-series-and-money-limit` lands; global reconcile and matcher job-status aggregation need measurement; S4-02c I3/I4 clock-skew and concurrent-ingestion ownership remain open. `USER_REVIEW_REQUIRED: false` applies only while no owner-facing copy, panel, or visual state is added.

### For the Architect batch

- Ratify the proposed migration 0013 schedule tables, `backend/assetops_backend/scheduling/adapters/postgres_schedule_store.py` as the eighth PostgreSQL writer, and the scoped `tools/checks/configuration-persistence.ps1` rule 8 amendment. These are in the packet's implementation scope but are **not yet approved**.
- Carry S4-02c I3/I4 into the next review and confirm the owner-visible-host installation gate tied to `I-late-reading-series-and-money-limit`.

Verification after fix round 1: the registry checker passed (224 nodes); `--next-work --out .agent/next-work-2026-10-14k.json` and `--verify-report .agent/next-work-2026-10-14k.json` passed. The report selects `I-analytic-finding-worker-schedule` 2.198 over `I-action-store` 2.016 (8.28% notice). The checker recognises the packet's `implementation-ready` status label; the same line explicitly retains the pending fresh review and Architect ratification. No registry edit or commit was made.
