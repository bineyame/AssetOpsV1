// PIPE-1 A6: the live honest-gap catalogue check, blocking on its own.
// The v69 dependency-registry guard (check_v69_dependency_registry.cjs, retired in declutter step 5 to
// archive/frontend/docs/architecture/) was advisory since PIPE-1 because the v69
// pilot registry and the S1-S7 queue it also checks are retired plumbing (owner O2; speed-up evaluation G5). The one
// piece of it that still protects honesty is this call: the "not available yet" copy and the missing-claim scan read
// the mock_gaps catalogue, so every gap ID, portion/ledger gap_ids join and placement must stay valid.
// Run from any directory: node frontend/docs/architecture/check_mock_gaps.cjs
const fs = require('node:fs');
const path = require('node:path');
const {validateMockGaps, summarizeMockGaps} = require('./mock_gaps.cjs');

const read = (name) => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
const registry = read('v69-dependency-registry-pilot.json');
const contracts = read('v69-panel-contracts.json').panels;
const screenLedger = read('v69-screen-ledger.json').screens;

// The same call, with the same inputs, as the retired check_v69_dependency_registry.cjs made.
const errors = validateMockGaps(registry, {contracts, screenIds: screenLedger.map((row) => row.id), screenLedger, requirePresent: true});
if (errors.length) {
  console.error(`Mock-gap catalogue invalid:\n${errors.map((e) => `- [${e.type}] ${e.id}: ${e.reason}`).join('\n')}`);
  process.exit(1);
}
const summary = summarizeMockGaps(registry);
console.log(`Mock-gap catalogue valid: ${JSON.stringify(summary)}`);
