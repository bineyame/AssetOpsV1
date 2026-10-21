# W3-02 commit 2 independent review (Evidence page, shell, eyebrow, wording)

Reviewer: fresh Claude reviewer, not an author of this range. Date: 2026-10-21.
Branch `task/W3-02-estate-evidence-money-basis`, head `44d2763c`. Range: `33b9711e..44d2763c`, non-merge commits only (d9f898e7 through 44d2763c). The W4-02 planning commits that arrived through main merges are outside this slice.
Authority: `main:.agent/W3-02-build-spec.md` closures 4 and 5 (commit 2), rulings c2, c2b and c2c, `.agent/W3-02-mock-measurements.md`, and v69 `globalevidence` (`screens.js:522-526`).

## Verdict: REVISE

One Medium finding: the committed partial-state captures were taken before the c2c fix and still show a raw code. Re-take them and the slice can be accepted. The code, copy, shell and registry work matches the rulings. The other findings are Low and do not block.

## Findings

### Medium

**M1. Partial-state captures are stale and show a raw observation code.** Files: `.agent/W3-02-evidence/evidence-partial-1440-app.png`, `evidence-partial-390-app.png` and `app-partial.json`.
- They were last committed in `c17bc864`, with `captured_at` 2026-10-21T02:06:54Z. That is before the c2c build commit `93b065e8`. Only the positive pair was re-taken, in `44d2763c`.
- In the partial 1440 PNG, the cold `Backup response` row's Current ceiling reads `Not observed: TRANSFER.`. That is the exact raw fragment c2-q7 forbids on any client-facing surface.
- **Why it matters:**
  - Commit-2 review evidence must show the head build in both captured states.
  - This image is the one most likely to be reused in the walkthrough index.
  - It also leaves the partial-state heights unproven at head, though the c2c change is backend text only, so those heights are probably unchanged.
- **Fix:** re-take the partial pair at 1440 and 390 on the head build with `capture.mjs`. Commit the PNGs and JSON, and record the heights in the handoff. Confirm that the Backup row reads `No record of power transferring to the generator.`

### High

None. Panel set, order, titles, eyebrow placement, subtitle, card labels, column headers, notice copy and the inert CTA slots all match the mock and the rulings. A finding for each, if there were any, would appear above.

### Low

**L1. `Record details` shows a raw JSON dump.** `frontend/src/estate/EstateEvidence.tsx:160` (`RowDetails`) prints `JSON.stringify({constituents, reasons, prior_selection})` in a `<pre>`.
- The spec allows raw IDs and state in the disclosure (ledger line 82, c2-q4), and c2c's mapping keeps step codes out of it, so this is within contract.
- Even so, keys such as `missing_roles`, `assessment_revision_id` and `prior_selection: null` are system vocabulary on a client-facing page.
- **Suggested fix:** carry it into the batched plain-language/UI pass. Render labelled facts, or keep the JSON behind a second, inner disclosure.

**L2. Named frontend test `meetsMeasuredNarrowLayoutWithoutDocumentOverflow` is absent.** It is listed in build-spec "Proof and builder handoff" (line 201 at head) among the eight required frontend nodes.
- The 390 captures prove the behaviour in practice: `docScrollW == docClientW == 390`, `over: []`.
- The spec does not say which commit owns the test, and jsdom cannot measure layout anyway.
- **Suggested fix:** record in the handoff that the test belongs to commit 4 or is satisfied by the captures, so the commit-4 closeout does not lose it.

**L3. Ledger `data_owner` is stale.** In `frontend/docs/architecture/v69-screen-ledger.json`, the `globalevidence` entry still reads `"data_owner": "Unassigned Evidence read model"` while coverage is now `bounded`/W3-02.
- **Suggested fix:** name the `GET /api/estate/evidence` read (`estate/evidence_money.py`) when the registry is next touched.

**L4. Eyebrow case: ruling vs mock (Architect note, not an implementer defect).**
- c2b rules a small, muted, uppercase eyebrow, and the app renders `EVIDENCE` at 10 px.
- The checked-in mock capture `mock/mock-globalevidence-1440.png` shows sentence-case `Evidence`.
- The implementer followed the binding ruling. If exact mock fidelity is wanted, route it to the Architect.

**L5. The notice icon is missing (pre-existing shared primitive).**
- The mock notice has a leading info icon. The shared `Notice` (`ui/V69Layout.tsx:165`) renders none on every page.
- This range did not introduce it. Belongs to the UI/UX pass.

## Checklist results

**Panels, order, titles, eyebrow, copy.** All of the following match:
- Header: eyebrow `Evidence` above the h1 `Portfolio evidence`, then the subtitle, all in one `<header>`, with no breadcrumb.
- Page order: date bar, three cards, `Capability coverage across sites` with its mock subtitle under the title, `Recurring evidence gaps`, then the blue notice with the exact mock text.
- Column headers: 5 in coverage and 4 in gaps, exactly as in the mock.
- Cards: values and notes as closure 1 rules (`n of N` / `Not assessed` / `0 of 0`), all muted, and no mock number survives.
- `PageHeader` renders no eyebrow node when the prop is empty. `estateRoots.test.tsx` asserts this for Findings.

**System vocabulary and raw codes, including the c2c mapping.**
- `plain_limitation` covers exactly the eight `cold.STEPS` codes; the test asserts set equality with `cold.STEPS`.
- It is applied to cold `current_ceiling`, constituent limitations and `prior_selection`.
- EV uses an empty mapping, so it fails closed.
- An unexpected or malformed fragment gives only the fallback sentence.
- `assert_plain_observations` scans the whole wire row, disclosure included.
- Readiness and context words follow c2-q4. Raw state appears only inside the closed disclosure; `showsPlainReadinessAndContextWords` asserts this.
- The positive 1440 capture at head shows the mapped sentence.
- See M1 for the stale partial capture and L1 for the JSON dump.

**Refusal copy.** `EVIDENCE_REFUSAL_COPY` is pinned with `toEqual` to the exhaustive c2-q2 table, aliases included.
- An unknown code, a non-JSON body or the wrong schema falls back to the 503 sentence. The client test checks this.
- A refusal removes the tables and the prior rows.
- The refusal block exposes the code only as a `data-` attribute.

**Site display.**
- Each row shows `{stored site_name} · {domain_label}`, linked to the server's `links.site_readiness`, with `Opens current Site view` when the link falls back.
- The gap Sites cell shows the stored `site_names` from the wire, falls back to the stored code when a name is empty, and keeps the codes in the disclosure. Tests cover both the API side (gaps whose Sites are on another page) and the UI side.
- No mock Site name renders.

**Links.**
- The server owns the links; the page builds no Site route.
- B5 link-following: the three c2-q3 tests in `test_w302_evidence_links_postgres.py` follow cold and EV links through the W2 Site reads with the exact window and cutoff (200, not 422), and check the placeholder fallback.
- The "selected row, but its cutoff cannot be proved" branch is covered by commit-1 pure tests: `test_w302_evidence_api.py:286-289` exercises `window_links`.
- Inert example destinations: 4 slots, exact text and accessible names, no `href` or `button` in the gaps panel.

**Shell route, rail, guard tuple and fixtures.**
- `EVIDENCE_PATH="/evidence"` mounts `EstateEvidenceFrame`, whose `<main>` has the accessible name "Evidence". It is pinned equal to `ESTATE_EVIDENCE_PATH`.
- `/sites/{code}/evidence` keeps its existing handler; `w302EstateEvidenceShellRoute.test.tsx` checks this.
- The rail entry is now live in the `ASSURANCE` group, and Financials is still unavailable.
- The truthfulness tuple is `live|Evidence|ASSURANCE|/evidence`.
- Four new rail fixtures: missing target, route removed, demoted, Financials promoted.

**Registry.**
- `I-estate-evidence-root` uses area `estate-aggregation`, requires `A-estate-index-scope` and `I-capability-read`, and is open with null evidence.
- `globalevidence:1/:2` are `gap`, with exactly the c2-q5 `requires` lists. Their reason text says it "awaits independent review ... no owner acceptance is recorded".
- The brief lists the node, and the ledger links it to `P-estate-area`. The tier is still "pending owner review".
- No owner-acceptance claim is made anywhere.

**Captures and heights.** Checked against the JSON:

| Capture | Cards | Coverage | Gaps | Notice |
| --- | ---: | ---: | ---: | ---: |
| positive 1440 | 115 | 279 | 183 | 43 |
| positive 390 | 280 | 421 | 350 | 80 |
| partial 1440 | 108 | 302 | 183 | 43 |
| partial 390 | 277 | 445 | 350 | 80 |
| ceiling maximum 1440 | 137 | 314 | 316 | 66 |
| ceiling maximum 390 | 291 | 468 | 703 | 102 |

- Every capture is within the maxima.
- At 390 the table scroll widths are 520 and 330, against the mock's 531 and 337.
- The 390 cards keep the 2+1 grid.
- Document scroll width equals client width at both widths.
- The partial pair is stale (M1).

**`settled.ts`.** The change only adds the alternative `evidence across the estate` to the `LOADING` regex. Nothing is removed and no wait is shortened, so no other test is weakened.

**Non-vacuity.**
- Backend: the eight-code test pins exact sentences, set equality with `cold.STEPS`, and the fallback and EV-empty cases. The scope test also requires that a mapped sentence is present.
- Frontend: the tests assert exact strings, tones, ordering, hrefs and absence conditions.
- `rendersTheSelectedColdBackupCeilingInPlainWords` is a passthrough check, because the fake already carries the mapped text. The c2c ruling places the real proof in the backend, so this is acceptable.
- I did not repeat the implementers' revert experiments.

## Checks I ran (head `44d2763c`)

- **Backend:** focused W3-02 Evidence files `test_w302_evidence_api.py`, `test_w302_evidence_scope_snapshot_postgres.py`, `test_w302_evidence_links_postgres.py` and `test_w302_evidence_ev_postgres.py`.
  - Run in my own detached worktree with `PYTHONPATH` set to its backend, contracts, simulator and gateway, on a private `assetops_w302rv_test` database (created, then dropped).
  - Result: **28 passed** in 202 s.
  - My first attempt errored at collection: PYTHONPATH initially missed simulator and contracts, and the DB did not yet exist. Both were environment problems, fixed before the run above.
- **`npx.cmd tsc --noEmit`** in `AssetOpsV1-review2/frontend`: exit 0.
- **Focused vitest** (estate, the W3-02 shell route, sharedVisualVocabulary, operatorRailInventory): 5 files, **52 passed**.
- **Full `npm.cmd test`:** **96 files, 2384 passed**, 165 s. In this session vitest ran without the sandbox esbuild failure.
- **`tools/check-all.ps1`** in `AssetOpsV1-review2` (clean, HEAD `44d2763c`): all **11 passed**. Architecture and agent-workflow passed too.
  - In my fresh worktree, the architecture and check-all runs failed: rule-8 reported the EV insert checks "vacuous", one `.mjs` fixture failed, and the worktree has no `.venv`.
  - The same scripts pass on the clean `AssetOpsV1-review2` checkout at the same HEAD, so I read this as a worktree environment problem rather than a code defect. I did not investigate further.
- **Not run:** `npm.cmd run build` (tsc and the suite cover types and modules; the packet reports build 0), the full backend suite (it is due at commit 4 by the spec), and live captures (Chrome plus backend not exercised).

## Residual risk not named in the packet

- `plain_limitation`'s regex `Not observed:([^.]*)\.?` stops at the first `.`. A future code containing a dot, such as a decimal, would fall to the fallback sentence. That is safe, but the result would be unhelpful.
- The coverage list shows 3 rows in a 176 px internal scroll. With 9 to 15 real rows, most Site rows sit below the fold of the scroll region. The 1440 positive capture shows only the cold rows. Within the spec's rules, but worth noting for the owner walkthrough.
