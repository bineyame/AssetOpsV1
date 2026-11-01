// Guard 12, "Mock deviation labels and client vocabulary" (POLISH §2, P-04): the label scanner's four fixtures and the
// repository scan. Run: node --test tools/checks/test_mock_deviation_labels.mjs (tools/check-all.ps1 runs it).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { checkLabels, repositoryInputs } from "./mock-deviation-labels.mjs";
import { GLOSSES, classifyCapture } from "../demo-combined-vocabulary.mjs";

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

// --- Client vocabulary region rules (build sheet Addendum 5) -----------------------------------------------------

/** Texts as CAPTURE_TEXTS would read them for a page with the given visible body and exempt regions. */
function capture(body, regions = []) {
  const join = (keep) => [body, ...regions.filter((r) => keep.includes(r.attr)).map((r) => r.text)].join("\n");
  return {
    full: join(["data-technical-details", "data-vocabulary-exempt", "data-time-zone-note"]),
    ids: join(["data-vocabulary-exempt", "data-time-zone-note"]),
    utc: join(["data-vocabulary-exempt"]),
    words: join(["data-time-zone-note"]),
    regions,
  };
}
const UUID = "685ffc5f-5d95-476c-b074-7c9b65d142ad";
const kinds = (hits) => hits.map((h) => `${h.kind}:${h.match}`);

test("vocabulary: an id inside data-vocabulary-exempt still counts (only Technical details hide ids)", () => {
  const r = classifyCapture(capture("What happened", [{ attr: "data-vocabulary-exempt", value: "source-reference", text: `REC ${UUID}` }]));
  assert.ok(kinds(r.vocabulary).includes(`uuid:${UUID}`));
  assert.equal(r.counted, 1);
});

test("vocabulary: an id inside Technical details is not counted but is recorded as an exempt hit", () => {
  const r = classifyCapture(capture("Overview", [{ attr: "data-technical-details", value: "", text: `Record ${UUID} at 2026-10-29T16:00:00Z` }]));
  assert.equal(r.counted, 0);
  assert.deepEqual(r.exempt_hits.map((h) => `${h.region}|${h.kind}`).sort(), ["data-technical-details=|raw timestamp", "data-technical-details=|uuid"]);
  assert.ok(r.exempt_hits.every((h) => h.context.length > 0 && h.match));
});

test("vocabulary: data-vocabulary-exempt exempts product kinds only, recorded with its value", () => {
  const r = classifyCapture(capture("Sites", [{ attr: "data-vocabulary-exempt", value: "user-owned", text: "Cold replay lab, generator running at 16:00 UTC" }]));
  // "UTC" is not exempt here; the Lab name and the product terms are.
  assert.deepEqual(kinds(r.vocabulary), ["time zone suffix:UTC"]);
  assert.equal(r.counted, 1);
  const ex = kinds(r.exempt_hits);
  assert.ok(ex.includes("lab name:replay lab") && ex.some((k) => k.startsWith("product term (T028): replay")), ex.join(", "));
  assert.ok(r.exempt_hits.every((h) => h.region === "data-vocabulary-exempt=user-owned"));
});

test("vocabulary: data-time-zone-note exempts only UTC", () => {
  const r = classifyCapture(capture("Board", [{ attr: "data-time-zone-note", value: "", text: `All times UTC ${UUID} scenario` }]));
  assert.deepEqual(kinds(r.exempt_hits), ["time zone suffix:UTC"]);
  assert.ok(kinds(r.vocabulary).includes(`uuid:${UUID}`), "an id in a time-zone note counts");
  assert.ok(kinds(r.vocabulary).includes("product term (T028): scenario:scenario"), "a product term in a time-zone note counts");
});

test("vocabulary: MOCK DEVIATION is never exempt; review mode records it without counting", () => {
  const page = capture("Board", [{ attr: "data-technical-details", value: "", text: "MOCK DEVIATION D2 (R453)" }]);
  assert.equal(classifyCapture(page).counted, 1);
  const review = classifyCapture(page, { reviewLabels: true });
  assert.equal(review.counted, 0);
  assert.ok(kinds(review.vocabulary).includes("mock deviation label:MOCK DEVIATION"));
});

test("vocabulary: the -open capture counts ids and MOCK DEVIATION, not product terms or UTC", () => {
  const r = classifyCapture(capture(`Every disclosure open: scenario, 16:00 UTC, ACT-000001, MOCK DEVIATION D1 (R06)`), { open: true });
  assert.deepEqual(kinds(r.vocabulary).sort(), ["mock deviation label:MOCK DEVIATION", "zero-padded record code:ACT-000001"]);
  assert.equal(r.counted, 2);
});

test("vocabulary: glosses come from productVocabulary.json and strip only their exact phrase", () => {
  assert.ok(GLOSSES.includes("generator running"));
  const r = classifyCapture(capture("The generator running hours; maintenance by running hours"));
  assert.deepEqual(kinds(r.vocabulary), ["product term (T028): running:running"]);
});
