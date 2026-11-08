# Review — OWN-G3b, operational records entry form (frontend)

Reviewer: fresh Claude (Opus) reviewer, independent of the implementer. Branch `task/OWN-G3b-operational-entry-form`,
head `61ccdc73c`, diff `main...HEAD` (20 files). Spec: build sheet OWN-GAPS §1, §3.2, §3.3, §3.5 (G3b), Rev 1, Rev 2
R2-G3b 1-16. Mock: `frontend/mockups/v69/index.html` screen `oprecords`.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. Four Low notes below; none blocks the merge.

## What was checked against the spec

- **Layout and fields (§3.3, R2-G3b 7/13).** Row 1 Site + Reading, row 2 Value + Taken at, the Ticket row only for
  Fuel delivery, then the footer. Four Reading options with the right values, default TANK_DIP. Unit suffix L/L/kg/kWh
  and the four placeholders. `datetime-local`, `step=60`, empty on load and after a success, label
  "Taken at (Site local time)". Ticket placeholder "e.g. KIS-DT-0002". Button keeps "Submit for review".
  `OperationalRecords.tsx:481-575`.
- **Validation timing (R2-G3b 10).** `attempted` gates display (`:430`). Messages appear after the first Submit and
  are recomputed every render, so they update live. Value and Ticket are trimmed. The ticket pattern is the server's
  `^[A-Za-z0-9][A-Za-z0-9 /._-]{0,39}$` (`:120`). The delivery `> 0` check applies only when the value pattern
  passes. All six literals match the sheet exactly.
- **Request body (§3.2).** Exactly five keys in order, `ticket_reference` null unless FUEL_DELIVERY, no actor. Path
  `/api/sites/{encodeURIComponent(code)}/work/operational-entries`, POST, JSON (`globalWorkClient.ts:390-396`).
- **Idempotency key (R2-G3b 6/11/12).** Made at the first valid submit (`key.current ??=`, `:442`). Every field
  `onChange` goes through `edit()`, which nulls the key, including mid-flight edits. The key is nulled on success and
  kept after unconfirmed, a 5xx and a 4xx. The plain-http fallback uses 16 `getRandomValues` bytes as 32 lowercase
  hex (`globalWorkClient.ts:302-307`); the vitest stubs `crypto` without `randomUUID` and asserts the form.
- **Client parsing (R2-G3b 1/5).** 2xx needs `schema_version === "operational-record-1"` and a string `public_code`,
  else unconfirmed (key kept). A thrown fetch is unconfirmed. Non-2xx carries `detail.code`. A client without
  `submitOperationalEntry` gives the 403 row. The app's route passes `createGlobalWorkClient()` (`App.tsx:183,541`),
  so the live page has the method.
- **Outcomes (§3.3, R2-G3b 2/14).** "Saved as {displayCode(public_code)}, status Submitted." plus the fuel second line
  for TANK_DIP/FUEL_DELIVERY only. 403 forbidden, 422 NO_TANK/FUTURE/TOO_OLD, duplicate matched on the code alone,
  other 4xx, and 5xx/503/network → "could not be confirmed". All literals match the sheet (`:105-142`).
- **Site during reload (R2-G3b 4).** `siteChoice` is component state. The panel is not unmounted when `shown` goes
  false during the re-read (`OperationalRecords.tsx:637`, `globalWorkParts.tsx:348-352`). While options are empty
  the select shows "No Site selected" and Submit is disabled; when they return the kept code is re-selected, else the
  first. The result line is in the same component, so it survives the re-read. The test asserts both.
- **In flight.** Button `disabled={inFlight || site === null}` and the label is unchanged. `submit` also returns early
  on `inFlight`. Fields stay enabled (R2-G3b 12).
- **By column (Rev 1, R2-G3b 15).** `actorLabel` maps only `service:operator-entry`; only the Operational records By
  cell uses it (`:213`).
- **Banner (R2-G3b 16).** `OperatorShellLayout.tsx:12` reads "Demonstration · example sites and records". No source
  or tool pins the old literal; only historical audit evidence JSON quotes it.
- **Removed.** `MANUAL_READING_REASON`, `UnavailableInline` on the button, `.global-work-form-reason`. No remaining
  source reference.
- **Register.** R12 closed; R362 note "Taken at superseded by MD-OWN-G3-2"; R651 note as ruled; R710-R713 rows for
  MD-OWN-G3-1..4 match the code comment at `OperationalRecords.tsx:8-20`.
- **Mock comparison.** I viewed `mock-1440/390`, `app-1440/390-idle`, `-delivery-errors`, `-delivery-saved` and
  `app-1440-table`. Panel pair, panel heading, row order, label positions, select and input styling and the button
  match v69. Every difference is labelled: the description line and the result line (MD-OWN-G3-3), the Fuel delivery
  option, Ticket row and unit suffix (MD-OWN-G3-1), the empty native date-time input with the "(Site local time)" label
  (MD-OWN-G3-2), the By label and the third paragraph (MD-OWN-G3-4), and the existing "How records are used" prose
  (R31). The 390 delivery state stacks cleanly with no overflow. I found no unlabelled mismatch.
- **Wording.** All copy is plain language. The form text carries no forbidden fuel words, and `fuel_wording.py` is
  clean.
- **Accessibility.** Every control has a `<label htmlFor>`. Errors are linked through `aria-describedby` with
  `aria-invalid`. The unit is in the Value field's description. There is one `role="status"` `aria-live="polite"`
  region. All controls are native and keyboard operable. Implicit Enter submission is blocked while the button is
  disabled. See L1 and L2.

## Findings

### Low

- **L1 — the live region is `display:none` while it is empty.** `globalWork.css` `.global-work-form-result:empty {
  display: none; }`, region at `OperationalRecords.tsx:568`. A live region outside the accessibility tree until its
  first content appears is often not announced by screen readers (NVDA/JAWS with Chrome), so the first outcome, which
  is usually the only one, may be silent. A repeated identical outcome, such as two "could not be confirmed" in a row,
  also produces no DOM change, so it is not re-announced. Why it matters: the outcome is the form's only feedback, and
  it gives no focus move. Fix: keep the region rendered with no box (for example, drop the `:empty` rule and move the
  `p` margin onto `p + p` or a padding that collapses when empty). Clear `result` at the start of `submit` so a repeat
  is a change. This is a preference-level a11y hardening, not a spec gap; the sheet asks only for the role and
  aria-live.
- **L2 — focus is not moved on a failed Submit.** `OperationalRecords.tsx:438-441`. After a Submit with errors, focus
  stays on the button. The errors are associated and announced only when a field is focused. Common practice (GOV.UK)
  is to focus the first invalid field. Not required by §3.3.
- **L3 — the R651 register row still quotes the old banner in its built-state column.**
  `.agent/mock-departure-register.md:641`. The note at the end records the change, but the row's description still
  says "…records prepared for this walkthrough". Fix: update the quoted literal, or leave it if the register keeps
  built-state history by convention.
- **L4 — the evidence is not reproducible from the repo, and nothing pins the new banner literal.** The capture script
  `g3b-capture.mjs` lives in a session scratchpad, and the captures used Chrome request interception rather than §3.5's
  "fixture serve". This was a reasonable choice under the no-demo-DB instruction, but the method should be stated as a
  departure. The packet also does not record `tools/layout-evidence.mjs` as `not run` with its blocking precondition.
  No test asserts `DEMONSTRATION_BANNER`, so a regression to the old wording would pass. R2-G3b 16 only required
  updating pinning tests, and none existed. Fix (optional): add a one-line literal assertion in an existing shell test,
  and note the capture method in the packet.

## Checks I ran (head `61ccdc73c`)

- `vitest run src/work/__tests__/operationalEntryForm.test.tsx src/work/__tests__/operationalRecords.test.tsx`: **2
  files, 30 passed** (12 + 18). This went through the worktree's `node_modules` junction to `AssetOpsV1-plan2`, and
  config loading succeeded in this shell.
- `vitest run src/shell/__tests__/siteFoundationRevision.test.tsx` (the banner-adjacent shell test): **114 passed**.
- `tsc --noEmit -p .`: **exit 0**.
- `node tools/checks/frontend-hardwiring.mjs`: passed, totals `{"api":12,"href":24,"lit":70,"cmp":51,"code":3}`.
- `tools/checks/fuel_wording.py`: "clean (693 files scanned)".
- `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1`: **not run**. Without `-ExecutionPolicy`, which
  the dispatch forbids, PowerShell refuses with `UnauthorizedAccess`. The merge check-all must cover them.

## Not verified

- The full frontend suite and the production build. I did not run them (dispatch: targeted files only), and the
  packet does not claim them.
- The captures' `measurements.json` overflow numbers. I did not re-measure them; I inspected only the PNGs.
- **The real G3a route.** Everything here is against the §3.2 contract with typed or stubbed answers. The 201/200
  body shape (`schema_version`, `public_code`), the `detail.code` envelope, and the scope-refusal codes must be
  confirmed on the integrated build after G3a merges, as the packet says. A mismatch would show "could not be
  confirmed" for a record that was actually saved.

## Residual risk not named in the packet

- A Site read refusal (401/403/404 from `open_scope`) shows "Check the values and try again.", which misdirects the
  user. This is the sheet's "other 4xx" row, so it is compliant, but it is worth knowing for the walkthrough.
- After a success the old "Saved as…" line stays while the next entry is typed, until the next Submit replaces it.
  This is harmless, but a presenter may read it as belonging to the new entry.
