# W5-02b questions (K2a/K2b capture producer, tools/w502_cold_work_walkthrough.py)

Points where the ruling is ambiguous or contradicts merged code. The producer runs with the noted provisional
reading; none changes a product status.

1. **GEN-CR-01 asset code.** "Producer and clocks" names the Incident/WR asset as the returned Foundation backup
   generator `GEN-CR-01` ID. The merged COLD-LAB-001 Foundation (`backend/tests/fixtures/w2/cold-lab-001.yaml`)
   registers the backup generator as asset code `generator-1`; no `GEN-CR-01` exists anywhere in backend/config.
   The producer uses the returned `generator-1` asset ID (never a free code) and records the code in the manifest.
   Ruling needed: accept `generator-1`, or is a display-label mapping expected in UI copy?

2. **403 principal mechanism.** P-G-5 asks for a scoped operator principal and a separate ungranted principal.
   `main.create_app` builds the domain-work `WorkGate` with the default `development_access` (no read-access seam),
   and s603's mechanism is server configuration, not a request header. The tool therefore runs the product host app
   (`host/lab_app.py`) through a tool-local uvicorn entry that puts the same `build_domain_work_router` with a
   `WorkGate(access=<server-configured Site grant>)` ahead of the product domain-work routes; the 403 process holds
   a principal with no Site grant and the real gate returns `SITE_SCOPE_FORBIDDEN`. Only domain-work routes are
   scoped; every other route keeps `development_access` in all processes. No shared plumbing was edited. Confirm
   this is acceptable, or whether main.py should gain an access seam for domain-work reads (shared plumbing).

3. **Selected Finding per mode.** Positive/worstcase/unknown pin the selected `COLD_START_FAILURE` Finding (matches
   'Witness automatic-start test' and the run-5 UNKNOWN test); pending/stale pin the selected `COLD_EXCURSION`
   Finding, as `test_w502_domain_work_links_postgres.py` does. The fixture title is the same in every mode.

4. **Incident links.** The spec says the WR pins the returned INC, Finding and explicit domain Action case link; it
   gives no Finding link for the INC. The producer gives the INC no `finding_links` (both cases get the explicit
   domain Action case link). `occurred_at` for INC/WR/record uses the W4 test helper defaults (DB-real time minus
   1h / 20 min), not the shifted source window.

5. **Attested `raised_at`.** The fixture and the five worst-case Actions use `raised_at` strictly between K0 and the
   DB read before the first POST, so the Action follows its evidence; K1..K3 are the returned recorded_at values.
   Worst-case: the five long Actions are raised after the fixture, so page one holds the five long rows and the
   fixture Action is on the Next page (total 6, limit 5).

## Frontend builder (K2a/K2b list, routes and domain Action shell)

Provisional reading noted for each; nothing here invents a product state.

6. **Topbar date-range slot, Site switch and range picker do not exist.** P-K2a-39 asks for "a cold range control in
   the existing topbar date-range slot" and U2 asks tests to assert the "topbar Site switch, range picker and
   provenance tag from the shell remain visible". Merged `OperatorShellLayout.tsx` renders only the rail, brand and
   `<Outlet/>`; there is no topbar, Site switch or range picker anywhere in `frontend/src` (the v6.9 `topbar` with
   `siteSwitch`/`rangePicker` was never built). The provenance tag exists only in `SitePageHeader` (Site pages, not the
   mock `cold-action` page, whose mock heading has no prov tag). Provisional: no range control was built and no topbar
   assertion was written; the cold Actions window comes from `from,to,known_at` in the URL with the W4 seven-day
   default, and every cold Work href preserves it. Ruling needed: where the cold range control goes (a new shell
   topbar is shared plumbing and a mock element of its own), and what the domain Action shell should assert instead.

7. **Cold Site subtitle field.** P-K2a-40: "stored `display_name`/Site subtitle … when subtitle is null use
   `Cold-room operations at this site.`". `SiteSummary`/`SiteDetailReadModel` have no subtitle field (Foundation has
   only `summary`, a configuration-document summary). Provisional: the fallback is always shown on COLDCHAIN Work
   pages (all three, since they share `ChangesWorkPageHeader`); `foundation.summary` is not used. Confirm.

8. **W1 ID on a cold Site's `/verification`.** The older Shared-UI text says "a W1 ID on `/verification` shows the W1
   verification presenter"; the later P-K2a-34 and U1 say a domain 404 "never falls back to W1". On a cold Site the
   W1 Action page's own Verification tab therefore leads to `Action was not found at this site.` Provisional: the
   later ruling (no fallback) is implemented; a bare/legacy W1 address probes the domain read first, and a validated
   domain Action redirects to `/verification`, anything else (404, refusal) keeps the W1 presenter. Ruling needed on
   the W1 Verification tab of a W1 Action on a cold Site, and whether a refused probe on a bare address should keep W1.

9. **Detail refusal shape.** P-K2a-33 says the refused detail is `{detail:{code,message},intent:null,results:null}`;
   merged `domain_work_api.py` returns `{detail:{code,message,intent:null,results:null}}` (the pair inside
   `detail`). Provisional: the client accepts either placement and treats a non-null `intent`/`results` in a refusal
   as an unexpected shape; tests pin the merged shape. Ruling: which shape is authoritative.

10. **Placeholder panel heading and notice.** U2 says a 200 shows `Action details are being prepared.` "inside the mock
    panel" and "mock panel/notice structure", while P-K2a-45 says the `cold-action` panel headings wait for K4a.
    Provisional: one untitled `section.panel` holding the sentence, then the mock blue notice `Completed inspection
    does not establish successful service restoration.` (only on a loaded read). Confirm, or name the heading.

11. **Unknown-count literal on the cold strip.** U3: "Loading/refusal strip uses an unknown count and never renders mock
    zero" with no literal. Provisional: `Scoped to {short} · — actions`, the em dash matching the subtab's
    `Actions (—)`. Ruling: confirm or supply the literal.

12. **Revision disclosure summary.** P-K2a-37 puts the selected Finding revision "in a disclosure" without a summary
    literal. Provisional: summary `Finding version` (the existing cold-view label for `finding_revision_id`), inline
    variant, body is the revision UUID. The Action status line shows the disclosure only when the selected intent
    basis carries `finding_revision_id` (the detail wire has no other labelled revision field). Confirm.

13. **Two-line preview and `overflow`.** P-K2a-44 says the sticky-first-column styling uses no `overflow:hidden|clip`;
    a CSS two-line preview (`-webkit-line-clamp`) needs `overflow:hidden` on the preview element. Provisional: the
    scroller and its ancestors have no hidden/clip; the preview reuses the existing W4 `.work-cases-clamp` class
    (`w4-work-cases.css`), so no new hidden/clip rule was written. `Disclosure` renders
    `<details class="disclosure"><summary class="disclosure__summary">Read full text</summary><div
    class="disclosure__body">…</div></details>`. Confirm both.

14. **Vocabulary scan hit on the ruled criterion summary.** The T028 product-vocabulary scan flags "runs" in the
    server's ruled `Start requested → generator runs → power → cooling`. No `cold-work` screen gloss is registered.
    Provisional: `coldWorkActions.test.tsx` sets aside exactly that literal; no gloss was added to the shared
    vocabulary registry. Ruling: add a `cold-work` screen gloss (registry owner) or keep the scoped exception.

15. **Currentness notice and the panel-structure guard.** The ruled notice sits between the strip and panel 1; the
    `expectV69Panels` leading-element guard admits only listed leading patterns, and `.notice` is not one. Provisional:
    `expectV69Panels('cold-work')` is asserted on CURRENT (no notice), complete-zero and refused states; non-current
    states assert the notice text and its position directly. Ruling: whether `[data-cold-work-currentness]` should be
    admitted as a leading pattern in `test/panelStructure.ts`.

16. **Currentness notice tone and fold expander after opening.** Not ruled. Provisional: blue info notice for
    HISTORICAL/UNKNOWN and amber for PENDING_RECOMPUTE/STALE_SOURCE (the W4 strip tones); after `Show all N Actions`
    is clicked the expander is removed (the W1 `Show the first 4` toggle is a removed helper string). Confirm.

## Capture (K2b browser evidence)

17. **503 capture mechanism shows Site unavailable, not the cold refusal.** P-G-5 says "503 from a separate API
    process with an invalid private DB URL". On the merged base that process also fails the Site read, so the page
    renders `Site unavailable` and the cold `Cold work unavailable` + `WORK_STORE_UNAVAILABLE` + Retry panel never
    mounts (evidence F5, `.agent/W5-02b-evidence/README.md`). The cold 503 panel is proven only in jsdom
    (`coldWorkActions.test.tsx`). Options: (a) accept the Site-level 503 capture plus the component test; (b) let the
    tool-local `serve_entry.py` give only the domain-work router the invalid DB URL while the Site read stays
    healthy. Not decided; the browser capture of the cold 503 panel is recorded as unproven.
