/* IA-2a unit 2 stub (spec §5.1.2 to §5.1.4, D-IA.49). Loaded with w.eval by plan_shape_check (and the other IA-2a checks) only under
   IA_FORCE_LANDED=IA-2a when the window has no shapePlan (before 3(a) lands the builders). It defines the plan shape with the §5.1.2
   placement, pushes the three tab routes, sets IA_TAB_GROUPS.Plan, points the plan route at shapePlan(ctx, 'items') and carries
   docTitle, then renders again. Top-level function declarations only, so a check's plant can reassign any of them with w.eval. */
var IA_PLAN_STEPS = ['DRAFT', 'PROPOSED', 'APPROVED', 'CLOSED'];
function iaPlanSteps(state) { const cur = state === 'REVISED' ? 1 : IA_PLAN_STEPS.indexOf(state); if (cur < 0) throw new Error(`plan state ${state} has no step`); return { steps: IA_PLAN_STEPS.map(s => STATE_WORD[s]), cur }; }
function iaPlanStepper(op) { const { steps, cur } = iaPlanSteps(uxPlanState(op).state); return `<ol class="ux-dsteps ia-plan-steps" aria-label="Where this plan is">${steps.map((s, i) => `<li class="${i < cur ? 'is-done' : i === cur ? 'is-current' : ''}"${i === cur ? ' aria-current="step"' : ''}>${s}</li>`).join('')}</ol>`; }
function iaCrewTiles(op, P) { const o = OPS[op], ms = crewByMonth(op, P); return ms.map(m => uxKpi(`${cap(o.crewWord)} used${ms.length > 1 ? `, ${m.month}` : ''}`, `${num(m.used)} <small>of ${num(m.limit)}</small>`, [], uxMeterBar(m.used, m.limit, `${num(m.used)} of ${num(m.limit)} ${o.crewWord}${ms.length > 1 ? ` in ${m.month}` : ''}`))).join(''); }
function iaPlanBand(op, P, budget) { const B = uxPlanBandParts(op, P, budget); return `<section class="ux-planband" aria-label="The plan at a glance"><div class="heroes ux-kpis">${B.spend}${iaCrewTiles(op, P) || B.crew}${B.value}</div>${B.act}</section>`; }
function iaPlanCaseLabel(op) { const t = document.createElement('template'); t.innerHTML = switches(op); return [...t.content.querySelectorAll('fieldset')].map(f => `${f.querySelector('legend').textContent}: ${((f.querySelector('input[checked]') || {}).parentNode || { textContent: '' }).textContent.trim()}`).join('; '); }
function iaPlanCaseLine(op, here) { return DEFAULT_CASE(op) ? '' : `<p class="ia-plan-case">Showing the case you chose: ${escapeHtml(iaPlanCaseLabel(op))}. <a href="${here ? '#sw-h' : '#/plan'}">Change the case</a></p>`; }
function iaPlanHead(op, p, here) { return `${iaPlanStepper(op)}${iaPlanBand(op, p.P, p.budget)}${p.ap.releases}${p.ap.notice}${iaPlanCaseLine(op, here)}<p class="ia-plan-rules">${uxOpener('ia-plan-thresholds', 'Release thresholds', 'ux-link')}</p>`; }
function iaPlanHistory(op) {
  const S = uxPlanState(op), S0 = PSTATE(), L = (uxMock().log || []).filter(e => e.op === op && (e.key === 'approve-plan' || e.key === 'send-back'));
  const rows = [...L.map((e, i) => `<li data-ia-hist="log:${i}">${e.toast} <small>${e.by} · ${hhmm(e.at) || ''}</small></li>`), `<li data-ia-hist="proposed">Version ${num(S0.version)} proposed <small>The system · ${fdate(S0.proposed)}</small></li>`, `<li data-ia-hist="opened">Opened within the executive’s limits <small>The system · ${fdate(S0.opened)}</small></li>`];
  return sec('Versions and approvals', `<ul class="list ia-plan-history">${rows.join('')}</ul><p class="note">Changes made here are shown in this demonstration only.</p>`, `Version ${num(S.version)}, ${STATE_WORD[S.state].toLowerCase()}`);
}
function shapePlan(ctx, tab) {
  const op = ctx.op, p = planParts(op), side = tab === 'items' || tab === 'left-out', lv = (n, x) => x ? `<div data-level="${n}">${x}</div>` : '';
  const l1 = `<div data-level="L1">${iaPlanHead(op, p, side)}</div>`, drawers = `<div data-ia-drawers>${uxDrawer('ia-plan-thresholds', 'Release thresholds', p.ap.thrBody)}</div>`;
  if (side) {
    const l2 = tab === 'items' ? p.l2 : uxSecA('Left out of the plan, and why', p.leftAns, p.leftBody, true), l3 = tab === 'items' ? `${p.diff}${p.paths}${p.crew}${p.cases}` : `${p.listed}${p.returned}`;
    return `<section data-shape="plan">${p.sticky}${l1}<div class="layout-main-side"><div>${lv('L2', l2)}${lv('L3', l3)}</div><aside class="side-panel" data-level="L3">${p.switches}</aside></div>${drawers}</section>`;
  }
  return `<section data-shape="plan">${p.sticky}${l1}${lv('L2', tab === 'review' ? whatChangedParts(op).review : iaPlanHistory(op))}${drawers}</section>`;
}
/* the routes, the tab group and docTitle (what 3(a) adds to ia-routes.js, iaScreen and render()) */
function iaPlanTabRoute(id, tab, key) { return { id, shape: 'plan', object: 'plan', home: 'Plan', unit: 'IA-2a', tab, tabGroup: 'Plan', title: ctx => iaLegacy('portfolio/act-first/plan').title, subtitle: ctx => iaLegacy('portfolio/act-first/plan').subtitle, docTitle: ctx => `${tab} · ${iaLegacy('portfolio/act-first/plan').title}`, crumbs: ctx => [['Plan', 'plan'], [tab]], render: ctx => shapePlan(ctx, key) }; }
(function () {
  if (!IA_ROUTES.some(r => r.id === 'plan/left-out')) { const i = IA_ROUTES.findIndex(r => r.id === 'plan'); IA_ROUTES.splice(i + 1, 0, iaPlanTabRoute('plan/left-out', 'Left out', 'left-out'), iaPlanTabRoute('plan/review', 'Review', 'review'), iaPlanTabRoute('plan/history', 'History', 'history')); }
  const r = IA_ROUTES.find(x => x.id === 'plan'); r.tab = 'Items'; r.tabGroup = 'Plan'; r.render = ctx => shapePlan(ctx, 'items');
  IA_TAB_GROUPS.Plan = ctx => [['Items', 'plan'], ['Left out', 'plan/left-out'], ['Review', 'plan/review'], ['History', 'plan/history']];
  const base = iaScreen; iaScreen = function (route, path) { const s = base(route, path); s.docTitle = route.docTitle ? route.docTitle(s.ctx) : s.title; return s; };
  const base2 = render; render = function () { base2(); const s = currentScreen(); if (s && s.ia && s.docTitle && s.docTitle !== s.title) document.title = `${s.docTitle} · ${OPS[LS.op].name}`; };
  render();
})();
