# Owner autonomy window 2026-10-15 (about 12:20 to 22:00 EAT)

Owner (verbatim): "I'll be unavailable until 10PM in the evening but i want you to continue to work towards completing wave1 with the architect making a call on my behalf. keep the computer on and i'll do pending walthroughs when i return. If there is a internet discconnection, try in a given interval.Goal is to be able to progress well in my abscence."

Rules applied (owner-absent rule, memory): owner-decision points (close next-work contests, sequencing) go to the Codex Architect; USER_REVIEW_REQUIRED slices are built and fresh-reviewed but their merge is held for the owner walkthrough; stacked branches allowed. Keep-awake held for the window. Network failures retried on an interval. Delegated decisions are listed for the owner on return.

(Rebuilt by the coordinator at ~19:45 after the uncommitted copy lost its early entries during a branch switch; entries are reconstructed from the session record and the committed Architect answer files, which remain the authority.)

## Delegated decisions (Architect, on the owner's behalf)

1. **Work order** `D-2026-10-15-owner-absence-work-order` (`.agent/architect-autonomy-2026-10-15-answers.md`): LR-01 -> S5-01 (stacked, held) -> I-action-store/S6-01 -> I-stored-demo-provenance -> price succession -> I3 decided_at -> F-B writer guard -> OPS-01 Lows; A-finding-index planning only. Pre-ruled contests: LR-01 over I-action-store (0.20%, later 0.79%); S5-01 over Action store if within 5%; Action store over stored provenance if within 5%.
2. **LR-01 overlap rule** (Follow-up M1 in `.agent/architect-LR-01-answers.md`): order readings by placement instant +/- attested error; touching 5-minute means are not overlap; genuine overlap stays ambiguous; disjoint placement means a late arrival is just late.
3. **S5-01 money card Finding choice** `D-2026-10-15-s501-finding-choice`: latest episode_start intersecting the selected UTC day (half-open), tie by smallest UUID, independent of price/eligibility, kept through stale/withheld states.
4. **S6-01 Action store and UI** `D-2026-10-15-s601-action-store-and-ui`: split into S6-01a (non-UI) and S6-01b (UI, held). Reserve proposal = versioned rule `reserve-trial-1` (reserve minus 5 points, only with usable battery SOC evidence; labelled an experimental control change, no savings/runtime claim). Action lock before Site lock, one transaction, FAILED after rollback; 404 without event for wrong-Site IDs; demo controls only with a server-granted SYSTEM demonstration capability; ninth database writer `actions/adapters/postgres_action_store.py` (insert-only); accepted recommendation stored as an immutable snapshot; a bounded backdated `OBSERVED` demo note (<= 30 days).
5. **S4-05 stored provenance** `D-2026-10-15-s405-stored-demo-provenance`: designation is a SYSTEM publication committed before its exact batch is admitted (no retroactive authorship). Two positive classes: AUTHORED_DEMONSTRATION (demo fixtures P01/P02) and REGISTERED_SIMULATION (ordinary simulator runs with a server-recorded run identity). Unregistered, broken or foreign = UNKNOWN; crossing classes = MIXED; both block any current amount even when CURRENT PRICED and LR-01 ELIGIBLE. New follow-on node `I-attested-real-source-provenance` added to pilot requirements. **FOR OWNER: once S4-05b lands, old unregistered data shows no current amount; the source wording and pilot source choice stay your decisions.**
6. **LR-01 known deviations** (`.agent/architect-LR-01-deviations-answers.md`): accept dropping the all-history Finding basis uniqueness (A->B->A appends a new revision; downgrade refuses rather than erases); S5 keeps money eligibility and schedule currentness as separate fields; accept conservative +/-6 h withholding; money shows on the Financials bridge, the Finding page shows the SERIES_LIMIT statement; unwired consequence reads show no amount.
7. **P02 demonstration label** `D-2026-10-15-p02-demonstration-label`: the late-power demo case gets the same "Demonstration data" label as P01 now (temporary fixture rule on LR-01; S4-05 replaces it).

## Coordinator dispositions (within those rulings)

- S6-01a: demo grants scoped to tenant + Site + fixture records; re-accepting with a new key is a 409 "already accepted"; the stricter lowest-SOC reading recorded as a deviation.
- S4-05a: a consequence whose Finding-revision part is UNKNOWN (incl. empty citation set) resolves UNKNOWN, never positive.
- S4-05a plan: USER_REVIEW_REQUIRED false (no UI; copy proposal moves to S4-05b).
- Merge order (migration numbering): LR-01 (0014/0015), then S5-01, after your walkthroughs; then S6-01a and S4-05a re-chain their migrations in turn, each with one quiet full suite; OPS-02 (writer guard) merges last and absorbs their rule-8 entries.
- Reduced parallel builds after the machine hit 100% CPU (two reviewers' full runs hit the 20-minute cap).

## Status at a glance

- **Merged to main:** OPS-01 (test suite ~8 min), S4-06 price succession (`5bfff665`), S4-07 evidence decision time on DB clock (`c4ae3dd2`).
- **Ready for your walkthrough (merge held):** both run from the main checkout `C:\Users\assef\Bineyame\AssetOpsV1` on branch `task/S5-01-site-overview`, which contains all of LR-01 (head `e8d555bc`) plus S5-01. Do LR-01 first (`.agent/LR-01-owner-walkthrough.md`), then S5-01 (`.agent/S5-01-owner-walkthrough.md`). Merge order after acceptance: LR-01 branch, then S5-01.
- **Reviewed, waiting for migration re-chain + quiet full suite, non-UI:** S6-01a, S4-05a. OPS-02 waits to merge last.
- **Building:** S6-01b (Action UI; phase 1 reviewed, phase 2 building; held for a later walkthrough).
- **Not started:** S4-05b (producers, reads, source wording; held for walkthrough).
- **Backlog carry:** `test_runs_api.py` reads gitignored `var/sites/mg-001.yaml`; commit a test fixture (small OPS follow-on).
8. **A-finding-index** `D-2026-10-15-a-finding-index` (Architect, after a review RETURN and fix round): Site Finding list for a half-open UTC window up to 31 days; latest revision per canonical Finding from one consistent basis; stable order (episode start desc, then UUID); a closed source gate returns 409 `PERFORMANCE_CUTOVER_CLOSED` with no current rows or "no Findings" claim; "no Findings" only after complete current discovery. Next-work now ranks `I-finding-index` first (5.7% over late-readings; LR-01 is built), an owner-notice band.
