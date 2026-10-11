// Fixtures for the PRE-S3-03 next-work report. Run: node --test frontend/docs/architecture/test_delivery_next_work.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const nw = require('./delivery_next_work.cjs');

const node = (id, status, requires = [], extra = {}) => ({id, kind: 'implementation', layer: 'task', area: 'a1', owner: 'Implementer / Reviewer',
  status, requires, effort: 'M', evidence: status === 'resolved' ? 'x.md' : null, ...extra});
const portion = (id, extra) => ({id, claim: 'c', variant: 'bounded', core: true, state: 'open', technical_requires: [], proposed_gates: [], boundary: 'b', ...extra});

// Small world: a mixed S1/S2 panel (`site:1`), a money-gated Overview panel and a work panel.
function fixture() {
  const registry = {
    nodes: [
      {id: 'A-root', kind: 'architecture', area: 'a1', owner: 'Architect', status: 'resolved', requires: [], effort: 'M', evidence: 'd.md'},
      node('I-S1-01', 'resolved', ['A-root'], {task: 'S1-01'}),
      node('I-S4-02', 'open', ['A-root'], {task: 'S4-02'}),
      node('I-S5-01', 'open', ['A-root', 'I-S4-02'], {task: 'S5-01', sequenced_after: ['I-S4-02']}), // technical S5 money edge
      node('I-S6-01', 'open', ['A-root'], {task: 'S6-01', sequenced_after: ['I-S5-01'], area: 'a2'}), // ordering-only edge
      node('I-S7-01', 'open', ['A-root'], {task: 'S7-01', effort: 'S'}),
    ],
    delivery_plan: {
      active_wave: 'W1',
      waves: {W1: {manifest_ids: ['site', 'overview', 'work'], k: 10}},
      owner_inputs: {W1: {approved_manifest_ids: ['site', 'overview', 'work'], k: 10, evidence: 'owner.md',
        core_panels: {site: ['site:1'], overview: ['overview:1'], work: ['work:1']}, demo_values: {site: 3, overview: 5, work: 4}}},
      visual_gates: {'V-01': {packet: 'V-01.md', status: 'open', owner: 'Implementer / Reviewer', effort: null, user_review_required: true,
        requires: ['I-S1-01'], manifest_ids: ['site']}},
      outside_ranking: [],
      w1_panel_mapping: [
        {key: 'site:1', title: 'Site', reviewed_mapping: true, mapping_review: {evidence: 'r.md'}, panel_status: 'partial', visual_gate: 'V-01',
          claim_portions: [
            portion('site:1#a', {state: 'delivered', delivered_by: ['I-S1-01'], evidence: ['s1.md'], technical_requires: ['I-S1-01']}),
            portion('site:1#b', {variant: 'positive', technical_requires: ['I-S7-01']}),
            portion('site:1#c', {variant: 'unknown', technical_requires: ['I-S7-01']}),
          ]},
        {key: 'overview:1', title: 'Overview', reviewed_mapping: true, mapping_review: {evidence: 'r.md'}, panel_status: 'gap', visual_gate: null,
          claim_portions: [portion('overview:1#a', {technical_requires: ['I-S5-01']})]},
        {key: 'work:1', title: 'Work', reviewed_mapping: true, mapping_review: {evidence: 'r.md'}, panel_status: 'gap', visual_gate: null,
          claim_portions: [portion('work:1#a', {technical_requires: ['I-S6-01']})]},
      ],
    },
  };
  const contracts = [['site', 'Site'], ['overview', 'Overview'], ['work', 'Work']].map(([s, t]) => ({screen_id: s, panel_index: 1, panel_title: t}));
  const briefs = {areas: [{id: 'a1', primary_screens: ['site', 'overview']}, {id: 'a2', primary_screens: ['work']}]};
  const queue = [['S1-01', 'done'], ['S4-02', 'outline'], ['S5-01', 'outline'], ['S6-01', 'outline'], ['S7-01', 'outline']]
    .map(([task, status]) => ({task, packet: `${task}.md`, meta: {status, user_review_required: true}}));
  return {registry, contracts, briefs, queue, fingerprints: {registry: 'r1', owner_input: 'o1'}};
}
const run = (mutate = () => {}) => { const ctx = fixture(); mutate(ctx); return nw.nextWork(ctx); };
const cand = (report, id) => report.candidates.find((c) => c.id === id);
const refusalTypes = (report) => report.refusals.map((r) => r.type);

test('valid fixture ranks with raw facts, path proof and stops', () => {
  const r = run();
  assert.equal(r.status, 'ranked');
  // Delivered S1/S2 closeout is a satisfied gate, never a candidate or distance.
  assert.equal(cand(r, 'I-S1-01'), undefined);
  // Mixed panel: positive portion stays open and reaches I-S7-01 once, though two portions name it.
  const s7 = cand(r, 'I-S7-01');
  assert.equal(s7.panel_reach, 1);
  assert.deepEqual(s7.paths[0].portions, ['site:1#b', 'site:1#c']);
  assert.equal(s7.paths[0].d, 0);
  assert.equal(s7.ready_now, 1);
  // V-01 receives visual reach only, and no technical candidate is credited with the visual gap.
  const v01 = cand(r, 'V-01');
  assert.equal(v01.visual_reach, 1);
  assert.equal(v01.technical_reach, 0);
  assert.equal(s7.visual_reach, 0);
  assert.ok(v01.blocked.some((b) => b.stop === 'effort'), 'unsized V-01 is blocked, not scored as eligible');
  // Technical S5 money edge blocks; closure-unlock counts the panel after the named upstream gate.
  const s5 = cand(r, 'I-S5-01');
  assert.ok(s5.blocked.some((b) => b.stop === 'technical' && b.reason.includes('I-S4-02')));
  assert.equal(s5.closure_unlock, 1);
  assert.deepEqual(s5.paths[0].proof, ['I-S4-02']);
  const s4 = cand(r, 'I-S4-02');
  assert.equal(s4.paths[0].d, 1);
  assert.equal(s4.closure_unlock, 0);
  // Ordering-only S6 edge does not block.
  assert.deepEqual(cand(r, 'I-S6-01').blocked, []);
  // Score arithmetic: S7 reaches one panel at d=0, demo 3, one area, effort S.
  const P = 5 * (1 - Math.exp(-1 / 10));
  assert.equal(s7.score.score, Math.round((0.4 * 3 + 0.3 * P + 0.2 * 1 - 0.1 * 1) * 1000) / 1000);
  assert.deepEqual(r.eligible.sort(), ['I-S4-02', 'I-S6-01', 'I-S7-01']);
});

test('panel counted once across technical and visual paths for one candidate', () => {
  const r = run(({registry}) => { registry.delivery_plan.visual_gates['V-01'].effort = 'M'; });
  const v01 = cand(r, 'V-01');
  assert.equal(v01.panel_reach, 1);
  assert.ok(v01.score);
  assert.deepEqual(v01.blocked, []);
});

test('V-01 distance includes the panel open technical gates (review F1)', () => {
  const r = run(({registry}) => { registry.delivery_plan.visual_gates['V-01'].effort = 'M'; });
  const p = cand(r, 'V-01').paths[0];
  assert.equal(p.path, 'visual');
  assert.equal(p.d, 1, 'I-S7-01 still open on site:1');
  assert.deepEqual(p.proof, ['I-S7-01']);
  assert.equal(cand(r, 'V-01').ready_now, 0);
  assert.equal(cand(r, 'V-01').closure_unlock, 0, 'V-01 closure alone does not unlock site:1');
  // When V-01 itself requires the panel's technical gate, the union is one gate and closure unlocks it.
  const r2 = run(({registry}) => {
    registry.delivery_plan.visual_gates['V-01'].effort = 'M';
    registry.delivery_plan.visual_gates['V-01'].requires = ['I-S7-01'];
  });
  assert.equal(cand(r2, 'V-01').paths[0].d, 1);
  assert.equal(cand(r2, 'V-01').closure_unlock, 1);
});

test('fully delivered core panel contributes no technical reach; V-01 still reaches it', () => {
  const r = run(({registry}) => {
    const row = registry.delivery_plan.w1_panel_mapping[0];
    row.claim_portions = [row.claim_portions[0]];
    registry.delivery_plan.visual_gates['V-01'].effort = 'S';
  });
  assert.equal(cand(r, 'I-S7-01'), undefined, 'no reviewed path once the panel core is delivered');
  assert.equal(cand(r, 'V-01').visual_reach, 1);
});

test('missing owner demo value fails closed', () => {
  const r = run(({registry}) => { delete registry.delivery_plan.owner_inputs.W1.demo_values.work; });
  assert.equal(r.status, 'refused');
  assert.ok(refusalTypes(r).includes('missing_owner_input'));
  assert.equal(r.decision.action, 'none');
});

test('missing owner input entirely fails closed', () => {
  const r = run(({registry}) => { delete registry.delivery_plan.owner_inputs; });
  assert.deepEqual(refusalTypes(r).slice(0, 1), ['missing_owner_input']);
});

test('unmapped approved panel fails closed', () => {
  const r = run(({registry}) => {
    const row = registry.delivery_plan.w1_panel_mapping[2];
    row.reviewed_mapping = false;
    delete row.mapping_review;
  });
  assert.equal(r.status, 'refused');
  assert.ok(r.refusals.some((x) => x.type === 'unmapped_approved_panel' && x.reason.includes('work:1')));
});

test('non-empty delivery_plan.enables is refused with a typed reason; empty stays valid (review C5)', () => {
  const r = run(({registry}) => { registry.delivery_plan.enables = [{from: 'I-S4-02', to: 'I-S5-01'}]; });
  assert.equal(r.status, 'refused');
  assert.ok(refusalTypes(r).includes('unsupported_enables'));
  const ok = run(({registry}) => { registry.delivery_plan.enables = []; });
  assert.notEqual(ok.status, 'refused');
});

test('proposed-only node is not a reviewed path', () => {
  const r = run(({registry}) => {
    registry.delivery_plan.w1_panel_mapping[2].claim_portions[0] = portion('work:1#a', {technical_requires: ['I-S6-01'], proposed_gates: ['R-work']});
  });
  assert.equal(r.status, 'refused');
  assert.ok(refusalTypes(r).includes('proposed_only'));
  const r2 = run(({registry}) => { registry.delivery_plan.w1_panel_mapping[2].claim_portions[0].state = 'unmapped'; });
  assert.ok(refusalTypes(r2).includes('reviewed_mapping'));
  assert.ok(refusalTypes(r2).includes('unmapped_approved_panel'));
});

test('unknown referenced node is a typed mapping error', () => {
  const r = run(({registry}) => { registry.delivery_plan.w1_panel_mapping[2].claim_portions[0].technical_requires = ['I-missing']; });
  assert.ok(refusalTypes(r).includes('unknown_node'));
});

test('delivered portion needs resolved closeout and evidence', () => {
  const r = run(({registry}) => { registry.delivery_plan.w1_panel_mapping[0].claim_portions[0].delivered_by = ['I-S7-01']; });
  assert.ok(refusalTypes(r).includes('delivered_proof'));
  const r2 = run(({registry}) => { registry.delivery_plan.w1_panel_mapping[0].panel_status = 'real'; });
  assert.ok(refusalTypes(r2).includes('panel_status'), 'a partial panel cannot be marked real');
});

test('stale fingerprint refuses to rank', () => {
  const r = run((ctx) => { ctx.expected_fingerprints = {registry: 'r0', owner_input: 'o1'}; });
  assert.equal(r.status, 'refused');
  assert.ok(r.refusals.some((x) => x.type === 'stale_input' && x.reason.includes('registry')));
  assert.equal(run((ctx) => { ctx.expected_fingerprints = {...ctx.fingerprints}; }).status, 'ranked');
  assert.deepEqual(nw.fingerprints({a: 'x\r\ny'}), nw.fingerprints({a: 'x\ny'}), 'line endings alone do not make inputs stale');
  assert.notDeepEqual(nw.fingerprints({a: 'x'}), nw.fingerprints({a: 'y'}));
  assert.deepEqual(nw.staleInputs({a: '1', b: '2'}, {a: '1', b: '3', c: '4'}), ['b', 'c']);
});

test('queue and packet status must agree with registry', () => {
  const r = run(({queue}) => { queue[1].meta.status = 'done'; });
  assert.ok(r.refusals.some((x) => x.type === 'queue_mismatch' && x.reason.includes('S4-02')));
  const r2 = run(({queue}) => { queue.pop(); });
  assert.ok(refusalTypes(r2).includes('queue_mismatch'));
});

test('XL candidate is blocked with no score', () => {
  const r = run(({registry}) => { registry.nodes.find((n) => n.id === 'I-S6-01').effort = 'XL'; });
  const c = cand(r, 'I-S6-01');
  assert.equal(c.score, undefined);
  assert.ok(c.blocked.some((b) => b.stop === 'xl'));
  assert.ok(!r.eligible.includes('I-S6-01'));
});

test('active task and review stops apply before ranking', () => {
  const r = run(({queue}) => { queue[3].meta.status = 'in_review'; });
  assert.equal(r.decision.action, 'stop');
  assert.ok(cand(r, 'I-S6-01').blocked.some((b) => b.stop === 'review'));
  const r2 = run(({queue}) => { queue[4].meta.status = 'active'; });
  assert.equal(r2.decision.action, 'stop');
  assert.ok(cand(r2, 'I-S7-01').blocked.some((b) => b.stop === 'active_task'));
});

test('a PRE-S3 gate packet in review or active stops selection (Q7)', () => {
  const gate = (status) => ({task: 'PRE-S3-09', packet: 'PRE-S3-09.md', meta: {status, user_review_required: false}});
  assert.notEqual(run(({}) => {}).decision.action, 'stop');
  const done = run((ctx) => { ctx.gate_queue = [gate('done (accepted 2026-10-11)')]; });
  assert.notEqual(done.decision.action, 'stop', 'a done (...) gate packet does not stop');
  const r = run((ctx) => { ctx.gate_queue = [gate('in_review')]; });
  assert.equal(r.decision.action, 'stop');
  assert.ok(r.global_stops.some((s) => s.reason.includes('PRE-S3-09')));
  const r2 = run((ctx) => { ctx.gate_queue = [gate('active')]; });
  assert.equal(r2.decision.action, 'stop');
});

test('umbrella/index packet status is not_started, not unknown', () => {
  assert.equal(nw.packetPhase('umbrella/index; not a scored gate or implementation packet'), 'not_started');
  assert.equal(nw.packetPhase('done (accepted 2026-10-11)'), 'done');
});

test('gate packet discovery reads every linked packet', () => {
  assert.deepEqual(nw.parseGateQueue('x [PRE-S3-03](a.md) y [PRE-S3-04](b.md) [PRE-S3-03](a.md) [V-01](v.md) [S2-02r](r.md) [S3-02](s.md) [docs](http://x/y.html)'),
    [{task: 'PRE-S3-03', packet: 'a.md'}, {task: 'PRE-S3-04', packet: 'b.md'}, {task: 'V-01', packet: 'v.md'},
      {task: 'S2-02r', packet: 'r.md'}, {task: 'S3-02', packet: 's.md'}]);
});

test('a visual-gate or follow-up packet that is active or in review stops selection (C9)', () => {
  for (const id of ['V-01a', 'S2-02r', 'S4-03']) for (const [status, stop] of [['active', 'active_task'], ['in_review', 'review']]) {
    const r = run((ctx) => { ctx.gate_queue = [{task: id, packet: id + '.md', meta: {status, user_review_required: false}}]; });
    assert.equal(r.decision.action, 'stop', `${id} ${status}`);
    assert.ok(r.global_stops.some((s) => s.stop === stop && s.reason.includes(id)));
  }
  const missing = run((ctx) => { ctx.gate_queue = [{task: 'V-01a', packet: 'x.md', meta: null}]; });
  assert.equal(missing.status, 'refused');
});

test('outside-ranking shared contract is listed but not eligible', () => {
  const r = run(({registry}) => { registry.delivery_plan.outside_ranking = [{id: 'I-S6-01', reason: 'mandatory'}]; });
  assert.ok(cand(r, 'I-S6-01').blocked.some((b) => b.stop === 'outside_ranking'));
});

test('valid one-candidate result selects without a notice', () => {
  const r = run(({registry}) => {
    for (const id of ['I-S4-02', 'I-S7-01']) registry.nodes.find((n) => n.id === id).effort = 'XL';
  });
  assert.deepEqual(r.eligible, ['I-S6-01']);
  assert.equal(r.decision.action, 'select');
  assert.equal(r.decision.selected, 'I-S6-01');
  assert.equal(r.decision.notice, null);
  assert.equal(r.decision.user_review_required, true, 'checkpoint carried, never cleared');
});

const e = (id, score, gates = 0, effort = 'M') => ({id, score: {score}, open_gates_on_paths: gates, effort});
test('contest boundaries: tie, 5%, 10%', () => {
  // Exact tie: owner stop with tie-break recommendation (fewer gates wins).
  let d = nw.decide([e('B', 3, 2), e('A', 3, 1)]);
  assert.equal(d.action, 'stop_owner');
  assert.equal(d.recommendation, 'A');
  // gap exactly 5% stops for owner.
  d = nw.decide([e('A', 3), e('B', 2.85)]);
  assert.equal(d.action, 'stop_owner');
  // just above 5%: tie-break selection with notice (lower effort wins over higher score).
  d = nw.decide([e('A', 3, 0, 'L'), e('B', 2.84, 0, 'S')]);
  assert.equal(d.action, 'select');
  assert.equal(d.selected, 'B');
  assert.match(d.notice, /coordinator-handoff/);
  // exactly 10%: still the notice band.
  d = nw.decide([e('A', 3), e('B', 2.7)]);
  assert.ok(d.notice);
  assert.equal(d.selected, 'A', 'stable ID decides when gates and effort tie');
  // above 10%: top score, no notice.
  d = nw.decide([e('Z', 3), e('A', 2.69)]);
  assert.deepEqual([d.action, d.selected, d.notice], ['select', 'Z', null]);
  // scores below 1 use max(|top|,1) as the denominator.
  d = nw.decide([e('A', 0.5), e('B', 0.46)]);
  assert.equal(d.action, 'stop_owner');
  assert.equal(nw.decide([]).action, 'none');
});

test('task discovery reads ordered queue rows and packet metadata', () => {
  const readme = '| S1 Foundation | [S1-01](S1-01-x.md) | a | b | Merged |\n| S2 Evidence | [S2-01a](S2-01a-y.md) | a | b | Done |\nnot a row [S3-01](z.md)\n';
  assert.deepEqual(nw.parseQueue(readme), [{task: 'S1-01', packet: 'S1-01-x.md'}, {task: 'S2-01a', packet: 'S2-01a-y.md'}]);
  assert.deepEqual(nw.packetMeta('# T\n\nStatus: done (merged)\nUSER_REVIEW_REQUIRED: false\n'), {status: 'done (merged)', user_review_required: false});
  assert.equal(nw.packetPhase('implementation-ready packet; **not activated**'), 'not_started');
  assert.equal(nw.packetPhase('mystery'), 'unknown');
});

test('labeled packet links are discovered by target filename (B1)', () => {
  const readme = '| [V-01a Site/Foundation fidelity](V-01a-foundation-visual-fidelity.md) | x |\n| [V-01b Lab/Evidence fidelity](V-01b-evidence-lab-visual-fidelity.md) | x |\n[S2-02r](S2-02r-x.md) [docs](http://x/PRE-S3-09-x.md) [arch](../frontend/docs/architecture/notes.md)';
  assert.deepEqual(nw.parseGateQueue(readme).map((q) => q.task), ['V-01a', 'V-01b', 'S2-02r']);
});

test('open visual-gate status is not_started; only literal umbrella/index is exempt (B1, C1)', () => {
  assert.equal(nw.packetPhase('open W1 visual gate (L); activate after startup guards'), 'not_started');
  assert.equal(nw.packetPhase('opening soon'), 'unknown');
  assert.equal(nw.packetPhase('umbrella/index; not a scored gate'), 'not_started');
  assert.equal(nw.packetPhase('umbrella of active work'), 'unknown');
});

test('labeled V-01a/V-01b through discovery: open does not stop or refuse, active/in_review stops (B1)', () => {
  const gq = (st) => nw.parseGateQueue('[V-01a Site fidelity](V-01a-x.md) [V-01b Lab fidelity](V-01b-y.md)')
    .map((q) => ({...q, meta: {status: q.task === 'V-01a' ? st : 'open W1 visual gate (L)', user_review_required: true}}));
  const open = run((ctx) => { ctx.gate_queue = gq('open W1 visual gate (L); activate after startup guards'); });
  assert.notEqual(open.status, 'refused');
  assert.ok(!open.global_stops.some((s) => /V-01[ab]/.test(s.reason)));
  for (const [st, stop] of [['active', 'active_task'], ['in_review', 'review']]) {
    const r = run((ctx) => { ctx.gate_queue = gq(st); });
    assert.equal(r.decision.action, 'stop', st);
    assert.ok(r.global_stops.some((s) => s.stop === stop && s.reason.includes('V-01a')));
  }
});

// ---- Graph-pass fixtures (S4-04 / S5-02 / S6-03) against the real committed registry and tasks/README.md ----
const fs = require('node:fs');
const path = require('node:path');
const repo = path.resolve(__dirname, '../../..');
const realRegistry = JSON.parse(fs.readFileSync(path.join(__dirname, 'v69-dependency-registry-pilot.json'), 'utf8'));
const realNodes = new Map(realRegistry.nodes.map((n) => [n.id, n]));
const realReadme = fs.readFileSync(path.join(repo, 'tasks/README.md'), 'utf8');
const closure = (ids) => { // technical `requires` closure only; sequenced_after is ordering, not a path
  const seen = new Set(); const stack = [...ids];
  while (stack.length) { const id = stack.pop(); if (seen.has(id)) continue; seen.add(id); stack.push(...(realNodes.get(id)?.requires || [])); }
  return seen;
};
const panelsReaching = (nodeId) => realRegistry.delivery_plan.w1_panel_mapping
  .filter((p) => p.claim_portions.some((c) => closure(c.technical_requires).has(nodeId))).map((p) => p.key);
const portionReaching = (key, nodeId) => realRegistry.delivery_plan.w1_panel_mapping.find((p) => p.key === key)
  .claim_portions.map((c) => closure(c.technical_requires).has(nodeId));

test('real README links the new packets and the renamed S4-03; real packets are not_started (graph pass)', () => {
  const gq = nw.parseGateQueue(realReadme);
  for (const [task, file] of [['S4-03', 'S4-03-finding-evidence-history.md'], ['S4-04', 'S4-04-site-finding-index.md'],
    ['S5-02', 'S5-02-overview-finding-list.md'], ['S6-03', 'S6-03-site-work-list.md']]) {
    const found = gq.find((q) => q.task === task);
    assert.ok(found, `${task} discovered from tasks/README.md`);
    assert.equal(found.packet, file);
    assert.ok(fs.existsSync(path.join(repo, 'tasks', file)), `${file} exists`);
    const meta = nw.packetMeta(fs.readFileSync(path.join(repo, 'tasks', file), 'utf8'));
    assert.equal(nw.packetPhase(meta.status), 'not_started', `${task} status "${meta.status}"`);
  }
  assert.ok(!gq.some((q) => q.packet === 'S4-03-finding-evidence.md'), 'no stale pre-rename S4-03 link');
});

test('each of S4-03, S4-04, S5-02, S6-03 stops selection when active or in review (graph pass)', () => {
  const gq = nw.parseGateQueue(realReadme).filter((q) => ['S4-03', 'S4-04', 'S5-02', 'S6-03'].includes(q.task));
  assert.equal(gq.length, 4);
  for (const g of gq) for (const [status, stop] of [['active', 'active_task'], ['in_review', 'review']]) {
    const r = run((ctx) => { ctx.gate_queue = [{...g, meta: {status, user_review_required: true}}]; });
    assert.equal(r.decision.action, 'stop', `${g.task} ${status}`);
    assert.ok(r.global_stops.some((s) => s.stop === stop && s.reason.includes(g.task)), `${g.task} ${status} names the packet`);
  }
  const unknown = run((ctx) => { ctx.gate_queue = [{...gq[0], meta: {status: 'mystery', user_review_required: true}}]; });
  assert.equal(unknown.status, 'refused', 'unknown status refuses');
  const open = run((ctx) => { ctx.gate_queue = gq.map((g) => ({...g, meta: {status: 'implementation-ready packet; not activated', user_review_required: true}})); });
  assert.notEqual(open.status, 'refused');
  assert.ok(!open.global_stops.some((s) => /S4-0[34]|S5-02|S6-03/.test(s.reason)), 'not-started packets do not stop');
});

test('A-finding-index reaches the Site Finding list and both mini:3 variants, not Evidence/History or mini:1/2/4 (graph pass)', () => {
  const reach = panelsReaching('A-finding-index');
  assert.ok(reach.includes('sitefindings:1'));
  assert.ok(reach.includes('mini:3'));
  assert.deepEqual(portionReaching('mini:3', 'A-finding-index'), [true, true], 'empty and positive variants both gated');
  assert.deepEqual(portionReaching('sitefindings:1', 'A-finding-index'), [true, true]);
  for (const k of ['finding-evidence:1', 'finding-evidence:2', 'finding-history:1', 'mini:1', 'mini:2', 'mini:4']) assert.ok(!reach.includes(k), `${k} must not reach A-finding-index`);
  // Only I-S4-04 (and I-S5-02 for the Overview integration) own the index work.
  for (const k of ['sitefindings:1', 'mini:3']) assert.ok(panelsReaching('I-S4-04').includes(k));
  assert.ok(panelsReaching('I-S5-02').includes('mini:3'));
  assert.ok(!panelsReaching('I-S5-02').includes('sitefindings:1'));
});

test('S4-03 and S5-01 are technically closable while the Site index stays open (graph pass)', () => {
  for (const id of ['I-S4-03', 'I-S5-01']) {
    assert.ok(!closure([id]).has('A-finding-index'), `${id} does not require A-finding-index`);
    assert.ok(!closure([id]).has('I-S4-04'), `${id} does not require I-S4-04`);
  }
  assert.ok(closure(['I-S4-04']).has('I-S4-01'));
  assert.ok(closure(['I-S5-02']).has('I-S5-01') && closure(['I-S5-02']).has('I-S4-04'));
});

test('A-action-index reaches only sitework:1, via S6-03 (graph pass)', () => {
  assert.deepEqual(panelsReaching('A-action-index'), ['sitework:1']);
  assert.deepEqual(panelsReaching('I-S6-03'), ['sitework:1']);
  const realPanels = realRegistry.delivery_plan.w1_panel_mapping.map((p) => p.key);
  const actionish = realPanels.filter((k) => /^(action|recommendation|changes|verification|plan)/.test(k));
  assert.ok(actionish.length > 0, 'non-empty set of Action/Recommendation/Change/Verification panels');
  for (const k of actionish) assert.ok(!panelsReaching('A-action-index').includes(k), `${k} does not need A-action-index`);
  assert.ok(!closure(['I-S6-01']).has('A-action-index') && !closure(['I-S6-02']).has('A-action-index'));
});

test('S6 ordering: I-S6-01 requires I-S4-01; I-S6-02 follows S6-01 not S6-03 (graph pass)', () => {
  assert.ok(realNodes.get('I-S6-01').requires.includes('I-S4-01'));
  assert.ok(realNodes.get('I-S6-02').requires.includes('I-S6-01'));
  assert.ok(!closure(['I-S6-02']).has('I-S6-03'));
  assert.ok(realNodes.get('I-S6-03').requires.includes('I-S6-01'));
  assert.deepEqual(realNodes.get('I-S6-03').sequenced_after, ['I-S6-02'], 'S6-03 is queue-ordered after S6-02, not technically dependent');
  assert.ok(!closure(['I-S6-03']).has('I-S6-02'));
});
