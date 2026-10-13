// Fixtures for the G-01 mock-gap catalogue validator. Run: node --test frontend/docs/architecture/test_mock_gaps.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {validateMockGaps, summarizeMockGaps} = require('./mock_gaps.cjs');

const gap = (id, extra = {}) => ({id, screen_ids: ['readiness'], panel_portion_ids: [], element_ids: ['readiness:2.firmware'],
  claim: 'c', boundary: {window: 'w', subject: 's', source: 'none', cannot_mean: 'n'}, missing_kind: 'data_source',
  status: 'open', target_wave: 'unplanned', allocation: 'pending owner review', requires: [], source_status: 'absent',
  ui_placements: [`readiness.${id.slice('G-readiness-'.length)}`], unplaced_reason: null, owner_or_role: 'Owner',
  evidence: {source: null, ui: null, visual: null, reviewed_by: null}, review_trigger: 't', ...extra});

function world(gaps = [gap('G-readiness-firmware')], extra = {}) {
  const registry = {
    nodes: [
      {id: 'A-root', kind: 'architecture', status: 'resolved', requires: []},
      {id: 'I-open', kind: 'implementation', status: 'open', requires: []},
      {id: 'P-readiness', kind: 'product', status: 'open', requires: []},
    ],
    delivery_plan: {
      waves: {W1: {manifest_ids: ['readiness', 'sld']}, W2: {manifest_ids: ['other']}},
      visual_gates: {'V-01': {}},
      w1_panel_mapping: [
        {key: 'readiness:2', claim_portions: [{id: 'readiness:2#a', core: false, state: 'open'}, {id: 'readiness:2#b', core: true, state: 'open'}]},
        {key: 'sld:1', claim_portions: [{id: 'sld:1#a', core: false, state: 'delivered'}]},
      ],
    },
    mock_gaps: {version: 1, gap_enrolled_screens: [], gaps},
    ...extra,
  };
  const contracts = [['readiness', 1], ['readiness', 2], ['sld', 1], ['other', 1]].map(([screen_id, panel_index]) => ({screen_id, panel_index}));
  const screenLedger = [{id: 'readiness'}, {id: 'sld'}, {id: 'other'}];
  return {registry, opts: {contracts, screenLedger, screenIds: screenLedger.map((r) => r.id), requirePresent: true}};
}
const errorsOf = (mutate) => { const w = world(); mutate(w); return validateMockGaps(w.registry, w.opts); };
const hasError = (errors, type, pattern) => errors.some((e) => e.type === type && pattern.test(e.reason));

test('the real registry catalogue and ledger joins are valid', () => {
  const read = (name) => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
  const registry = read('v69-dependency-registry-pilot.json');
  const screenLedger = read('v69-screen-ledger.json').screens;
  const errors = validateMockGaps(registry, {contracts: read('v69-panel-contracts.json').panels, screenLedger,
    screenIds: screenLedger.map((r) => r.id), requirePresent: true});
  assert.deepEqual(errors, []);
  const firmware = registry.mock_gaps.gaps.find((g) => g.id === 'G-readiness-gateway-firmware');
  assert.deepEqual(firmware.ui_placements, ['readiness.gateway.firmware']);
  assert.equal(firmware.status, 'open');
  assert.equal(firmware.source_status, 'absent');
  assert.deepEqual(registry.mock_gaps.gap_enrolled_screens, [], 'G-01 enrolls no screen; G-02 enrolls the V-01a four');
  assert.deepEqual(screenLedger.find((r) => r.id === 'readiness').gap_ids, ['G-readiness-gateway-firmware']);
});

test('valid fixture passes; absent catalogue is an error only when required', () => {
  assert.deepEqual(errorsOf(() => {}), []);
  const w = world();
  delete w.registry.mock_gaps;
  assert.ok(hasError(validateMockGaps(w.registry, w.opts), 'catalogue', /missing/));
  assert.deepEqual(validateMockGaps(w.registry, {...w.opts, requirePresent: false}), []);
  assert.equal(summarizeMockGaps(w.registry).present, false);
});

test('catalogue version and shape', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.version = 2; }), 'catalogue', /version/));
  assert.ok(hasError(errorsOf((w) => { delete w.registry.mock_gaps.gaps[0].review_trigger; }), 'gap_shape', /review_trigger/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].boundary.cannot_mean = ''; }), 'gap_shape', /boundary/));
});

test('duplicate, malformed, colliding and wrongly prefixed IDs are rejected', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps.push(gap('G-readiness-firmware', {ui_placements: ['readiness.other']})); }), 'gap_duplicate', /duplicate/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].id = 'G-Readiness_Firmware'; }), 'gap_id', /must match/));
  assert.ok(hasError(errorsOf((w) => { w.registry.nodes.push({id: 'G-readiness-firmware', kind: 'data', status: 'open', requires: []}); }), 'gap_duplicate', /collides/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].id = 'G-sld-firmware'; }), 'gap_id', /prefix/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].id = 'G-shared-firmware'; w.registry.mock_gaps.gaps[0].ui_placements = ['shared.firmware']; }), 'gap_id', /at least two/));
});

test('unknown screen, portion and element references are rejected', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].screen_ids.push('nowhere'); }), 'gap_reference', /unknown screen nowhere/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].panel_portion_ids = ['readiness:9#z']; }), 'gap_reference', /unknown panel portion/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].panel_portion_ids = ['sld:1#a']; }), 'gap_reference', /not on a listed screen/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].element_ids = ['readiness:7.firmware']; }), 'gap_reference', /unknown panel/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].element_ids = ['readiness-firmware']; }), 'gap_reference', /must be/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].element_ids = []; }), 'gap_reference', /no panel portion or element/));
});

test('enum and wave/status/source combinations are enforced', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].missing_kind = 'vibes'; }), 'gap_enum', /missing_kind/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].status = 'closed'; }), 'gap_enum', /status/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].target_wave = 'W9'; }), 'gap_enum', /target_wave/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].allocation = 'later'; }), 'gap_combination', /pending owner review/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].target_wave = 'W2'; }), 'gap_combination', /owner allocation evidence/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].source_status = 'existing'; }), 'gap_combination', /cannot claim an existing source/));
});

test('resolved gaps need an existing source, a planned wave and reviewed source, UI and visual evidence', () => {
  const errors = errorsOf((w) => { Object.assign(w.registry.mock_gaps.gaps[0], {status: 'resolved'}); });
  assert.ok(hasError(errors, 'gap_combination', /existing source/));
  assert.ok(hasError(errors, 'gap_combination', /cannot be unplanned/));
  assert.ok(hasError(errors, 'gap_combination', /lacks reviewed evidence: source, ui, visual, reviewed_by/));
  assert.ok(hasError(errors, 'gap_combination', /ui_transition/));
  const resolved = errorsOf((w) => {
    Object.assign(w.registry.mock_gaps.gaps[0], {status: 'resolved', source_status: 'existing', target_wave: 'W1', allocation: 'owner.md',
      requires: ['A-root'], evidence: {source: 's.md', ui: 'u.md', visual: 'v.md', reviewed_by: 'r.md', ui_transition: 't.md'}});
  });
  assert.deepEqual(resolved, []);
  assert.ok(hasError(errorsOf((w) => {
    Object.assign(w.registry.mock_gaps.gaps[0], {status: 'resolved', source_status: 'existing', target_wave: 'W1', allocation: 'owner.md',
      requires: ['I-open'], evidence: {source: 's.md', ui: 'u.md', visual: 'v.md', reviewed_by: 'r.md', ui_transition: 't.md'}});
  }), 'gap_combination', /requires open node I-open/));
});

test('owner_withheld needs a recorded owner decision and revisit trigger', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].status = 'owner_withheld'; }), 'gap_combination', /owner_decision/));
  assert.deepEqual(errorsOf((w) => {
    Object.assign(w.registry.mock_gaps.gaps[0], {status: 'owner_withheld', owner_decision: {evidence: 'o.md', reason: 'r', revisit_trigger: 't'}});
  }), []);
});

test('requires must be known non-product nodes or gaps, with no gap cycles', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].requires = ['I-missing']; }), 'gap_requires', /unknown or product node I-missing/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].requires = ['P-readiness']; }), 'gap_requires', /product node/));
  assert.ok(hasError(errorsOf((w) => {
    w.registry.mock_gaps.gaps = [gap('G-readiness-a', {requires: ['G-readiness-b']}), gap('G-readiness-b', {requires: ['G-readiness-a']})];
  }), 'gap_cycle', /cycle/));
});

test('open gaps need exactly one of a placement or an unplaced reason; built W1 screens cannot say "not built"', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].ui_placements = []; }), 'gap_placement', /neither/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].unplaced_reason = 'Pending'; }), 'gap_placement', /both/));
  assert.ok(hasError(errorsOf((w) => { Object.assign(w.registry.mock_gaps.gaps[0], {ui_placements: [], unplaced_reason: 'Screen not built until W5'}); }), 'gap_placement', /not built/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].ui_placements = ['sld.firmware']; }), 'gap_placement', /listed screen/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].ui_placements = ['Readiness Firmware']; }), 'gap_placement', /invalid placement/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps.push(gap('G-readiness-other', {ui_placements: ['readiness.firmware']})); }), 'gap_placement', /already belongs/));
});

test('portion gap_ids must be known and joined in both directions', () => {
  assert.ok(hasError(errorsOf((w) => { w.registry.delivery_plan.w1_panel_mapping[0].claim_portions[0].gap_ids = ['G-readiness-nope']; }), 'gap_join', /unknown gap/));
  assert.ok(hasError(errorsOf((w) => { w.registry.delivery_plan.w1_panel_mapping[0].claim_portions[0].gap_ids = ['G-readiness-firmware']; }), 'gap_join', /does not list this portion/));
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gaps[0].panel_portion_ids = ['readiness:2#a']; }), 'gap_join', /does not list this gap/));
  assert.deepEqual(errorsOf((w) => {
    w.registry.mock_gaps.gaps[0].panel_portion_ids = ['readiness:2#a'];
    w.registry.delivery_plan.w1_panel_mapping[0].claim_portions[0].gap_ids = ['G-readiness-firmware'];
  }), []);
});

test('ledger gap_ids must equal exactly the gaps listing that screen', () => {
  assert.deepEqual(errorsOf((w) => { w.opts.screenLedger[0].gap_ids = ['G-readiness-firmware']; }), []);
  assert.ok(hasError(errorsOf((w) => { w.opts.screenLedger[0].gap_ids = []; }), 'gap_ledger', /must equal/));
  assert.ok(hasError(errorsOf((w) => { w.opts.screenLedger[1].gap_ids = ['G-readiness-firmware']; }), 'gap_ledger', /must equal/));
});

test('enrolled screens need gap_ids on every non-core undelivered portion and on their ledger row', () => {
  const errors = errorsOf((w) => { w.registry.mock_gaps.gap_enrolled_screens = ['readiness']; });
  assert.ok(hasError(errors, 'gap_enrollment', /readiness:2#a has no gap_ids/));
  assert.ok(!errors.some((e) => /readiness:2#b/.test(e.reason)), 'core portions are not enrolled coverage');
  assert.ok(hasError(errors, 'gap_enrollment', /ledger row/));
  assert.deepEqual(errorsOf((w) => { w.registry.mock_gaps.gap_enrolled_screens = ['sld']; w.opts.screenLedger[1].gap_ids = []; }), [],
    'a delivered non-core portion needs no gap');
  assert.ok(hasError(errorsOf((w) => { w.registry.mock_gaps.gap_enrolled_screens = ['nowhere']; }), 'gap_enrollment', /unknown/));
});
