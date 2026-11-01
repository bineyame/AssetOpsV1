// Guard 12, "Mock deviation labels and client vocabulary" (POLISH §2, P-04): the label scanner's four fixtures and the
// repository scan. Run: node --test tools/checks/test_mock_deviation_labels.mjs (tools/check-all.ps1 runs it).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { checkLabels, repositoryInputs } from "./mock-deviation-labels.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const FIX = join(HERE, "fixtures", "mock-deviation-labels");
const read = (name) => readFileSync(join(FIX, name), "utf8");
const run = (tsx, css = "hide-rule.css") =>
  checkLabels({ files: [{ path: tsx, source: read(tsx) }], register: read("register.md"), css: read(css), cssPath: css });

test("fixture: tagged labels with registered ids, the shared component and the hide rule pass", () => {
  assert.deepEqual(run("pass.tsx.txt"), []);
});

test("fixture: an untagged label fails, naming its line", () => {
  const problems = run("untagged.tsx.txt");
  assert.equal(problems.length, 1);
  assert.match(problems[0], /^untagged\.tsx\.txt:6: untagged MOCK DEVIATION label/);
});

test("fixture: an unknown id fails, both on a tagged element and on <MockDeviation>", () => {
  const problems = run("unknown-id.tsx.txt");
  assert.equal(problems.length, 2);
  assert.match(problems[0], /data-mock-deviation="R999" is not a register row/);
  assert.match(problems[1], /<MockDeviation id="R998"> is not a register row/);
});

test("fixture: a stylesheet without the hide rule (only a commented-out copy) fails", () => {
  const problems = run("pass.tsx.txt", "no-hide-rule.css");
  assert.equal(problems.length, 1);
  assert.match(problems[0], /^no-hide-rule\.css: the hide rule is missing/);
});

test("the repository: every label tagged, every id registered, the hide rule present", () => {
  const inputs = repositoryInputs(REPO);
  assert.ok(inputs.files.length > 100, `scanned ${inputs.files.length} files`);
  // Non-vacuous: the scan covers real labels (the shared component and the inline ones), not an empty set.
  const labelled = inputs.files.filter((f) => /data-mock-deviation=/.test(f.source));
  assert.ok(labelled.length >= 10, `files with tagged labels: ${labelled.length}`);
  assert.deepEqual(checkLabels(inputs), []);
});
