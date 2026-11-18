# A-action-lifecycle Architect decision review

Reviewer: fresh Claude reviewer. I did not write the Architect request, the answers, the decision or the registry edit.
Reviewed: commit `09a5a40d` on `plan/A-S5-overview`, diff `0e209e09..09a5a40d` only (`.ai/DECISIONS.md` +10 lines, `D-2026-10-14-action-lifecycle-and-policy-application`; registry node `A-action-lifecycle` set from open to resolved). I left out later commits (`75207a37`, `07841a19`, `ee391521`) and the Planner's uncommitted edits.
Supporting material (read, but not part of the commit): `.agent/architect-contest-2026-10-14d-request.md` (committed in `0e209e09`), `.agent/architect-contest-2026-10-14d-answers.md`, the Architect log, `.agent/next-work-2026-10-14e.json` and `.agent/owner-autonomy-2026-10-14.md`.

Checked against: `D-2026-10-09-pre-s3-claim-routes-and-actor` (`A-claim-work-routes`, `A-actor-identity`), `A-demo-scenarios` (two-run S6 verification, DECISIONS :3816), the S1 Postgres publish rule (DECISIONS :7, Site-row lock), `D-2026-10-13-s4-bounded-financial-basis` (actor and SYSTEM-fixture rule), `D-2026-10-14-s5-selected-window-overview`, technical design §1 (`action`, `action_event`, `verification_plan_revision`, `foundation_revision`, `policy`), §4.5 (Verify) and the root ownership rule (:207), `tasks/S6-01..03`, the v6.9 manifest screens `action-overview|plan|execution|evidence|history`, `recommendation`, `changes`, `verification` and `sitework`, and the shipped S1 publish path (`backend/assetops_backend/sites/foundation_service.py` `publish_battery_reserve` and `_publish_content_change`).

## Verdict: ACCEPT with carries

- **Contest handling is sound.** The gap was (2.020 - 2.009) / 2.020 = 0.54%, inside the owner-contest band, and it was decided inside the owner's 08:40-10:40 delegation (commit 10:29 +0300). The Architect went against the report's tie-break and said why: this was a bounded Architect decision that could close inside the same call, while the consequence work still needs a Planner packet, an implementation and a review. I checked the claim of "roughly fifteen W1 core portions". Exactly 15 core W1 portions have `A-action-lifecycle` in their closure: `changes:1#a/1#b/2#a`, `recommendation:1-3#a`, `verification:1-3#a`, `sitework:1#a` and `action-overview|plan|execution|evidence|history:1#a`. Two non-core portions are also gated: `finding:3#a` and `mini:5#b`. The Architect rightly did not reuse the pre-decision ranking.
- **The follow-up choice at 0.20% is sound.** `I-evidence-acceptance-consequence-work` scores 2.020 and `I-action-store` 2.016. That choice is the report's own tie-break, and the node is the hard AND prerequisite of S5-01's money read under `D-2026-10-14-s5-selected-window-overview`. The answer limits it to Planner refinement, keeps independent review, and correctly says no separate owner visual checkpoint is needed only if the work adds no UI or owner-facing copy.
- **The decision is consistent with prior rulings.** It keeps the canonical Site-scoped Action route. It derives state from ActionEvents with exact event and cutoff selection, and invents no ActionRevision (pre-S3 ruling). It keeps actor-identity rules: no author is inferred from a gateway credential, client field, OS user or SYSTEM fixture, and SYSTEM is allowed only as a labelled, server-authorized demo command. It uses S1 Foundation publish under the Site lock rather than a Lab override, which matches the S6-01 outline. It keeps the two-run S6-02 baseline and later run (`A-demo-scenarios`). It pins an exact FindingRevision with no silent rewrite, which matches the S4 Finding revision semantics. It does not touch the S5 money rule.
- **It does not overreach.** The registry shows `A-S6-verification` and `A-action-index` still open, and I-S6-02 and I-S6-03 remain gated by them. No portion was promoted. The S6-02 paragraph restates technical design §4.5 and `A-demo-scenarios` and explicitly leaves the full comparison rule open. See L2 for the one blurred edge.
- **UTF-8 is clean.** The 10 added lines in `DECISIONS.md` and the edited registry line are pure ASCII. The registry is valid UTF-8 at the reviewed commit. `DECISIONS.md` was already invalid at the base `0e209e09` because of the A-S5 cp1252 bytes (A-S5 review L1). This commit carried those bytes over and did not add any. They are fixed at `ee391521`, which I confirmed valid. The answers file and 14e are valid UTF-8.

No finding blocks the decision. M1 is a provenance gap to fix on the branch. The rest are carries for the S6-01 Planner refinement.

## Checks run (as observed)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs` in the worktree, whose registry is byte-identical to `09a5a40d`: exit 0, "Registry valid: 222 nodes, 11 linked pilot panels".
- `--verify-report .agent/next-work-2026-10-14e.json` in the worktree: exit 0, ranked, fingerprints `registry=8d58e000a88d4695 queue=c3f7cdbe3ee0acf4`.
- Same two commands on a scratch `git archive 09a5a40d`, so the Planner's later edits cannot affect them: registry valid, 14e verifies (exit 0), and `--next-work` regenerates a report byte-identical to the 14e on disk. Decision `stop_owner`: `I-evidence-acceptance-consequence-work` 2.02 vs `I-action-store` 2.016, gap 0.20%, tie-break recommends the consequence work.
- I computed the closure count of W1 portions gated by `A-action-lifecycle` from the registry: 15 core and 2 non-core (above).
- UTF-8: `iconv -f UTF-8` on both committed files at base, at the commit and at HEAD; byte scan of the added diff lines.
- Not run: `tools/check-all.ps1` scan guards (no `node_modules` here, as instructed), backend pytest and frontend tests, build and tsc. There is no code in the diff.

## Findings

### M1 (Medium, fix on branch). The answers file and 14e are not committed, yet the resolved node cites them.

- **Where:** registry node `A-action-lifecycle.evidence[1]` = `../../../.agent/architect-contest-2026-10-14d-answers.md`. The files `.agent/architect-contest-2026-10-14d-answers.md`, `.agent/architect-contest-2026-10-14d-log.txt` and `.agent/next-work-2026-10-14e.json` are all gitignored and untracked (`git status --ignored` shows `!!`).
- **What is wrong:** the precedent (`7affc6a1`) force-added its answers, log and next-work reports. This commit added none of them. The registry checker does not resolve evidence paths, so it passes on a clean archive that lacks the file.
- **Why it matters:** the owner delegation requires the Architect to record its justification so the owner can be told afterwards. `DECISIONS.md` holds the 0.54% justification. The second delegated choice is different: the 0.20% pick of `I-evidence-acceptance-consequence-work` and the shape of its packet (M, mostly non-UI, no separate owner checkpoint unless UI or copy is added) exist only in the uncommitted answers file and the commit subject. 14e, the report that routes the next work, is also uncommitted. A worktree cleanup would lose all of this, and the merged registry would cite a missing file.
- **Fix:** `git add -f` the answers file, the Architect log and `next-work-2026-10-14e.json` on this branch before merge. Optionally add one sentence to the decision recording the 0.20% follow-up choice.

### L1 (Low, Planner carry). The Action creation point and `PROPOSED` contradict each other.

- **Where:** `DECISIONS.md` (`09a5a40d`) :4125 says "each accepted recommendation creates or idempotently returns one Action". :4127 lists `PROPOSED`/`ACCEPTED` as an Action state dimension.
- **What is wrong:** if an Action exists only after acceptance, an Action can never be observed in `PROPOSED`. If it exists while proposed, acceptance does not "create" it. The technical design's `action` row has nullable `finding_id`, no recommendation reference and no creation-idempotency key other than `UNIQUE(tenant_id, action_code)`.
- **Why it matters:** this choice decides the event transition table, the idempotency key for Action creation, and whether the Recommendation tab (Findings root, `recommendation:1#a`) reads an Action or a separate recommendation object.
- **Fix:** the Planner states one model explicitly. Option (a): a server-derived recommendation keyed to the FindingRevision, and the Action created at the ACCEPTED command, so `PROPOSED` belongs to the recommendation. Option (b): the Action created at `PROPOSED`. Either way, name the server-defined command key and its uniqueness constraint. If the Planner cannot settle this from the decision text, it should go to the Architect as a question, not be decided in implementation.

### L2 (Low). The S6-02 paragraph partly pre-states `A-S6-verification`.

- **Where:** `DECISIONS.md` :4131.
- **What is wrong:** the paragraph sets plan pinning, the two-run basis, `INCONCLUSIVE` on missing or conflicting evidence, guardrail failure blocking `VERIFIED`, and append or supersede for outcomes, while saying `A-S6-verification` "remains open". It leaves out the outline's `Ineffective` outcome (`tasks/S6-02-verification.md` "Verified, Ineffective or Inconclusive"). The content agrees with technical design §4.5 and `A-demo-scenarios`, so nothing is wrong today.
- **Why it matters:** the later `A-S6-verification` decision must treat this paragraph as binding or amend it explicitly. A reader could otherwise take the omission of `Ineffective` as a ruling.
- **Fix:** none needed now. The `A-S6-verification` request should cite this paragraph and state the full outcome vocabulary, including `INEFFECTIVE`.

### I1 (Info). The shipped S1 publish path differs from the decision's "old/new revision" wording.

`_publish_content_change` checks only that exactly one current period covers `effective_from`. It does not check an expected revision ID. One publish supersedes one row and inserts an `origin=SPLIT` prefix revision plus the `PUBLISH` revision, and in the same transaction it replaces every binding-set revision that named the superseded row (S1-02 Q5/Q6). It also accepts a retroactive `effective_from` inside any current period, and returns `FOUNDATION_NO_CHANGE` (422) when the value already matches. The decision is implementable on this path, but the Planner must add the items in carries P3-P5. None of this makes the decision wrong.

## Carries for the S6-01 Planner refinement

P1. **Creation model and keys.** Resolve L1. Name the Action-creation idempotency key and its scope (tenant, Site, origin FindingRevision, recommendation/command key), the `action_code` allocation rule (technical design `UNIQUE(tenant_id,action_code)`), and the `ActionEvent` uniqueness rule (`UNIQUE(action_id,idempotency_key)`, with conflicting reuse refused and identical retry returning the original event).

P2. **Recommendation source.** State where the proposed reserve-SOC value comes from: a versioned server rule over the pinned FindingRevision, or an operator value authored by a verified principal. A mock value or a client value is not allowed. The mock's "what is it worth?" money on `recommendation` stays out, or appears only as the bounded S4 consequence for that exact revision. The recommendation must never be shown as a saving (decision :4125).

P3. **Expected-revision check.** Add an explicit expected `foundation_revision_id` (and Site) check inside the existing Site-locked planner callback. Refuse a stale expected revision with a typed 409, and record a FAILED application event that carries no effective-policy claim.

P4. **Change artifact shape.** Model the artifact on what the publish actually writes: the superseded revision ID, the new `PUBLISH` revision ID, any `SPLIT` prefix revision, and the binding-set revisions replaced in the same transaction. Also record field, value, unit and asset code (`reserve-state-of-charge`, `%`, battery asset). `APPLIED` is written in the same transaction as the publish, or confirmed only after the publish commits, never before.

P5. **No retroactive Action-driven publish.** Require an Action-driven `effective_from` at or after server `recorded_at` (and after the ACCEPTED event), or state a reviewed alternative. A backdated reserve change would supersede the Foundation that S6-02's baseline window ran under. Also decide how an identical retry relates to `FOUNDATION_NO_CHANGE`: an applied command's retry returns the original event, and a "no change" proposal is refused at recommendation time.

P6. **Origin versus latest Finding.** The Action detail shows the pinned origin FindingRevision. When a newer FindingRevision or an episode change exists, it says so; it does not swap in the newer revision.

P7. **Actor path.** With no verified operator principal today, S6-01's accept and apply commands are the labelled, server-authorized SYSTEM demonstration only, with stable service/job provenance. The UI and the owner walkthrough must show that label. "Accepted" must not read as a human approval.

P8. **Routes and roots.** Use `/sites/{site_code}/actions/{action_id}` (the decision's `{site}` is the pre-S3 `site_code`) with a parallel `/api/sites/{site_code}/actions/...`, and 401/403/404 per the pre-S3 ruling. The mock's Action tabs sit under the Actions root, Recommendation under Findings, and `changes` under Site Foundation. State which route renders `changes:1#a` and how it links to the Action and the event. Keep Plan, Evidence and Verification tabs hidden or honestly unavailable in S6-01, not empty.

P9. **Fixtures and states.** Persisted positive, pending, failed (stale expected revision, wrong Site, invalid value), idempotent-retry, concurrent-command and reload cases. Exact `event_id` and cutoff selection, including a backdated `occurred_at` shown as such. 1440/390 app-versus-mock comparison of `action-overview`, `action-execution`, `action-history`, `recommendation:1` and `changes:1#a`. Keep `USER_REVIEW_REQUIRED` and the owner-absent merge hold.

P10. **Technical design extension.** `action_event` currently has only `actor_id` and `payload`. The decision adds actor kind, source channel, authorization basis and triggering command/job/content revision, and `action` gains the origin FindingRevision, assessment and basis pins. The migration must add these as real columns, or as a reviewed typed payload schema.

## Residual risk not named in the output

- Delegated provenance could be lost (M1) if the branch merges without the force-added `.agent` files.
- The retroactive-publish gap (P5) would not show up with forward-dated fixtures. It would surface only when a backdated reserve edit silently changes the baseline Foundation of an S6-02 comparison.
