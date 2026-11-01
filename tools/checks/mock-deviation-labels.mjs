/**
 * Guard 12, "Mock deviation labels and client vocabulary" (POLISH §2, P-04). Client screens never show a
 * MOCK DEVIATION label; each label stays in the DOM, tagged, and renders only in review mode. Three checks:
 *   (a) every non-comment `MOCK DEVIATION D` text in frontend/src/**\/*.tsx (tests excluded) sits in an element whose
 *       opening tag carries `data-mock-deviation=` (the shared `MockDeviation` component does, with `={id}`);
 *   (b) every `data-mock-deviation` id, and every `<MockDeviation id="...">`, is a row in the register; a dynamic
 *       value is allowed only inside the `MockDeviation` component itself;
 *   (c) the hide rule is present in frontend/src/ui/mock-deviation.css.
 *
 *   node tools/checks/mock-deviation-labels.mjs        (scans the repository; exit 1 on any problem)
 *   node --test tools/checks/test_mock_deviation_labels.mjs   (fixtures plus the repository scan; check-all guard 12)
 */
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

export const HIDE_RULE = ':root:not([data-review-labels="on"]) [data-mock-deviation] { display: none !important; }';
const HIDE_RULE_RE = /:root:not\(\[data-review-labels="on"\]\)\s+\[data-mock-deviation\]\s*\{\s*display:\s*none\s*!important;?\s*\}/;

/**
 * Removes comments, keeping line numbers: block comments (including JSX `{/* *\/}`) and `//` line comments not
 * preceded by `:` (so `http://` in a string survives). Replaced characters become spaces; newlines stay.
 */
export function stripComments(source) {
  const blank = (m) => m.replace(/[^\n]/g, " ");
  return source.replace(/\/\*[\s\S]*?\*\//g, blank).replace(/(^|[^:\\])\/\/[^\n]*/g, (m, lead) => lead + blank(m.slice(lead.length)));
}

const lineOf = (text, index) => text.slice(0, index).split("\n").length;

/** Problems in one .tsx source: untagged labels (a) and label ids (b). `register` is the set of register row ids. */
export function scanSource(path, source, register) {
  const problems = [];
  const code = stripComments(source.replace(/\r\n/g, "\n"));
  const OPEN_TAG = /<([A-Za-z][\w.]*)\b([^<>]*?)>/g;
  for (const m of code.matchAll(/MOCK DEVIATION D/g)) {
    const before = code.slice(0, m.index);
    let tag = null;
    for (const t of before.matchAll(OPEN_TAG)) tag = t;
    const between = tag ? before.slice(tag.index + tag[0].length) : before;
    const tagged = tag && !tag[0].endsWith("/>") && !between.includes("<") && /\bdata-mock-deviation=/.test(tag[2]);
    if (!tagged) problems.push(`${path}:${lineOf(code, m.index)}: untagged MOCK DEVIATION label (its element has no data-mock-deviation)`);
  }
  const component = /export function MockDeviation\b[\s\S]*?\n}\n/.exec(code);
  for (const m of code.matchAll(/data-mock-deviation=(?:"([^"]*)"|\{([^}]*)\})/g)) {
    const at = `${path}:${lineOf(code, m.index)}`;
    if (m[1] !== undefined) {
      if (!register.has(m[1])) problems.push(`${at}: data-mock-deviation="${m[1]}" is not a register row`);
    } else if (!(component && m.index >= component.index && m.index < component.index + component[0].length)) {
      problems.push(`${at}: dynamic data-mock-deviation={${m[2]}} outside the MockDeviation component`);
    }
  }
  for (const m of code.matchAll(/<MockDeviation\b([^<>]*?)\/?>/g)) {
    const at = `${path}:${lineOf(code, m.index)}`;
    const id = /\bid="([^"]*)"/.exec(m[1]);
    if (!id) problems.push(`${at}: <MockDeviation> without a literal id`);
    else if (!register.has(id[1])) problems.push(`${at}: <MockDeviation id="${id[1]}"> is not a register row`);
  }
  return problems;
}

/** The register's row ids: the first cell of each table row, `| Rnnn |`. */
export function registerIds(markdown) {
  return new Set([...markdown.matchAll(/^\| (R\d+) \|/gm)].map((m) => m[1]));
}

/** (c) The hide rule is present. */
export function cssProblems(path, css) {
  return HIDE_RULE_RE.test(stripComments(css.replace(/\r\n/g, "\n"))) ? [] : [`${path}: the hide rule is missing (${HIDE_RULE})`];
}

/** Every check over `files` ([{ path, source }]), the register text and the stylesheet text. */
export function checkLabels({ files, register, css, cssPath = "frontend/src/ui/mock-deviation.css" }) {
  const ids = registerIds(register);
  return [...files.flatMap((f) => scanSource(f.path, f.source, ids)), ...cssProblems(cssPath, css)];
}

function tsxFiles(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== "__tests__" && entry.name !== "test") tsxFiles(p, out);
    } else if (entry.name.endsWith(".tsx") && !/\.test\.tsx$/.test(entry.name)) out.push(p);
  }
  return out;
}

/** The repository inputs: frontend/src/**\/*.tsx without tests, the register and the stylesheet. */
export function repositoryInputs(repo) {
  const src = join(repo, "frontend", "src");
  const files = tsxFiles(src).map((p) => ({ path: relative(repo, p).replaceAll("\\", "/"), source: readFileSync(p, "utf8") }));
  return {
    files,
    register: readFileSync(join(repo, ".agent", "mock-departure-register.md"), "utf8"),
    css: readFileSync(join(src, "ui", "mock-deviation.css"), "utf8"),
  };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const repo = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
  const inputs = repositoryInputs(repo);
  const problems = checkLabels(inputs);
  for (const p of problems) console.log(p);
  console.log(problems.length ? `FAIL  ${problems.length} label problem(s)` : `OK  ${inputs.files.length} files, labels tagged, ids registered, hide rule present`);
  process.exitCode = problems.length ? 1 : 0;
}
