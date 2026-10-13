// Mock-gap catalogue validation (G-01, D-2026-10-12-mock-gap-closure-mechanism sections 1-2).
// Pure: callers supply the parsed registry, panel contracts and (optionally) manifest screen IDs and ledger rows.
// check_v69_dependency_registry.cjs runs it with requirePresent: true; delivery_next_work.cjs nextWork runs it with
// requirePresent: false and never lets gaps touch candidates, scores, paths or the decision.

const GAP_ID_RE = /^G-[a-z0-9]+(-[a-z0-9]+)+$/;
const ELEMENT_RE = /^([a-z0-9-]+):(\d+)\.([a-z0-9-]+)$/;
const PLACEMENT_RE = /^[a-z0-9-]+(\.[a-z0-9-]+)+$/;
const MISSING_KINDS = ['decision', 'data_source', 'contract', 'build', 'visual'];
const STATUSES = ['open', 'resolved', 'owner_withheld'];
const SOURCE_STATUSES = ['existing', 'absent', 'undecided'];
const PENDING_ALLOCATION = 'pending owner review';
const FIELDS = ['id', 'screen_ids', 'panel_portion_ids', 'element_ids', 'claim', 'boundary', 'missing_kind', 'status',
  'target_wave', 'allocation', 'requires', 'source_status', 'ui_placements', 'unplaced_reason', 'owner_or_role',
  'evidence', 'review_trigger'];
const ARRAY_FIELDS = ['screen_ids', 'panel_portion_ids', 'element_ids', 'requires', 'ui_placements'];

const nonEmpty = (value) => typeof value === 'string' && value.trim().length > 0;
const strOrNull = (value) => value === null || nonEmpty(value);

// opts: {contracts, screenIds?, screenLedger?, requirePresent}
// Returns [{type, id, reason}]; empty means the catalogue and every gap_ids join are valid.
function validateMockGaps(registry, opts = {}) {
  const errors = [];
  const err = (type, id, reason) => errors.push({type, id, reason});
  const catalogue = registry.mock_gaps;
  const plan = registry.delivery_plan || {};
  const mapping = plan.w1_panel_mapping || [];
  const contracts = opts.contracts || [];

  let gaps = [];
  let enrolled = [];
  if (catalogue === undefined) {
    if (opts.requirePresent) err('catalogue', 'mock_gaps', 'mock_gaps catalogue is missing');
  } else if (!catalogue || typeof catalogue !== 'object' || Array.isArray(catalogue)) {
    err('catalogue', 'mock_gaps', 'mock_gaps must be an object');
  } else {
    if (catalogue.version !== 1) err('catalogue', 'mock_gaps', `unsupported catalogue version ${catalogue.version}`);
    if (!Array.isArray(catalogue.gaps)) err('catalogue', 'mock_gaps', 'gaps must be an array');
    else gaps = catalogue.gaps;
    if (!Array.isArray(catalogue.gap_enrolled_screens)) err('catalogue', 'mock_gaps', 'gap_enrolled_screens must be an array');
    else enrolled = catalogue.gap_enrolled_screens;
  }

  const nodes = new Map((registry.nodes || []).map((node) => [node.id, node]));
  const visualGateIds = new Set(Object.keys(plan.visual_gates || {}));
  const knownScreens = new Set(opts.screenIds ? [...opts.screenIds] : contracts.map((panel) => panel.screen_id));
  const knownPanels = new Set(contracts.map((panel) => `${panel.screen_id}:${panel.panel_index}`));
  const portions = new Map();
  for (const row of mapping) for (const portion of row.claim_portions || []) {
    portions.set(portion.id, {portion, screen: row.key.split(':')[0]});
  }
  const w1Screens = new Set(plan.waves?.W1?.manifest_ids || []);
  const waveKeys = new Set(Object.keys(plan.waves || {}));

  // ---- per-gap shape, identity and references ----
  const gapById = new Map();
  const placementOwner = new Map();
  for (const [index, gap] of gaps.entries()) {
    const label = typeof gap?.id === 'string' ? gap.id : `gaps[${index}]`;
    if (!gap || typeof gap !== 'object') { err('gap_shape', label, 'gap must be an object'); continue; }
    const missing = FIELDS.filter((field) => !(field in gap));
    if (missing.length) { err('gap_shape', label, `missing fields: ${missing.join(', ')}`); continue; }
    const badArrays = ARRAY_FIELDS.filter((field) => !Array.isArray(gap[field]));
    if (badArrays.length) { err('gap_shape', label, `not arrays: ${badArrays.join(', ')}`); continue; }
    if (!nonEmpty(gap.claim) || !nonEmpty(gap.owner_or_role) || !nonEmpty(gap.review_trigger)) {
      err('gap_shape', label, 'claim, owner_or_role and review_trigger must be non-empty strings');
    }
    const boundary = gap.boundary;
    if (!boundary || ['window', 'subject', 'source', 'cannot_mean'].some((key) => !nonEmpty(boundary[key]))) {
      err('gap_shape', label, 'boundary needs non-empty window, subject, source and cannot_mean');
    }
    const evidence = gap.evidence;
    if (!evidence || ['source', 'ui', 'visual', 'reviewed_by'].some((key) => !(key in evidence) || !strOrNull(evidence[key]))) {
      err('gap_shape', label, 'evidence needs source, ui, visual and reviewed_by (string or null)');
    }
    if (!strOrNull(gap.unplaced_reason)) err('gap_shape', label, 'unplaced_reason must be a non-empty string or null');

    // Identity.
    if (!GAP_ID_RE.test(gap.id)) err('gap_id', label, 'id must match G-<screen-or-shared>-<claim>');
    if (gapById.has(gap.id)) err('gap_duplicate', label, 'duplicate gap id');
    else gapById.set(gap.id, gap);
    if (nodes.has(gap.id) || visualGateIds.has(gap.id)) err('gap_duplicate', label, 'gap id collides with a registry node or visual gate');
    const screenIds = gap.screen_ids;
    if (!screenIds.length || new Set(screenIds).size !== screenIds.length) err('gap_reference', label, 'screen_ids must be non-empty and unique');
    const shared = typeof gap.id === 'string' && gap.id.startsWith('G-shared-');
    if (shared ? screenIds.length < 2 : !screenIds.some((screen) => gap.id.startsWith(`G-${screen}-`))) {
      err('gap_id', label, shared ? 'G-shared- needs at least two screens' : 'id prefix must be G-<one of screen_ids>- or G-shared-');
    }

    // References.
    for (const screen of screenIds) if (!knownScreens.has(screen)) err('gap_reference', label, `unknown screen ${screen}`);
    for (const portionId of gap.panel_portion_ids) {
      const found = portions.get(portionId);
      if (!found) err('gap_reference', label, `unknown panel portion ${portionId}`);
      else if (!screenIds.includes(found.screen)) err('gap_reference', label, `portion ${portionId} is not on a listed screen`);
    }
    for (const elementId of gap.element_ids) {
      const m = typeof elementId === 'string' && elementId.match(ELEMENT_RE);
      if (!m) err('gap_reference', label, `element ${elementId} must be <screen>:<panel>.<slug>`);
      else if (!screenIds.includes(m[1])) err('gap_reference', label, `element ${elementId} is not on a listed screen`);
      else if (!knownPanels.has(`${m[1]}:${m[2]}`)) err('gap_reference', label, `element ${elementId} names unknown panel ${m[1]}:${m[2]}`);
    }
    if (!gap.panel_portion_ids.length && !gap.element_ids.length) err('gap_reference', label, 'gap names no panel portion or element');

    // Enums.
    if (!MISSING_KINDS.includes(gap.missing_kind)) err('gap_enum', label, `invalid missing_kind ${gap.missing_kind}`);
    if (!STATUSES.includes(gap.status)) err('gap_enum', label, `invalid status ${gap.status}`);
    if (!SOURCE_STATUSES.includes(gap.source_status)) err('gap_enum', label, `invalid source_status ${gap.source_status}`);
    if (gap.target_wave !== 'unplanned' && !waveKeys.has(gap.target_wave)) err('gap_enum', label, `invalid target_wave ${gap.target_wave}`);

    // Combinations.
    const unplanned = gap.target_wave === 'unplanned';
    if (unplanned !== (gap.allocation === PENDING_ALLOCATION) || !nonEmpty(gap.allocation)) {
      err('gap_combination', label, unplanned ? `unplanned gap allocation must be "${PENDING_ALLOCATION}"`
        : 'a planned wave needs owner allocation evidence, not a pending allocation');
    }
    if (gap.status === 'resolved') {
      if (gap.source_status !== 'existing') err('gap_combination', label, 'resolved gap needs an existing source');
      if (unplanned) err('gap_combination', label, 'resolved gap cannot be unplanned');
      const lacking = ['source', 'ui', 'visual', 'reviewed_by'].filter((key) => !nonEmpty(evidence?.[key]));
      if (lacking.length) err('gap_combination', label, `resolved gap lacks reviewed evidence: ${lacking.join(', ')}`);
      if (gap.ui_placements.length && !nonEmpty(evidence?.ui_transition)) {
        err('gap_combination', label, 'resolved gap still placed in the UI needs evidence.ui_transition');
      }
    }
    if (gap.status === 'owner_withheld') {
      const decision = gap.owner_decision;
      if (!decision || ['evidence', 'reason', 'revisit_trigger'].some((key) => !nonEmpty(decision[key]))) {
        err('gap_combination', label, 'owner_withheld needs owner_decision evidence, reason and revisit_trigger');
      }
    }
    if (gap.status !== 'resolved' && gap.missing_kind === 'data_source' && gap.source_status === 'existing') {
      err('gap_combination', label, 'an unresolved data_source gap cannot claim an existing source');
    }

    // Placement.
    const placed = gap.ui_placements.length > 0;
    const reasoned = nonEmpty(gap.unplaced_reason);
    if (gap.status === 'open' && placed === reasoned) {
      err('gap_placement', label, placed ? 'open gap has both ui_placements and unplaced_reason' : 'open gap has neither ui_placements nor unplaced_reason');
    }
    for (const placement of gap.ui_placements) {
      if (typeof placement !== 'string' || !PLACEMENT_RE.test(placement)) { err('gap_placement', label, `invalid placement ${placement}`); continue; }
      const head = placement.split('.')[0];
      if (head !== 'shared' && !screenIds.includes(head)) err('gap_placement', label, `placement ${placement} does not start with a listed screen or shared`);
      if (placementOwner.has(placement)) err('gap_placement', label, `placement ${placement} already belongs to ${placementOwner.get(placement)}`);
      else placementOwner.set(placement, label);
    }
    if (reasoned && /not built/i.test(gap.unplaced_reason) && screenIds.some((screen) => w1Screens.has(screen))) {
      err('gap_placement', label, 'a W1 screen cannot use "not built" as unplaced_reason; name the real absence or pending placement');
    }
  }

  // ---- requires: known non-product nodes or gaps; resolved closure; no gap cycles ----
  for (const gap of gapById.values()) {
    for (const dep of gap.requires) {
      if (gapById.has(dep)) {
        if (gap.status === 'resolved' && gapById.get(dep).status !== 'resolved') err('gap_combination', gap.id, `resolved gap requires unresolved gap ${dep}`);
      } else if (!nodes.has(dep) || nodes.get(dep).kind === 'product') {
        err('gap_requires', gap.id, `requires unknown or product node ${dep}`);
      } else if (gap.status === 'resolved' && nodes.get(dep).status !== 'resolved') {
        err('gap_combination', gap.id, `resolved gap requires open node ${dep}`);
      }
    }
  }
  const state = new Map();
  const visit = (id, trail) => {
    if (state.get(id) === 'done') return;
    if (state.get(id) === 'active') { err('gap_cycle', id, `gap requires cycle: ${[...trail, id].join(' -> ')}`); return; }
    state.set(id, 'active');
    for (const dep of gapById.get(id).requires) if (gapById.has(dep)) visit(dep, [...trail, id]);
    state.set(id, 'done');
  };
  for (const id of gapById.keys()) visit(id, []);

  // ---- portion gap_ids joins ----
  for (const [portionId, {portion}] of portions) {
    if (portion.gap_ids === undefined) continue;
    if (!Array.isArray(portion.gap_ids)) { err('gap_join', portionId, 'gap_ids must be an array'); continue; }
    for (const gapId of portion.gap_ids) {
      if (!gapById.has(gapId)) err('gap_join', portionId, `unknown gap ${gapId}`);
      else if (!gapById.get(gapId).panel_portion_ids.includes(portionId)) err('gap_join', portionId, `${gapId} does not list this portion`);
    }
  }
  for (const gap of gapById.values()) for (const portionId of gap.panel_portion_ids) {
    const found = portions.get(portionId);
    if (found && !(found.portion.gap_ids || []).includes(gap.id)) err('gap_join', gap.id, `portion ${portionId} gap_ids does not list this gap`);
  }

  // ---- ledger gap_ids ----
  const ledger = opts.screenLedger ? new Map(opts.screenLedger.map((row) => [row.id, row])) : null;
  if (ledger) for (const row of ledger.values()) {
    if (row.gap_ids === undefined) continue;
    const expected = [...gapById.values()].filter((gap) => gap.screen_ids.includes(row.id)).map((gap) => gap.id).sort();
    if (!Array.isArray(row.gap_ids) || JSON.stringify([...row.gap_ids].sort()) !== JSON.stringify(expected)) {
      err('gap_ledger', row.id, `ledger gap_ids must equal the gaps listing this screen: [${expected.join(', ')}]`);
    }
  }

  // ---- enrolled screens: complete coverage ----
  for (const screen of enrolled) {
    if (!knownScreens.has(screen)) { err('gap_enrollment', screen, 'enrolled screen is unknown'); continue; }
    for (const [portionId, {portion, screen: portionScreen}] of portions) {
      if (portionScreen !== screen || portion.core || portion.state === 'delivered') continue;
      if (!Array.isArray(portion.gap_ids) || !portion.gap_ids.length) err('gap_enrollment', screen, `non-core ${portion.state} portion ${portionId} has no gap_ids`);
    }
    if (ledger && !Array.isArray(ledger.get(screen)?.gap_ids)) err('gap_enrollment', screen, 'enrolled screen ledger row has no gap_ids');
  }
  return errors;
}

// Informational summary for reports; never an input to scoring.
function summarizeMockGaps(registry) {
  const catalogue = registry.mock_gaps;
  const gaps = Array.isArray(catalogue?.gaps) ? catalogue.gaps : [];
  const byStatus = {};
  for (const gap of gaps) byStatus[gap.status] = (byStatus[gap.status] || 0) + 1;
  return {present: catalogue !== undefined, gaps: gaps.length, by_status: byStatus,
    enrolled_screens: Array.isArray(catalogue?.gap_enrolled_screens) ? [...catalogue.gap_enrolled_screens] : [],
    scoring: 'ignored for candidate scoring until an owner-approved W1-exit policy'};
}

module.exports = {validateMockGaps, summarizeMockGaps};
