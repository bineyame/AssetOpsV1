// Validate the pilot dependency overlay against the existing mock panel inventory.
// Run from any directory: node frontend/docs/architecture/check_v69_dependency_registry.cjs
const fs = require('node:fs');
const path = require('node:path');

const here = __dirname;
const read = (name) => JSON.parse(fs.readFileSync(path.join(here, name), 'utf8'));
const registry = read('v69-dependency-registry-pilot.json');
const briefs = read('v69-subject-area-briefs.json');
const contracts = read('v69-panel-contracts.json').panels;
const screenLedger = read('v69-screen-ledger.json').screens;
const modelHomes = read('v69-model-homes.json').models;
const taskQueue = fs.readFileSync(path.resolve(here, '../../../tasks/README.md'), 'utf8');
const fail = (message) => { throw new Error(message); };
const delivery = require('./delivery_next_work.cjs');
const mockGaps = require('./mock_gaps.cjs');
const queueRows = delivery.parseQueue(taskQueue);
const gateRows = delivery.parseGateQueue(taskQueue);

if (registry.schema !== 'assetops.v69.dependency-registry.pilot.v3') fail('Wrong schema');
if (registry.s2_device_input_in_effect !== 'SIMULATED_ONLY' || !registry.physical_peer_gate?.includes('First real pilot')) {
  fail('S2 demo source choice or first-pilot physical gate missing');
}
if (registry.subject_area_briefs !== 'v69-subject-area-briefs.json') fail('Wrong subject-area brief reference');
if (briefs.schema !== 'assetops.v69.subject-area-briefs.v1') fail('Wrong subject-area brief schema');
for (const [task, gate] of [['S4-01', 'A-claim-work-routes'], ['S4-02', 'A-actor-identity']]) {
  const row = taskQueue.split(/\r?\n/).find((line) => line.startsWith(`| S4 Finding + Financials | [${task}]`));
  if (!row?.includes(gate)) fail(`${task}: pre-S4 Architect gate missing from task queue`);
}
if (!taskQueue.includes('S6-01 reuses both accepted contracts') || !taskQueue.includes('queue_baseline_nodes')) {
  fail('Task queue lacks cross-cutting gate reuse or baseline refinement rule');
}
for (const gate of ['A-lab-registered-basis', 'A-edge-batch-signature', 'A-edge-diagnostics', 'A-real-peer-source', 'A-demo-scenarios',
  'I-edge-fault-scenarios', 'I-sim-dispatch-cases', 'I-sim-verification-cases']) {
  if (!taskQueue.includes(gate)) fail(`Task queue lacks simulation/edge gate ${gate}`);
}
const areas = new Set(registry.areas.map((area) => area.id));
const nodes = new Map();
for (const node of registry.nodes) {
  if (nodes.has(node.id)) fail(`Duplicate node ${node.id}`);
  if (!areas.has(node.area)) fail(`${node.id}: unknown area`);
  if (!['architecture', 'implementation', 'data', 'product'].includes(node.kind)) fail(`${node.id}: invalid kind`);
  if (!Array.isArray(node.requires)) fail(`${node.id}: requires must be an array`);
  if (node.kind === 'product') {
    if (node.status !== 'pending owner' && node.status !== 'recorded') fail(`${node.id}: invalid product status`);
    if (!('target_tier' in node) || !('priority' in node) || !Array.isArray(node.core_panels)) fail(`${node.id}: incomplete product decision`);
    if (node.scope === 'area' && (!Array.isArray(node.governs_areas) || !node.governs_areas.length || node.governs_areas.some((area) => !areas.has(area)))) fail(`${node.id}: invalid area default`);
    if (node.scope === 'screens' && (!Array.isArray(node.governs) || !node.governs.length)) fail(`${node.id}: invalid screen override`);
    if (!['area', 'screens'].includes(node.scope)) fail(`${node.id}: invalid product scope`);
    if (node.requires.length) fail(`${node.id}: product choice cannot satisfy a dependency`);
    if (node.status === 'recorded' &&
        (!['Real', 'Real with honest gaps', 'Deferred', 'Dropped'].includes(node.target_tier) ||
         !node.priority || !node.evidence)) fail(`${node.id}: recorded choice lacks tier, priority or evidence`);
  } else {
    if (!['open', 'resolved'].includes(node.status)) fail(`${node.id}: invalid status`);
    if (!['S', 'M', 'L'].includes(node.effort)) fail(`${node.id}: missing effort size`);
    if (node.status === 'resolved' && !node.evidence) fail(`${node.id}: resolved without evidence`);
    if (node.kind === 'implementation' && !['task', 'persistence', 'projection', 'ui', 'edge', 'producer', 'ingestion'].includes(node.layer)) fail(`${node.id}: missing implementation layer`);
  }
  nodes.set(node.id, node);
}

const visiting = new Set();
const visited = new Set();
function visit(id) {
  if (visiting.has(id)) fail(`Dependency cycle at ${id}`);
  if (visited.has(id)) return;
  const node = nodes.get(id);
  if (!node) fail(`Unknown node ${id}`);
  visiting.add(id);
  for (const dependency of node.requires) {
    if (!nodes.has(dependency)) fail(`${id}: unknown dependency ${dependency}`);
    if (nodes.get(dependency).kind === 'product') fail(`${id}: product node used as prerequisite`);
    visit(dependency);
  }
  visiting.delete(id);
  visited.add(id);
}
for (const id of nodes.keys()) visit(id);
for (const [id, prerequisites] of [
  ['I-S2-01a', ['I-lab-registered-basis']],
  ['I-S2-01b', ['I-S2-01a', 'I-edge-outbox', 'I-edge-simulated-adapter']],
  ['I-S2-01c', ['I-S2-01b', 'I-edge-diagnostics-publish', 'I-edge-fault-scenarios']],
  ['I-S2-02', ['I-S2-01c', 'I-accepted-evidence-store', 'I-edge-diagnostics-store']],
  ['I-S3-01', ['I-sim-dispatch-cases']],
  ['D-verification-window', ['I-sim-verification-cases']],
  ['I-S7-01', ['I-edge-diagnostics-store', 'D-edge-health-cases']],
  ['D-cold-domain', ['I-cold-world', 'D-cold-physical-peer']],
  ['D-cold-physical-peer', ['I-cold-device-adapter']],
  ['D-ev-domain', ['I-ev-world', 'D-ev-physical-peer']],
  ['D-ev-physical-peer', ['I-ev-device-adapter']]
]) {
  if (prerequisites.some((dependency) => !nodes.get(id)?.requires.includes(dependency))) {
    fail(`${id}: missing simulation/edge technical prerequisite`);
  }
}
const queueVisiting = new Set();
const queueVisited = new Set();
function visitQueue(id) {
  if (queueVisiting.has(id)) fail(`Combined technical/queue cycle at ${id}`);
  if (queueVisited.has(id)) return;
  const node = nodes.get(id);
  if (node.sequenced_after !== undefined && !Array.isArray(node.sequenced_after)) fail(`${id}: sequenced_after must be an array`);
  queueVisiting.add(id);
  for (const dependency of [...node.requires, ...(node.sequenced_after || [])]) {
    if (!nodes.has(dependency) || nodes.get(dependency).kind === 'product') fail(`${id}: invalid queue dependency ${dependency}`);
    visitQueue(dependency);
  }
  queueVisiting.delete(id);
  queueVisited.add(id);
}
for (const id of nodes.keys()) visitQueue(id);
const expectedTasks = queueRows.map((row) => row.task);
const registryTasks = registry.nodes.filter((node) => node.kind === 'implementation' && node.layer === 'task' && /^S[1-7]-/.test(node.task || '')).map((node) => node.task);
if (!expectedTasks.length || new Set(expectedTasks).size !== expectedTasks.length ||
    expectedTasks.length !== registryTasks.length || expectedTasks.some((task) => !registryTasks.includes(task)) ||
    expectedTasks[0] !== 'S1-01' || expectedTasks.at(-1) !== 'S7-01' ||
    queueRows.some((row) => !fs.existsSync(path.resolve(here, '../../../tasks', row.packet)))) {
  fail('Task queue rows, packets and registry task sequence differ');
}
for (const [index, task] of expectedTasks.entries()) {
  const node = nodes.get(`I-${task}`);
  if (!node || node.kind !== 'implementation' || node.layer !== 'task' || node.task !== task) {
    fail(`${task}: missing S1–S7 task gate`);
  }
  if (!node.requires.some((id) => nodes.get(id).kind === 'architecture')) fail(`${task}: no direct architecture gate`);
  const predecessor = index && !['S6-01', 'S7-01'].includes(task) ? [`I-${expectedTasks[index - 1]}`] : [];
  if (JSON.stringify(node.sequenced_after || []) !== JSON.stringify(predecessor)) fail(`${task}: queue order differs from S1–S7 plan`);
}
for (const node of nodes.values()) if (node.kind === 'implementation' && node.layer !== 'task' && expectedTasks.includes(node.task)) {
  if (node.status !== nodes.get(`I-${node.task}`).status) fail(`${node.id}: layered capability and ${node.task} must resolve together`);
}
for (const [layer, ids] of Object.entries({
  producer: ['I-lab-registered-basis', 'I-edge-fault-scenarios', 'I-sim-dispatch-cases', 'I-sim-verification-cases', 'I-sim-battery-cases', 'I-cold-world', 'I-ev-world'],
  edge: ['I-edge-outbox', 'I-edge-simulated-adapter', 'I-edge-batch-sign', 'I-edge-physical-adapter', 'I-edge-diagnostics-publish', 'I-cold-device-adapter', 'I-ev-device-adapter'],
  ingestion: ['I-batch-signature-verify']
})) for (const id of ids) if (nodes.get(id)?.layer !== layer) fail(`${id}: wrong simulation/edge layer`);

function ancestors(id, result = new Set()) {
  for (const dependency of nodes.get(id).requires) {
    if (!result.has(dependency)) {
      result.add(dependency);
      ancestors(dependency, result);
    }
  }
  return result;
}
for (const node of nodes.values()) {
  if (['implementation', 'data'].includes(node.kind) &&
      ![...ancestors(node.id)].some((id) => nodes.get(id).kind === 'architecture')) {
    fail(`${node.id}: ${node.kind} has no architecture prerequisite`);
  }
  if (node.kind === 'data' && !node.requires.some((id) => nodes.get(id).kind === 'implementation' && nodes.get(id).layer === 'persistence')) {
    fail(`${node.id}: data must depend directly on persistence`);
  }
  if (node.kind === 'data' && !node.requires.some((id) => nodes.get(id).kind === 'architecture')) {
    fail(`${node.id}: data must depend directly on its governing architecture`);
  }
}
if (!Array.isArray(registry.queue_baseline_nodes) ||
    new Set(registry.queue_baseline_nodes).size !== registry.queue_baseline_nodes.length) fail('Invalid queue baseline');
const queueBaseline = new Set(registry.queue_baseline_nodes);
for (const id of ['I-edge-batch-sign', 'I-batch-signature-verify', 'I-edge-physical-adapter', 'I-sim-battery-cases']) {
  if (queueBaseline.has(id) || nodes.get(id)?.task !== null) fail(`${id}: deferred capability is not in S1–S7 queue`);
}
for (const id of queueBaseline) {
  if (!nodes.has(id) || nodes.get(id).kind === 'product') fail(`${id}: invalid queue baseline node`);
  for (const dependency of ancestors(id)) {
    if (nodes.get(dependency).status === 'open' && !queueBaseline.has(dependency)) {
      fail(`${id}: queue baseline omits open technical prerequisite ${dependency}`);
    }
  }
}
for (const task of expectedTasks) if (!queueBaseline.has(`I-${task}`)) fail(`${task}: missing from queue baseline`);
for (const node of nodes.values()) if (node.kind === 'implementation' && expectedTasks.includes(node.task) && !queueBaseline.has(node.id)) {
  fail(`${node.id}: queue-owned implementation missing from baseline`);
}

// Subject-area briefs assign every manifest model and screen exactly one primary home.
const briefAreas = new Set([...areas].filter((area) => area !== 'platform'));
if (briefs.areas.length !== briefAreas.size || new Set(briefs.areas.map((area) => area.id)).size !== briefAreas.size ||
    briefs.areas.some((area) => !briefAreas.has(area.id))) fail('Subject-area brief IDs differ from registry areas');
const enablingAreas = briefs.areas.filter((area) => area.role === 'cross-cutting enabler');
if (enablingAreas.length !== 1 || enablingAreas[0].id !== 'simulation-edge' ||
    enablingAreas[0].models_owned.length || enablingAreas[0].primary_screens.length) {
  fail('Simulation-edge must be the sole non-product enabling area and own no manifest models/screens');
}
const exactCoverage = (expected, actual, label) => {
  if (actual.length !== new Set(actual).size || expected.length !== actual.length ||
      expected.some((id) => !actual.includes(id))) fail(`${label}: incomplete or duplicate primary coverage`);
};
exactCoverage(modelHomes.map((model) => model.model), briefs.areas.flatMap((area) => area.models_owned), 'Models');
exactCoverage(screenLedger.map((screen) => screen.id), briefs.areas.flatMap((area) => area.primary_screens), 'Screens');
const modelByName = new Map(modelHomes.map((model) => [model.model, model]));
for (const area of briefs.areas) {
  if (!area.question || !area.fixture_gate || !area.owner_choice ||
      !(area.owner_priority === null || typeof area.owner_priority === 'string')) fail(`${area.id}: incomplete brief`);
  for (const [field, kind] of [['decision_nodes', 'architecture'], ['projection_nodes', 'architecture'],
    ['implementation_nodes', 'implementation'], ['fixture_nodes', 'data']]) {
    if (!Array.isArray(area[field]) || !area[field].length || area[field].some((id) => nodes.get(id)?.kind !== kind)) {
      fail(`${area.id}: invalid ${field}`);
    }
  }
  if (area.projection_contracts.some((name) => !modelByName.has(name))) fail(`${area.id}: unknown projection model`);
  if (area.role === 'cross-cutting enabler') {
    if (!Array.isArray(area.consuming_screens) || !area.consuming_screens.length ||
        area.consuming_screens.some((id) => !screenLedger.some((row) => row.id === id))) {
      fail(`${area.id}: invalid consuming screens`);
    }
    if ([...nodes.values()].some((node) => node.kind === 'product' &&
        (node.area === area.id || node.governs_areas?.includes(area.id)))) {
      fail(`${area.id}: enabling area cannot own a product tier`);
    }
  } else {
    const productDefault = [...nodes.values()].filter((node) => node.kind === 'product' && node.scope === 'area' &&
      node.governs_areas.includes(area.id));
    if (productDefault.length !== 1) fail(`${area.id}: missing or duplicate area product default`);
  }
}

const knownPanels = new Set(contracts.map((panel) => `${panel.screen_id}:${panel.panel_index}`));
const plan = registry.delivery_plan;
if (plan?.version !== 1 || !plan.waves || !Array.isArray(plan.w1_panel_mapping)) fail('Missing versioned delivery plan');
const manifestIds = new Set(screenLedger.map((row) => row.id));
const waveIds = Object.values(plan.waves).flatMap((wave) => wave.manifest_ids || []);
if (waveIds.length !== manifestIds.size || new Set(waveIds).size !== waveIds.length ||
    waveIds.some((id) => !manifestIds.has(id))) fail('Delivery waves do not allocate every manifest screen exactly once');
const w1Ids = new Set(plan.waves.W1?.manifest_ids || []);
const w1Keys = new Set(contracts.filter((panel) => w1Ids.has(panel.screen_id)).map((panel) => `${panel.screen_id}:${panel.panel_index}`));
const mappedKeys = plan.w1_panel_mapping.map((row) => row.key);
if (mappedKeys.length !== w1Keys.size || new Set(mappedKeys).size !== mappedKeys.length ||
    mappedKeys.some((key) => !w1Keys.has(key)) ||
    plan.w1_panel_mapping.some((row) => !Array.isArray(row.claim_portions) || !row.claim_portions.length ||
      row.title !== contracts.find((panel) => `${panel.screen_id}:${panel.panel_index}` === row.key)?.panel_title)) {
  fail('W1 panel mapping differs from panel contracts');
}
const ownerW1 = plan.owner_inputs?.W1;
if (plan.active_wave === 'W1') {
  const movedW1 = ['sitefindings', 'finding-history', 'action-plan', 'action-execution', 'action-evidence', 'action-history'];
  if (w1Ids.size !== 27 || plan.waves.W4?.manifest_ids?.length !== 9 || w1Keys.size !== 64 ||
      movedW1.some((id) => !w1Ids.has(id) || plan.waves.W4.manifest_ids.includes(id)) ||
      plan.waves.W1.k !== 10 || !plan.waves.W1.owner_start?.evidence ||
      JSON.stringify(ownerW1?.approved_manifest_ids) !== JSON.stringify(plan.waves.W1.manifest_ids) ||
      ownerW1?.k !== 10 || ownerW1.evidence !== plan.waves.W1.owner_start.evidence ||
      Object.keys(ownerW1.core_panels || {}).length !== w1Ids.size ||
      Object.keys(ownerW1.demo_values || {}).length !== w1Ids.size) fail('Recorded W1 owner input or revised allocation incomplete');
  for (const screen of w1Ids) {
    const core = ownerW1.core_panels[screen];
    const value = ownerW1.demo_values[screen];
    if (!Array.isArray(core) || !core.length || core.some((key) => !w1Keys.has(key) || !key.startsWith(`${screen}:`)) ||
        !Number.isInteger(value) || value < 1 || value > 5) fail(`${screen}: invalid approved W1 core or demo value`);
  }
}
// Delivery mapping structure (claim-portion states, delivered proof, visual gates) is
// validated on every run; ranking refusals for unreviewed rows apply only to --next-work.
const mappingErrors = delivery.validateMapping(registry, contracts);
if (mappingErrors.length) fail(`Delivery mapping invalid:\n${mappingErrors.map((e) => `- [${e.type}] ${e.key}: ${e.reason}`).join('\n')}`);
// Mock-gap catalogue (G-01): every present gap ID, portion/ledger gap_ids join and placement is validated;
// complete coverage is required only for mock_gaps.gap_enrolled_screens.
const gapErrors = mockGaps.validateMockGaps(registry, {contracts, screenIds: screenLedger.map((row) => row.id), screenLedger, requirePresent: true});
if (gapErrors.length) fail(`Mock-gap catalogue invalid:\n${gapErrors.map((e) => `- [${e.type}] ${e.id}: ${e.reason}`).join('\n')}`);
for (const [id, gate] of Object.entries(plan.visual_gates || {})) {
  const row = taskQueue.split(/\r?\n/).find((line) => line.startsWith('|') && line.includes(`(${gate.packet})`));
  if (!row || !fs.existsSync(path.resolve(here, '../../../tasks', gate.packet)) ||
      gate.manifest_ids.some((screen) => !row.includes(`\`${screen}\``) || !w1Ids.has(screen))) {
    fail(`${id}: visual gate packet/manifest IDs differ from tasks/README.md or the active wave`);
  }
  for (const row of plan.w1_panel_mapping) {
    if ((row.visual_gate === id) !== gate.manifest_ids.includes(row.key.split(':')[0])) fail(`${row.key}: visual gate ${id} assignment differs from its manifest IDs`);
  }
}
for (const entry of plan.outside_ranking || []) {
  if (!nodes.has(entry.id) || !entry.reason) fail(`outside_ranking ${entry.id}: unknown node or missing reason`);
}
const seenPanels = new Set();
const pilotScreens = new Set(registry.panels.map((panel) => panel.screen_id));
const screenAreas = new Map(briefs.areas.flatMap((area) => area.primary_screens.map((screen) => [screen, area.id])));
for (const panel of registry.panels) {
  if (screenAreas.get(panel.screen_id) !== panel.area) fail(`${panel.screen_id}: panel area differs from primary brief`);
}
const defaults = new Map();
const overrides = new Map();
for (const node of nodes.values()) if (node.kind === 'product') {
  if (node.scope === 'area') for (const area of node.governs_areas) {
    if (defaults.has(area)) fail(`${area}: multiple area defaults`);
    defaults.set(area, node.id);
  }
  if (node.scope === 'screens') for (const screen of node.governs) {
    if (!screenAreas.has(screen) || overrides.has(screen) || (screenAreas.get(screen) !== node.area && !node.cross_area)) fail(`${screen}: invalid screen override`);
    overrides.set(screen, node.id);
  }
}
const governed = new Map();
for (const [screen, area] of screenAreas) {
  const defaultId = defaults.get(area);
  if (!defaultId) fail(`${screen}: no area product default`);
  governed.set(screen, overrides.get(screen) || defaultId);
}
for (const node of nodes.values()) if (node.kind === 'product' && node.status === 'recorded') {
  const effectiveScreens = [...governed].filter(([, id]) => id === node.id).map(([screen]) => screen);
  const allowed = new Set(effectiveScreens.flatMap((screen) => plan.w1_panel_mapping
    .filter((panel) => panel.key.startsWith(`${screen}:`)).map((panel) => panel.key)));
  if (node.core_panels.some((key) => !allowed.has(key))) fail(`${node.id}: unknown core panel`);
  if (node.priority === 'W1' && (effectiveScreens.length !== 1 ||
      JSON.stringify(node.core_panels) !== JSON.stringify(ownerW1?.core_panels?.[effectiveScreens[0]]) ||
      node.demo_value !== ownerW1?.demo_values?.[effectiveScreens[0]] ||
      node.evidence !== ownerW1.evidence)) fail(`${node.id}: differs from recorded owner W1 input`);
  if (node.target_tier === 'Real with honest gaps' && effectiveScreens.some((screen) =>
    !node.core_panels.some((key) => key.startsWith(`${screen}:`)))) {
    fail(`${node.id}: Real with honest gaps requires core panels for every governed screen`);
  }
}
for (const screen of pilotScreens) {
  const expected = contracts.filter((panel) => panel.screen_id === screen).length;
  const actual = registry.panels.filter((panel) => panel.screen_id === screen).length;
  if (expected !== actual) fail(`${screen}: only ${actual}/${expected} panels mapped`);
  const ledgerRow = screenLedger.find((row) => row.id === screen);
  const productId = governed.get(screen);
  const expectedNodes = [...new Set(registry.panels.filter((panel) => panel.screen_id === screen)
    .flatMap((panel) => panel.requires))];
  if (!ledgerRow || ledgerRow.registry_dependencies?.product_node_id !== productId ||
      JSON.stringify(ledgerRow.registry_dependencies?.node_ids) !== JSON.stringify(expectedNodes)) {
    fail(`${screen}: ledger and registry node IDs diverge`);
  }
}
for (const row of screenLedger) if (row.registry_dependencies && !pilotScreens.has(row.id)) {
  fail(`${row.id}: registry link has no pilot panels`);
}
for (const panel of registry.panels) {
  const key = `${panel.screen_id}:${panel.panel_index}`;
  if (!knownPanels.has(key) || seenPanels.has(key)) fail(`${key}: unknown or duplicate panel`);
  seenPanels.add(key);
  if (!areas.has(panel.area)) fail(`${key}: unknown area`);
  if (!['real', 'withheld', 'gap'].includes(panel.status)) fail(`${key}: invalid panel status`);
  if (!panel.requires.length || !panel.reason) fail(`${key}: incomplete gate`);
  for (const id of panel.requires) {
    if (!nodes.has(id) || nodes.get(id).kind === 'product') fail(`${key}: invalid prerequisite ${id}`);
  }
  const layers = panel.requires.map((id) => nodes.get(id).layer);
  if (!layers.includes('ui') || !layers.includes('projection')) fail(`${key}: missing UI or projection gate`);
  if (!panel.structural && !panel.requires.some((id) => nodes.get(id).kind === 'data')) fail(`${key}: claim panel lacks data gate`);
  if (panel.status === 'real' && panel.requires.some((id) =>
    nodes.get(id).status !== 'resolved' || [...ancestors(id)].some((ancestor) => nodes.get(ancestor).status !== 'resolved'))) {
    fail(`${key}: real panel has an open prerequisite`);
  }
  if (panel.status === 'withheld' && !panel.owner_approval) fail(`${key}: withheld needs owner approval evidence`);
}

const nextWorkMode = process.argv.includes('--next-work') || process.argv.includes('--verify-report');
if (!nextWorkMode) {
const counts = {};
for (const area of areas) counts[area] = {architecture: 0, implementation: 0, data: 0, product: 0};
for (const node of nodes.values()) if (node.status === 'open' || node.status === 'pending owner') counts[node.area][node.kind]++;
console.log(`Registry valid: ${nodes.size} nodes, ${seenPanels.size} linked pilot panels`);
console.log(`Panel gate coverage: ${seenPanels.size}/${contracts.length}; ${contracts.length - seenPanels.size} require subject-area wave refinement before readiness scoring`);
console.log(`Area briefs valid: ${briefs.areas.length - enablingAreas.length} product areas + ${enablingAreas.length} cross-cutting enabler, ${modelHomes.length} primary models, ${screenLedger.length} primary screens`);
const overrideChoices = [...nodes.values()].filter((node) => node.kind === 'product' && node.scope === 'screens').length;
const pendingChoices = [...nodes.values()].filter((node) => node.kind === 'product' && node.status === 'pending owner').length;
console.log(`Owner choice coverage: ${governed.size} screens, ${defaults.size} area defaults, ${overrideChoices} exception choices covering ${overrides.size} screens; ${pendingChoices} choices pending owner`);
console.log('Area coverage (area | models | primary screens | screens touched | deferred touched | total panels | mapped pilot panels):');
for (const area of briefs.areas) {
  const touched = new Set(area.role === 'cross-cutting enabler' ? area.consuming_screens :
    area.models_owned.flatMap((name) => modelByName.get(name).manifest_screens));
  const deferred = [...touched].filter((id) => screenLedger.find((row) => row.id === id).proposed_fidelity_tier === 'Deferred');
  const totalPanels = contracts.filter((panel) => screenAreas.get(panel.screen_id) === area.id).length;
  console.log(`${area.id} | ${area.models_owned.length} | ${area.primary_screens.length} | ${touched.size} | ${deferred.length} | ${totalPanels} | ${registry.panels.filter((panel) => panel.area === area.id).length}`);
}
console.log('Open nodes by area and kind:', JSON.stringify(counts));
const facts = [];
for (const node of nodes.values()) {
  if (node.kind === 'product' || node.status !== 'open') continue;
  const closure = new Set([node.id, ...ancestors(node.id)]);
  const reached = registry.panels.filter((panel) => panel.requires.some((id) =>
    id === node.id || ancestors(id).has(node.id)));
  const closureUnlocked = reached.filter((panel) => panel.status !== 'real' &&
    panel.requires.every((id) => nodes.get(id).status === 'resolved' || closure.has(id)) &&
    panel.requires.some((id) => id === node.id || ancestors(id).has(node.id)));
  const readyNow = reached.filter((panel) => panel.status !== 'real' &&
    [...new Set(panel.requires.flatMap((id) => [id, ...ancestors(id)]))]
      .filter((id) => nodes.get(id).status === 'open').every((id) => id === node.id));
  facts.push({id: node.id, ready_now: readyNow.length, closure_unlock: closureUnlocked.length,
    pilot_panel_reach: reached.length, pilot_area_reach: new Set(reached.map((panel) => panel.area)).size,
    open_upstream: [...ancestors(node.id)].filter((id) =>
      nodes.get(id).status === 'open').length, effort: node.effort});
}
if (process.argv.includes('--json')) {
  console.log('Pilot leverage facts:', JSON.stringify(facts));
} else {
  const byReach = [...facts].sort((a, b) => b.pilot_panel_reach - a.pilot_panel_reach ||
    a.open_upstream - b.open_upstream || a.id.localeCompare(b.id));
  console.log('Unweighted reach sample (node | ready now | closure unlock | panels | areas | open upstream | effort):');
  for (const fact of byReach.slice(0, 12)) console.log(
    `${fact.id} | ${fact.ready_now} | ${fact.closure_unlock} | ${fact.pilot_panel_reach} | ${fact.pilot_area_reach} | ${fact.open_upstream} | ${fact.effort}`);
}
console.log(`Newly promotable screens: 0; W1 owner target ${plan.active_wave === 'W1' ? 'recorded' : 'pending'}; priority ranking awaits reviewed claim paths and PRE-S3-03.`);
const effortPoints = {S: 1, M: 3, L: 5};
const openForPanel = (panel) => [...new Set(panel.requires.flatMap((id) => [id, ...ancestors(id)]))]
  .filter((id) => nodes.get(id).status === 'open').sort();
const points = (ids) => ids.reduce((sum, id) => sum + effortPoints[nodes.get(id).effort], 0);
const marginal = (ids) => ids.filter((id) => !queueBaseline.has(id));
const detailed = process.argv.includes('--details');
console.log('Screen and panel readiness (unique open nodes; effort points S=1, M=3, L=5; marginal excludes queue baseline):');
for (const screen of pilotScreens) {
  const panels = registry.panels.filter((panel) => panel.screen_id === screen);
  const screenOpen = [...new Set(panels.flatMap(openForPanel))].sort();
  console.log(`${screen} | ${panels.length} ${panels.length === 1 ? 'panel' : 'panels'} | ${screenOpen.length} open / ${points(screenOpen)} total | ${marginal(screenOpen).length} marginal / ${points(marginal(screenOpen))} points | ${governed.get(screen)}`);
  if (detailed) {
    console.log(`  screen nodes: ${screenOpen.join(', ')}`);
    console.log(`  marginal nodes: ${marginal(screenOpen).join(', ') || '(none)'}`);
  }
  for (const panel of panels) {
    const open = openForPanel(panel);
    const title = contracts.find((row) => row.screen_id === screen && row.panel_index === panel.panel_index).panel_title;
    console.log(`  ${panel.panel_index} ${title} | ${open.length} open / ${points(open)} total | ${marginal(open).length} marginal / ${points(marginal(open))} points`);
    if (detailed) console.log(`    nodes: ${open.join(', ')}`);
  }
}
}

// ---- next-work report (PRE-S3-03) ----
// --next-work [--json] [--out <file>]: validate everything above, then publish the report.
// --verify-report <file>: refuse (exit 3) when any input changed since that report was generated.
if (nextWorkMode) {
  const root = path.resolve(here, '../../..');
  const readText = (rel) => fs.readFileSync(path.resolve(root, rel), 'utf8');
  const packets = [...queueRows, ...gateRows, ...Object.values(plan.visual_gates || {}).map((gate) => ({task: null, packet: gate.packet}))];
  const packetText = (packet) => { try { return readText(path.join('tasks', packet)); } catch { return null; } };
  const ownerEvidence = plan.owner_inputs?.[plan.active_wave]?.evidence;
  const currentPrints = delivery.fingerprints({
    registry: readText('frontend/docs/architecture/v69-dependency-registry-pilot.json'),
    queue: taskQueue,
    packet_status: packets.map((p) => {
      const text = packetText(p.packet);
      return `${p.packet}|${text === null ? 'MISSING' : JSON.stringify(delivery.packetMeta(text))}`;
    }).join('\n'),
    panel_contracts: readText('frontend/docs/architecture/v69-panel-contracts.json'),
    manifest: readText('frontend/mockups/v69/screen-manifest.json'),
    owner_input: JSON.stringify(plan.owner_inputs || null) + (ownerEvidence ? readText(path.join('frontend/docs/architecture', ownerEvidence)) : 'NO-EVIDENCE'),
  });
  const verifyIndex = process.argv.indexOf('--verify-report');
  let expected;
  if (verifyIndex > 0) expected = JSON.parse(fs.readFileSync(process.argv[verifyIndex + 1], 'utf8')).fingerprints;
  const report = delivery.nextWork({registry, contracts, briefs, fingerprints: currentPrints, expected_fingerprints: expected,
    queue: queueRows.map((row) => {
      const text = packetText(row.packet);
      return {...row, meta: text === null ? null : delivery.packetMeta(text)};
    }),
    gate_queue: gateRows.map((row) => {
      const text = packetText(row.packet);
      return {...row, meta: text === null ? null : delivery.packetMeta(text)};
    })});
  const outIndex = process.argv.indexOf('--out');
  if (outIndex > 0) fs.writeFileSync(process.argv[outIndex + 1], JSON.stringify(report, null, 2) + '\n');
  console.log(process.argv.includes('--json') ? JSON.stringify(report, null, 2) : delivery.formatReport(report));
  if (report.status === 'refused') process.exitCode = 3;
}
