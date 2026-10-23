# W5-02b K3a + K3b re-review (cold Incidents and Maintenance tabs)

Reviewer: fresh independent Claude reviewer, 2026-10-24. Branch `task/W5-02b-K3-cold-cases`, reviewed at `6cd7f733`, then at `5352c035` (ruling 25), per the coordinator. The review is against `.agent/W5-02b-K3-review.md` (`a0e7d88f`, M1-M3, L1-L5, items 1-7) and build-spec K3 rulings 17-25.

I read:
- the fix diff `a0e7d88f..5352c035`, covering `frontend/src`, `tools/w502*` and the evidence;
- the handoff;
- the evidence README and the measurements JSON;
- the PNGs: narrow Incidents worstcase and one-open, narrow Maintenance worstcase, desktop Incidents worstcase, and desktop Maintenance every-disclosure.

## Verdict: ACCEPT

Counts: **High 0, Medium 0, Low 2.** Neither Low blocks the merge.

## Closure of the original findings and rulings

| Item | Closed? | Evidence |
|---|---|---|
| M1 / ruling 18: all-open definition | Yes | `OPEN_READ_FULL` (`tools/w502-cold-work-evidence.mjs`) opens a `Activity recorded`/`Outcome note` parent only when it holds a nested control, then every `Read full text`. The claim asserts all controls open, no preview while open, each value once, and `otherOpen` empty. Measured: Incidents 8/8, Maintenance 12/12, matching 4 long rows × 2 and × 3 long cells. The every-disclosure state is separate and INFO only, and both expanded states drop only the panel and page-main height claims (`capCase(..., false)`). The strip, notice, rows, containment, focus and overflow claims are kept. |
| M2 / ruling 20: one-line UUIDs | Yes | `w1f4-action.css:225-236`: `contain: inline-size; overflow-x: auto` on the body, and `white-space: nowrap` with no `overflow-wrap`/`word-break` on `code`. The stacked fact grid is kept. The capture claims lines === 1, reachable and `cellFits` for every opened code. The desktop Maintenance every-disclosure PNG shows one-line UUIDs with an in-body scrollbar and unchanged column widths. |
| L2 / ruling 20: one-line Window | Yes | `w1f4-action.css:283-285` targets the `span[data-work-window]` only (`siteWorkCases.tsx:704`), so `UTC and IDs` (`RowDetail`) still wraps beneath it. The desktop Incidents PNG reads `22 Oct · from 19:15` on one line. A `windowLines` claim is present. |
| M3 / ruling 21: no vertical box on cold Incidents at 390 | Yes | `w1f4-action.css:289-293`, at specificity (0,4,0), beats W4's (0,3,0) `w4-work-cases.css:134`, which is unchanged. The claim asserts `maxHeight === none` and every row inside the scroller. The narrow PNG shows all five rows. |
| Ruling 21: MINIGRID keeps the 224 px box | Yes, by code | `data-cold-cases` is set only when `cold` is non-null (`siteWorkCases.tsx:980`, COLDCHAIN only). The W4 rule is untouched. No test asserts it; see L2. |
| L1 / ruling 19: CURRENT capture | Yes | The producer adds a `current` window with `from,to` only and records the returned `known_at`/`status`. Attest requires `current:*` on positive. The capture claims no `known_at=` in the URL, manifest `CURRENT` and no currentness notice. The false comment is corrected. |
| Ruling 22: WR completion | Yes | The literals match: ASSIGN at D+16h41m `{"assignee":"Maintenance lead"}`, key `w502b-{mode}-wr-assign-{tag}`; COMPLETE at D+16h42m citing the returned record ID. They run after the record and **before** the case-link loop and the intent. The latest-`work_event` link therefore pins the COMPLETE event. Returned IDs, times and states are asserted and stored. The producer blocks unless positive `current:maintenance` is `["COMPLETED"]` and worstcase is COMPLETED + 4×OPEN. The capture asserts the exact chip multiset. |
| Ruling 22: K2 Actions invariants | Unaffected | K2 invariants: the K0<K1<K2<K3 assert is unchanged and still runs after the new events. Attest (ATTEST OK in the handoff) still runs the DB-lineage and served action-index checks. The Action count, title and due date are unchanged by construction. K4 `Related activity` is out of scope here. |
| L3: dead CSS | Yes | The earlier `margin-top: 2px` rule is deleted. |
| L4: long-text tests | Yes | A parametrised test over narrative, activity and outcome note opens the outer parent where needed, then the inner control. It asserts the preview is removed, the value appears once, and the preview is restored. |
| L5: returned record time | Yes | The fixture and extra records are re-read from `maintenance_record.occurred_at`, asserted equal to the requested time, and the stored value is written to the manifest. |
| Item 7 / ruling 24: 403 copy | Routed | No K3 change, as ruled. |
| Ruling 25: 390 Incidents one-open 680 | Yes, only that cap | `5352c035` adds an optional `panelCap` to `capCase` and passes 680 only for `kind === "incidents" && W === "narrow"` in the one-open call. Every other call and the `CASE_CAPS` table are unchanged. The JSON edit changes only that claim's name and `ok`, plus `failed` 1→0, and labels it `"reevaluated": "K3 ruling 25"` with a no-recapture note. The measured value is still 664. No product code changed. |

On open item 3, the 664 px panel is content, not a layout bug. The narrow PNG shows the opened 160-character title wrapping in the sticky first column. The roughly 88 px closed rows come from the off-screen two-link Linked-findings cell, which is real content. Ruling 25 now covers it.

**Mock fidelity.** At 1440 and 390 the captures keep the five v69 columns, the strip literals, `Manage in … →`, the domain foot notice and horizontal table scrolling (`index.html:334-342`). They have no vertical case box. Every fix restores a spec rule (spec :78) or applies a ruling. I found no new implementer decision and no unlabelled mock departure.

## Findings

### Low

**L1. The ruling-20 scroll rule applies to every cold disclosure body, and the capture tool's relaxed containment test then passes any such body, so long-text containment is no longer actually tested.**

Where:
- `frontend/src/sites/w1f4-action.css:227-230` puts `contain: inline-size; overflow-x: auto` on every `td .disclosure .disclosure__body`. That includes the `Read full text`, `Activity recorded` and `Outcome note` bodies, not only `UTC and IDs` and `Finding version`.
- `tools/w502-cold-work-evidence.mjs:380` (`inside`) and `:385` (`openBodyFits`) now accept any element or body whose `.disclosure__body` is `overflow-x: auto`.

Why it matters: for the long-text bodies, `openBodyInside` and `openBodyFits` now hold automatically. Long text that failed to wrap would become a hidden in-body horizontal scroller and still pass. Today the text wraps (`overflow-wrap: anywhere` at `:269-273`, and the PNGs confirm it), so nothing is visibly wrong. Only the evidence is weaker than its claim wording.

Fix, either of:
- scope the scroll and containment rule to the ID disclosures (for example, bodies that contain `code`, or a data attribute on `RowDetail` and the Finding-version disclosure);
- or limit the tool's relaxation to bodies that contain `code`.

This can be done on the branch or tracked as a Low in the backlog. No recapture is needed for the CSS-only variant if the long-text bodies keep wrapping.

**L2. No test locks the MINIGRID side of ruling 21.** `frontend/src/sites/__tests__/coldWorkCases.test.tsx:448-460`, the `mini-grid isolation` test, does not assert that `[data-cold-cases]` is absent. The cold-side tests do not assert that it is present either.

Why it matters: the only thing keeping W4's 224 px box on MINIGRID and removing it on cold is that attribute. jsdom cannot test the CSS, but it can test the hook.

Fix: add `expect(main.querySelector("[data-cold-cases]")).toBeNull()` to the MINIGRID test and a non-null check to one cold test.

### Notes (no finding)
- `overflow-y: visible` beside `overflow-x: auto` (`w1f4-action.css:292`) computes to `auto`. It is harmless because `max-height` is `none`, but the declaration does not mean what it says.
- The `caps` header in the measurements JSON still lists `panel: [650, 650]`. The single 680 exception is visible only in the re-evaluated claim and the `reevaluation` note. That is acceptable, because the evidence was re-evaluated rather than recaptured.
- The `:208` comment, "disclosure text wraps inside the cell", now sits above rules that keep IDs on one line. It is cosmetic.

## Checks I ran

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` (frontend, at `5352c035`) | exit 0 |
| `npx.cmd vitest run` on `coldWorkCases`, `siteWorkCases`, `coldWorkActions` and `w1f4ChangesWorkStructure` | 4 files, 91/91 pass |
| `tools/check-all.ps1` | All 11 guards passed, including architecture, agent workflow, screen ledger (110 screens, 258 panels), dependency registry and missing-claim scan |
| `node --check tools/w502-cold-work-evidence.mjs` | OK |
| `ast.parse` of `tools/w502_cold_work_walkthrough.py` | OK |
| `git diff 6cd7f733 5352c035 --stat` | Only `tools/w502-cold-work-evidence.mjs`, evidence README/JSON, the handoff, and the spec and Architect request from the merge |

## Not verified

- The full frontend suite (2835) and `npm run build` were not rerun. They rest on the implementer's batch.
- Producer `prepare`, `serve` and `attest`, and the captures, were not rerun, per the dispatch. They rest on the handoff (ATTEST OK) and the measurements JSON.
- The ruling-25 result is a re-evaluation of stored measurements, not a fresh capture. That is acceptable because no product or CSS code changed after the capture tree (`6815ae65`, frontend unchanged through `5352c035`).
- No focused Postgres run was done. No backend file changed, and the w502 tests do not import the producer.

## Residual risk

- Weakened long-text containment evidence (L1).
- K4 `Related activity` must later prove both branches of ruling 22: the completed sentence at a current cutoff, and `No completed inspection is linked to this Action.` at a pre-completion cutoff. K3 does not exercise either.
