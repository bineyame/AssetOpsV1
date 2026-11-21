/* IA-1 gate runner (spec §2.5, R10): the three checks, then every plant of every landed unit, each as its own
   process. Exits non-zero if a check fails or a plant passes. One line per run: check · plant · expected · got.
   IA-2a (D-IA.49): --force IA-2a sets IA_FORCE_LANDED=IA-2a for every child and treats the unit as landed here, so its checks and plants
   run before the flip; once IA-2a is in IA_LANDED, an IA-2a check whose output says "dormant" is BAD.
   Run: node tools/ia_gates.cjs [--force IA-2a] */
const { spawnSync } = require('child_process'), fs = require('fs'), path = require('path');
const fi = process.argv.indexOf('--force'), force = fi > 0 ? String(process.argv[fi + 1] || '').split(',').filter(Boolean) : [];
const dir = __dirname, real = new Set((fs.readFileSync(path.join(dir, '..', 'ia-routes.js'), 'utf8').match(/const IA_LANDED = new Set\(\[([^\]]*)\]\)/) || [, ''])[1].match(/IA-\w+/g) || []), landed = new Set([...real, ...force]);
/* the plants each unit lands (spec §2.5) */
const PLANTS = {
  'IA-1a': [['shape_check', 'SHAPE_PLANT', ['unlink', 'stub', 'rail', 'palette', 'primary', 'lab', 'tabstop', 'notfound', 'noact', 'lablegacy']], ['click_depth_check', 'G1_PLANT', ['engine']], ['after_render_check', 'AR_PLANT', ['text', 'attr', 'late', 'replace']]],
  'IA-1b': [['shape_check', 'SHAPE_PLANT', ['selflink', 'aliaskey', 'crossop', 'linkprimary', 'landing', 'foreignscope']], ['click_depth_check', 'G1_PLANT', ['tile', 'driver', 'hidden', 'details', 'closed', 'siteclosed']],
    ['count_check', 'COUNT_PLANT', ['choose', 'capsel', 'capmore', 'adverse', 'phone']], ['outcomes_table_check', 'OUT_PLANT', ['cap', 'group', 'scope', 'sort', 'notarget', 'headline']]],
  'IA-1c': [['shape_check', 'SHAPE_PLANT', ['decprimary', 'stickyact', 'anchor', 'sitecrumb', 'decscope']], ['click_depth_check', 'G1_PLANT', ['inbox']], ['count_check', 'COUNT_PLANT', ['foryou', 'nolog']], ['after_render_check', 'AR_PLANT', ['fitlate']]],
  /* spec §5.1.8, D-IA.49 to D-IA.52 */
  'IA-2a': [['plan_shape_check', 'PLAN_PLANT', ['tabs', 'place', 'l1', 'approval', 'thr', 'stepdone', 'cap', 'revised', 'sticky']], ['count_check', 'COUNT_PLANT', ['planstep', 'planhist', 'planver']],
    ['shape_check', 'SHAPE_PLANT', ['doctitle']], ['click_depth_check', 'G1_PLANT', ['plantabs']], ['plan_switch_check', 'PS_PLANT', ['crewtile', 'release', 'leftout']],
    ['ux_interaction_check', 'UXI_PLANT', ['planans', 'planwait']], ['copy_check', 'COPY_PLANT', ['plan']], ['qty_check', 'QTY_PLANT', ['clause', 'wait']]]
};
/* the checks of a unit whose output must not say "dormant" once the unit is landed (D-IA.49) */
const OWN = { 'IA-2a': ['plan_shape_check', 'count_check', 'shape_check', 'click_depth_check', 'plan_switch_check', 'ux_interaction_check', 'copy_check', 'qty_check'] };
const runs = [['shape_check', null, null], ['click_depth_check', null, null], ['after_render_check', null, null], ...(landed.has('IA-1b') ? [['count_check', null, null], ['outcomes_table_check', null, null]] : []), ...(landed.has('IA-2a') ? [['plan_shape_check', null, null], ['plan_switch_check', null, null], ['ux_interaction_check', null, null], ['copy_check', null, null], ['qty_check', null, null]] : [])];
for (const [unit, list] of Object.entries(PLANTS)) if (landed.has(unit)) for (const [check, env, names] of list) for (const n of names) runs.push([check, env, n]);
let bad = 0; const t0 = Date.now();
for (const [check, env, plant] of runs) {
  const r = spawnSync(process.execPath, [path.join(dir, `${check}.cjs`)], { env: { ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/_PLANT$/.test(k) && k !== 'IA_FORCE_LANDED')), ...(force.length ? { IA_FORCE_LANDED: force.join(',') } : {}), ...(env ? { [env]: plant } : {}) }, encoding: 'utf8', maxBuffer: 1 << 24 });
  const dormant = /dormant/.test(r.stdout || '') && Object.entries(OWN).some(([u, cs]) => landed.has(u) && cs.includes(check));
  const got = dormant ? 'dormant' : r.status === 0 ? 'pass' : r.status === 1 ? 'fail' : `error ${r.status}`, want = plant ? 'fail' : 'pass', ok = got === want;
  if (!ok) bad++;
  const why = got === 'fail' ? ((r.stdout.split('\n').find(l => /FAIL$/.test(l)) ? r.stdout.split('\n')[r.stdout.split('\n').findIndex(l => /FAIL$/.test(l)) + 1] : '') || '').trim().slice(0, 110) : '';
  console.log(`${ok ? 'ok ' : 'BAD'} ${check} · ${plant || '-'} · expected ${want} · got ${got}${why ? ` · ${why}` : ''}${!ok && r.stderr ? ` · ${(r.stderr.trim().split('\n').find(l => /Error|error:/.test(l)) || r.stderr.trim().split('\n')[0]).trim().slice(0, 200)}` : ''}`);
}
console.log(`ia_gates: ${runs.length} runs, landed ${[...real].join(', ')}${force.length ? `, forced ${force.join(', ')}` : ''}, ${bad ? `${bad} BAD` : 'all as expected'} (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
process.exit(bad ? 1 : 0);
