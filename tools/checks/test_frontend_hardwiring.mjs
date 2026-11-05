// Mutation fixtures for the CH-5b1 frontend hard-wiring ratchet. Run: node --test tools/checks/test_frontend_hardwiring.mjs
import assert from 'node:assert/strict';
import test from 'node:test';
import { compare, countText, isProductSource, readBaseline, scan, shrink } from './frontend-hardwiring.mjs';

test('the committed baseline equals today\'s counts', () => {
  const { rises, shrinks, problems } = compare(readBaseline().files, scan());
  assert.deepEqual({ rises, shrinks, problems }, { rises: [], shrinks: [], problems: [] });
});

test('each pattern counts its §13 shape and skips the look-alikes', () => {
  const src = [
    'if (site.site_type === "MINIGRID") {}', 'if (siteType !== EV_SITE_TYPE) {}', 'typeof x.site_type === "string";',
    'row.site_type === undefined;', 'const c = "KOBO-001"; const o = "MG-2"; const e = "EV-LAB-001";',
    'fetch("/api/sites"); <a href={item.links.evidence}/> <Link to={row.href}/> <a href={toUi(row.href)}/>',
  ].join('\n');
  assert.deepEqual(countText('x.tsx', src), { cmp: 2, lit: 1, code: 2, oid: 1, api: 1, href: 2 });
  assert.deepEqual(countText('x.ts', 'fetch("/api/sites")'), {}, '/api counts in .tsx components only');
});

test('a rise in one file fails', () => {
  const base = { 'shell/A.tsx': { cmp: 2 } };
  const { rises } = compare(base, { 'shell/A.tsx': { cmp: 3 } });
  assert.deepEqual(rises, [{ file: 'shell/A.tsx', pattern: 'cmp', base: 2, now: 3 }]);
});

test('a file outside the baseline counts from 0 (new file, rename)', () => {
  const { rises } = compare({ 'shell/A.tsx': { lit: 1 } }, { 'shell/A.tsx': { lit: 1 }, 'blocks/OutcomeRow.tsx': { lit: 1 } });
  assert.deepEqual(rises, [{ file: 'blocks/OutcomeRow.tsx', pattern: 'lit', base: 0, now: 1 }]);
});

test('a baseline row under F/blocks/ is refused', () => {
  const { problems } = compare({ 'blocks/FindingCard.tsx': { cmp: 1 } }, { 'blocks/FindingCard.tsx': { cmp: 1 } });
  assert.equal(problems.length, 1);
});

test('--shrink lowers cells, drops zero rows and never raises or adds', () => {
  const base = { 'a.tsx': { cmp: 3, lit: 2 }, 'gone.tsx': { api: 1 } };
  assert.deepEqual(shrink(base, { 'a.tsx': { cmp: 1, lit: 2 } }), { 'a.tsx': { cmp: 1, lit: 2 } });
});

test('--shrink refuses while any cell has risen', () => {
  assert.throws(() => shrink({ 'a.tsx': { cmp: 3 } }, { 'a.tsx': { cmp: 1, lit: 1 } }), /refused/);
  assert.throws(() => shrink({}, { 'new.tsx': { oid: 1 } }), /refused/);
});

test('tests, vocabulary and the view registry are out of scope', () => {
  for (const rel of ['sites/__tests__/x.tsx', 'sites/a.test.tsx', 'test/settled.ts', 'blocks/vocabulary.ts',
    'blocks/vocabularyEn.ts', 'views/registry.ts', 'styles.css']) assert.equal(isProductSource(rel), false, rel);
  assert.equal(isProductSource('blocks/OutcomeRow.tsx'), true);
});
