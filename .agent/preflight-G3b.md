# G3b pre-flight — operational records entry form (frontend)

Implementer (Claude), branch `task/OWN-G3b-operational-entry-form` from main `60858f6cc`. Read-only; no product code.
Spec: `.agent/build-sheet-OWN-GAPS-2026-11-08.md` (main worktree `AssetOpsV1-plan2`) Rev 1, §1, §3.1-§3.5 (frontend
parts), API contract §3.2. Mock: `frontend/mockups/v69/index.html:983-987`, manifest `screen-manifest.json:2205-2219`.

## Checked and matching (no question)

- `frontend/src/work/OperationalRecords.tsx` exists; the form is `ManualReadingPanel` (`:303-354`), the pair at
  `:413-416`, `RecordsUsedPanel` `:357-370`. `MANUAL_READING_DESCRIPTION` `:58`, `MANUAL_READING_REASON` `:59`,
  `UnavailableInline` import `:20` / use `:345`, By cell `row.actor_id` `:142-146`. `manualReadingSites(body)` `:290-297`
  (R362) exists as named.
- Mock order matches the spec layout: row 1 Site + Reading, row 2 Value + Taken at, footer with `Submit for review`
  (`index.html:986`); "How records are used" `:987`. Manifest id `oprecords` at `screen-manifest.json:2205`.
- `GlobalOperationalRow.actor_id` exists (`globalWorkClient.ts:170`); fuel kinds TANK_DIP/FUEL_DELIVERY are listed under
  "All" only (`globalWorkClient.ts:146-150`, `work/global_index.py:52`).
- Service codes and statuses the outcome table names exist: `WORK_WRITE_FORBIDDEN` 403, `WORK_EVENT_DUPLICATE_KEY` 409,
  `WORK_OCCURRED_AT_FUTURE`/`_TOO_OLD` 422 (`backend/assetops_backend/work/model.py:40-74`).
- The page has a reload: `useGlobalWorkPage(...).reload` (`globalWorkParts.tsx:367-371`).
- Guards: `frontend-hardwiring.mjs` `api` pattern applies to `.tsx` only (`:31-34`), so an `/api/sites` literal in
  `globalWorkClient.ts` is not counted; `fuel_wording.py` scans non-test `frontend/src/**/*.ts(x)` (`:114-117`).
- Register rows exist: R12 (`.agent/mock-departure-register.md:31`, D1, to be closed) and R362 (`:464`, D4, open).

## Questions (each with a proposed answer)

**Q1. Success body field name.** §3.3 outcome row says "Saved as {displayCode(code)}". The service's 201/200 lineage
body has no `code`; it is `{"schema_version": "operational-record-1", "id", "canonical_record_id", "public_code",
"state", "recorded_at"}` (`backend/assetops_backend/work/service.py:562-563`).
Proposed: read `public_code`; a 2xx whose body is not an object with `schema_version === "operational-record-1"` and a
string `public_code` is treated as "could not be confirmed" (the 5xx/network row, key kept).

**Q2. "It is listed above as Submitted" may be false after the re-read.** The list is a 5-row page
(`GLOBAL_WORK_PAGE_LIMIT = 5`, `globalWorkClient.ts:16`) over a 7-day UTC window (`defaultGlobalWorkWindow`, `:701-705`),
optionally with an explicit `known_at` cutoff (HISTORICAL) and a kind chip (`KIND_CHIPS`, `OperationalRecords.tsx:77-83`;
a TANK_DIP / FUEL_DELIVERY never appears under a kind chip). The form accepts entries up to 30 days back. So a saved
record can be off the first page, outside the window, after the cutoff, or filtered out — and `reload` on a later
page navigates to the first page (`globalWorkParts.tsx:369-370`).
Proposed (pick one): (a) keep the literal as specified (Architect accepts the imprecision for the demo beat, where the
dip is the newest record in the default window); or (b) second sentence becomes "It is listed above as Submitted when
its time falls in the shown window." Builder default if no ruling: (a).

**Q3. Form while the list is HISTORICAL (explicit `known_at`) or kind-filtered.** Should the form be enabled there?
Proposed: enabled everywhere `shown` is true (no extra rule); covered by the Q2 answer.

**Q4. Site options flicker during the re-read.** `reload` makes `read`/`body` null until the new read lands
(`globalWorkParts.tsx:351-353`), and the panel is fed `shown ? body : null` (`OperationalRecords.tsx:414`), so the Site
list falls to "No Site selected" and the button disables for the read's duration.
Proposed: the form keeps the selected Site code in its own state; while options are empty it shows the placeholder and
the button is disabled; when options return, the kept code is re-selected if present, else the first option. The
result line stays visible across the re-read (the panel is not unmounted).

**Q5. Client method shape and path.** §3.3 says "the same base path and fetch helper as the reads". The reads' base is
`/api/work` (`globalWorkClient.ts:13`, `createGlobalWorkClient(basePath)` `:326`) and the helper `readGlobalWork` is a
GET that collapses unknown codes to `WORK_STORE_UNAVAILABLE` (`:305-324`); the write path is
`/api/sites/{site_code}/work/operational-entries` (§3.2), which the `/api/work` base cannot produce.
Proposed: new constant `SITE_WORK_API_PATH = "/api/sites"`; `createGlobalWorkClient(basePath, sitesPath =
SITE_WORK_API_PATH)`; `submitOperationalEntry?(siteCode, body)` is **optional** on `GlobalWorkClient` (like the other
optional methods, `:259-267`), posting JSON with `fetch` (`method: "POST"`, `Content-Type: application/json`) and
`encodeURIComponent(siteCode)`; result union `{status:"saved", publicCode} | {status:"refused", httpStatus, code:
string | null} | {status:"unconfirmed"}` (network error, 5xx, or unreadable 2xx). A client without the method shows the
403 row ("Saving records is not switched on for this installation.").

**Q6. `crypto.randomUUID` needs a secure context.** It is undefined on plain `http://` other than localhost. If the
presenter ever opens the demo by LAN IP/hostname over http, the submit would throw.
Proposed: use `crypto.randomUUID` when present, else 16 bytes from `crypto.getRandomValues` (available in insecure
contexts) as 32 lowercase hex; same `oprec-entry-<32 hex>` format.

**Q7. Unit suffix and per-Reading placeholders are not in the MD list.** §3.3 adds a unit suffix L/L/kg/kWh beside
Value and changes the placeholder per Reading; the mock has one placeholder "e.g. 192 L" and no suffix
(`index.html:986`). MD-OWN-G3-1..4 do not name either.
Proposed: fold both into MD-OWN-G3-1 ("Fuel delivery option, its Ticket row, and the per-reading unit suffix and
placeholder"), or name a new MD-OWN-G3-5. Builder default: fold into MD-OWN-G3-1.

**Q8. Visible MOCK DEVIATION labels.** The page renders visible labels for registered departures (`MockDeviation`,
`globalWorkParts.tsx:103-109`; R362 inside the form at `OperationalRecords.tsx:308`). §1 asks for the MD-OWN-G3 label
"in the code comment and in the register" only. Also R362's register text describes the inert form's mock values and
"Event time" placeholder, which MD-OWN-G3-2 now supersedes in part.
Proposed: MD-OWN-G3-1..4 in code comments and the register only (no visible label; `MockDeviation`'s `category` type
also has no MD-OWN form); keep the visible `MOCK DEVIATION D4 (R362)` label (Site options still come from the response,
not the mock); R362 register row gets a note "Taken at superseded by MD-OWN-G3-2"; R12 status → closed by G3b.

**Q9. "How records are used second paragraph, an addition".** The panel already has two paragraphs
(`RECORDS_USED_FIRST_*`, `RECORDS_USED_SECOND`, `OperationalRecords.tsx:71-74`).
Proposed: the new sentence is a **third** `<p>` after the existing two; existing two unchanged.

**Q10. When client validation shows, and trimming.** Not specified.
Proposed: messages appear under their field after the first Submit attempt and then update live; nothing is sent while
any message shows. Value and Ticket are trimmed before validation and in the body. Client checks Value with the
server's regex `^\d{1,6}(\.\d{1,3})?$` (a 7-digit value gets the "0 or more, at most 3 decimals" message); Ticket is
checked only for non-empty (a malformed ticket reaches the server and gets "Check the values and try again.").
`taken_at_local` is the `datetime-local` value as-is (`YYYY-MM-DDTHH:MM`; with `step="60"` there are no seconds). After a
success the shown messages reset (cleared fields do not immediately show errors).

**Q11. Idempotency key timing and 4xx.** "Made when the form first becomes valid" vs observable behaviour; 4xx is not
listed for keep/replace.
Proposed: the key is created lazily at the first valid submit and held in state; cleared on any field edit and on
success; **kept** after network/5xx **and after a 4xx** (only an edit or a success replaces it). Observable behaviour
matches the spec's tests (kept after network error, replaced after edit or success).

**Q12. Fields while a save is in flight.** Spec disables only the button. If a field is edited mid-flight and the save
then succeeds, the success reset would clear that edit.
Proposed: fields stay enabled; an edit mid-flight clears the key (next submit gets a new one); on success, Value, Ticket
and Taken at are cleared regardless. Alternative: disable all fields in flight. Builder default: the first.

**Q13. "Taken at" initial value and the default Reading.** Mock shows a filled text value; spec gives none.
Proposed: empty on load and after success; Reading defaults to "Fuel tank dip" (mock's first option); Site defaults to
the first option (spec).

**Q14. Two-line fuel success text, and which statuses map to "other 4xx".**
Proposed: one `role="status"` region (with `aria-live="polite"`) under the footer holding one or two `<p>`; the fuel
second line shows for TANK_DIP and FUEL_DELIVERY only. "Other 4xx" covers 401 UNAUTHENTICATED, 403 other than
`WORK_WRITE_FORBIDDEN` (e.g. `SITE_SCOPE_FORBIDDEN`), 404 `SITE_NOT_FOUND`, 422 `OPREC_ENTRY_INVALID`,
`OPREC_ENTRY_TICKET_REQUIRED`, `WORK_RECORD_QUANTITY_INVALID`. The duplicate-key row matches on the code regardless of
status (409 today). 503 `WORK_STORE_UNAVAILABLE` takes the 5xx row.

**Q15. "Entered by site admin" scope.** Other screens render the actor id: `WorkRequestHistory.tsx:256`
(`actor_kind · actor_id`) and `SiteActionVerification.tsx:949` (`<Ref value={record.actor_id} />`, the Kisiwa fuel
action verification records a G1/screen dip could appear in).
Proposed: change only the Operational records By column, as §3.3 says; other screens unchanged (follow-up if wanted).
