# AssetEcon Layer 4 mock-up: builder notes

**The owner's guide is `walkthroughs.md`** (what the mock-up shows, how to open it, the guided tour, and the owner's checklist; plan F #8, which folded in this README's owner content and the former `owner-inspection-checklist.md`). This file keeps only what a builder needs. No API is wired; every figure comes from `../demo-site-scenario-manifest.yaml` through `../evaluate_structure.py`.

## Rebuild

```
python3 tools/rebase_v70.py     # re-creates the re-based v7.0 copies (screens.js, portfolio.js, outcomes.js, css) from src-v70-baseline
python3 ../evaluate_structure.py # evaluates the declared structures bottom-up and writes ../derived-values.json (every computed figure, with its formula)
python3 tools/gen_fixtures.py   # runs the evaluator again, embeds derived-values.json as DERIVED (all computed figures on screen come from it); only if the scenario file changed: regenerates fixtures.js (private oracle removed) and the replay-dependent figure set
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

## Data the screens read

`fixtures.js` embeds the manifest (`MANIFEST`, oracle removed) and the evaluator output (`DERIVED`). Since design rev 16.11 it also carries `MANIFEST.home_categories` (every node's heading, the bridge-driver map, the decisions' headings) and `MANIFEST.snapshot` (as-of time and pending recalculation per portfolio).
