// Mutation fixtures for the UQ-FI-1 style ratchet (D-UQFI.3). Run: node --test tools/checks/test_style_ratchet.mjs
import assert from 'node:assert/strict';
import test from 'node:test';
import { compare, countText, customProperties, isStyleSource, readBaseline, resolvePx, scan, shrink, wall, wallFor } from './style-ratchet.mjs';

test('the committed baseline equals today\'s counts and the 12px wall holds', () => {
  const { rises, shrinks } = compare(readBaseline().files, scan());
  assert.deepEqual({ rises, shrinks }, { rises: [], shrinks: [] });
  assert.deepEqual(wall(), []);
});

test('raw font sizes, families and hex count; the allowed values do not', () => {
  const css = [
    '.a{font-size:11px}', '.b{font-size: var(--text-sm)}', '.c{font-size: var(--font-size-200) !important;}',
    '.d{font-size:inherit}', '.e{font-size:1em}', '.f{font-size:100%}', '.g{font-size:0.9em}',
    '.h{font-family: Georgia, serif}', '.i{font-family: var(--font-mono)}', '.j{font-family: inherit}',
    '.k{font: italic 600 11px/1 Georgia, serif}', '.l{font: var(--text-sm) / 1.8 var(--font-mono)}', '.m{font: inherit}',
    '.n{color:#fff; border-color:#a1b2c3}',
  ].join('\n');
  assert.deepEqual(countText('x.css', css), { rawFontSize: 3, rawFontFamily: 2, rawHex: 2 });
  assert.deepEqual(countText('x.tsx', '<text fontSize={10} style={{ fontFamily: "x" }} fill="#123456" href="#top"/>'),
    { rawFontSize: 1, rawFontFamily: 1, rawHex: 1 });
});

test('a rise in one file fails; a new file counts from 0', () => {
  assert.deepEqual(compare({ 'a.css': { rawHex: 2 } }, { 'a.css': { rawHex: 3 } }).rises,
    [{ file: 'a.css', cell: 'rawHex', base: 2, now: 3 }]);
  assert.deepEqual(compare({}, { 'new.css': { rawFontSize: 1 } }).rises,
    [{ file: 'new.css', cell: 'rawFontSize', base: 0, now: 1 }]);
});

test('--shrink lowers cells and refuses while any cell has risen', () => {
  assert.deepEqual(shrink({ 'a.css': { rawHex: 3 }, 'gone.css': { rawHex: 1 } }, { 'a.css': { rawHex: 1 } }), { 'a.css': { rawHex: 1 } });
  assert.throws(() => shrink({ 'a.css': { rawHex: 1 } }, { 'a.css': { rawHex: 2 } }), /refused/);
  assert.throws(() => shrink({}, { 'b.css': { rawFontFamily: 1 } }), /refused/);
});

test('the 12px wall: px, rem, tokens through var() chains, and relative sizes', () => {
  const props = customProperties(':root{--font-size-100:0.75rem;--text-xs:var(--font-size-100);--text-tiny:0.6875rem}');
  assert.deepEqual(resolvePx('var(--text-xs)', props), [12]);
  assert.deepEqual(resolvePx('11px', props), [11]);
  assert.deepEqual(resolvePx('inherit', props), []);
  const bad = wallFor([
    ['ok.css', '.a{font-size:var(--text-xs)}.b{font-size:12px}.c{font-size:1em}'],
    ['low.css', '.a{font-size:11px}.b{font-size:var(--text-tiny)}.c{font-size:0.9em}.d{font: 10px/1 var(--font-mono)}'],
    ['tokens.css', ':root{--text-tiny:0.6875rem;--text-primary:#17243b}'],
  ], props);
  assert.deepEqual(bad.map((b) => `${b.file} ${b.value}`),
    ['low.css 11px', 'low.css var(--text-tiny)', 'low.css 0.9em', 'low.css 10px', 'tokens.css 0.6875rem']);
});

test('tests and the token files are out of the ratchet scan', () => {
  for (const rel of ['ui/tokens.css', 'ui/fonts.css', 'sites/__tests__/x.tsx', 'sites/a.test.tsx', 'test/settled.ts', 'x.ts'])
    assert.equal(isStyleSource(rel), false, rel);
  assert.equal(isStyleSource('ui/primitives.css'), true);
  assert.equal(isStyleSource('sites/OutcomeBoard.tsx'), true);
});

test('the codemod maps by the rev 6 table, drops fallbacks, keeps relative values, and is idempotent', async () => {
  const { rewriteType, mapFontSize, snapSpace, rewriteSpacing } = await import('../uqfi-type-codemod.mjs');
  const tokens = new Set(['--text-sm', '--font-size-100']);
  for (const [v, want] of [['9.5px', 100], ['12px', 100], ['0.75rem', 100], ['13px', 200], ['14px', 300], ['15px', 400],
    ['1rem', 400], ['19px', 500], ['22px', 600], ['27px', 700], ['0.85em', 100]]) assert.equal(mapFontSize(v, tokens), `var(--font-size-${want})`, v);
  assert.equal(mapFontSize('var(--text-sm, 12px)', tokens), 'var(--text-sm)');
  assert.equal(mapFontSize('var(--text-md, 1rem)', tokens), 'var(--font-size-400)');
  assert.equal(mapFontSize('var(--font-size-sm, 0.85em)', tokens), 'var(--font-size-100)');
  for (const keep of ['inherit', '1em', '100%']) assert.equal(mapFontSize(keep, tokens), keep);
  assert.equal(mapFontSize('3vw', tokens), null);
  const once = rewriteType('.a{font-size:10px}.b{font: 11px/1.8 Consolas, monospace;font-family:var(--font-mono, monospace)}', tokens);
  assert.equal(once.text, '.a{font-size:var(--font-size-100)}.b{font: var(--font-size-100)/1.8 var(--font-mono);font-family:var(--font-mono)}');
  assert.equal(rewriteType(once.text, tokens).text, once.text);
  assert.deepEqual(rewriteType('.a{font-size:3vw}', tokens).unmapped, ['3vw']);
  assert.deepEqual([snapSpace(1), snapSpace(6), snapSpace(10), snapSpace(14), snapSpace(28), snapSpace(80)],
    [null, 'var(--space-1)', 'var(--space-2)', 'var(--space-3)', 'var(--space-6)', null]);
  assert.equal(rewriteSpacing('.a{padding:6px 1px;margin:-6px;gap:calc(10px + 1em);width:10px}').text,
    '.a{padding:var(--space-1) 1px;margin:-6px;gap:calc(10px + 1em);width:10px}');
});
