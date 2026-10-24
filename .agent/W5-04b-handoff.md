# W5-04b handoff: V3a and V3b (EV Incidents and Maintenance tabs, captures, registry)

Branch `task/W5-04b-ev-cases`, from main `ad7b82f9`. Main was merged at `84e9a233` (`f5f7f70b`, rulings 67-68).
The review is not done. No questions file was written: I found no ruling that contradicts merged code.
Judgment calls are listed below for the reviewer to confirm.

## Commits

| Commit | Unit | Content |
| --- | --- | --- |
| `2ab74ff9` | V3a | `siteWorkCases.tsx`: an EV_CHARGING Site gets the domain case presentation (details below). `SiteAnalyticsFrames.tsx`: mounts the page-local `DomainWorkWindow` (`legacyCold=false`) and passes `windowForm=false` on EV, together (ruling 57). `panelStructure.ts`: adds `SCREEN_LEADING['ev-work-incidents'/'ev-work-maintenance'] = [data-domain-work-currentness]` (ruling 17). `w1f4-changes-work.css`: a copy of the cold K3 cell rules, scoped to `.work-cases[data-domain-cases="EV_CHARGING"]`. |
| `46bbb279`, `66ba8250` | V3a | New `evWorkCases.test.tsx` (23 tests). EV case fixtures added to `evWorkFixtures.ts`. Cold and mini-grid isolation assertions added to `coldWorkCases.test.tsx`. The V2a ruling-57 interim assertion in `evWorkActions.test.tsx` now expects the mounted Window. |
| `b7be1218` | V3b | Walkthrough `worstcase` mode adds `_worstcase_cases`: 5 INC and 5 WR (each WR with a record), 160 code points in title, narrative, activity and outcome, posted through the W4 case commands. It refuses unless W lists all five of each. Adds `W504_API_PORT_BASE` (default 8980, so behaviour is unchanged). The producer test is extended. |
| `81fcbc5a`, `5c9551a4`, `ae58f4d1` | V3b | `tools/w504-ev-work-evidence.mjs` gains a `W504B_EVIDENCE=cases` mode, which only captures. It also gets robustness fixes: the cold UUID-scroller rule, an about:blank step between captures with its width check, and a bounded evaluate retry. |
| `9aa4ef25`, `cda90a33` | V3b | Promotes the ledger and panel-contract rows for `ev-work`, `ev-work-incidents` and `ev-work-maintenance`: coverage partial, task W5-04, `follow_on` null, `to_candidate` null, `unresolved_panels` [], and the build-spec panel literals with `claim_limit`. Remaining work and acceptance are preserved, and the owner tier stays pending. `data_owner` uses the ruling-68 literal. |
| `ff302700` | V3b | `.agent/W5-04b-evidence/`: 32 PNGs, `w504b-cases-measurements.json`, the run log, the prepare log and the walkthrough manifest. |

## V3a behaviour (EV, `/sites/{site}/work/incidents|maintenance`)

- **Layout.** v69 order: subtabs, then the Window (R112, labelled `From (UTC)` / `To (UTC, exclusive)` per R77), then the strip, the notice and the panel. Exactly one form.
- **Strip and Manage link.**
  - The strip reads `Scoped to EV · n incidents|maintenance` (R111, using the mock noun).
  - The strip detail is `Same records and states as the global {kind} list`.
  - `Manage in {kind} →` goes to the mounted W6 root and keeps the window and cutoff.
- **Notices.**
  - R80/R104: the currentness notice sits between the strip and the panel. It comes from the W4 `status` and uses the cold literals and tones.
  - R03: the context notice is the first sentence only.
- **Panel.** The panel-head subtitle is kept. R105 (basis disclosure) and R106 (pager) apply, and complete zero shows the exact mock empty card.
- **Refusals.** The W4 `Refused` state is unchanged, with no Retry and no zero.
- **Cells.**
  - Incident title: the INC code is plain (R85).
  - Window: `siteWindowText` in the stored Site zone (R-10).
  - Linked findings: plain `Finding {id8}`, with a `Finding version` disclosure holding the revision and the R75 sentence.
  - WR title: links to the W6 Overview with `site_id` and the explicit cutoff (R83).
  - Asset: `asset_label` unchanged, else `No asset linked` (ruling 13). No cold GENERATOR mapping and no asset-ID fact.
  - Activity: the state chip plus an `Activity recorded` disclosure (R81).
  - Outcome: `Unverified` plus an `Outcome note` disclosure (R82).
  - Next evidence: the selected copy, else `No next evidence recorded` (R84).
  - Long text: two-line previews with `Read full text` (R107).
- **R113 plain links.** Inside `UTC and IDs`, a W4 `DOMAIN_ACTION` link is plain text (`data-work-action-plain`) while `EV_ACTION_LINK_LIVE` is false. This avoids a dead link to the W1 presenter before V4a.
- **Naming.** EV gets only `data-domain-work-*` / `domain-work-*` names. Cold keeps every K3 cold name byte-for-byte and adds only `data-domain-cases="COLDCHAIN"` (ruling 18). Mini-grid gets neither. The CSS is EV-scoped, so the cold computed styles are untouched and no cold recapture was needed.
- **Non-vacuity proofs.** Each mutation was run on committed code, then reverted with `git checkout`.

  | Mutation | Failed tests |
  | --- | --- |
  | EV removed from domain types | 13 |
  | `SCREEN_LEADING` entry removed | 4 |
  | W4 form left on for EV | 2 |
  | EV given cold names | 11 |
  | R113 plain-link switch off | 1 |
  | Cold asset mapping applied to EV | 1 (the test was added after this proof first passed vacuously) |

## V3b captures: 472 PASS, 0 FAIL, 12 INFO

Run with `W504B_EVIDENCE=cases node tools/w504-ev-work-evidence.mjs <manifest> .agent/W5-04b-evidence`. Heights are main/strip/panel in px:

| State | Incidents 1440 | Incidents 390 | Maintenance 1440 | Maintenance 390 |
| --- | --- | --- | --- | --- |
| submitted | 595/39/212 | 746/84/201 | 579/39/195 | 762/84/216 |
| historical | 656/39/212 | 806/84/201 | 639/39/195 | 822/84/216 |
| zero (cap 460/560) | 721/39/337 | 889/84/344 | 701/39/317 | 869/84/324 |
| forbidden-403 | 529/39/145 | 698/84/153 | 529/39/145 | 698/84/153 |
| worst (5 rows) | 886/39/502 | 990/84/445 | 886/39/502 | 990/84/445 |
| worst-one-open (390 cap 680) | 939/39/556 | 1071/84/526 | 956/39/572 | 1102/84/557 |
| worst-all-open (exempt) | 2073/-/1690 | 2218/-/1672 | 2291/-/1907 | 2354/-/1808 |

- Every closed state is inside its cap: page 1600/2000, strip 100/150, populated panel 650/650, notice 110/160. There was no cap miss; I flagged none in advance and none occurred.
- The expanded `submitted-ids-open` and `worst-all-open` states are exempt. Their containment, one-line UUID scrollers and full 160-code-point text still pass.
- At 390 there is no document overflow, the first column is sticky and the table scrolls inside its panel.
- **Unavailable captures, which remain pure vectors in `evWorkCases.test.tsx`:**
  - pending, stale and unknown (ruling 54; the manifest records them as unavailable);
  - an in-panel W4 503 with a healthy Site read, because the walkthrough stops the whole API (the same limitation as V2b).
- **Producer.** `prepare` took 3m50 with positive, zero and worstcase ready. `serve` ran on 8991/8992/8993/8996/8997 and `attest` returned 403 `SITE_SCOPE_FORBIDDEN` and stopped 8997.
  - The submitted WR is OPEN and has its record, so the chip reads `Open` and the asset shows `c1 · EV_CONNECTOR`. That is the real W4 state; `attest` does not ASSIGN or COMPLETE the request.

## Checks (final revision `cda90a33`)

- `tsc --noEmit`: clean. `vite build`: green.
- Full vitest (`--minWorkers=1 --maxWorkers=2`, on `ff302700`): 126 files, 2930 passed, 505 s. Later commits touched only the tool, the ledger and merged `.agent` documents.
- Targeted vitest: 9 adjacent files, 230 passed.
- Focused Postgres: `test_w504_ev_work_producer_postgres.py` and `test_w504_ev_work_cases.py`.
  - `-n 4`, private base `assetops_w504b_test`, with this worktree's backend, gateway, simulator, contracts, host and tools on `PYTHONPATH`.
  - Result: 22 passed. JUnit: tests=22, skipped=0, failures=0, errors=0. Wall time 123 s.
- `tools/check-all.ps1`: All 11 guards passed. The ledger and dependency-registry checkers pass.

## Cleanup

- Vite PIDs 21424, 15304, 18984 and 20148 were stopped by PID after a command-line check. PID 6996 had already exited silently and was restarted as 21424.
- Walkthrough `drop` dropped `w504a_{positive,zero,worstcase,unknown}_v3b_test` and removed the work folder. I also dropped `assetops_w504b_test`.
- Ports 5491-5496 and 8991-8996 are closed. No owned process remains.

## Judgment calls (please confirm)

1. **Walkthrough edited (outside the V3b file list).** The five-row case worst-case state needs data, and pre-flight 23 keeps the `.mjs` capture-only. I followed the V2b re-review M1 precedent. The port-base env var is additive.
2. **`evWorkActions.test.tsx` (outside the V3a list).** Ruling 57 made V2a's interim assertion false, so I made a 4-line flip. W5-04c V4a now also owns this file (ruling 67), which is a merge-conflict risk.
3. **Ports.** The tools derive the Vite port as API port - 3500, so 899x API gives 549x Vite, not 548x.
4. **Case refusal cap.** The forbidden-403 case panel is measured against the populated-case cap of 650/650, following the cold K3b precedent. No cap is named for it explicitly.
5. **Strip noun.** It stays as the mock's `1 incidents` / `1 maintenance`. R79's singular form covers `ev-work` Actions only.
6. **R75 sentence.** It also appears in the Incident `Finding version` disclosure, as in the EV Actions Source cell.
7. **Ledger fields.** `interaction` and `unknown_or_empty` were left untouched (cold judgment 6). `proposed_fidelity_tier` is set to `Real with honest gaps`, following the cold precedent.
8. **For V4a.** When `EV_ACTION_LINK_LIVE` flips, the case-row domain Action link in `UTC and IDs` will render the W4 server href, `/sites/{site}/actions/{id}/verification`, without `from`/`to`. Ruling 67 covers only the Actions list link.

## Shared plumbing touched

Yes, limited:

- `SiteAnalyticsFrames.tsx`, the `SiteWorkCasesFrame` region only (Window condition and `windowForm`).
- `siteWorkCases.tsx`, generalised from cold-only to the domain cells.
- `panelStructure.ts`, two leading entries.
- `w1f4-changes-work.css`, an EV-scoped block added.
- `tools/w504_ev_work_walkthrough.py`, a mode extension plus the port env var.

There are no backend product, `App.tsx`, route or register edits; R74-R85 and R104-R113 already cover V3.
