# S4-02a fix round 1: fresh Claude re-review

Reviewer: fresh Claude (did not build S4-02a, review it, or write the fixes). Branch `task/S4-02a-site-assumptions`,
diff `4c67de0..fc8e03f` (`778875d` code/fixture/tools, `fc8e03f` packet). Scope: M1, L1, L3, L4, L6 from
`.agent/S4-02a-review.md`; L2 and L5 to stay untouched.

## Verdict: ACCEPT

All five items are fixed as asked, with no scope creep. There are no blocking findings; two Info notes follow.

## Item checks

- **M1: fixed.**
  - `tools/layout-evidence.mjs:1893-1894`, `:4774-4775` and `:5046-5047` now expect
    `Overview|Foundation|Performance|Findings|Financials|Evidence`, and `:5047` uses `slice(0, 6)`.
  - This matches the slice's other tab claims at `:1802`, `:4572` and `:4668`. No five-tab predicate remains (grep).
  - Only the label strings and these predicates changed; the subtab and view conjuncts in `:5047` are unchanged.
  - The packet's "Checks run" sentence now names the real causes (MG-001 absent, two Lab/legacy-Kobo preconditions) and
    records M1 as a predicate change. Layout evidence was honestly recorded as not rerun.
- **L1: fixed.**
  - `financial_read_api.py:82-85` builds `api_next_page` with `urlencode`.
  - The new test `test_s4_assumption_read_postgres.py:109-117` follows the link with a recorded cutoff and asserts a 200
    and the second revision.
  - I restored the `4c67de0` version of `financial_read_api.py`, and the test FAILED (the link carried a bare
    `+00:00`). After `git checkout --` it passes.
- **L3: fixed.**
  - All three fixture steps now read "Demonstration price set by the system (...)". This is the `source_reference`
    rendered as Source at `SiteFinancials.tsx:170`.
  - No frontend, test or evidence-tool text still asserts the old wording.
  - The fixture name survives only in the stored `provenance` JSON. That JSON is not exposed by the read API or the UI.
  - Digest safety:
    - `assetops_s402awalk` and `assetops_s402aempty` do not exist in `assetopsv1-postgres-1`, so no owner DB holds the
      old step digest.
    - In `assetops_s402a_evwalk`, revisions 1-3 store the new text (re-prepared 2026-10-13 20:30Z). `_evempty` has no
      revisions by design.
- **L4: fixed.**
  - `SiteFinancials.tsx:445,447` say "What this finding means in money".
  - This matches `:463` and the Finding page link `SiteAnalyticsFrames.tsx:366`.
- **L6: fixed in the packet.**
  - Every key it cites exists in `v69-dependency-registry-pilot.json`:
    - `financials:1`, `financials:1#a`, `financials:3`, `financials:3#a/#b`;
    - `assumptions:1`, `assumptions:1#a`, `assumptions:2`, `assumptions:2#a`, `assumptions:3`.
  - The states it describes match the registry: `financials:3#a/#b` and `assumptions:2#a` are unmapped.
  - The Scenarios wording matches the manifest's `adapted` text.
- **Scope.** The diff touches only the six files above. Nothing in the tab-row CSS or the paging UI changed, so L2 and
  L5 are untouched.

## Info (non-blocking)

- **I1.** The packet's Fix round 1 L3 line (`.agent/S4-02a-review-packet.md`, Fix round 1 section) says the fixture
  name remains "in the stored provenance shown under 'Record details'". In fact `RecordDetails`
  (`SiteFinancials.tsx:100-143`) does not render `provenance`. It shows the publication key `demo-diesel-price-v1`,
  not the fixture slug. The product outcome is better than the claim, but the wording is inaccurate. Optional
  correction.
- **I2.** The original L6 also named the `SiteFinancials.tsx` header comment as prose-by-screen. Only the packet was
  re-keyed. The original fix asked for IDs when the G-05 handoff is written, so this is a carry for that handoff, not a
  gap now.
- A database named `assetops_s402a_test` exists in the container. It is not mine, and it is not the `s402a_fix_test`
  that the packet names. It is harmless, but the owner may want it cleaned up.

## Checks I ran

- **Backend.** Scratch DB `assetops_s402a_rr_test` (created, then dropped). I ran `test_s4_assumption_read_postgres.py`,
  `test_s4_assumption_read_api.py`, `test_s4_assumptions_postgres.py` and `test_s4_assumption_publication.py`:
  **64 passed**.
- **L1 non-vacuity.** With the old router restored, `-k next_page` gave 1 failed. The file was then restored, and
  `git status` is clean for `backend/`.
- **`npx.cmd tsc --noEmit`:** exit 0.
- **`npx.cmd vitest run src/sites`:** 13 files, **437 passed**. Vitest ran on this machine.
- **`tools/check-all.ps1`:** **all 9 guards passed**. The orphan scan reports 31 tagged / 12 baselined, and the ledger
  is valid.
- **Not run:**
  - full backend, full vitest and the build (not requested);
  - `layout-evidence.mjs` and the slice browser tool (no MG-001 store; not required for this round).
