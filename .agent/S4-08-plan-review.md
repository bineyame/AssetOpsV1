# S4-08 plan review: Site assumption and consequence history

Reviewer: fresh independent Claude reviewer (plan review; nothing built).
Reviewed: `f33e84ef` (`git diff f33e84ef~1..f33e84ef`): `tasks/S4-08-assumption-consequence-history.md`, registry edits, `tasks/README.md` row, `tasks/W1-UX-mockup-fidelity.md` map row. I did not review the Planner log in detail.
Authority checked: `D-2026-10-14-s402-post-review-follow-ons`, `.agent/architect-S4-02-batch-answers.md` Q4, `D-2026-10-15-s405-stored-demo-provenance`, `D-2026-10-16-s405b-label`, `D-2026-10-16-w1-ux`, `.agent/owner-walkthrough-policy-2026-10-16.md`, and the S6-03 cursor precedent `D-2026-10-16-w1-remaining-questions` 1 (as implemented in `backend/assetops_backend/actions/site_index.py:10-14`).

## Verdict: RETURN

Two Medium findings block: M1, which can let money through, and M2, a paging/cutoff gap. M3 is a contract gap against the existing price read. All three can be fixed in the packet text. Code reality is otherwise accurate, the registry is valid, and the migration, rule-8 and walkthrough handling are sound.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 240 nodes, 11 linked pilot panels`, exit 0. `assumptions:3#a` `technical_requires` already include `I-assumption-consequence-history-read` and `-ui`. `I-S4-08` is in `queue_baseline_nodes`, and its `requires` and `sequenced_after` resolve.
- I ran no suites, as the dispatch asked.

## Code reality (cited path:line)

| Packet citation | Found |
| --- | --- |
| `financials/assumption_read.py:3-5,63-96` | Correct (cutoff semantics :3-6; `series` :63-96). |
| `financial_read_api.py:64-85` | Lines are correct, but the file is `backend/assetops_backend/financial_read_api.py`, not under `financials/` as the table row implies (L1). |
| `financials/assumptions.py:193-217` | Correct; the equal-start succession branch is :215-218. |
| `adapters/postgres_consequence_store.py:381-436` | `chain` is :381-434. Correct. |
| `financials/consequence_read.py:169-268` | `read` is :169-271. Gates: provenance :223-236, `presented_as_current` :239-241, `withheld_reasons` :274-287. Correct. |
| `finding_api.py:245-268` | Correct (`finding_consequences`, scope at :250, closed-source refusal :258-259). |
| `0011_financial_consequences.py:43-123,143-152` | Correct. Indexes are only `(tenant, site, window_start, window_end)` and `(tenant, site, finding, finding_revision, revision_no)`. There is no `recorded_at` index (see Migration below). |
| Migration head `0019_verification_core` | Correct. |
| `evidence/provenance_read.py:23-36,60-83` | Correct (`source_gate` :35-39, `consequence_provenance` :73-87). |
| `frontend/src/sites/sourceProvenance.tsx:1-94` | The file exists (172 lines). |
| `frontend/src/sites/SiteFinancials.tsx:192-231,356-390` | Correct (`SiteAssumptions` URL handling; Price history panel). |
| `frontend/mockups/v69/index.html:485-490` | Correct. The `assumptions` screen is at :486-489. |

## Findings

### M1 (Medium, fail-open risk): no rule stops a current amount at the server-defaulted cutoff

Packet item 1 makes every request carry a cutoff: a missing `recorded_at` becomes a server-fixed instant, which is then placed in UI URLs. Item 3 lists the gates that forbid a current amount, which implies that a row passing all of them may show one. Architect question 3 recommends "no current amount for a selected past cutoff; only today's exact-head read may make a current-money claim". An implementer can reasonably read "today's exact-head read" as this endpoint at its default cutoff (the cutoff is "now", and the row is the exact head). Several things go wrong under that reading:
- The cutoff is written into the URL, so the same URL reloaded tomorrow is a past cutoff. Either the view's money claim changes on reload, or the server shows current money for a stale instant.
- The existing gates are evaluated now, not at the cutoff. `derive()` compares against today's price timeline (`consequence_read.py:200-212`), and LR-01 eligibility and the source gate are current reads. None of them can certify "current at cutoff C".
- Running `derive()` for every Finding on a 100-row Site page is also an unplanned cost.

Why it matters: this is the one route by which this view could show current money that no current read justified.

Fix: state in item 3 that this endpoint and panel never make a current-money claim at any cutoff, the defaulted one included. Every amount is a labelled "recorded" amount, and is shown only where the existing closed-source rule and the row's stored `state = PRICED` allow. A row marked `CURRENT_AT_CUTOFF` links to Finding Financials for the current amount and its gates. Name the response field (for example, a constant `current_amount_shown: false`, or no such field) and add a test at the defaulted cutoff with all gates passing. This also sharpens the question 3 recommendation: as worded it is safe only if "today's exact-head read" means the existing per-Finding Financials read, so the Architect ruling should say that.

### M2 (Medium, paging/cutoff soundness): the cursor has no fence, so rows committed after the cutoff can enter later pages

Consequence `recorded_at` is the database's `clock_timestamp()`, taken inside the writer transaction before commit (`postgres_consequence_store.py:14,181`). A version can be stamped before the fixed cutoff C and commit after it. The first page's snapshot does not see that version. A later page's new repeatable-read snapshot does, because `recorded_at <= C`. With `(recorded_at DESC, id DESC)` paging, the version is then either skipped (when its stamp sorts above the cursor) or it "enters page two" (when it sorts below). The packet's own required test ("a late appended version after fixed cutoff must not enter page two") only covers a stamp later than C, which the filter already excludes, so the real race goes untested. "One repeatable-read snapshot" holds per request, not across pages.

Why it matters: the paging contract claims "neither duplicate nor skip" and cannot deliver it as specified. The project already has a ruled pattern for this: the S6-03 fence in the cursor with a typed 409 and a reload of page one (`actions/site_index.py:10-14,174-182`).

Fix: bind a fence into the cursor. Use at least the count and the maximum `(recorded_at, id)` of all rows with `recorded_at <= C` for this tenant/Site, computed in the same snapshot. On mismatch, refuse with a typed 409 such as `..._BASIS_CHANGED` and have the UI reload page one; keep 400 for tampering. Add a test with a deterministic interleaving: a row stamped before C and committed after page one. Record as a known limit that reloading the same cutoff later can show such a late-committed row; this is a property of pre-commit stamps.

### M3 (Medium, contract vs existing seam): the price read cannot share a server-fixed cutoff

Item 1 says "the Assumptions price and consequence requests must share that exact cutoff", and the code-reality table says to "reuse the exact UTC cutoff and URL selector". But today's price read treats a missing `recorded_at` as `CURRENT` (`recorded_to IS NULL`), returns `cutoff.recorded_at = null` (`assumption_read.py:83-84`), and `SiteAssumptions` sends `recordedAt = null` when the URL has none (`SiteFinancials.tsx:198-207`). Two independent default requests therefore select different instants. A consequence row can then cite a price revision that is missing from the displayed timeline. The default view also currently shows the "Show the current prices" notice only when the URL has `recorded_at` (:227-232), so putting the server cutoff into the URL changes existing behaviour and the `s402a_assumptions_walkthrough.py` default URL.

Fix: name the mechanism. Either (a) the UI requests the consequence history first and passes the returned cutoff to the price read, or (b) the price read gains the same server-fixed default and echoes it, as a stated extension of the existing API contract with its own test. In both cases, state whether the default Assumptions URL is rewritten to `?recorded_at=` (which affects the S4-02a notice copy and walkthrough) or the cutoff is carried in UI state only. Add a test that both reads report the same instant.

### L1 (Low): imprecise path

The code-reality row cites `financial_read_api.py:64-85` next to `backend/assetops_backend/financials/...`. The file is `backend/assetops_backend/financial_read_api.py`.

### L2 (Low, labelling): the time column and clock for "FindingRevision recorded by cutoff" are not named

`CURRENT_AT_CUTOFF` depends on the latest FindingRevision as of C. `finding_revision` has `created_at`, not `recorded_at` (`0009_finding_store.py`), and the value comes from the application (`finding_service.py:38,71`; tests inject it). Consequence `recorded_at` comes from the database clock. With injected or skewed clocks, a FindingRevision can appear to postdate its own consequence. Fix: name `finding_revision.created_at` and its clock, define the tie and skew rule (for example, a FindingRevision that has a consequence at or before C counts as recorded by C), and add one test with an injected FindingRevision clock. The question 2 recommendation itself is sound.

### L3 (Low): the price-filter parameter is implied but not defined

Item 4 refuses "foreign ... price IDs", and the UI is "reachable from selected price history", but the route has no `price_revision_id` filter. Either define the filter (scope it before lookup, refuse foreign IDs with 404, and leave the cursor bound to it) or drop "price IDs" from the refusal list and present the Site-wide list next to the price history.

### L4 (Low): the walkthrough tool is unnamed

The W1 map row says "S4-08 guarded case P/S/links (new)". Name the tool (a new `tools/s408_*_walkthrough.py`, or an extension of `s402a_assumptions_walkthrough.py`) so the coordinator's combined walkthrough can call it. Otherwise the route `/sites/{site}/financials/assumptions?recorded_at=` exists and the entry is reachable.

### L5 (Low, sequencing): S4-08 and W1-UX-02 edit the same component

W1-UX-02 (implementation-ready) restyles `assumptions` in `SiteFinancials.tsx` and does not mention the new consequence panel. State which merges first, and that W1-UX-02 applies its presentation to the S4-08 panel. This avoids a conflict and an unstyled panel at the combined walkthrough.

## Other checks (no finding)

- **Estate total:** forbidden explicitly ("No Site or estate sum"; "No count is required"). Consistent with question 4.
- **Withheld source:** a closed S3 source hides even recorded amounts, matching `FindingConsequence.tsx:552,570`. Mixed or unknown source and LR-01 pending or withheld allow only labelled prior amounts, which `D-2026-10-15-s405-stored-demo-provenance` permits ("prior values remain audit-only"). Labels follow `D-2026-10-16-s405b-label` through the reused `sourceProvenance.tsx`.
- **Foreign Site:** "scope before lookup" with 404 and no timing leak, reusing the `open_scope` pattern (`financial_read_api.py:37-50`). Sound.
- **Migration and rule 8:** no migration by default. A `(tenant_id, site_id, recorded_at, id)` index is the plausible addition if query proof demands one, and it is gated on Architect review. A read-only query adds no writer, and any write must be registered and guarded first. Handled.
- **Size S, one phase:** credible but tight. The proof matrix is wide: cutoff boundaries, equal-start succession, paging, refusal, five UI states at two widths, and a walkthrough tool. M1 and M3, once resolved, remove the per-row `derive()` work and settle the cutoff plumbing, which keeps it S.
- **Owner walkthrough policy:** the policy text names S6-03, S6-02b and S7-01b. Applying it to S4-08 matches the owner's general instruction ("progress without my walkthrough being a requirement for merge") and the W1-UX umbrella. Acceptable.
- **Architect questions:** recommendations 1 and 2 are safe. Recommendation 3 is safe only once M1's clarification is in.
