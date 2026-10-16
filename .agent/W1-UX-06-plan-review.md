# W1-UX-06 plan review: W1 closeout and combined owner walkthrough

Reviewer: fresh independent Claude reviewer (did not author the packet). Worktree `AssetOpsV1-review4`, packet commit `f39d78fe` (diff `f39d78fe~1..f39d78fe`: `tasks/W1-UX-06-closeout.md`, README row, registry node `I-W1-UX-06`, Planner log). Read-only; no suites run, as dispatched.

## Verdict: RETURN (one Medium)

The packet is accurate, small and safe on honest state. Every cited seam checks out (see below). One Medium blocks it: the 390 px fix covers only the five scripts it names. It does not cover every evidence script whose narrow claims the final walkthrough will rely on, including the S4-08 script the umbrella names for this walkthrough. A one-paragraph change to Phase 1 fixes it.

## Findings

### M1. Medium (acceptance gap): the width guard does not reach every evidence script used in the final 1440/390 evidence set

- **Where.** `tasks/W1-UX-06-closeout.md:13` (code-reality row) and `:34` (Phase 1: "Fix all five evidence scripts (`w1-ux-01/03/04/05-evidence.mjs`, `v01a-foundation-evidence.mjs`)").
- **What is wrong.**
  - **S4-08 script missing.** The umbrella names `s408-assumption-history-evidence.mjs` as the evidence for the S4-08 rows (`tasks/W1-UX-mockup-fidelity.md:76`), and this packet requires those rows. That script has the same defective pattern: an unchecked CDP override in `size()` at `tools/s408-assumption-history-evidence.mjs:96-98`, followed by overflow measured as `scrollWidth - clientWidth` (`:128-130`). The fix list does not include it.
  - **s502 script missing.** The umbrella says `s502` evidence "is required in the combined document" (`tasks/W1-UX-mockup-fidelity.md:89`). `tools/s502-overview-finding-list-evidence.mjs:106-108` has the same unchecked `size()`. Its overflow check (`:151`, `scrollWidth - innerWidth`) cannot detect an override that never took effect.
  - **Other screen scripts missing.** `s602b`, `s603`, `s601b`, `s3-dispatch`, `s302` and `s404` share the same `size()` pattern (for example `tools/s602b-verification-evidence.mjs:97-99`). The UX-04 review cites captures taken with `s602b` (`.agent/W1-UX-04-review.md:79`).
  - **UX-02 sibling not named.** W1-UX-02 is a dependency, and its packet requires a per-slice evidence script (`tasks/W1-UX-02-*.md:11`). That script covers 8 of the 26 screens: `sites`, `mini`, `sitefindings`, the three `finding*` screens, `financials` and `assumptions`. The packet names the UX-03/04 siblings "when they land" (`:13`) but never UX-02's.
  - **One named path does not exist.** `tools/w1-ux-04-evidence.mjs` is not on `task/W1-UX-04`, which only ships `w1-ux-01-evidence.mjs`. So the fixed list is both incomplete and wrong about what exists.
- **Why it matters.** Phase 2 says "Re-run every 1440/390 capture with the fixed tool". The final-proof reviewer must also confirm that "390 claims were measured at 390" (`:41`). A 390 claim from an unguarded script repeats the exact UX-05 L1 defect: `clientWidth` 1425 at a nominal 390. That defect is the reason this slice exists, and the plan as written fixes it only in some scripts.
- **Fix (packet wording).** Replace "five" with an inventory rule, and drop or condition the `w1-ux-04-evidence.mjs` path. In Phase 1, after the dependencies merge, the Implementer:
  1. Lists every evidence script whose 1440/390 claims or screenshots the combined walkthrough cites. At minimum: the existing w1-ux-0N siblings (including UX-02's), `v01a`, `s408`, `s502`, and any `s*` or `v01b` screen script used for a row.
  2. Applies the shared width guard (one helper module) to each of them.
  3. Records the list in the packet.

  Any cited script left unguarded has its narrow claims recorded as **not established**, never as met.

### L1. Low: as-of regex description is slightly off

`:14` calls `/^As of /` "permissive". It is permissive for any text after "As of ", but because of the colon it *rejects* the honest `As of: time not recorded`. The Phase 1 fix (`:34`) is correct either way; only the description is off.

### L2. Low (sizing): Phase 2 is the long pole

Phase 1 is S. Phase 2 re-serves about 15 walkthrough tools one at a time and captures 26 screens plus S4-08 at two widths, which is closer to M+ than S-M in elapsed time. Registry effort `M` is acceptable. Consider letting Phase 2 captures be committed in batches ordered by tool, so that one failing tool records **not run** instead of stalling the slice. This does not block.

## Code reality: verified

| Claim | Checked |
| --- | --- |
| `w1-ux-01/05-evidence.mjs:99-114,130-141,184-186`: `size()` without a width check, measure, `/^As of /` | Confirmed (`size` :103-106, measure :123-145, claims :184-186 in both) |
| `v01a-foundation-evidence.mjs:107-135,164,209,250` | Confirmed: unchecked `size` :107-110, `overflow()` :131-135, `layout()` :164, `within()` :209 (uses `clientWidth`), WIDTHS loop :248-250 |
| `productPresentation.ts:25-40` accepts only `^As of ` | Confirmed (:39) |
| `productWords.ts:399-402` emits `As of: time not recorded` | Confirmed |
| `siteHealthBoundary.test.tsx:406-421` local substitute | Confirmed (`expectRefusedStateLine`) |
| `source_health.py:258` raw `received_at - observed_at` | Confirmed. Fixture `s7_health_api_contract.json:466` has `-90` with `GATEWAY_CLOCK_UNTRUSTED`. The contract test compares against the fixture (`test_s7_health_contract_postgres.py:95-100`), and the frontend imports the same fixture (`siteHealthBoundary.test.tsx:17`). The UI shows lag only when it is `>= 60` (`SiteHealth.tsx:107`). |
| Three "signal binding set" sentences | Confirmed at `foundation_api.py:340-343`, `binding_service.py:773-775` and `:935-939`. The frontend overrides are at `FoundationBindingsPanel.tsx:96-101`, used at :196, :249 and :373. The only exact-string test outside the backend is `frontend/src/shell/__tests__/siteFoundationRevision.test.tsx`; no backend test pins the sentence text. |
| Label seams | `READINESS_WORD` at `FoundationBindingsPanel.tsx:31-35`. "Nothing is missing" is in `foundationHeadlines.tsx` (~:316). "All ${n} enabled gateways..." is at `healthHeadlines.tsx:166-168` and reads positive when `enabled.length === 0` and the status is not `NO_REGISTERED_SOURCE`, so Q4 is a real case. Selected gateway: `SiteHealth.tsx:472-480`. |

## Backend minimality and contract

The backend change is minimal: one null-on-negative at the read boundary, three reworded sentences, an updated committed contract fixture, and direct backend and UI tests. Nulling only the negative value keeps the `GATEWAY_CLOCK_UNTRUSTED` reason, so nothing is hidden behind a positive, and nonnegative lag is retained. The single full backend suite command matches `backend/TESTING.md:107`.

## Combined walkthrough plan

For a plan whose dependencies are not merged yet, Phase 2 is concrete enough:

- It names the deliverable file and the source map: umbrella :56-89, all 26 rows plus the S4-08 default and `recorded_at` cases.
- It serves one private case at a time, using each tool's own transition and cleanup modes and only tool-printed URLs and IDs.
- It records **not run** with the blocking precondition, keeps no-card missing states explicit, and keeps the owner gate closed if any claim is unestablished.
- It rightly defers literal commands until dependencies land. The existing draft at `.agent/W1-UX-combined-owner-walkthrough.md` covers only the UX-05 rows.

With M1 fixed, the "measured at 390" acceptance is achievable for every row.

## Honest state

No risk found. All four Architect recommendations move copy away from positive claims: "Set up to report", "Set-up steps", "In contact; its latest report is old", and non-positive fallbacks, including for zero enabled gateways. None is unsafe. There is no panel promotion, and the packet explicitly does not infer owner acceptance from screenshots.

## Registry and records

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs` exits 0: "Registry valid: 241 nodes, 11 linked pilot panels"; area briefs valid.
- `I-W1-UX-06` requires UX-01..05 and `I-S4-08`, with status open and effort M. It sits outside the ranking with a reason that gives it no core score.
- The README row is present.
- The packet is 41 lines, within the brief's ~120.

## Not run

No suites were run (as dispatched). The evidence tools were not run; they need Chrome, the walkthrough DBs and a dev server.
