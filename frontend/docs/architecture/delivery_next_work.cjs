// Delivery-plan validation and the deterministic `next-work` report (PRE-S3-03).
// Implements D-2026-10-09-owner-delivery-strategy "Selection within the active wave".
// Pure functions over already-loaded inputs, so fixtures can exercise every refusal;
// check_v69_dependency_registry.cjs supplies the real files.
const crypto = require('node:crypto');

const PORTION_STATES = ['delivered', 'open', 'unmapped', 'excluded'];
const VARIANTS = ['bounded', 'positive', 'unknown'];
const PANEL_STATUSES = ['gap', 'partial', 'real'];
const EFFORTS = {S: 1, M: 3, L: 5};
const EPS = 1e-9;

// ---- task discovery --------------------------------------------------------

// S1-S7 queue rows: `| S<n> ... | [S<n>-NN<x>](packet.md) | ... | status |`.
function parseQueue(readme) {
  return [...readme.matchAll(/^\|\s*S[1-7][^|]*\|\s*\[(S[1-7]-\d{2}[a-z]?)\]\(([^)]+)\)[^\n]*$/gm)]
    .map((m) => ({task: m[1], packet: m[2]}));
}

// Gate packets (PRE-S3-NN) are linked anywhere in tasks/README.md. They are not registry task nodes, but an
// active or in-review one stops selection (Architect Q7).
function parseGateQueue(readme) {
  const seen = new Map();
  for (const m of readme.matchAll(/\[(PRE-S\d-\d{2}[a-z]?)\]\(([^)]+\.md)\)/g)) if (!seen.has(m[1])) seen.set(m[1], {task: m[1], packet: m[2]});
  return [...seen.values()];
}

function packetMeta(text) {
  const status = (text.match(/^Status:\s*(.*)$/m) || [])[1];
  const review = (text.match(/^USER_REVIEW_REQUIRED:\s*(.*)$/m) || [])[1];
  return {status: status?.trim() ?? null, user_review_required: review ? !/^false\b/i.test(review.trim()) : null};
}

const packetPhase = (status) => {
  if (!status) return 'unknown';
  if (/^done\b/i.test(status)) return 'done';
  if (/^in_review\b/i.test(status)) return 'in_review';
  if (/^(active|in_progress|in progress)\b/i.test(status)) return 'active';
  if (/^(outline|executable|carry|implementation-ready|refined)/i.test(status) || /not activated/i.test(status)) return 'not_started';
  return 'unknown';
};

// ---- fingerprints ----------------------------------------------------------

// Line endings are normalised so a CRLF checkout and an LF working copy agree.
const sha = (text) => crypto.createHash('sha256').update(text.replace(/\r\n/g, '\n')).digest('hex').slice(0, 16);
function fingerprints(inputs) {
  // inputs: {registry, queue, packet_status, panel_contracts, manifest, owner_input} as raw strings
  return Object.fromEntries(Object.entries(inputs).map(([key, text]) => [key, sha(text)]));
}
function staleInputs(expected, actual) {
  return Object.keys({...expected, ...actual}).filter((key) => expected[key] !== actual[key]);
}

// ---- graph helpers ---------------------------------------------------------

function graph(registry) {
  const nodes = new Map(registry.nodes.map((node) => [node.id, node]));
  const memo = new Map();
  const ancestors = (id) => {
    if (memo.has(id)) return memo.get(id);
    const out = new Set();
    for (const dep of nodes.get(id)?.requires || []) {
      out.add(dep);
      for (const a of ancestors(dep)) out.add(a);
    }
    memo.set(id, out);
    return out;
  };
  const isOpen = (id) => nodes.get(id)?.status === 'open';
  // Open gates needed to close `ids`: the ids themselves and every open ancestor.
  const openClosure = (ids) => {
    const out = new Set();
    for (const id of ids) for (const x of [id, ...ancestors(id)]) if (isOpen(x)) out.add(x);
    return out;
  };
  return {nodes, ancestors, isOpen, openClosure};
}

// ---- mapping validation (structural; runs in the normal checker) -------------

// Returns typed errors; an empty list means the delivery mapping is well formed.
// Unreviewed rows are allowed here; ranking refuses them separately.
function validateMapping(registry, contracts) {
  const errors = [];
  const err = (type, key, reason) => errors.push({type, key, reason});
  const {nodes} = graph(registry);
  const plan = registry.delivery_plan;
  const visualGates = plan.visual_gates || {};
  // Fail closed (Architect C5 ruling): `enables` edges are not parsed or scored, so a non-empty list may not be silently ignored.
  if (plan.enables !== undefined && !(Array.isArray(plan.enables) && plan.enables.length === 0)) {
    err('unsupported_enables', 'delivery_plan.enables', 'non-empty enables edges are not supported by the next-work parser; keep the list empty until a reviewed parser, path rule and tests exist');
  }
  for (const [id, gate] of Object.entries(visualGates)) {
    if (nodes.has(id)) err('visual_gate', id, 'visual gate id collides with a technical node');
    if (!['open', 'accepted'].includes(gate.status)) err('visual_gate', id, 'status must be open or accepted');
    if (!Array.isArray(gate.requires) || gate.requires.some((dep) => !nodes.has(dep) || nodes.get(dep).kind === 'product')) {
      err('unknown_node', id, 'visual gate requires an unknown or product node');
    }
    if (gate.effort !== null && !['S', 'M', 'L', 'XL'].includes(gate.effort)) err('visual_gate', id, 'effort must be S/M/L/XL or null');
    if (gate.status === 'accepted' && !gate.evidence) err('visual_gate', id, 'accepted visual gate lacks evidence');
  }
  const titles = new Map(contracts.map((p) => [`${p.screen_id}:${p.panel_index}`, p.panel_title]));
  for (const row of plan.w1_panel_mapping) {
    if (!titles.has(row.key)) err('unknown_panel', row.key, 'not in panel contracts');
    if (!PANEL_STATUSES.includes(row.panel_status)) err('panel_status', row.key, `invalid panel_status ${row.panel_status}`);
    if (row.visual_gate != null && !visualGates[row.visual_gate]) err('unknown_node', row.key, `unknown visual gate ${row.visual_gate}`);
    const ids = new Set();
    for (const portion of row.claim_portions) {
      const where = `${row.key} ${portion.id || '(no id)'}`;
      if (!portion.id || !portion.id.startsWith(`${row.key}#`) || ids.has(portion.id)) err('portion_id', where, 'missing, foreign or duplicate portion id');
      ids.add(portion.id);
      if (!PORTION_STATES.includes(portion.state)) err('portion_state', where, `invalid state ${portion.state}`);
      if (!VARIANTS.includes(portion.variant)) err('portion_variant', where, `invalid variant ${portion.variant}`);
      if (typeof portion.core !== 'boolean') err('portion_core', where, 'core must be boolean');
      if (portion.core && portion.state === 'excluded') err('portion_core', where, 'a core portion cannot be excluded');
      for (const id of portion.technical_requires || []) {
        if (!nodes.has(id)) err('unknown_node', where, `technical_requires names unknown node ${id}`);
        else if (nodes.get(id).kind === 'product') err('unknown_node', where, `product node ${id} cannot be a technical gate`);
      }
      if (portion.state === 'delivered') {
        if (!Array.isArray(portion.delivered_by) || !portion.delivered_by.length) err('delivered_proof', where, 'delivered portion names no closeout');
        for (const id of portion.delivered_by || []) {
          if (!nodes.has(id) || nodes.get(id).status !== 'resolved') err('delivered_proof', where, `delivered_by ${id} is not a resolved node`);
        }
        if (!Array.isArray(portion.evidence) || !portion.evidence.length) err('delivered_proof', where, 'delivered portion cites no evidence');
        if ((portion.proposed_gates || []).length) err('delivered_proof', where, 'proposed IDs cannot prove delivery');
        if ((portion.technical_requires || []).some((id) => nodes.get(id)?.status === 'open')) err('delivered_proof', where, 'delivered portion still requires an open node');
      }
      if (portion.state === 'open') {
        if (!(portion.technical_requires || []).length) err('open_path', where, 'open portion has no technical path');
        if ((portion.proposed_gates || []).length) err('proposed_only', where, 'open portion still relies on proposed IDs');
      }
    }
    const live = row.claim_portions.filter((p) => p.state !== 'excluded');
    const delivered = live.filter((p) => p.state === 'delivered').length;
    const expected = delivered === 0 ? 'gap' : 'partial';
    if (row.panel_status === 'real') {
      if (delivered !== live.length || !row.visual_gate || visualGates[row.visual_gate]?.status !== 'accepted') {
        err('panel_status', row.key, 'real requires every portion delivered and visual acceptance recorded');
      }
    } else if (row.panel_status !== expected) err('panel_status', row.key, `panel_status ${row.panel_status} should be ${expected}`);
    if (row.reviewed_mapping) {
      const core = row.claim_portions.filter((p) => p.core);
      if (!core.length) err('reviewed_mapping', row.key, 'reviewed mapping has no core portion');
      for (const p of core) if (!['delivered', 'open'].includes(p.state)) {
        err('reviewed_mapping', row.key, `reviewed mapping has ${p.state} core portion ${p.id}`);
      }
      if (!row.mapping_review?.evidence) err('reviewed_mapping', row.key, 'reviewed mapping cites no review evidence');
    }
  }
  return errors;
}

// ---- next-work report ------------------------------------------------------

// ctx: {registry, contracts, briefs, queue: [{task, packet, meta}], fingerprints, expected_fingerprints?}
function nextWork(ctx) {
  const {registry, contracts, briefs, queue} = ctx;
  const plan = registry.delivery_plan;
  const wave = plan.active_wave;
  const refusals = [];
  const refuse = (type, reason) => refusals.push({type, reason});
  const g = graph(registry);

  // Staleness first: nothing computed from changed inputs is trusted.
  if (ctx.expected_fingerprints) {
    const stale = staleInputs(ctx.expected_fingerprints, ctx.fingerprints);
    if (stale.length) refuse('stale_input', `inputs changed since report generation: ${stale.join(', ')}; regenerate the report`);
  }

  // Owner input for the active wave.
  const owner = plan.owner_inputs?.[wave];
  const waveDef = plan.waves?.[wave];
  if (!owner || !Array.isArray(owner.approved_manifest_ids) || !owner.core_panels || !owner.demo_values || !owner.evidence) {
    refuse('missing_owner_input', `${wave}: owner approved IDs, core panels, demo values or evidence not recorded`);
  } else {
    if (!Number.isFinite(owner.k) || owner.k <= 0 || owner.k !== waveDef?.k) refuse('missing_owner_input', `${wave}: owner K missing or differs from wave K`);
    for (const screen of owner.approved_manifest_ids) {
      const value = owner.demo_values[screen];
      if (!Number.isInteger(value) || value < 1 || value > 5) refuse('missing_owner_input', `${screen}: owner demo value missing or outside 1-5`);
      if (!Array.isArray(owner.core_panels[screen]) || !owner.core_panels[screen].length) refuse('missing_owner_input', `${screen}: owner core panels missing`);
    }
  }

  // Structural mapping errors are typed refusals too.
  for (const e of validateMapping(registry, contracts)) refuse(e.type, `${e.key}: ${e.reason}`);

  // Queue: tasks discovered from tasks/README.md must match registry task nodes and packet phase.
  const registryTasks = registry.nodes.filter((n) => n.kind === 'implementation' && n.layer === 'task' && /^S[1-7]-/.test(n.task || ''));
  const queueTasks = queue.map((q) => q.task);
  if (!queueTasks.length || new Set(queueTasks).size !== queueTasks.length ||
      registryTasks.length !== queueTasks.length || registryTasks.some((n) => !queueTasks.includes(n.task))) {
    refuse('queue_mismatch', 'tasks/README.md rows and registry task nodes differ');
  }
  const taskInfo = new Map();
  for (const q of queue) {
    const node = g.nodes.get(`I-${q.task}`);
    const phase = packetPhase(q.meta?.status);
    taskInfo.set(q.task, {...q, phase});
    if (!q.meta || phase === 'unknown') refuse('queue_mismatch', `${q.task}: packet ${q.packet} missing or has an unrecognised Status`);
    else if (node && (node.status === 'resolved') !== (phase === 'done')) {
      refuse('queue_mismatch', `${q.task}: registry ${node.status} but packet Status "${q.meta.status}"`);
    }
  }

  // Approved core panels must have reviewed paths with no proposed/unmapped core portion.
  const rows = new Map(plan.w1_panel_mapping.map((row) => [row.key, row]));
  const approvedScreens = owner?.approved_manifest_ids || [];
  const corePanels = [];
  const unmapped = [];
  for (const screen of approvedScreens) for (const key of owner.core_panels?.[screen] || []) {
    const row = rows.get(key);
    if (!row) { refuse('unmapped_approved_panel', `${key}: approved core panel has no mapping row`); continue; }
    const badCore = row.claim_portions.filter((p) => p.core && !['delivered', 'open'].includes(p.state));
    if (!row.reviewed_mapping || badCore.length || !row.claim_portions.some((p) => p.core)) {
      unmapped.push(key);
      continue;
    }
    corePanels.push({key, screen, row});
  }
  if (unmapped.length) {
    refuse('unmapped_approved_panel', `${unmapped.length} approved core panel(s) lack a reviewed claim-portion path: ${unmapped.join(', ')}`);
  }

  const report = {
    schema: 'assetops.next-work.v1', wave, k: owner?.k ?? null, fingerprints: ctx.fingerprints,
    authority: 'Non-authoritative until mapped paths and scoring are independently reviewed; never clears USER_REVIEW_REQUIRED.',
  };
  if (refusals.length) return {...report, status: 'refused', refusals, decision: {action: 'none', reason: 'fail closed; no task selected'}};

  // ---- per-panel gate sets ----
  const screenArea = new Map(briefs.areas.flatMap((area) => area.primary_screens.map((s) => [s, area.id])));
  const visualGates = plan.visual_gates || {};
  const panels = corePanels.map(({key, screen, row}) => {
    const openCore = row.claim_portions.filter((p) => p.core && p.state === 'open');
    const needed = g.openClosure(openCore.flatMap((p) => p.technical_requires));
    const vGate = row.visual_gate && visualGates[row.visual_gate]?.status === 'open' ? row.visual_gate : null;
    return {key, screen, area: screenArea.get(screen), value: owner.demo_values[screen], needed, openCore, vGate,
      delivered: row.claim_portions.filter((p) => p.core && p.state === 'delivered').map((p) => p.id)};
  });
  for (const p of panels) if (p.openCore.length && !p.needed.size) {
    return {...report, status: 'refused', decision: {action: 'none', reason: 'fail closed'},
      refusals: [{type: 'open_path', reason: `${p.key}: open core portion has no open gate; record its closeout or fix the path`}]};
  }

  // ---- candidates ----
  const outside = new Map((plan.outside_ranking || []).map((x) => [x.id, x.reason]));
  const taskOf = (node) => node.task ? taskInfo.get(node.task) : null;
  const candidates = [];
  const technical = [...g.nodes.values()].filter((n) => n.kind !== 'product' && n.status === 'open');
  const visual = Object.entries(visualGates).filter(([, v]) => v.status === 'open')
    .map(([id, v]) => ({id, kind: 'visual', owner: v.owner, effort: v.effort, requires: v.requires, packet: v.packet, user_review_required: v.user_review_required, visual: true}));
  for (const c of [...technical, ...visual]) {
    const openUp = c.visual ? [...g.openClosure(c.requires)] : [...g.ancestors(c.id)].filter(g.isOpen);
    const upstream = new Set(openUp);
    const reach = new Map();
    for (const p of panels) {
      if (!c.visual && p.needed.has(c.id)) {
        const d = p.needed.size - 1;
        reach.set(p.key, {key: p.key, screen: p.screen, area: p.area, value: p.value, path: 'technical', d,
          proof: [...p.needed].filter((x) => x !== c.id).sort(), portions: p.openCore.map((x) => x.id),
          closure_unlock: [...p.needed].every((x) => x === c.id || upstream.has(x))});
      }
      if (c.visual && p.vGate === c.id) {
        // The panel is only ready once V-01's own prerequisites AND the panel's open technical gates are closed.
        const all = new Set([...upstream, ...p.needed]);
        const d = all.size;
        const prior = reach.get(p.key);
        if (!prior || d < prior.d) reach.set(p.key, {key: p.key, screen: p.screen, area: p.area, value: p.value, path: 'visual', d,
          proof: [...all].sort(), portions: [], closure_unlock: [...p.needed].every((x) => upstream.has(x))});
      }
    }
    const reached = [...reach.values()].sort((a, b) => a.key.localeCompare(b.key));
    const blocked = [];
    if (outside.has(c.id)) blocked.push({stop: 'outside_ranking', reason: outside.get(c.id)});
    if (openUp.length) blocked.push({stop: 'technical', reason: `open prerequisites: ${openUp.sort().join(', ')}`});
    if (c.owner === 'Owner') blocked.push({stop: 'owner', reason: 'owner-held decision'});
    const t = c.visual ? null : taskOf(c);
    if (t?.phase === 'in_review') blocked.push({stop: 'review', reason: `${t.task} awaits review`});
    if (t?.phase === 'active') blocked.push({stop: 'active_task', reason: `${t.task} already active`});
    if (!reached.length) blocked.push({stop: 'no_reviewed_path', reason: 'no reviewed path to an unfinished approved core portion or pending V-01 gate'});
    if (c.effort == null) blocked.push({stop: 'effort', reason: 'effort size unrecorded'});
    const entry = {id: c.id, kind: c.kind, effort: c.effort, task: c.task || null, visual: !!c.visual,
      ready_now: reached.filter((r) => r.d === 0).length,
      closure_unlock: reached.filter((r) => r.d > 0 && r.closure_unlock).length,
      panel_reach: reached.length,
      technical_reach: reached.filter((r) => r.path === 'technical').length,
      visual_reach: reached.filter((r) => r.path === 'visual').length,
      eligible_screens: [...new Set(reached.map((r) => r.screen))].sort(),
      open_gates_on_paths: [...new Set(reached.flatMap((r) => r.proof))].length,
      paths: reached, blocked};
    if (c.effort === 'XL') {
      entry.blocked.push({stop: 'xl', reason: 'XL has no autonomous score; split into S/M/L or request an owner exception'});
    } else if (reached.length && EFFORTS[c.effort]) {
      const B = reached.reduce((s, r) => s + 1 / (1 + r.d), 0);
      const P = 5 * (1 - Math.exp(-B / owner.k));
      const D = Math.max(...reached.map((r) => r.value));
      const R = Math.min(5, new Set(reached.map((r) => r.area)).size);
      const E = EFFORTS[c.effort];
      entry.score = {D, B: round(B), P: round(P), R, E, score: round(0.4 * D + 0.3 * P + 0.2 * R - 0.1 * E)};
    }
    if (reached.length || c.visual) candidates.push(entry);
  }
  const eligible = candidates.filter((c) => !c.blocked.length && c.score);
  eligible.sort(rankOrder);
  const gateInfo = (ctx.gate_queue || []).map((q) => ({...q, phase: packetPhase(q.meta?.status)}));
  for (const q of gateInfo) if (!q.meta || q.phase === 'unknown') refuse('queue_mismatch', `${q.task}: gate packet ${q.packet} missing or has an unrecognised Status`);
  const activeTasks = [...taskInfo.values(), ...gateInfo].filter((t) => ['active', 'in_review'].includes(t.phase));
  const globalStops = activeTasks.map((t) => ({stop: t.phase === 'active' ? 'active_task' : 'review',
    reason: `${t.task} is ${t.phase}; finish or review it before selecting new work`}));
  const decision = globalStops.length ? {action: 'stop', reason: globalStops.map((s) => s.reason).join('; ')} : decide(eligible);
  if (decision.selected) {
    const sel = eligible.find((c) => c.id === decision.selected);
    const t = sel.task ? taskInfo.get(sel.task) : null;
    decision.user_review_required = sel.visual ? visual.find((v) => v.id === sel.id)?.user_review_required ?? true : t?.meta?.user_review_required ?? null;
  }
  return {...report, status: 'ranked', global_stops: globalStops, decision,
    eligible: eligible.map((c) => c.id),
    candidates: candidates.sort((a, b) => (b.score?.score ?? -Infinity) - (a.score?.score ?? -Infinity) || a.id.localeCompare(b.id))};
}

const round = (x) => Math.round(x * 1000) / 1000;
function rankOrder(a, b) {
  return b.score.score - a.score.score || tieOrder(a, b);
}
// Published tie-break: fewer unresolved technical gates, lower effort, stable ID.
function tieOrder(a, b) {
  return a.open_gates_on_paths - b.open_gates_on_paths || EFFORTS[a.effort] - EFFORTS[b.effort] || a.id.localeCompare(b.id);
}

// eligible: sorted by rankOrder. Returns the selection decision with contest handling.
function decide(eligible) {
  if (!eligible.length) return {action: 'none', reason: 'no eligible candidate; see blocked reasons'};
  if (eligible.length === 1) return {action: 'select', selected: eligible[0].id, notice: null, reason: 'single eligible candidate'};
  const [top, second] = eligible;
  const gap = (top.score.score - second.score.score) / Math.max(Math.abs(top.score.score), 1);
  const facts = {top: top.id, top_score: top.score.score, second: second.id, second_score: second.score.score, gap: round(gap)};
  const byTie = [top, second].sort(tieOrder)[0];
  if (gap <= 0.05 + EPS) {
    return {action: 'stop_owner', ...facts, recommendation: byTie.id,
      reason: `contested ranking (gap ${(gap * 100).toFixed(2)}% <= 5%): owner chooses; tie-break recommends ${byTie.id}`};
  }
  if (gap <= 0.10 + EPS) {
    return {action: 'select', selected: byTie.id, ...facts,
      notice: `Ranking notice: ${top.id} ${top.score.score} vs ${second.id} ${second.score.score} (gap ${(gap * 100).toFixed(2)}%, within 5-10%); `
        + `selected ${byTie.id} by published tie-break (fewer unresolved technical gates, lower effort, stable ID). Record in .agent/coordinator-handoff.md.`,
      reason: 'gap within 5-10%: tie-break selection with owner notice'};
  }
  return {action: 'select', selected: top.id, ...facts, notice: null, reason: 'gap above 10%: top score'};
}

function formatReport(report) {
  const lines = [`next-work report (${report.schema}) wave ${report.wave} K=${report.k}: ${report.status}`];
  lines.push(`Authority: ${report.authority}`);
  lines.push(`Input fingerprints: ${Object.entries(report.fingerprints || {}).map(([k, v]) => `${k}=${v}`).join(' ')}`);
  if (report.status === 'refused') {
    lines.push('REFUSED (fail closed, no task selected):');
    for (const r of report.refusals) lines.push(`- [${r.type}] ${r.reason}`);
    return lines.join('\n');
  }
  for (const s of report.global_stops) lines.push(`STOP [${s.stop}] ${s.reason}`);
  lines.push('Candidates (id | effort | ready-now | closure-unlock | panels tech/visual | D P R E | score | blocked):');
  for (const c of report.candidates) {
    const s = c.score ? `${c.score.D} ${c.score.P} ${c.score.R} ${c.score.E} | ${c.score.score}` : '- | -';
    lines.push(`${c.id} | ${c.effort ?? '?'} | ${c.ready_now} | ${c.closure_unlock} | ${c.technical_reach}/${c.visual_reach} | ${s} | ${c.blocked.map((b) => `${b.stop}: ${b.reason}`).join('; ') || 'eligible'}`);
    for (const p of c.paths) lines.push(`    ${p.key} [${p.path}] d=${p.d}${p.proof.length ? ` after ${p.proof.join(' + ')}` : ''}${p.portions.length ? ` portions ${p.portions.join(',')}` : ''}`);
  }
  lines.push(`Decision: ${JSON.stringify(report.decision)}`);
  return lines.join('\n');
}

module.exports = {parseQueue, parseGateQueue, packetMeta, packetPhase, fingerprints, staleInputs, validateMapping, nextWork, decide, formatReport};
