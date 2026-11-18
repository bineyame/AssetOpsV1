# V-01b registry closeout review

Reviewer: a fresh Claude reviewer who did not write this change. Branch `closeout/V-01b-registry` @ 58e117e vs main 34b2a9f. Metadata only.

## Verdict: ACCEPT. No blocking findings. Three low-severity carries.

## Verified
- I diffed the registry and ledger JSON structurally, not only as text. The only changes are: gate `visual_gates.V-01b` moved from open to accepted, with `accepted_on` 2026-10-13, 8 evidence paths and a new note; `visual_acceptance` and `caveat` were added to the 9 V-01b rows (lab:1-4, evidence:1-3, evidence-analysis:1-2); and the three ledger `unknown_or_empty` strings (lab, evidence, evidence-analysis) were appended. No `panel_status`, `reviewed_mapping`, claim-portion `state`/`core`, or W1 core mapping changed. Nothing was marked real. evidence:3 stays `gap`/unmapped, and evidence:1#b, evidence:2#b and evidence-analysis:2#b stay unmapped/open.
- All 8 gate evidence files exist under `.agent/` and are tracked.
- The conditional wording matches the owner record (`.agent/owner-V-01b-walkthrough-2026-10-13.md`): "Accept conditionally", headings kept, "How each limit is set" / "Data sources · data quality" kept. The gate note, every row caveat and every ledger append say conditional, layout/copy only, not technical closure, not Real. Nothing claims more than the owner said. The cited decision D-2026-10-13-v01b-visual-and-lab-read-boundaries exists in `.ai/DECISIONS.md:4093`.
- Each row caveat matches column 3 of the `.agent/V-01b-review-packet.md` panel table. I also checked the visible missing-state copy in the current UI. The copy for lab:1, 2 and 4 is in `RunIngestionOverview.tsx`. The copy for evidence:1-3 and evidence-analysis:1-2 is in `LedgerSiteEvidence.tsx`. For lab:3, the "Nothing ... received centrally" copy is present and no Stage upload/no-receipt assertion remains.
- The rows the packet marks as having no named gap (lab:1, lab:3, evidence-analysis:1) are correctly identified as such in the gate note and the caveats.
- The scorer (`*.cjs`) does not read `caveat`, `visual_acceptance` or `unknown_or_empty`. So the only change to scoring inputs is the V-01b gate status.

## Checks run (actual)
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0.
- `node frontend/docs/architecture/test_delivery_next_work.cjs`: fail 0.
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python python`: "All 6 guards passed."
- `--verify-report .agent/next-work-2026-10-13b.json`: exit 0. Decision: stop_owner, A-S4-financial 2.215 vs I-finding-evidence-read 2.187. The report's `gap` field is 0.013 and its reason text says 1.26%; the raw score difference is 0.028, which is 1.26% of 2.215. That is within the 5% limit, and the tie-break recommends I-finding-evidence-read.
- I regenerated the report with `--next-work` into scratch. Every top-level key equals the committed report, including the decision.

## Carries (low, non-blocking)
1. The evidence:2 caveat names "end-of-period status, quality grade and Affects". The packet's gap column also names outage/pressure health (`evidence:2#b`). The `#b` pointer covers it, but the caveat text is narrower than the packet.
2. The V-01a gate note listed its carries (C1-C4); the V-01b gate note lists none. The decision's open items are not recorded in the registry except through the decision id: the historical Lab drawing should resolve the pinned Foundation basis, which leaves V-01b's drawing layout assertions unverified, and the Stage contract still has to be corrected. lab:3 does record that backend field retirement stays open. Consider naming these in the note at the next registry touch.
3. Every V-01b row's `visual_acceptance.condition` says "conditional on the named data gaps", including the three rows with no named gap. The caveats clarify it, so this is wording only. Also, unlike the V-01a closeout, this one gives the gap row evidence:3 a `visual_acceptance`. That is justified, because the packet table gives evidence:3 an owner-column condition.

## Not verified
The frontend vitest suite and build were not run; frontend code is untouched and the diff is metadata only. I did not recompute the scoring algorithm by hand; I relied on regenerating the report and on `--verify-report`.
