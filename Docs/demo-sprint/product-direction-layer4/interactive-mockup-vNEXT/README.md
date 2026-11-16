# AssetEcon vNEXT decision mock-up (Layer 4, Deliverable 6)

**Not approved: awaits owner inspection.**

A new version of the existing interactive mock-up, not a new visual concept. It keeps every v7.0 screen and adds a decision layer for three demo operators (Lakeside Power mini-grid, Harvest Cold Network cold rooms, Metro Bus Depots captive EV fleet), October 2026, books closed 6 Nov 2026. All figures are illustrative and come from `../demo-site-scenario-manifest.yaml`.

| | Path |
|---|---|
| Old version | `frontend/mockups/v70/` (`index.html`, 110 screens) |
| New version | `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/` (`index.html`, 146 screens) |
| v7.0 sources, untouched, for diffing | `src-v70-baseline/` |

## Launch

- Open `index.html` directly in a browser (no server needed), or
- from this folder: `python3 -m http.server 8790 --bind 127.0.0.1`, then open `http://127.0.0.1:8790/`.

It opens on the decision home (`#/decide-lakeside`). The v7.0 Portfolio is in the left menu as **Operations view** (`#/portfolio`). The review bar's screen selector lists every screen.

## Rebuild

```
python3 tools/gen_fixtures.py   # only if the manifest changed: regenerates fixtures.js (strips the private oracle block)
node build.mjs                  # writes index.html from the css and js sources
```

Sources: v7.0 `mockups.css`, `portfolio.css`, `outcomes.css`, `portfolio.js`, `outcomes.js`, `screens.js` (minimal recorded edits); new `decisions.css`, `fixtures.js` (generated), `decisions.js` (data-driven templates).

## Audit and screenshots

```
tools/run-audit.sh --shots      # this server (sets library and font paths)
CHROME=/path/to/chrome PW=/path/to/playwright-core node tools/audit.mjs --shots   # elsewhere
```

Writes `tools/audit-results.json`, `screen-manifest-vnext.json` and `screenshots/`; then `node tools/gen_audit_md.cjs` rewrites `browser-audit.md`.

Revision: rev 2 (Architect fix round on `../REVIEW.md`), see CHANGE-REGISTER §7.

## Review pack

| File | Contents |
|---|---|
| `CHANGE-REGISTER.md` | Before/after inventory of all 110 v7.0 screens and 36 added screens; shared-shell changes; behaviour needing owner approval |
| `fixture-mapping.md` | Every on-screen figure → manifest path or stated derivation |
| `screenshots/INDEX.md` | Before/after for the changed screen; captures of every added screen; 390 px captures |
| `browser-audit.md` | Scripted browser audit results, issues fixed and open |
| `walkthroughs.md` | Seven-minute walkthrough per vertical with opening scripts and exact clicks |
| `owner-inspection-checklist.md` | Owner decisions and things to click |
| `screen-manifest-vnext.json` | Screen inventory with vNEXT status (also in the review-notes export) |

No API is wired: this is a design mock-up. No production UI code was changed.
