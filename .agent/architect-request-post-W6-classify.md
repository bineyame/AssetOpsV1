# Architect request: classify the post-W6 audit and plan the fix slices

You are the AssetOps Architect. Read `.agent/post-W6-audit-spec.md` (your plan), `.agent/post-W6-audit/agent-brief.md`, `.ai/ROLE_CONFIG.md` lesson 15, and the register `.agent/mock-departure-register.md`. The audit is complete: 19 batch folders `.agent/post-W6-audit/batch-01` … `batch-19`, each with `batch-NN.md` (ledger), `batch-NN.json`, `differences.json` (some batches keep differences only in the .md), `index.html` and screenshots. Every disposition in those ledgers is an agent PROPOSAL; you decide. Implementer decisions are defects; you decide every one.

Produce, on this branch:

1. `.agent/post-W6-audit/classification.md`, with one row for EVERY difference ID in all 19 ledgers (B1-01 … B19-xx, including the X1 citation rows). Columns: ID, screens/pairs, disposition. The disposition is one of:
   - (a) an existing Rxx, with its status verified or corrected;
   - (b) a new D1/D2/D4/D5/D6, with the new register ID;
   - (c) D3, with the fix-slice name and severity;
   - "informational/no change".
   Cross-batch duplicates must be merged under one canonical ID, with the others pointing to it. Typical families are the shell top bar, 390 header, prose size, plurals, refusal copy, raw identifiers, domain Site Findings wiring (B7-01/B9-10), EV tab and links seam (B11-01/B16-16/B18-04), default window excludes today, and UTC vs Site-local.
2. Update `.agent/mock-departure-register.md`:
   - Add new rows for every (b) and (c), with a visible label rule for D1/D2/D4/D5/D6.
   - Correct stale rows the audit found (for example R12/R29-R31 "review pending", R40, R111/R112 "planned" now built, R20 screen list, `cold-cooling` vs `cooling` ID).
   - Recompute counts from distinct rows: open, resolved, withdrawn.
   - Register the W1-F5b/W3/W4/W6 rulings the audit found unregistered (B10-01, B12-01, B18-09, W1-F5b overage reasons).
3. Rule every panel-height case the audit flagged as needing a ruling (>1.3x or "needs a cap"), ONCE, per lesson 15:
   - size the cap from worst-case content;
   - give the all-disclosures-open exemption;
   - state the fallback if a remeasure exceeds it.
   B3-17 (assumptions history at 8.6x/17x) is the largest.
4. Coverage gaps and inventory:
   - Rule on the spec errors (cold-finding-excursion inventory B6-23; the route/producer column errors B2-31, B7, B12-13, B14-15, B18).
   - Rule on the producer gaps: no cold or EV authored-scenario producer (B14-16/B16-09); missing depth states (B16-10); no VERIFICATION_WINDOW/CANCELLED linked request (B15-10/B17-12); populated estate lenses (B10); populated Alternatives (B13-10); a KOBO-001-serving W1 producer for mini landings (B11-03); the stale ignored `var/sites` yaml and the `ASSETOPS_WORK_CURSOR_KEY_HEX` walkthrough env (B18-18).
   For each gap, say whether it is a producer-mode task inside a fix slice, or an accepted unverifiable state with a reason.
5. `.agent/post-W6-audit/fix-slices.md`: one D3 fix slice per shared seam, per spec §Fix slices. The seams are: shell/typography/copy; W1 mini/Action; W2 cold; W2 EV; W3 estate; W4 mini; W5 cold Work; W5 EV Work; W6 global Work. Split a seam into a/b if it has more than about 6 units. Each fix card names:
   - the exact D3 IDs;
   - panels and order;
   - data source;
   - states;
   - files;
   - tests;
   - the paired recaptures required;
   - caps.
   Mark which slices can run in parallel without sharing a file, and the merge order. Name the carried Architect items you are closing in the same pass: the K4 VERIFICATION_WINDOW/CANCELLED copy; the registry chain owner; W5-04c A1–A3 (see `.ai/MILESTONE_REVIEW_BACKLOG.md`).
6. `.agent/post-W6-audit/audit-index.json` + `index.html`: a merged machine-readable and human index of all pairs across the 19 batches, linking to each batch's own index and screenshots. Do not copy images. Report the total pair count against the 174 minimum.

Do not edit product code. Keep plain-language owner notes short. When done, list in your final message the counts by disposition, the slice list with sizes, and any decision that genuinely needs the owner (≤5% contests or D2 owner-approval items, as a short list).

## Owner context (2026-10-24, verbatim)
"I want to do the walkthrough after a demo sprint which i'll provide context on once the fixes comes through and are complete. We need to be able to bootstrap sites and portfolios based on story we want to present to our clients across the 2 verticals." Owner correction: "3 verticals i meant" (mini-grid, cold chain, EV charging).

Implication for this plan: the fix slices still close every D3. For item 4, mark each producer gap as one of: (i) needed to verify a D3 fix now; (ii) better served by the later story-based site/portfolio bootstrap (do not design that tool now; the owner will give context); or (iii) an accepted unverifiable state. Do not build throwaway producer modes that the bootstrap would replace, unless a D3 fix cannot be verified without one.

## Items needing explicit rulings
- **B19-15 (possible access-control defect, rule its severity first).** A principal with no Site access gets a real 403 on Site Work routes, yet reads the same request through the global work-request route, because it is composed with development_access (`main.py:582-585`). Decide whether this is production-reachable. If it is, it is a High D3.
- **Capture rules.** Batch 19's capture tool clicked History's client-only "Next" pager, which sends no request. Batch 11 declined a "Load more" click. Rule whether a client-only, non-mutating click is allowed under capture-only, so recaptures are consistent.
- **Mock values in a live form.** B18-14: the inert manual-reading form shows mock-only values.
