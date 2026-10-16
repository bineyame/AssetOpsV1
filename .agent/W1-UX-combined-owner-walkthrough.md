# W1 combined owner walkthrough (draft written at W1-UX-05 closeout, 2026-10-17)

Source: umbrella `tasks/W1-UX-mockup-fidelity.md` "Combined walkthrough coverage and authorship". Owner: whichever UX slice merges last. UX-05 wrote this draft; if UX-02, 03 or 04 merges later, that slice refreshes its rows and captures. The coordinator checks all 26 rows before scheduling the owner session.

## How to run it

- Serve one tool at a time; never serve two at once.
- Substitute only the IDs and selectors that the tool's `links`/`serve` output prints.
- Compare the app with `frontend/mockups/v69/index.html#/<id>` at 1440 and 390 px. Check keyboard access, the exact links and a reload.
- Drop each guarded case afterwards.
- Do not compare numbers across cases.

All data is authored or generated test data, not field equipment readings. Label it that way in the guide and in every screenshot.

### Prerequisites

1. Postgres must be running on 127.0.0.1:55432 (`ASSETOPS_PG_PASSWORD`).
2. Copy the Kobo site file into this worktree: `var/sites/kobo-001.yaml`, taken from the main checkout (`var/` is ignored).
3. Run `python tools/s4_finding_cases.py run` once. It produces the `assetops_s4cases` database and manifest that `v01a`, `v01b` and the S4 tools copy.
4. `s2_demo_walkthrough.py` has `run|serve|setup`, with no `prepare` mode.
   - Use `run`, then `serve`.
   - `run` recreates the fixed database `assetops_s2demo`; drop it afterwards, because the tool has no drop mode.
5. `s5_overview_walkthrough.py prepare` needs `var/sites/kobo-001.yaml`. Run `tick` within 5 minutes before viewing.
6. **Frontend for each tool:** from `frontend/`, set `$env:ASSETOPS_API_PORT="<api>"` and run `npm.cmd run dev -- --port <web> --strictPort`.
   - Vite listens on `localhost`, not `127.0.0.1`.
   - Open the printed path on `http://localhost:<web>`.
7. **Captures:** `node tools/w1-ux-05-evidence.mjs <out> <mock-id>[:<case>]=<url> ...` (or the UX-01, 02, 03 or 04 sibling script for that slice's cards).

## UX-05 rows: run, captured and dropped at `af9b6406`

### Foundation, Readiness and SLD (`v01a_foundation_walkthrough.py`)

**Commands:**

```
python tools/v01a_foundation_walkthrough.py --db assetops_v01awalk_w1ux05 --empty-db assetops_v01aempty_w1ux05 --work-name v01a-w1ux05 prepare|links|serve|drop
```

- API on 8860, web on 5360.
- The database is a copy of `assetops_s4cases`: authored test configuration of KOBO-001, imported and published Foundation versions.

| Screen | Tool-printed URL (`localhost:5360`) | State shown | 1440/390 |
| --- | --- | --- | --- |
| `foundation` | `/sites/KOBO-001/foundation` | in effect now, configured settings, one not recorded | captured |
| `foundation` | `/sites/KOBO-001/foundation?at=2026-10-22T00:00:00Z` | scheduled, not in effect | captured |
| `foundation` | `/sites/KOBO-001/foundation?at=2026-09-01T00:00:00Z` | no stored version (missing), state line only | **not run**: the evidence script captures only pages that have a card; this state has none by design |
| `readiness` | `/sites/KOBO-001/foundation/readiness` | set up to report (neutral), commissioning not known, stale gateway contact below | captured |
| `readiness` | `/sites/KOBO-001/foundation/readiness?at=2026-09-30T00:00:00Z` | imported period (limited) | captured |
| `sld` | `/sites/KOBO-001/foundation/sld` | linked/unlinked devices, reporting not known, gap tags | captured |
| `sld` | `/sites/KOBO-001/foundation/sld?at=2026-10-22T00:00:00Z&component=battery` | part selected; kept across reload | captured |

### Health and battery (`s701_health_walkthrough.py`)

**Commands:**

```
python tools/s701_health_walkthrough.py --db assetops_s701_owner_w1ux05 --work var/s701_owner_w1ux05 prepare|serve|deliver|attest|drop
```

- API on 8947, web on 5447.
- Run `deliver` right before viewing; `attest` returned ok.
- The data is a registered test case set: eight generated gateways on KOBO-001, and KOBO-002 with no enabled gateway.

| Screen | Tool-printed URL (`localhost:5447`) | State shown | 1440/390 |
| --- | --- | --- | --- |
| `health` | `/sites/KOBO-001/health` | current contact, old facts, never received, unknown age | captured |
| `health` | `/sites/KOBO-002/health` | no source (no zero bars) | captured |
| `health` | `/sites/KOBO-001/health?gateway=<id printed by serve>` | selected gateway, exact link and reload | jsdom only; served capture **not run** |
| `asset` | `/sites/KOBO-001/assets/<asset id printed by serve>` (this run: `f3d905c9-7b96-4969-98c3-f2c5f3e8d9de`) | condition cannot yet be judged, missing inputs | captured |
| `asset` | `/sites/KOBO-002/assets/00000000-0000-4000-8000-000000000000` | refusal: asset outside the basis | **not run** (refusal panel has no card) |

**Captures:** screenshots are in `%TEMP%\w1ux05-shots` (not committed). The 390 px overflow claim is visual only; see `.agent/W1-UX-05-review-packet.md` "Served evidence".

## Rows owned by other UX slices: not run by UX-05

For each row below, the owning slice or the coordinator fills in the tool-printed URL, the states shown and the captures after that slice merges. The blocking precondition is the same for every row: that slice's migration is not on this branch, and serving it here would capture pre-migration screens.

| Screen | Tool (modes) | Route template | State to show | Owner |
| --- | --- | --- | --- | --- |
| `sites` | `v01a_foundation_walkthrough.py` P/S/links | `/sites` | registered/limited | UX-02 |
| `mini` | `s5_overview_walkthrough.py` P/S; `s502_overview_finding_list_walkthrough.py` P/S/late/settle/gate/drop | `/sites/{site}` | supported/pending, late, proved-zero | UX-02 (card part: UX-01) |
| `evidence` | `s2_demo_walkthrough.py` run/serve; `s405_provenance_walkthrough.py` P/S/links | `/sites/{site}/evidence` | accepted/rejected; labelled source/unknown | UX-03 (card part: UX-01) |
| `evidence-analysis` | `s302_claim_limit_walkthrough.py` P/S/T late | `/sites/{site}/evidence?view=analysis&day={day}&revision={revision}` | supported/limited/stale | UX-03 |
| `dispatch` | `s3_dispatch_walkthrough.py` P/S | `/sites/{site}/performance/dispatch` | supported/limited | UX-03 |
| `analysis` | `s3_dispatch_walkthrough.py` P/S | `...dispatch?day={day}&revision={revision}&view=analysis` | supported/limited | UX-03 |
| `finding` | `s4_finding_walkthrough.py` P/S | `/sites/{site}/findings/{finding}` | selected/limited | UX-02 |
| `finding-evidence` | `s405_provenance_walkthrough.py` P/S/links | `/sites/{site}/findings/{finding}/evidence?revision_id={revision}` | labelled source/unknown | UX-02 |
| `finding-history` | `s4_finding_walkthrough.py` P/S | `/sites/{site}/findings/{finding}/history?revision_id={revision}` | historical | UX-02 |
| `sitefindings` | `s404_finding_index_walkthrough.py` P/S/T late; `s502` (above) | `/sites/{site}/findings?from={from}&to={to}` | supported/proved-zero/stale | UX-02 |
| `financials` | `s402b_fuel_cost_walkthrough.py` P/S; `s405` P/S/links | `/sites/{site}/financials?finding_id={finding}&revision_id={revision}` | priced/withheld/unknown source | UX-02 |
| `assumptions` | `s402a_assumptions_walkthrough.py` P/S; S4-08 guarded case | `/sites/{site}/financials/assumptions?recorded_at={cutoff}` | effective/historical; missing/withheld/closed source | UX-02 |
| `recommendation` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/findings/{finding}/recommendation?revision_id={revision}` | proposed/limited | UX-04 |
| `changes` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/foundation/changes/{change}` | applied/unknown effect | UX-04 |
| `action-overview` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/actions/{action}` | recorded/pending | UX-04 (card part: UX-01) |
| `action-execution` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/actions/{action}/execution` | applied/failed | UX-04 |
| `action-history` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/actions/{action}/history?event_id={event}` | historical | UX-04 |
| `action-plan` | `s602b_verification_walkthrough.py` P/S/capture | `/sites/{site}/actions/{action}/plan?plan_revision_id={plan}` | planned/limited | UX-04 |
| `action-evidence` | `s602b_verification_walkthrough.py` P/S/capture | `...evidence?plan_revision_id={plan}&outcome_id={outcome}` | covered/missing | UX-04 |
| `verification` | `s602b_verification_walkthrough.py` P/S/capture | `...verification?plan_revision_id={plan}&outcome_id={outcome}` | sampled pass/guardrail fail/withdrawn | UX-04 |
| `sitework` | `s603_site_work_walkthrough.py` P/S/attest | `/sites/{site}/work?from={from}&to={to}` | active/proved-zero | UX-04 |

**Gate:** the walkthrough is not ready to schedule until every row above has a tool-printed URL, its states and its 1440/390 captures, or an explicit **not run** with its blocking precondition.
