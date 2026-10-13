// Missing-claim orphan scan (G-01, D-2026-10-12-mock-gap-closure-mechanism section 2).
//
// Product source only (frontend/src, excluding tests and test helpers). It enforces:
//   1. the typed UI mirror (frontend/src/ui/gapCatalogue.ts) equals the registry mock_gaps placements
//      that the UI may reference (open with placements, or resolved with a reviewed ui_transition);
//   2. every <MissingClaim gapId placement> uses literal, catalogued pairs, and every catalogued placement is used;
//   3. missing-capability copy ("not available yet" and equivalents) is either rendered through <MissingClaim>
//      or listed in the dated legacy baseline, which must match exactly and may only shrink.
//
// Run: node tools/checks/missing-claim-scan.mjs   (exit 1 with file:line on failure)
// Do not weaken these checks to make a task pass; shrink the baseline by tagging copy instead.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(path.join(repoRoot, 'frontend/package.json'));
const ts = require('typescript');

export const BASELINE_PATH = 'tools/checks/missing-claim-baseline.json';
export const REGISTRY_PATH = 'frontend/docs/architecture/v69-dependency-registry-pilot.json';
export const MIRROR_PATH = 'frontend/src/ui/gapCatalogue.ts';
export const SCAN_ROOT = 'frontend/src';
// Frozen at the dated G-01 seed. The baseline total can never exceed it, even on a branch whose
// merge-base baseline is missing. Lowering it is allowed; raising it is a guard change for review.
export const SEED_CEILING = 16;
// Missing-capability phrasing. Runtime zero/error copy ("unavailable", "not recorded", "no results") is not
// matched: those are states of an existing capability, not catalogued gaps.
export const PATTERNS = [/not available yet/i, /not yet available/i, /no reviewed source/i];

const toPosix = (p) => p.split(path.sep).join('/');
const normalize = (text) => text.replace(/\s+/g, ' ').trim().slice(0, 160);

export function isProductSource(relPath) {
  const p = toPosix(relPath);
  if (!p.startsWith(`${SCAN_ROOT}/`) || !/\.(ts|tsx)$/.test(p) || p.endsWith('.d.ts')) return false;
  if (/(^|\/)__tests__\//.test(p) || /\.test\.(ts|tsx)$/.test(p) || p.startsWith(`${SCAN_ROOT}/test/`)) return false;
  return true;
}

const parse = (file) => ts.createSourceFile(file.path, file.text, ts.ScriptTarget.Latest, true,
  file.path.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
const lineOf = (sf, node) => sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
const tagName = (node) => (ts.isJsxElement(node) ? node.openingElement.tagName : ts.isJsxSelfClosingElement(node) ? node.tagName : null);
const isMissingClaimElement = (node) => tagName(node)?.getText() === 'MissingClaim';
function insideMissingClaim(node) {
  for (let cur = node.parent; cur; cur = cur.parent) if (ts.isJsxElement(cur) && isMissingClaimElement(cur)) return true;
  return false;
}
function stringParts(node) {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  if (ts.isTemplateHead(node) || ts.isTemplateMiddle(node) || ts.isTemplateTail(node)) return node.text;
  if (ts.isJsxText(node)) return node.text;
  return null;
}
// The const a literal initialises, through parentheses, concatenation and template spans.
function owningConst(node) {
  let cur = node;
  while (cur.parent && (ts.isParenthesizedExpression(cur.parent) || ts.isBinaryExpression(cur.parent) ||
    ts.isTemplateSpan(cur.parent) || ts.isTemplateExpression(cur.parent) || ts.isAsExpression(cur.parent))) cur = cur.parent;
  const decl = cur.parent;
  if (decl && ts.isVariableDeclaration(decl) && decl.initializer === cur && ts.isIdentifier(decl.name) &&
      decl.parent && (decl.parent.flags & ts.NodeFlags.Const)) return decl.name.text;
  return null;
}

/**
 * Pure analysis. files: [{path, text}] product sources (repo-relative, posix); registry: parsed registry JSON;
 * mirror: {path, text}; baseline: parsed baseline JSON; mainBaseline: parsed merge-base baseline or null.
 * Returns {errors: [{type, where, reason}], untagged: [{file, line, text}], usages: [{file, line, gapId, placement}]}.
 */
export function analyze({ files, registry, mirror, baseline, mainBaseline = null, seedCeiling = SEED_CEILING }) {
  const errors = [];
  const err = (type, where, reason) => errors.push({ type, where, reason });

  // ---- 1. mirror equals the registry's UI-referable placements ----
  const expected = new Map();
  for (const gap of registry?.mock_gaps?.gaps || []) {
    if (!Array.isArray(gap.ui_placements) || !gap.ui_placements.length) continue;
    if (gap.status === 'open') expected.set(gap.id, { status: 'open', placements: [...gap.ui_placements].sort() });
    else if (gap.status === 'resolved' && gap.evidence?.ui_transition) expected.set(gap.id, { status: 'resolved_transition', placements: [...gap.ui_placements].sort() });
  }
  const mirrorMap = new Map();
  const msf = parse(mirror);
  let mirrorFound = false;
  const visitMirror = (node) => {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === 'UI_GAP_CATALOGUE' && node.initializer) {
      mirrorFound = true;
      let init = node.initializer;
      while (ts.isAsExpression(init) || ts.isSatisfiesExpression(init) || ts.isParenthesizedExpression(init)) init = init.expression;
      if (!ts.isObjectLiteralExpression(init)) { err('mirror', MIRROR_PATH, 'UI_GAP_CATALOGUE must be an object literal'); return; }
      for (const prop of init.properties) {
        const id = prop.name && (ts.isStringLiteral(prop.name) || ts.isIdentifier(prop.name)) ? prop.name.text : null;
        const value = ts.isPropertyAssignment(prop) ? prop.initializer : null;
        if (!id || !value || !ts.isObjectLiteralExpression(value)) { err('mirror', `${MIRROR_PATH}:${lineOf(msf, prop)}`, 'each entry must be a literal {status, placements}'); continue; }
        const field = (name) => value.properties.find((p) => ts.isPropertyAssignment(p) && p.name.getText(msf) === name)?.initializer;
        const status = field('status');
        const placements = field('placements');
        if (!status || !ts.isStringLiteral(status) || !placements || !ts.isArrayLiteralExpression(placements) ||
            placements.elements.some((e) => !ts.isStringLiteral(e))) {
          err('mirror', `${MIRROR_PATH}:${lineOf(msf, prop)}`, `${id}: status and placements must be string literals`); continue;
        }
        if (mirrorMap.has(id)) err('mirror', `${MIRROR_PATH}:${lineOf(msf, prop)}`, `${id}: duplicate mirror entry`);
        mirrorMap.set(id, { status: status.text, placements: placements.elements.map((e) => e.text).sort() });
      }
    }
    ts.forEachChild(node, visitMirror);
  };
  visitMirror(msf);
  if (!mirrorFound) err('mirror', MIRROR_PATH, 'UI_GAP_CATALOGUE not found');
  for (const [id, entry] of mirrorMap) {
    const want = expected.get(id);
    if (!want) err('mirror_unknown', MIRROR_PATH, `${id} is not an open (or reviewed resolved-transition) registry gap with ui_placements`);
    else if (JSON.stringify(want) !== JSON.stringify(entry)) err('mirror_mismatch', MIRROR_PATH, `${id}: mirror ${JSON.stringify(entry)} differs from registry ${JSON.stringify(want)}`);
  }
  for (const id of expected.keys()) if (!mirrorMap.has(id)) err('mirror_missing', MIRROR_PATH, `${id} has registry ui_placements but no UI mirror entry`);

  // ---- 2 and 3. product source scan ----
  const usages = [];
  const literalHits = [];
  const constRefs = new Map(); // const name -> [{inside}]
  for (const file of files) {
    const sf = parse(file);
    const visit = (node) => {
      if ((ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) && isMissingClaimElement(node)) {
        const opening = ts.isJsxElement(node) ? node.openingElement : node;
        const attr = (name) => opening.attributes.properties.find((a) => ts.isJsxAttribute(a) && a.name.getText(sf) === name);
        const literal = (a) => (a?.initializer && ts.isStringLiteral(a.initializer) ? a.initializer.text : null);
        const where = `${file.path}:${lineOf(sf, node)}`;
        const gapId = literal(attr('gapId'));
        const placement = literal(attr('placement'));
        if (opening.attributes.properties.some((a) => ts.isJsxSpreadAttribute(a)) || gapId === null || placement === null) {
          err('ui_usage', where, 'MissingClaim needs literal gapId and placement attributes (no spread or expression)');
        } else {
          usages.push({ file: file.path, line: lineOf(sf, node), gapId, placement });
          const entry = mirrorMap.get(gapId);
          if (!entry) err('ui_unknown_gap', where, `unknown gap ID ${gapId}; register it in mock_gaps and the UI mirror`);
          else if (!entry.placements.includes(placement)) err('ui_unknown_placement', where, `${placement} is not a registered placement of ${gapId}`);
        }
      }
      if (ts.isIdentifier(node) && node.parent && !ts.isImportSpecifier(node.parent) && !ts.isExportSpecifier(node.parent) &&
          !(ts.isVariableDeclaration(node.parent) && node.parent.name === node) && !ts.isImportClause(node.parent)) {
        if (!constRefs.has(node.text)) constRefs.set(node.text, []);
        constRefs.get(node.text).push({ inside: insideMissingClaim(node) });
      }
      const text = stringParts(node);
      if (text !== null && PATTERNS.some((re) => re.test(text))) {
        literalHits.push({ file: file.path, line: lineOf(sf, node), text: normalize(text), inside: insideMissingClaim(node), constName: owningConst(node) });
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
  }
  const used = new Set(usages.map((u) => `${u.gapId}\u0000${u.placement}`));
  for (const [id, entry] of mirrorMap) for (const placement of entry.placements) {
    if (!used.has(`${id}\u0000${placement}`)) err('unused_placement', MIRROR_PATH, `${id} placement ${placement} is never rendered; place it or give the gap an unplaced_reason`);
  }
  const untagged = literalHits.filter((hit) => {
    if (hit.inside) return false;
    if (!hit.constName) return true;
    const refs = constRefs.get(hit.constName) || [];
    return !(refs.length > 0 && refs.every((r) => r.inside));
  }).map(({ file, line, text }) => ({ file, line, text }));

  // ---- baseline: exact, dated, enumerated, shrink-only ----
  const keyOf = (e) => `${e.file}\u0000${e.text}`;
  const current = new Map();
  for (const hit of untagged) {
    const k = keyOf(hit);
    if (!current.has(k)) current.set(k, { file: hit.file, text: hit.text, lines: [] });
    current.get(k).lines.push(hit.line);
  }
  const entries = Array.isArray(baseline?.entries) ? baseline.entries : null;
  if (!baseline || !/^\d{4}-\d{2}-\d{2}$/.test(baseline.dated || '') || !baseline.scope || !baseline.reason || !entries) {
    err('baseline_shape', BASELINE_PATH, 'baseline needs dated (YYYY-MM-DD), scope, reason and entries');
  }
  const base = new Map();
  for (const entry of entries || []) {
    if (!entry || typeof entry.file !== 'string' || typeof entry.text !== 'string' || !Number.isInteger(entry.count) || entry.count < 1 || !entry.reason) {
      err('baseline_shape', BASELINE_PATH, `entry ${JSON.stringify(entry)} needs file, text, positive integer count and reason`); continue;
    }
    if (base.has(keyOf(entry))) err('baseline_shape', BASELINE_PATH, `duplicate entry ${entry.file}: "${entry.text}"`);
    base.set(keyOf(entry), entry);
  }
  for (const [k, hit] of current) {
    const entry = base.get(k);
    if (!entry) {
      for (const line of hit.lines) err('untagged_copy', `${hit.file}:${line}`, `untagged missing-capability copy "${hit.text}"; register a mock_gaps gap and render it through <MissingClaim gapId placement>`);
    } else if (entry.count !== hit.lines.length) {
      err('baseline_count', `${hit.file}:${hit.lines[0]}`, `"${hit.text}" occurs ${hit.lines.length} time(s); baseline records ${entry.count}. Tag new copy; lower the count when legacy copy is removed`);
    }
  }
  for (const [k, entry] of base) if (!current.has(k)) err('baseline_stale', BASELINE_PATH, `${entry.file}: "${entry.text}" no longer occurs untagged; remove the entry (the baseline only shrinks)`);
  const total = [...base.values()].reduce((sum, e) => sum + e.count, 0);
  if (baseline && baseline.total !== total) err('baseline_shape', BASELINE_PATH, `total ${baseline.total} differs from the summed entry counts ${total}`);
  if (total > seedCeiling) err('baseline_growth', BASELINE_PATH, `baseline total ${total} exceeds the frozen G-01 seed ceiling ${seedCeiling}`);
  if (mainBaseline && Array.isArray(mainBaseline.entries)) {
    const mainMap = new Map(mainBaseline.entries.map((e) => [keyOf(e), e]));
    for (const [k, entry] of base) {
      const prior = mainMap.get(k);
      if (!prior) err('baseline_growth', BASELINE_PATH, `${entry.file}: "${entry.text}" is not in the main baseline; the baseline cannot gain entries`);
      else if (entry.count > prior.count) err('baseline_growth', BASELINE_PATH, `${entry.file}: "${entry.text}" count ${entry.count} exceeds main ${prior.count}`);
    }
  }
  return { errors, untagged, usages };
}

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(path.join(repoRoot, dir), { withFileTypes: true })) {
    const rel = `${dir}/${entry.name}`;
    if (entry.isDirectory()) walk(rel, out);
    else if (isProductSource(rel)) out.push({ path: rel, text: fs.readFileSync(path.join(repoRoot, rel), 'utf8') });
  }
  return out;
}

function mergeBaseBaseline() {
  try {
    const run = (args) => execFileSync('git', args, { cwd: repoRoot, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 20000 }).trim();
    const mergeBase = run(['merge-base', 'HEAD', 'main']);
    return JSON.parse(run(['show', `${mergeBase}:${BASELINE_PATH}`]));
  } catch {
    return null; // first introduction (no baseline on main yet) or no main ref: the seed ceiling still applies
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const read = (rel) => fs.readFileSync(path.join(repoRoot, rel), 'utf8');
  const result = analyze({
    files: walk(SCAN_ROOT),
    registry: JSON.parse(read(REGISTRY_PATH)),
    mirror: { path: MIRROR_PATH, text: read(MIRROR_PATH) },
    baseline: JSON.parse(read(BASELINE_PATH)),
    mainBaseline: mergeBaseBaseline(),
  });
  if (process.argv.includes('--list')) for (const u of result.untagged) console.log(`${u.file}:${u.line}\t${u.text}`);
  if (result.errors.length) {
    for (const e of result.errors) console.log(`- [${e.type}] ${e.where}: ${e.reason}`);
    console.log(`Missing-claim scan FAILED: ${result.errors.length} problem(s).`);
    process.exit(1);
  }
  console.log(`Missing-claim scan passed: ${result.usages.length} tagged placement use(s), ${result.untagged.length} baselined legacy occurrence(s).`);
}
