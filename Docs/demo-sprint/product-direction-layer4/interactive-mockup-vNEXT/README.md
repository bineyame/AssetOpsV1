# AssetEcon Layer 4 mock-up (rev 4): the restructured Portfolio

**Not approved: awaits owner inspection.** Rev 7 (targeted revisions after review): see CHANGE-REGISTER §7, §7a and §7b.

A new version of the v7.0 interactive mock-up, built to the Layer 4 design (`../layer4-transformation-design.md`, §2, §3.4, §6, §7). It keeps the v7.0 shell and left menu, keeps the Portfolio's six owner-approved tabs (Overview, Act first, Outcomes by site, Opportunity, What changed, Scope & coverage) and re-bases their content on the five mechanics: outcomes are computed from declared factor structures, deviations show at the factor where they arise, options change factors and are compared with no action, a plan is chosen under budget and crews, and proof is three separate verdicts. Three demo operators (Lakeside Power mini-grids, Harvest Cold Network cold rooms, Metro Bus Depots captive EV fleet), October 2026, books closed 6 Nov. Every figure is illustrative and comes from `../demo-site-scenario-manifest.yaml`.

| | Path |
|---|---|
| Old version | `frontend/mockups/v70/` (`index.html`, 110 screens) |
| New version | `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/` (`index.html`, 184 screens) |
| v7.0 sources, byte-identical, for diffing | `src-v70-baseline/` |

## Launch

- Open `index.html` directly in a browser (no server needed), or
- from this folder: `python3 -m http.server 8790 --bind 127.0.0.1`, then open `http://127.0.0.1:8790/`.

It opens on the Portfolio Overview (`#/portfolio`). Choose the **Demo operator** in the blue review bar at the top (review tooling, not part of the product). The review bar's screen selector lists every screen; "What changed" summarises the restructure.

Main routes (rev 6 tab order): `#/portfolio`, `#/portfolio/outcomes-by-site`, `#/portfolio/demand-and-capacity` (old `#/portfolio/opportunity` redirects), `#/portfolio/act-first`, `#/portfolio/what-changed`, `#/portfolio/scope`, `#/portfolio/scope/pilot`, `#/sites`, `#/site/<kobo|kisiwa|mto|mwea|thika|kirinyaga|embakasi|kasarani|ruiru>`, `#/site/<site>/economics`, `#/decision/<id>` (14 decisions), `#/globalfinancials`. Every v7.0 route still works; merged ones redirect to the site economics page that absorbed them.

## Rebuild

```
python3 tools/rebase_v70.py     # re-creates the re-based v7.0 copies (screens.js, portfolio.js, outcomes.js, css) from src-v70-baseline
python3 tools/gen_fixtures.py   # only if the scenario file changed: regenerates fixtures.js (private oracle removed)
node build.mjs                  # writes index.html; refuses a bundle containing the oracle
```

Sources: re-based v7.0 files (all edits in `tools/rebase_v70.py`, log in `tools/rebase-log.txt`); new `economics.css`, `loop-core.js` (data, factor structures, evidence drawer, shell hooks), `loop-decisions.js` (options, rights, 14 decisions), `loop-protect.js` (Protect measures), `loop-portfolio.js` (six tabs, Sites, Financials, pilot), `loop-site.js` (site overview, economics, decision pages), `loop-init.js` (registration, change status).

## Audit and screenshots

```
npm install --prefix /tmp/pw playwright-core && npx --prefix /tmp/pw playwright install chromium   # once
CHROME=/path/to/chrome PW=/tmp/pw/node_modules/playwright-core tools/run-audit.sh --shots
# hosts where Chromium lacks libraries or fonts: also set AUDIT_LD_LIBRARY_PATH and FONTCONFIG_FILE
```

Writes `tools/audit-results.json`, `screen-manifest-vnext.json`, `screenshots/`, then regenerates `CHANGE-REGISTER.md` and `browser-audit.md` (`tools/gen_docs.cjs`).

## Review pack

| File | Contents |
|---|---|
| `CHANGE-REGISTER.md` | All 110 v7.0 screens (Preserved / Changed / Merged / Retired) and the 74 added screens; shell changes; six-tab before/after; owner approvals; conflicts found |
| `fixture-mapping.md` | Every on-screen figure → scenario-file path or stated derivation |
| `screenshots/INDEX.md` | Key changed screens at 1440 px and 390 px, the four switch cases, and v7.0 "before" captures |
| `browser-audit.md` | Scripted audit results |
| `walkthroughs.md` | Seven-minute walkthrough per vertical with an opening insight and exact clicks |
| `owner-inspection-checklist.md` | Owner decisions and what to click |
| `screen-manifest-vnext.json` | Screen inventory with status and note |

No API is wired: this is a design mock-up. No product code, test, database or other mock-up version was changed.
