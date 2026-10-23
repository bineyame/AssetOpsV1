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
