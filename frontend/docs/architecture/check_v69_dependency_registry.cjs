// Validate the pilot dependency overlay against the existing mock panel inventory.
// Run from any directory: node frontend/docs/architecture/check_v69_dependency_registry.cjs
const fs = require('node:fs');
const path = require('node:path');

const here = __dirname;
const read = (name) => JSON.parse(fs.readFileSync(path.join(here, name), 'utf8'));
const registry = read('v69-dependency-registry-pilot.json');
const contracts = read('v69-panel-contracts.json').panels;
const screenLedger = read('v69-screen-ledger.json').screens;
const fail = (message) => { throw new Error(message); };

if (registry.schema !== 'assetops.v69.dependency-registry.pilot.v2') fail('Wrong schema');
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
    if (node.kind === 'implementation' && !['task', 'persistence', 'projection', 'ui'].includes(node.layer)) fail(`${node.id}: missing implementation layer`);
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
const expectedTasks = ['S1-01', 'S1-02', 'S2-01', 'S2-02', 'S3-01', 'S4-01', 'S4-02', 'S5-01', 'S6-01', 'S6-02', 'S7-01'];
for (const [index, task] of expectedTasks.entries()) {
  const node = nodes.get(`I-${task}`);
  if (!node || node.kind !== 'implementation' || node.layer !== 'task' || node.task !== task) {
    fail(`${task}: missing S1–S7 task gate`);
  }
  if (!node.requires.some((id) => nodes.get(id).kind === 'architecture')) fail(`${task}: no direct architecture gate`);
  const predecessor = index ? [`I-${expectedTasks[index - 1]}`] : [];
  if (JSON.stringify(node.sequenced_after || []) !== JSON.stringify(predecessor)) fail(`${task}: queue order differs from S1–S7 plan`);
}

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

const knownPanels = new Set(contracts.map((panel) => `${panel.screen_id}:${panel.panel_index}`));
const seenPanels = new Set();
const pilotScreens = new Set(registry.panels.map((panel) => panel.screen_id));
const screenAreas = new Map();
for (const panel of registry.panels) {
  if (screenAreas.has(panel.screen_id) && screenAreas.get(panel.screen_id) !== panel.area) fail(`${panel.screen_id}: panels span product areas`);
  screenAreas.set(panel.screen_id, panel.area);
}
const defaults = new Map();
const overrides = new Map();
for (const node of nodes.values()) if (node.kind === 'product') {
  if (node.scope === 'area') for (const area of node.governs_areas) {
    if (defaults.has(area)) fail(`${area}: multiple area defaults`);
    defaults.set(area, node.id);
  }
  if (node.scope === 'screens') for (const screen of node.governs) {
    if (!pilotScreens.has(screen) || overrides.has(screen) || screenAreas.get(screen) !== node.area) fail(`${screen}: invalid screen override`);
    overrides.set(screen, node.id);
  }
}
const governed = new Map();
for (const screen of pilotScreens) {
  const defaultId = defaults.get(screenAreas.get(screen));
  if (!defaultId) fail(`${screen}: no area product default`);
  governed.set(screen, overrides.get(screen) || defaultId);
}
for (const node of nodes.values()) if (node.kind === 'product' && node.status === 'recorded') {
  const effectiveScreens = [...governed].filter(([, id]) => id === node.id).map(([screen]) => screen);
  const allowed = new Set(effectiveScreens.flatMap((screen) => registry.panels
    .filter((panel) => panel.screen_id === screen).map((panel) => `${screen}:${panel.panel_index}`)));
  if (node.core_panels.some((key) => !allowed.has(key))) fail(`${node.id}: unknown core panel`);
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

const counts = {};
for (const area of areas) counts[area] = {architecture: 0, implementation: 0, data: 0, product: 0};
for (const node of nodes.values()) if (node.status === 'open' || node.status === 'pending owner') counts[node.area][node.kind]++;
console.log(`Pilot registry valid: ${nodes.size} nodes, ${seenPanels.size} linked panels`);
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
console.log('Newly promotable screens: 0; owner core-panel choices and priority ranking remain pending.');
const effortPoints = {S: 1, M: 3, L: 5};
const openForPanel = (panel) => [...new Set(panel.requires.flatMap((id) => [id, ...ancestors(id)]))]
  .filter((id) => nodes.get(id).status === 'open').sort();
const points = (ids) => ids.reduce((sum, id) => sum + effortPoints[nodes.get(id).effort], 0);
const detailed = process.argv.includes('--details');
console.log('Screen and panel readiness (unique open nodes; effort points S=1, M=3, L=5):');
for (const screen of pilotScreens) {
  const panels = registry.panels.filter((panel) => panel.screen_id === screen);
  const screenOpen = [...new Set(panels.flatMap(openForPanel))].sort();
  console.log(`${screen} | ${panels.length} panels | ${screenOpen.length} open | ${points(screenOpen)} points | ${governed.get(screen)}`);
  if (detailed) console.log(`  screen nodes: ${screenOpen.join(', ')}`);
  for (const panel of panels) {
    const open = openForPanel(panel);
    const title = contracts.find((row) => row.screen_id === screen && row.panel_index === panel.panel_index).panel_title;
    console.log(`  ${panel.panel_index} ${title} | ${open.length} open | ${points(open)} points`);
    if (detailed) console.log(`    nodes: ${open.join(', ')}`);
  }
}
