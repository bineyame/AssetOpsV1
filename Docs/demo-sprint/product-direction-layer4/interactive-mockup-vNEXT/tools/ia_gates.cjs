/* IA-1 gate runner (spec §2.5, R10): the three checks, then every plant of every landed unit, each as its own
   process. Exits non-zero if a check fails or a plant passes. One line per run: check · plant · expected · got.
   Run: node tools/ia_gates.cjs */
const { spawnSync } = require('child_process'), fs = require('fs'), path = require('path');
const dir = __dirname, landed = new Set((fs.readFileSync(path.join(dir, '..', 'ia-routes.js'), 'utf8').match(/const IA_LANDED = new Set\(\[([^\]]*)\]\)/) || [, ''])[1].match(/IA-\w+/g) || []);
/* the plants each unit lands (spec §2.5) */
const PLANTS = {
  'IA-1a': [['shape_check', 'SHAPE_PLANT', ['unlink', 'stub', 'rail', 'palette', 'primary', 'lab', 'tabstop', 'notfound', 'noact', 'lablegacy']], ['click_depth_check', 'G1_PLANT', ['engine']], ['after_render_check', 'AR_PLANT', ['text', 'attr', 'late', 'replace']]],
  'IA-1b': [['shape_check', 'SHAPE_PLANT', ['selflink', 'aliaskey', 'crossop', 'linkprimary', 'landing', 'foreignscope']], ['click_depth_check', 'G1_PLANT', ['tile', 'driver', 'hidden', 'details', 'closed', 'siteclosed']],
    ['count_check', 'COUNT_PLANT', ['choose', 'capsel', 'capmore', 'adverse', 'phone']], ['outcomes_table_check', 'OUT_PLANT', ['cap', 'group', 'scope', 'sort', 'notarget', 'headline']]],
  'IA-1c': [['shape_check', 'SHAPE_PLANT', ['decprimary', 'stickyact', 'anchor', 'sitecrumb', 'decscope']], ['click_depth_check', 'G1_PLANT', ['inbox']], ['count_check', 'COUNT_PLANT', ['foryou', 'nolog']]]
};
const runs = [['shape_check', null, null], ['click_depth_check', null, null], ['after_render_check', null, null], ...(landed.has('IA-1b') ? [['count_check', null, null], ['outcomes_table_check', null, null]] : [])];
for (const [unit, list] of Object.entries(PLANTS)) if (landed.has(unit)) for (const [check, env, names] of list) for (const n of names) runs.push([check, env, n]);
let bad = 0; const t0 = Date.now();
for (const [check, env, plant] of runs) {
  const r = spawnSync(process.execPath, [path.join(dir, `${check}.cjs`)], { env: { ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/_PLANT$/.test(k))), ...(env ? { [env]: plant } : {}) }, encoding: 'utf8', maxBuffer: 1 << 24 });
  const got = r.status === 0 ? 'pass' : r.status === 1 ? 'fail' : `error ${r.status}`, want = plant ? 'fail' : 'pass', ok = got === want;
  if (!ok) bad++;
  const why = got === 'fail' ? ((r.stdout.split('\n').find(l => /FAIL$/.test(l)) ? r.stdout.split('\n')[r.stdout.split('\n').findIndex(l => /FAIL$/.test(l)) + 1] : '') || '').trim().slice(0, 110) : '';
  console.log(`${ok ? 'ok ' : 'BAD'} ${check} · ${plant || '-'} · expected ${want} · got ${got}${why ? ` · ${why}` : ''}${!ok && r.stderr ? ` · ${r.stderr.trim().split('\n')[0].slice(0, 120)}` : ''}`);
}
console.log(`ia_gates: ${runs.length} runs, landed ${[...landed].join(', ')}, ${bad ? `${bad} BAD` : 'all as expected'} (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
process.exit(bad ? 1 : 0);
