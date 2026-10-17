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

// ---- G-02 carries: C7 reviewed cues and C1 visible merge-base skip ----

const withCopy = (jsx) => (w) => { w.files.push({ path: 'frontend/src/sites/New.tsx', text: `export function New() {\n  return ${jsx};\n}\n` }); };

test('C7 mutation: new untagged "not tracked yet" copy fails with file:line', () => {
  const r = world(withCopy('<p>Setup progress not tracked yet.</p>'));
  assert.ok(r.errors.some((e) => e.type === 'untagged_copy' && e.where === 'frontend/src/sites/New.tsx:2'), JSON.stringify(r.errors));
});

test('C7 mutation: new untagged commissioning-confirmation copy fails, also through an unwrapped const', () => {
  const direct = world(withCopy('<li>Commissioning confirmation not recorded</li>'));
  assert.ok(direct.errors.some((e) => e.type === 'untagged_copy' && e.where === 'frontend/src/sites/New.tsx:2'));
  const viaConst = world((w) => {
    w.files.push({ path: 'frontend/src/sites/New.tsx', text: 'export const C = "Commissioning confirmation not recorded";\nexport function New() {\n  return <li>{C}</li>;\n}\n' });
  });
  assert.ok(viaConst.errors.some((e) => e.type === 'untagged_copy' && e.where === 'frontend/src/sites/New.tsx:1'));
});

test('C7: the new cues pass when rendered through MissingClaim', () => {
  const r = world((w) => {
    w.files[0].text = TAGGED.replace('{FIRMWARE}', 'Setup progress not tracked yet. Commissioning confirmation not recorded.').replace(/^export const FIRMWARE.*$/m, '');
  });
  assert.deepEqual(r.errors.filter((e) => e.type === 'untagged_copy'), []);
});

test('C7: generic runtime copy stays outside the phrase set', () => {
  for (const copy of ['<p>Not recorded</p>', '<p>Gateway contact unavailable</p>', '<p>No results</p>', '<p>Reading not recorded for this hour</p>']) {
    const r = world(withCopy(copy));
    assert.deepEqual(r.errors, [], copy);
  }
});

test('C1: a failed merge-base makes the skip visible and leaves only the seed ceiling', async () => {
  const { mergeBaseBaseline, baselineComparisonNote } = await import('./missing-claim-scan.mjs');
  const failing = mergeBaseBaseline(() => { throw new Error('fatal: Not a valid object name main'); });
  assert.equal(failing.baseline, null);
  assert.match(failing.skipped, /merge-base HEAD main failed.*Not a valid object name main/);
  assert.match(baselineComparisonNote(failing, 16), /comparison SKIPPED .*only the seed ceiling 16 limits growth/);

  const noFile = mergeBaseBaseline((args) => {
    if (args[0] === 'show') throw new Error("fatal: path 'tools/checks/missing-claim-baseline.json' does not exist");
    return 'abc1234567890';
  });
  assert.equal(noFile.baseline, null);
  assert.match(baselineComparisonNote(noFile, 16), /SKIPPED \(no readable tools\/checks\/missing-claim-baseline\.json at merge-base abc1234567/);

  const ok = mergeBaseBaseline((args) => (args[0] === 'show' ? JSON.stringify(baselineOf([LEGACY_ENTRY])) : args[0] === 'rev-parse' ? 'def' : 'abc1234567890'));
  assert.equal(ok.skipped, null);
  assert.deepEqual(ok.baseline.entries, [LEGACY_ENTRY]);
  assert.match(baselineComparisonNote(ok, 16), /^baseline compared with merge-base abc1234567 on main/);
  const onMain = mergeBaseBaseline((args) => (args[0] === 'show' ? JSON.stringify(baselineOf([])) : 'abc1234567890'));
  assert.match(baselineComparisonNote(onMain, 16), /which is HEAD/);
});

test('C1: the real scan result line names its baseline comparison', () => {
  const out = execFileSync(process.execPath, [path.join(repoRoot, 'tools/checks/missing-claim-scan.mjs')], { encoding: 'utf8' });
  assert.match(out, /; (baseline compared with merge-base [0-9a-f]{10}|merge-base baseline comparison SKIPPED)/);
});

// ---- G-02 Q2 cues and the SVG variant ----

const SVG_TAGGED = `import { MissingClaimSvg } from "../ui";
export function Slot() {
  return <svg><MissingClaimSvg as="text" gapId="G-readiness-gateway-firmware" placement="readiness.gateway.firmware" x={1}>Readings not assessed here</MissingClaimSvg></svg>;
}
`;
const svgWorld = (text) => world((w) => { w.files[0] = { path: 'frontend/src/sites/Svg.tsx', text }; });

test('Q2 mutation: each narrow G-02 cue fails untagged and passes inside MissingClaim', () => {
  const cues = [
    ['p', 'Firmware not available here.'],
    ['text', 'Readings not assessed here'],
    ['p', 'Whether any reading has arrived is not assessed in this view.'],
    ['p', 'Monitoring links and reporting status are not assessed on this diagram.'],
    ['span', 'No proposed-change record here'],
    ['span', 'No linked constraint evidence'],
  ];
  for (const [tag, copy] of cues) {
    const bad = world(withCopy(`<${tag}>${copy}</${tag}>`));
    assert.ok(bad.errors.some((e) => e.type === 'untagged_copy' && e.where === 'frontend/src/sites/New.tsx:2'), copy);
    const ok = world(withCopy(`<MissingClaim gapId="G-readiness-gateway-firmware" placement="readiness.gateway.firmware">${copy}</MissingClaim>`));
    assert.deepEqual(ok.errors.filter((e) => e.type === 'untagged_copy'), [], copy);
  }
});

test('Q2: ordinary states and the Dispatch integration fallback stay outside the cues', () => {
  for (const copy of ['<p>Dispatch not available here</p>', '<p>Not assessed</p>', '<p>Not declared</p>', '<p>No import record here</p>', '<p>The day is not assessed</p>', '<p>No balance identity is recorded</p>']) {
    assert.deepEqual(world(withCopy(copy)).errors, [], copy);
  }
});

test('SVG variant: MissingClaimSvg text is tagged, validated and unique', () => {
  const single = svgWorld(SVG_TAGGED);
  assert.deepEqual(single.errors, []);
  assert.equal(single.usages.length, 1);
  assert.deepEqual(single.untagged.filter((u) => u.file.endsWith('Svg.tsx')), []);
  const dup = world((w) => { w.files.push({ path: 'frontend/src/sites/Svg.tsx', text: SVG_TAGGED }); });
  assert.ok(types(dup).includes('ui_duplicate_placement'));
  assert.ok(types(svgWorld(SVG_TAGGED.replace('G-readiness-gateway-firmware', 'G-nope'))).includes('ui_unknown_gap'));
  assert.ok(types(svgWorld(SVG_TAGGED.replace('readiness.gateway.firmware', 'sld.nope'))).includes('ui_unknown_placement'));
  assert.ok(types(svgWorld(SVG_TAGGED.replace('as="text"', 'as="p"'))).includes('ui_usage'));
  assert.ok(types(svgWorld(TAGGED.replace('as="p"', 'as="text"'))).includes('ui_usage'));
});

// W1-UX-07 (D-2026-10-17-w1-rail): the one reviewed exemption is the rail status const in NavRail.tsx.
const RAIL = `export const NAV_RAIL_UNAVAILABLE_STATUS = "Not available yet";
export function Row() {
  return <li aria-label={\`Assets, \${NAV_RAIL_UNAVAILABLE_STATUS}\`}><span>{NAV_RAIL_UNAVAILABLE_STATUS}</span></li>;
}
`;
const RAIL_PATH = 'frontend/src/ui/NavRail.tsx';

test('W1-UX-07: the rail status const in NavRail.tsx is the reviewed exemption', () => {
  const r = world((w) => { w.files.push({ path: RAIL_PATH, text: RAIL }); });
  assert.deepEqual(r.errors, []);
});

test('W1-UX-07 mutation: the exemption is narrow (other file, other const, inline copy, import leak, no list)', () => {
  // The same const and phrase in any other file is untagged.
  const moved = world((w) => { w.files.push({ path: 'frontend/src/sites/Panel2.tsx', text: RAIL }); });
  assert.deepEqual(moved.errors.map((e) => [e.type, e.where]), [['untagged_copy', 'frontend/src/sites/Panel2.tsx:1']]);
  // Another const in NavRail.tsx with the phrase is untagged.
  const other = world((w) => { w.files.push({ path: RAIL_PATH, text: RAIL.replaceAll('NAV_RAIL_UNAVAILABLE_STATUS', 'OTHER_STATUS') }); });
  assert.ok(other.errors.some((e) => e.type === 'untagged_copy' && e.where === `${RAIL_PATH}:1`));
  // Inline copy in NavRail.tsx outside the const is untagged.
  const inline = world((w) => { w.files.push({ path: RAIL_PATH, text: `${RAIL}export const P = () => <p>Not available yet</p>;\n` }); });
  assert.deepEqual(inline.errors.map((e) => [e.type, e.where]), [['untagged_copy', `${RAIL_PATH}:5`]]);
  // Different text in the exempt const is untagged.
  const text = world((w) => { w.files.push({ path: RAIL_PATH, text: RAIL.replace('"Not available yet"', '"Not available yet for this site"') }); });
  assert.ok(text.errors.some((e) => e.type === 'untagged_copy' && e.where === `${RAIL_PATH}:1`));
  // Rendering the const from another file (an import leak onto a panel) removes the exemption.
  const leak = world((w) => {
    w.files.push({ path: RAIL_PATH, text: RAIL });
    w.files.push({ path: 'frontend/src/sites/Leak.tsx', text: 'import { NAV_RAIL_UNAVAILABLE_STATUS } from "../ui";\nexport const L = () => <p>{NAV_RAIL_UNAVAILABLE_STATUS}</p>;\n' });
  });
  assert.ok(leak.errors.some((e) => e.type === 'untagged_copy' && e.where === `${RAIL_PATH}:1`));
  // With no reviewed exemption list the rail const is untagged: the exemption is what passes it.
  const none = world((w) => { w.files.push({ path: RAIL_PATH, text: RAIL }); w.exemptions = []; });
  assert.ok(none.errors.some((e) => e.type === 'untagged_copy' && e.where === `${RAIL_PATH}:1`));
});

// W1-F5b (D-2026-10-17-f5-subtabs-and-contact): the in-page status const in UnavailableEntry.tsx is the second
// reviewed exemption, equally narrow.
const IN_PAGE = `const IN_PAGE_UNAVAILABLE_STATUS = "Not available yet";
export function UnavailableTab({ label }) {
  return <li aria-label={\`\${label}, \${IN_PAGE_UNAVAILABLE_STATUS}\`}><span>{\`\${label} · \${IN_PAGE_UNAVAILABLE_STATUS}\`}</span></li>;
}
`;
const IN_PAGE_PATH = 'frontend/src/ui/UnavailableEntry.tsx';

test('W1-F5b: the in-page status const in UnavailableEntry.tsx is a reviewed exemption', () => {
  const r = world((w) => { w.files.push({ path: IN_PAGE_PATH, text: IN_PAGE }); });
  assert.deepEqual(r.errors, []);
});

test('W1-F5b mutation: the in-page exemption is narrow (other file, inline copy)', () => {
  const moved = world((w) => { w.files.push({ path: 'frontend/src/sites/Tabs2.tsx', text: IN_PAGE }); });
  assert.deepEqual(moved.errors.map((e) => [e.type, e.where]), [['untagged_copy', 'frontend/src/sites/Tabs2.tsx:1']]);
  const inline = world((w) => { w.files.push({ path: IN_PAGE_PATH, text: `${IN_PAGE}export const P = () => <p>Not available yet</p>;
` }); });
  assert.deepEqual(inline.errors.map((e) => [e.type, e.where]), [['untagged_copy', `${IN_PAGE_PATH}:5`]]);
});
