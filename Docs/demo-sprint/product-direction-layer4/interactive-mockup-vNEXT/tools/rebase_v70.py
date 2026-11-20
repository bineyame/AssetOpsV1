"""Re-base the v7.0 mock-up sources for the Layer 4 rev 4 mock-up.

Reads src-v70-baseline/ (byte-identical copy of frontend/mockups/v70) and writes the working copies
(mockups.css, portfolio.css, outcomes.css, portfolio.js, outcomes.js, screens.js) into this folder.
Every change to v7.0 code is made here, so the full set of edits is reviewable in one place:
  1. HOOKS: exact, single-occurrence string edits that let loop-*.js plug in (routing, top bar, tabs,
     breadcrumbs, review bar, click/change handlers). Each must match exactly once or the script fails.
  2. NAMES: display-name re-basing so the preserved pages describe the same world as the manifest
     (GreenHarvest Cold Room -> Thika cold room, Depot Charging Hub -> Ruiru depot, site ids).
Run: python3 tools/rebase_v70.py   (from the interactive-mockup-vNEXT folder)
"""
import pathlib, re, shutil, sys

here = pathlib.Path(__file__).resolve().parent.parent
src = here / 'src-v70-baseline'

HOOKS = {
 'screens.js': [
  # a captive fleet earns no tariff revenue (economic-metric-and-effect-contracts.md:104,114; placeholder audit, 20 Nov)
  ('pair(panel(\'Bounded money consequence\',`<div class="metric-value">$36.00</div><p class="prose">Gross tariff estimate for 120 kWh delivered in complete sessions at a $0.30/kWh scenario tariff. <strong>Not cash collected.</strong> The interrupted session is not priced: unmet demand is not established.</p>', 'pair(panel(\'Bounded money consequence\',`<div class="metric-value">Not applicable</div><p class="prose">A captive fleet earns no charging revenue, so no tariff is estimated. Its money measure is charging cost per required departure met. The interrupted session is not priced: unmet demand is not established.</p>'),
  # routing: aliases for merged screens, loop screens, operator from the screen
  ("function currentScreen(){return SCREENS.find(s=>s.id===location.hash.replace(/^#\\//,''))||SCREENS[0];}",
   "function currentScreen(){return resolveScreen(location.hash.replace(/^#\\//,''));}"),
  # site switch and site tab routes are provided by loop-core.js (operator's own sites; new Overview and Financials)
  ("function siteSwitch(s){", "function siteSwitchV70(s){"),
  ("function siteRoutes(domain){", "function siteRoutesV70(domain){"),
  # tabs: loop screens bring their own tab rows
  ("function tabs(s){\n if(s.gtabs)", "function tabs(s){\n if(s.ltabs)return s.ltabs(s);\n if(s.gtabs)"),
  # breadcrumbs: loop screens bring their own
  ("function breadcrumbs(s){\n", "function breadcrumbs(s){\n if(s.crumbs)return loopCrumbs(s);\n"),
  # shell: loop screens are period-scoped (October 2026), not range-scoped
  ("const global=!s.section||!!s.gtabs,lab=", "const global=!s.section||!!s.gtabs||!!s.loop,lab="),
  ("const body=(fid?affectsLine(fid):'')+", "const body=preBody(s)+(fid?affectsLine(fid):'')+"),
  ("${lab?'Simulator Lab · MG-DEMO-01':'Bineyame Operations'} <span class=\"muted\">/ Demo estate</span>",
   "${lab?'Simulator Lab · MG-DEMO-01':opName()} <span class=\"muted\">/ Demo operator</span>"),
  ("${rangePicker(global?null:s.domain)}", "${s.loop?periodChip(s):rangePicker(global?null:s.domain)}"),
  ("${s.root==='Sites'&&s.section&&!s.gtabs?provTag(s.domain):''}", "${s.root==='Sites'&&s.section&&!s.gtabs&&!s.loop?provTag(s.domain):''}"),
  ("${!global&&!lab&&s.root!=='Sites'?btn(SITES[s.domain].overview,'Open site'):''}",
   "${s.actions?s.actions(s):!global&&!lab&&s.root!=='Sites'?btn(siteOverviewFor(s.domain),'Open site'):''}"),
  # review bar (mock-review tooling): demo operator selector lives here, not in the product chrome
  ("<strong>ARCHITECTURE REVIEW</strong><span>Interactive mockup · illustrative data</span></div><div class=\"right\">",
   "<strong>LAYER 4 MOCK-UP REVIEW</strong><span>Not approved: awaits owner inspection · illustrative demo data</span></div><div class=\"right\">${reviewOperatorSelect()}"),
  ("${SCREENS.map(p=>`<option value=\"${p.id}\" ${p.id===s.id?'selected':''}>${p.root} · ${p.title}${p.section?' / '+p.section:''}</option>`).join('')}",
   "${SCREENS.map(p=>`<option value=\"${p.id}\" ${p.id===s.id?'selected':''}>${selectorLabel(p)}</option>`).join('')}"),
  ("<button data-notes>Review notes</button><a href=\"AssetOps-v70-Screen-Review.pdf\" target=\"_blank\" rel=\"noopener\">PDF screen book ↗</a>",
   "<button data-notes>Review notes</button><button data-loop-changes>What changed</button><a href=\"../../../../frontend/mockups/v70/AssetOps-v70-Screen-Review.pdf\" target=\"_blank\" rel=\"noopener\">v7.0 PDF screen book ↗</a>"),
  (" window.mockupReady=true;\n}", " if(typeof afterRender==='function')afterRender(s);\n window.mockupReady=true;\n}"),
  # review notes: loop screens carry their own design notes; storage key and spec link for this folder
  ("(s.id==='portfolio'?portfolioDesignNotes():'')", "(s.loopNotes?s.loopNotes(s):s.id==='portfolio'?portfolioDesignNotes():'')"),
  ("href=\"../../docs/architecture/assetops-v69-pivot-recommendation.md\"", "href=\"../layer4-transformation-design.md\""),
  # click and change handlers: loop-core.js handles its own data attributes first
  ("document.addEventListener('click',e=>{\n", "document.addEventListener('click',e=>{\n if(loopClick(e))return;\n"),
  ("document.addEventListener('change',e=>{", "document.addEventListener('change',e=>{if(loopChange(e))return;"),
  # rev 16.6 professional pass: plain footer (owner, 19 Nov: no technical words user-facing); review notes stay one click away
  ("<span>Illustrative mockup data · proposal for implementation · not connected to site telemetry</span><button data-notes>Canonical basis & implementation notes</button>",
   "<span>Illustrative demo data · not connected to live site data</span><button data-notes>Review notes</button>"),
  # theme toggle (light, dark, follow the system) in the top bar, before the avatar
  ("<span class=\"avatar\">BY</span>", "${themeToggle()}<span class=\"avatar\" title=\"${avatarName()}, illustrative operator executive\">${avatarInitial()}</span>"),
  # rev 16.12 Organisation settings (spec §8, OD-13, OD-14, OD-2, OD-12, OD-18): the five roles, the grant record, thresholds
  # and limits come from loop-portfolio.js orgUsersAndRoles(); no Admin and no Viewer role exists
  ("function settingsTenant(){return status(badge('Admin','blue'),'Organisation-wide settings for this demo tenant')+",
   "function settingsTenant(){return status(badge('Operator executive changes these','blue'),'Organisation-wide settings, read by every role')+"),
  ("['Organisation','Bineyame Operations']", "['Organisation',opName()]"),
  ("'Deployment-wide','Admin only. ", "'Deployment-wide','Operator executive only. "),
  (" panel('Users and roles',table(['User','Role','Can'],[['B. Yohannes','Admin','Everything, including settings'],['Operations manager','Manager','Accept recommendations, assign work'],['Site controls lead','Operator','Record changes and readings'],['Maintenance lead','Technician','Complete work and maintenance records'],['Finance analyst','Viewer','Read sites, findings and financials']]),'Small illustrative list');}",
   " orgUsersAndRoles();}"),
  # initial render moves to the end of loop-init.js (after loop screens register)
  ("window.mockupManifest=SCREENS.map(({render,...meta})=>meta);\nrender();", "/* Layer 4: manifest and initial render() moved to loop-init.js */"),
 ],
 'portfolio.js': [
  ("href=\"previews/portfolio-previous.png\"", "href=\"../../../../frontend/mockups/v70/previews/portfolio-previous.png\""),
 ],
 'outcomes.js': [
  # an empty history says what it means (placeholder audit, 20 Nov): nothing yet, not "not available yet"
  ('<p class="ob-none">${NAY}</p>', '<p class="ob-none">Nothing yet</p>'),
  # design rev 16.9/16.10 §2.0 named change 1 (OD-21): contribution is the outcome above Grow and Optimize, not a Grow row
  (",['Cash collected',`${NAY} · no billing or payment records`,null,null],['Site earnings',`${NAY} · needs site income, operating cost and capital records`,null,null]]", "]"),
  # rev 16.10 §2.0 (OD-21 corrected): collection of what was billed is Optimize (billed against collected), cash outside contribution
  ("contrib:[['Generator use','30 min avoidable, 30 min unclear','f104','dispatch'],", "contrib:[['Generator use','30 min avoidable, 30 min unclear','f104','dispatch'],['Cash collected',`${NAY} · no billing or payment records`,null,null],"),
  ("const CAT_OF={'MG-1':'grow','MG-3':'grow','MG-6':'grow',", "const CAT_OF={'MG-1':'grow','MG-3':'above','MG-6':'cost',"),
 ],
}
STORE = [("assetops-v70-review-notes", "assetecon-layer4-review-notes"), ("AssetOps-v70-review-notes.json", "AssetEcon-layer4-review-notes.json")]

# Display names: one world (main design §6.2). Order matters (longest first).
NAMES = [
 (r"GreenHarvest Cold Room", "Thika cold room"),
 (r"GreenHarvest", "Thika"),
 (r"Depot Charging Hub", "Ruiru depot"),
 (r"Depot charging hub", "Ruiru depot"),
 (r"(?<!Westfield )\bDepot\b(?! auxiliary| attendant)", "Ruiru"),
 (r"MG-DEMO-01", "KOBO-001"),
 (r"CR-DEMO-01", "COLD-THIKA"),
 (r"EV-DEMO-01", "EV-RUI"),
 (r"'B\. Yohannes'", "avatarName()"),  # a former real user's name; the setup history names the illustrative operator executive
 (r"Tenant configuration", "Organisation settings"),  # rev 16.6 plain-words pass
]

def main():
    log = []
    for f in ['mockups.css', 'portfolio.css', 'outcomes.css']:
        shutil.copyfile(src / f, here / f)
    for f in ['portfolio.js', 'outcomes.js', 'screens.js']:
        t = (src / f).read_text(encoding='utf-8')
        for a, b in HOOKS.get(f, []):
            n = t.count(a)
            if n != 1:
                sys.exit(f'HOOK FAILED ({n} matches) in {f}: {a[:80]}')
            t = t.replace(a, b)
            log.append(f'{f}: hook {a[:60]!r}')
        for a, b in STORE:
            t = t.replace(a, b)
        for pat, rep in NAMES:
            t, n = re.subn(pat, rep, t)
            if n:
                log.append(f'{f}: name {pat!r} -> {rep!r} x{n}')
        (here / f).write_text(t, encoding='utf-8')
    (here / 'tools' / 'rebase-log.txt').write_text('\n'.join(log) + '\n', encoding='utf-8')
    print('\n'.join(log))

if __name__ == '__main__':
    main()
