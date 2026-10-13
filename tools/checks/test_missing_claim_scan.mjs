// Mutation fixtures for the G-01 missing-claim orphan scan. Run: node --test tools/checks/test_missing_claim_scan.mjs
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { analyze, MIRROR_PATH } from './missing-claim-scan.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const gap = (id, extra = {}) => ({ id, status: 'open', ui_placements: ['readiness.gateway.firmware'], evidence: {}, ...extra });
const mirrorText = (entries = { 'G-readiness-gateway-firmware': ['open', ['readiness.gateway.firmware']] }) =>
  `export const UI_GAP_CATALOGUE = {\n${Object.entries(entries).map(([id, [status, placements]]) =>
    `  "${id}": { status: "${status}", placements: [${placements.map((p) => `"${p}"`).join(', ')}] },`).join('\n')}\n} as const satisfies Record<string, unknown>;\n`;
const TAGGED = `import { MissingClaim } from "../ui";
export const FIRMWARE = "Firmware not available yet: no reviewed source.";
export function Panel() {
  return <MissingClaim as="p" gapId="G-readiness-gateway-firmware" placement="readiness.gateway.firmware">{FIRMWARE}</MissingClaim>;
}
`;
const LEGACY = `export function Legacy() {
  return <p>Not available yet: uptime trend.</p>;
}
`;
const baselineOf = (entries) => ({ dated: '2026-10-13', scope: 's', reason: 'r', entries, total: entries.reduce((s, e) => s + e.count, 0) });
const LEGACY_ENTRY = { file: 'frontend/src/sites/Legacy.tsx', text: 'Not available yet: uptime trend.', count: 1, reason: 'legacy' };

function world(mutate = () => {}) {
  const w = {
    files: [{ path: 'frontend/src/sites/Panel.tsx', text: TAGGED }, { path: 'frontend/src/sites/Legacy.tsx', text: LEGACY }],
    registry: { mock_gaps: { gaps: [gap('G-readiness-gateway-firmware')] } },
    mirror: { path: MIRROR_PATH, text: mirrorText() },
    baseline: baselineOf([LEGACY_ENTRY]),
    mainBaseline: baselineOf([LEGACY_ENTRY]),
    seedCeiling: 1,
  };
  mutate(w);
  return analyze(w);
}
const types = (r) => r.errors.map((e) => e.type);

test('the real repository passes the scan', () => {
  const out = execFileSync(process.execPath, [path.join(repoRoot, 'tools/checks/missing-claim-scan.mjs')], { encoding: 'utf8' });
  assert.match(out, /Missing-claim scan passed: [1-9]\d* tagged placement use/);
});

test('valid fixture passes; a const rendered only through MissingClaim is tagged', () => {
  const r = world();
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.usages.map((u) => u.gapId), ['G-readiness-gateway-firmware']);
  assert.deepEqual(r.untagged.map((u) => `${u.file}:${u.line}`), ['frontend/src/sites/Legacy.tsx:2']);
});

test('mutation: an unknown UI gap ID fails', () => {
  const r = world((w) => { w.files[0].text = TAGGED.replace('gapId="G-readiness-gateway-firmware"', 'gapId="G-readiness-gateway-uptime"'); });
  assert.ok(types(r).includes('ui_unknown_gap'));
  assert.ok(r.errors.some((e) => e.where === 'frontend/src/sites/Panel.tsx:4'));
});

test('mutation: an unknown placement or a non-literal gapId fails', () => {
  assert.ok(types(world((w) => { w.files[0].text = TAGGED.replace('placement="readiness.gateway.firmware"', 'placement="readiness.gateway.signal"'); })).includes('ui_unknown_placement'));
  assert.ok(types(world((w) => { w.files[0].text = TAGGED.replace('gapId="G-readiness-gateway-firmware"', 'gapId={id}'); })).includes('ui_usage'));
});

test('mutation: an unused open catalogue ID without unplaced_reason fails', () => {
  const r = world((w) => {
    w.registry.mock_gaps.gaps.push(gap('G-readiness-gateway-signal', { ui_placements: ['readiness.gateway.signal'] }));
    w.mirror.text = mirrorText({ 'G-readiness-gateway-firmware': ['open', ['readiness.gateway.firmware']],
      'G-readiness-gateway-signal': ['open', ['readiness.gateway.signal']] });
  });
  assert.deepEqual(types(r), ['unused_placement']);
  // With an unplaced_reason (no placements) the gap stays out of the mirror and nothing is required of the UI.
  const reasoned = world((w) => { w.registry.mock_gaps.gaps.push(gap('G-readiness-gateway-signal', { ui_placements: [], unplaced_reason: 'pending' })); });
  assert.deepEqual(reasoned.errors, []);
});

test('mutation: the UI mirror must equal the registry', () => {
  assert.ok(types(world((w) => { w.registry.mock_gaps.gaps = []; })).includes('mirror_unknown'));
  assert.ok(types(world((w) => { w.registry.mock_gaps.gaps.push(gap('G-readiness-gateway-signal', { ui_placements: ['readiness.gateway.signal'] })); })).includes('mirror_missing'));
  assert.ok(types(world((w) => { w.registry.mock_gaps.gaps[0].ui_placements = ['readiness.gateway.other']; })).includes('mirror_mismatch'));
  // A resolved gap appears only as a reviewed resolved_transition.
  assert.ok(types(world((w) => { w.registry.mock_gaps.gaps[0].status = 'resolved'; })).includes('mirror_unknown'));
  const transition = world((w) => {
    Object.assign(w.registry.mock_gaps.gaps[0], { status: 'resolved', evidence: { ui_transition: 't.md' } });
    w.mirror.text = mirrorText({ 'G-readiness-gateway-firmware': ['resolved_transition', ['readiness.gateway.firmware']] });
  });
  assert.deepEqual(transition.errors, []);
});

test('mutation: new untagged missing-capability copy fails with file:line', () => {
  const r = world((w) => {
    w.files.push({ path: 'frontend/src/sites/New.tsx', text: 'export const X = () => <span>{"Signal strength not yet available"}</span>;\n' });
  });
  assert.deepEqual(r.errors.map((e) => [e.type, e.where]), [['untagged_copy', 'frontend/src/sites/New.tsx:1']]);
  // The same const also rendered outside MissingClaim is untagged.
  const leaked = world((w) => { w.files[0].text = `${TAGGED}export const Leak = () => <p>{FIRMWARE}</p>;\n`; });
  assert.ok(leaked.errors.some((e) => e.type === 'untagged_copy' && e.where === 'frontend/src/sites/Panel.tsx:2'));
  // A second copy of a baselined legacy string is a count change, not a free pass.
  const dup = world((w) => { w.files[1].text = LEGACY + 'export const Again = () => <p>Not available yet: uptime trend.</p>;\n'; });
  assert.ok(types(dup).includes('baseline_count'));
});

test('mutation: a catalogued placement used twice fails, naming both locations', () => {
  const r = world((w) => { w.files.push({ path: 'frontend/src/sites/Other.tsx', text: TAGGED.replaceAll('FIRMWARE', 'OTHER') }); });
  const e = r.errors.find((x) => x.type === 'ui_duplicate_placement');
  assert.ok(e, 'duplicate use must be reported');
  assert.match(e.where, /\.tsx:\d+$/);
  assert.match(e.reason, /already used at frontend\/src\/sites\/\w+\.tsx:\d+/);
  assert.equal(r.errors.length, 1);
});

test('tests, test helpers and comments are outside the scan', () => {
  const r = world((w) => {
    w.files.push({ path: 'frontend/src/sites/Commented.tsx', text: '// Not available yet: this is a comment\nexport const Y = 1;\n' });
  });
  assert.deepEqual(r.errors, []);
});

test('mutation: legacy-baseline expansion fails', () => {
  const extra = { file: 'frontend/src/sites/Legacy.tsx', text: 'Not yet available: more.', count: 1, reason: 'legacy' };
  const grown = world((w) => {
    w.files[1].text = LEGACY + 'export const More = () => <p>Not yet available: more.</p>;\n';
    w.baseline = baselineOf([LEGACY_ENTRY, extra]);
    w.seedCeiling = 5;
  });
  assert.deepEqual(types(grown), ['baseline_growth'], 'a new entry absent from the main baseline is growth');
  const counted = world((w) => {
    w.files[1].text = LEGACY + 'export const Again = () => <p>Not available yet: uptime trend.</p>;\n';
    w.baseline = baselineOf([{ ...LEGACY_ENTRY, count: 2 }]);
    w.seedCeiling = 5;
  });
  assert.deepEqual(types(counted), ['baseline_growth'], 'a higher count than main is growth');
  const ceiling = world((w) => {
    w.files[1].text = LEGACY + 'export const More = () => <p>Not yet available: more.</p>;\n';
    w.baseline = baselineOf([LEGACY_ENTRY, extra]);
    w.mainBaseline = null;
  });
  assert.ok(types(ceiling).includes('baseline_growth'), 'the frozen seed ceiling holds without a main baseline');
});

test('the baseline must match exactly: stale entries and a wrong total fail; shrinking passes', () => {
  assert.ok(types(world((w) => { w.files[1].text = 'export const Gone = 1;\n'; })).includes('baseline_stale'));
  assert.ok(types(world((w) => { w.baseline.total = 3; })).includes('baseline_shape'));
  assert.ok(types(world((w) => { delete w.baseline.dated; })).includes('baseline_shape'));
  const shrunk = world((w) => { w.files[1].text = 'export const Gone = 1;\n'; w.baseline = baselineOf([]); });
  assert.deepEqual(shrunk.errors, []);
});
