# Browser audit

Script: `tools/audit.mjs` (Playwright-core driving headless Chromium 1140 over `file://…/index.html`). Host wrapper: `tools/run-audit.sh` (sets the library and font paths for this server). Raw results: `tools/audit-results.json`. Run date: 16 Nov 2026, after the final build.

On another machine: `CHROME=/path/to/chrome PW=/path/to/node_modules/playwright-core node tools/audit.mjs --shots` from this folder.

## Summary

| Check | Scope | Result |
|---|---|---|
| Route renders (h1 present, no console error, no page error) | all 146 routes (110 v7.0 + 36 added) | **146 / 146 pass** |
| Every `#/` link on the page resolves to a screen id | all 146 routes | **146 / 146 pass** (0 broken links) |
| No horizontal page overflow at 390 × 844 (tables may scroll inside their container) | all 146 routes | **146 / 146 pass** |
| No internal vocabulary or codes on client-facing screens (option ids, Finding, thread, CONTRIBUTIONS, overlap group, enum names, >=, LOI, asset tags, undefined/NaN) | 36 added routes | **36 / 36 pass** |
| Role toggle (CEO/COO/CFO/CCO) changes order and question, never the numbers; focus returns to the pressed button | decision home | **4 / 4 pass** |
| Evidence drawer: opens from a money figure by keyboard, focus moves inside, Tab and Shift+Tab stay inside (30 presses), Escape closes, focus returns to the figure, provenance label and fixture path shown | decision home | **7 / 7 pass** |
| Focus visible (computed outline after keyboard focus) | menu link, role chip, money figure, operator select, table toggle, context tab | **6 / 6 pass** |
| Contrast spot checks (WCAG AA 4.5:1) | 13 text styles on the decision home | **13 / 13 pass** |
| Budget switch $5,000 → $6,500 (Lakeside) | plan-lakeside | **5 / 5 pass** (claim path at $5,000; spend $3,880 of $5,000; buy-now recommended at $6,500; spend $6,430 of $6,500; total +$3,546) |
| Pilot form shows only an example toast | pilot-lakeside | **pass** (“Example only: no request was sent.”) |

## Issues found during the audit and fixed

| # | Issue | Where | Fix |
|---|---|---|---|
| F1 | Page error: verification plan missing for Harvest and Metro (manifest has one only for Kobo) | `verify-harvest`, `verify-metro` | Template reads the plan defensively; proposed tests labelled "Proposed in this mock-up" |
| F2 | Horizontal page overflow at 390 px (393–422 px) on 9 comparators | `choice-*` | Visually hidden "show source records" text was positioned outside the table's scroll container; money buttons now `position: relative` |
| F3 | Option table at 390 px produced 300 px tall rows (squeezed columns) | `choice-*` | Below 760 px the option table becomes stacked cards with a label per value (no sideways scroll) |
| F4 | Manifest text with codes and symbols on screen (`>=`, LOI, INV-MT-02, P1, MG-L5, "Candidate", "Necessary", `x`) | home, comparators, bridge, site economics, proof | Plain-language rewrites (CHANGE-REGISTER §5.7); vocabulary scan extended to catch them |
| F5 | The conditional inverter option appeared twice (conditional list and not-chosen list) | home | Conditional options listed once |
| F6 | "Not modelled · no money effect modelled" repeated on repair rows | home, comparators | Repairs and remedies read "No saving claimed: a cost to keep service or evidence"; evidence column "Quoted cost" |
| F7 | Crew list showed four one-visit jobs against "3 of 3" visits | home (COO panel) | Huller and meter check read "Same visit as the inverter" |
| F8 | Units: "38 C", "0.5C" in contract terms | rights panels | °C and plain wording |

## Open issues (not fixed; for owner review)

| # | Issue | Severity |
|---|---|---|
| O1 | Context tabs at 390 px scroll sideways without a visible fade or arrow (same as v7.0 tabs) | Low |
| O2 | Left menu hidden below 760 px (v7.0 behaviour). Decision screens have in-page tabs and the operator switch; v7.0 screens are reached on a phone only through the review bar's screen selector | Medium |
| O3 | Bar charts stretch with the container (`preserveAspectRatio="none"`), so the hatch pattern on modelled steps is wider on wide screens; meaning is unchanged and every step also has a text label | Low |
| O4 | Screen-reader behaviour checked structurally only (roles, labels, `aria-current`, `aria-pressed`, hidden-text on money buttons); not tested with NVDA/VoiceOver | Medium |
| O5 | Screenshots use the fonts available on this server (system-ui fallback); type may look slightly different on the owner's machine | Low |
| O6 | Contrast checked on 13 styles of the decision home, not every element on every page; the role note is closest to the limit (4.69:1) | Low |
| O7 | No dark theme (none in v7.0 either) | Low |

## Contrast spot checks

| Style | Ratio | Font size |
|---|---|---|
| `.d-note` | 5.03:1 | 11px |
| `.d-cellnote` | 5.03:1 | 10px |
| `.d-rank small` | 5.03:1 | 11px |
| `.badge.green` | 5.67:1 | 10px |
| `.badge.amber` | 5.3:1 | 10px |
| `.badge.red` | 5.8:1 | 10px |
| `.badge.blue` | 5.83:1 | 10px |
| `.d-legal` | 8.18:1 | 11px |
| `.eyebrow` | 6.1:1 | 9px |
| `.d-focustag` | 6.7:1 | 10px |
| `.d-rolenote` | 4.69:1 | 11px |
| `.tabs a` | 6.25:1 | 12px |
| `.d-question p` | 15.53:1 | 18px |

## Focus checks

| Control | Focused element | Outline |
|---|---|---|
| `.rail a` | A | solid 3px |
| `.d-roles .chip` | BUTTON | solid 3px |
| `.d-money` | BUTTON | solid 3px |
| `#op-switch` | SELECT | solid 3px |
| `.d-table summary` | SUMMARY | auto 1px |
| `.tabs a` | A | solid 3px |

## Route results

| Route | Status | Renders | Broken links |
|---|---|---|---|
| `decide-lakeside` | Added | yes | 0 |
| `bridge-lakeside` | Added | yes | 0 |
| `decide-harvest` | Added | yes | 0 |
| `bridge-harvest` | Added | yes | 0 |
| `decide-metro` | Added | yes | 0 |
| `bridge-metro` | Added | yes | 0 |
| `econ-kobo` | Added | yes | 0 |
| `econ-kisiwa` | Added | yes | 0 |
| `econ-mto` | Added | yes | 0 |
| `econ-mwea` | Added | yes | 0 |
| `econ-thika` | Added | yes | 0 |
| `econ-kirinyaga` | Added | yes | 0 |
| `econ-embakasi` | Added | yes | 0 |
| `econ-kasarani` | Added | yes | 0 |
| `econ-ruiru` | Added | yes | 0 |
| `choice-kobo-generator` | Added | yes | 0 |
| `choice-kobo-battery` | Added | yes | 0 |
| `choice-kisiwa-generator` | Added | yes | 0 |
| `choice-mto-inverter` | Added | yes | 0 |
| `choice-mto-demand` | Added | yes | 0 |
| `choice-mto-billing` | Added | yes | 0 |
| `choice-mwea-demand` | Added | yes | 0 |
| `choice-thika-backup` | Added | yes | 0 |
| `choice-kirinyaga-energy` | Added | yes | 0 |
| `choice-embakasi-schedule` | Added | yes | 0 |
| `choice-kasarani-charger` | Added | yes | 0 |
| `choice-ruiru-expansion` | Added | yes | 0 |
| `plan-lakeside` | Added | yes | 0 |
| `verify-lakeside` | Added | yes | 0 |
| `pilot-lakeside` | Added | yes | 0 |
| `plan-harvest` | Added | yes | 0 |
| `verify-harvest` | Added | yes | 0 |
| `pilot-harvest` | Added | yes | 0 |
| `plan-metro` | Added | yes | 0 |
| `verify-metro` | Added | yes | 0 |
| `pilot-metro` | Added | yes | 0 |
| `portfolio` | Changed | yes | 0 |
| `sites` | Preserved | yes | 0 |
| `mini` | Preserved | yes | 0 |
| `foundation` | Preserved | yes | 0 |
| `readiness` | Preserved | yes | 0 |
| `changes` | Preserved | yes | 0 |
| `dispatch` | Preserved | yes | 0 |
| `renewable` | Preserved | yes | 0 |
| `evidence` | Preserved | yes | 0 |
| `finding` | Preserved | yes | 0 |
| `analysis` | Preserved | yes | 0 |
| `financials` | Preserved | yes | 0 |
| `assumptions` | Preserved | yes | 0 |
| `recommendation` | Preserved | yes | 0 |
| `verification` | Preserved | yes | 0 |
| `asset` | Preserved | yes | 0 |
| `health` | Preserved | yes | 0 |
| `lab` | Preserved | yes | 0 |
| `cold` | Preserved | yes | 0 |
| `temperature` | Preserved | yes | 0 |
| `cooling` | Preserved | yes | 0 |
| `coldbackup` | Preserved | yes | 0 |
| `ev` | Preserved | yes | 0 |
| `sessions` | Preserved | yes | 0 |
| `availability` | Preserved | yes | 0 |
| `energy` | Preserved | yes | 0 |
| `incident` | Preserved | yes | 0 |
| `workverification` | Preserved | yes | 0 |
| `service` | Preserved | yes | 0 |
| `fuel` | Preserved | yes | 0 |
| `backup` | Preserved | yes | 0 |
| `sitefindings` | Preserved | yes | 0 |
| `sitework` | Preserved | yes | 0 |
| `sitework-incidents` | Preserved | yes | 0 |
| `sitework-maintenance` | Preserved | yes | 0 |
| `evidence-analysis` | Preserved | yes | 0 |
| `assets` | Preserved | yes | 0 |
| `findings` | Preserved | yes | 0 |
| `actions` | Preserved | yes | 0 |
| `incidents` | Preserved | yes | 0 |
| `maintenance` | Preserved | yes | 0 |
| `globalevidence` | Preserved | yes | 0 |
| `globalfinancials` | Preserved | yes | 0 |
| `cold-foundation` | Preserved | yes | 0 |
| `cold-health` | Preserved | yes | 0 |
| `cold-evidence` | Preserved | yes | 0 |
| `cold-evidence-analysis` | Preserved | yes | 0 |
| `cold-financials` | Preserved | yes | 0 |
| `cold-assumptions` | Preserved | yes | 0 |
| `cold-findings` | Preserved | yes | 0 |
| `cold-work` | Preserved | yes | 0 |
| `cold-work-incidents` | Preserved | yes | 0 |
| `cold-work-maintenance` | Preserved | yes | 0 |
| `cold-finding` | Preserved | yes | 0 |
| `cold-recommendation` | Preserved | yes | 0 |
| `ev-foundation` | Preserved | yes | 0 |
| `ev-health` | Preserved | yes | 0 |
| `ev-evidence` | Preserved | yes | 0 |
| `ev-evidence-analysis` | Preserved | yes | 0 |
| `ev-financials` | Preserved | yes | 0 |
| `ev-assumptions` | Preserved | yes | 0 |
| `ev-findings` | Preserved | yes | 0 |
| `ev-work` | Preserved | yes | 0 |
| `ev-work-incidents` | Preserved | yes | 0 |
| `ev-work-maintenance` | Preserved | yes | 0 |
| `ev-finding` | Preserved | yes | 0 |
| `ev-recommendation` | Preserved | yes | 0 |
| `ev-action` | Preserved | yes | 0 |
| `finding-evidence` | Preserved | yes | 0 |
| `alternatives` | Preserved | yes | 0 |
| `finding-history` | Preserved | yes | 0 |
| `action-overview` | Preserved | yes | 0 |
| `action-plan` | Preserved | yes | 0 |
| `action-execution` | Preserved | yes | 0 |
| `action-evidence` | Preserved | yes | 0 |
| `action-history` | Preserved | yes | 0 |
| `opportunity-finding` | Preserved | yes | 0 |
| `cold-finding-excursion` | Preserved | yes | 0 |
| `cold-action` | Preserved | yes | 0 |
| `scenarios` | Preserved | yes | 0 |
| `cold-scenarios` | Preserved | yes | 0 |
| `ev-scenarios` | Preserved | yes | 0 |
| `cold-readiness` | Preserved | yes | 0 |
| `ev-readiness` | Preserved | yes | 0 |
| `sld` | Preserved | yes | 0 |
| `cold-sld` | Preserved | yes | 0 |
| `ev-sld` | Preserved | yes | 0 |
| `assets-warranty` | Preserved | yes | 0 |
| `asset-register` | Preserved | yes | 0 |
| `asset-overview` | Preserved | yes | 0 |
| `site-create-form` | Preserved | yes | 0 |
| `site-create-template` | Preserved | yes | 0 |
| `site-batch-upload` | Preserved | yes | 0 |
| `site-setup-history` | Preserved | yes | 0 |
| `asset-performance` | Preserved | yes | 0 |
| `asset-config` | Preserved | yes | 0 |
| `asset-edit` | Preserved | yes | 0 |
| `asset-work` | Preserved | yes | 0 |
| `asset-evidence` | Preserved | yes | 0 |
| `asset-warranty` | Preserved | yes | 0 |
| `findings-cost` | Preserved | yes | 0 |
| `findings-risks` | Preserved | yes | 0 |
| `findings-opportunities` | Preserved | yes | 0 |
| `maintenance-preventive` | Preserved | yes | 0 |
| `wr-overview` | Preserved | yes | 0 |
| `wr-record` | Preserved | yes | 0 |
| `wr-history` | Preserved | yes | 0 |
| `oprecords` | Preserved | yes | 0 |
| `settings-policies` | Preserved | yes | 0 |
| `settings-tenant` | Preserved | yes | 0 |
