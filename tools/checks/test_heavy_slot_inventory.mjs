// T1: the heavy-slot tripwire inventory (specs/T1-heavy-tool-slot-pool/spec.md §7.2). Static, under 2 s, every
// check-all run. Each check runs once on a planted fixture (it must report it) and once on the repository.
//
//   node --test tools/checks/test_heavy_slot_inventory.mjs
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const read = (rel) => fs.readFileSync(path.join(REPO, rel), "utf8");

// ---- 1. browser-launching files (spec §5.4) ----
// Scripts only: a document that names a browser tool launches nothing. The check module and this test are exempt.
const LAUNCH = /remote-debugging-port|playwright|puppeteer/;
const SCRIPT = /\.(mjs|cjs|js|ts|tsx|py|ps1|sh)$/;
const LAUNCH_EXEMPT = new Set(["tools/heavy_slot_check.cjs", "tools/checks/test_heavy_slot_inventory.mjs"]);

function launchingFiles() {
  const r = spawnSync("git", ["grep", "-l", "-E", LAUNCH.source, "--", ".", ":!archive/", ":!frontend/mockups/v69/",
                              ":!frontend/mockups/v71/"], { cwd: REPO, encoding: "utf8" });
  assert.ok(r.status === 0 || r.status === 1, `git grep failed: ${r.stderr}`);
  return r.stdout.split("\n").filter((f) => f && SCRIPT.test(f) && !LAUNCH_EXEMPT.has(f));
}

export function missingCaptureAssert(files) {
  return files.filter((f) => LAUNCH.test(f.text) && !f.text.includes("assertHeavySlot(")).map((f) => `${f.name}: no assertHeavySlot( call`);
}

// ---- 2. database entry points (spec §5.5) ----
const DB_MAIN = ["tools/demo_combined.py", "tools/chain_clone.py", "tools/mechanism_dataset.py"];
const DB_CHILDREN = ["kobo", "cold", "ev", "kisiwa", "mill", "finish", "ex1", "after"].map((n) => `tools/demo_combined_${n}.py`);
const DB_CALL = 'require("database job", db=True)';

// The call sits inside `def main(` (the parents) or the `__main__` block (the children); nothing at module level.
export function dbEntryProblems(name, text, where) {
  const out = [];
  const lines = text.split("\n");
  let calls = 0;
  let enclosing = "";
  lines.forEach((line, i) => {
    if (/^\S/.test(line) && !line.startsWith("#")) enclosing = line;
    if (/^(import|from)\s+heavy_slot_check\b/.test(line)) out.push(`${name}:${i + 1}: heavy_slot_check imported at module level`);
    if (!line.includes(DB_CALL)) return;
    calls++;
    const okBlock = where === "main" ? /^def main\(/.test(enclosing) : /^if __name__ == "__main__":/.test(enclosing);
    if (/^\S/.test(line) || !okBlock) {
      out.push(`${name}:${i + 1}: the database-job tripwire is outside ${where === "main" ? "main()" : "the __main__ block"}`);
    }
  });
  if (calls === 0) out.push(`${name}: no ${DB_CALL} call`);
  return out;
}

// ---- 3-6. vitest, the conftests, postinstall, the container runners ----
export function viteProblems(text) {
  const inline = text.split("\n").some((l) => l.includes("VITEST") && l.includes('assertHeavySlot("vitest")') && !/^\s*(\/\/|\*)/.test(l));
  const setup = /globalSetup:\s*\[[^\]]*heavy-slot-vitest-setup\.mjs/.test(text);
  return inline || setup ? [] : ["frontend/vite.config.ts: no VITEST tripwire and no heavy-slot globalSetup"];
}

// The first statement of pytest_configure is the tripwire.
export function conftestProblems(name, text) {
  const lines = text.split("\n");
  const at = lines.findIndex((l) => /^def pytest_configure\(/.test(l));
  if (at < 0) return [`${name}: no pytest_configure`];
  const first = lines.slice(at + 1).findIndex((l) => l.trim() && !l.trim().startsWith("#"));
  const line = first < 0 ? "" : lines[at + 1 + first];
  if (!/^\s+if os\.environ\.get\("ASSETOPS_TEST_DATABASE_URL"\): _heavy_slot_check\(\)\.require\(/.test(line)) {
    return [`${name}:${at + 2 + Math.max(first, 0)}: the first statement of pytest_configure is not the heavy-slot require(`];
  }
  return [];
}

const POSTINSTALL = "node ../tools/heavy-slot-shims.mjs install node_modules";
const RUNNERS = ["tools/run-backend-suite-in-container.ps1", "tools/profile-tests-in-container.ps1"];
const COMPOSE_LINE = "ASSETOPS_HEAVY_SLOT_CONTAINER: ${ASSETOPS_HEAVY_SLOT_CONTAINER:-}";

export function runnerProblems(name, text) {
  return text.split("\n").some((l) => /^\s*Assert-HeavySlotHeld\b/.test(l)) ? [] : [`${name}: no Assert-HeavySlotHeld call`];
}

// ---- 7. the spec §6 documents carry only pooled commands ----
const DOCS = [".agent/lane-rules-vps-2026-11-12.md", "backend/TESTING.md", ".ai/RULES.md", ".ai/START_HERE.md", "tools/select-tests.py"];
// Spec §6 also lists these two; the T1 dispatch forbids any `.claude/` change. Mid-build question 1
// (specs/T1-heavy-tool-slot-pool/mid-build-questions.md): reported below as a todo, not yet blocking.
const DOCS_PENDING = [".claude/agents/assetops-reviewer.md", ".claude/agents/assetops-implementer.md"];
const HEAVY = ["npx tsc", "npx vitest", "-m pytest", "run-host-tests.ps1 --", "run-backend-suite-in-container.ps1 -", "-evidence.mjs "];

export function unpooledLines(name, text) {
  const out = [];
  let history = false;
  text.split("\n").forEach((line, i) => {
    const h = /^##\s+(.*)$/.exec(line);
    if (h) history = /history/i.test(h[1]);
    if (history || /\b(unpooled|refused)\b/i.test(line)) return;
    for (const pat of HEAVY) {
      let at = line.indexOf(pat);
      while (at >= 0) {
        const pooled = line.lastIndexOf("heavy-slot.", at);
        if (pooled < 0) { out.push(`${name}:${i + 1}: unpooled \`${pat.trim()}\`: ${line.trim()}`); break; }
        at = line.indexOf(pat, at + 1);
      }
    }
  });
  return out;
}

// ---------------------------------------------------------------------------------------------------------------

test("1 every browser-launching script calls assertHeavySlot (planted fixture reported)", () => {
  assert.deepEqual(missingCaptureAssert([{ name: "tools/planted-evidence.mjs", text: 'spawn(CHROME, ["--remote-debugging-port=9222"]);' }]),
                   ["tools/planted-evidence.mjs: no assertHeavySlot( call"]);
  const files = launchingFiles();
  assert.ok(files.length >= 30, `only ${files.length} browser-launching scripts found; the inventory lost its files`);
  assert.deepEqual(missingCaptureAssert(files.map((f) => ({ name: f, text: read(f) }))), []);
});

test("2 each database entry point calls require(\"database job\", db=True) in its dispatch, never at module level", () => {
  const planted = `import os\nimport heavy_slot_check\nheavy_slot_check.${DB_CALL}\n\ndef main():\n    pass\n`;
  assert.deepEqual(dbEntryProblems("tools/planted.py", planted, "main"), [
    "tools/planted.py:2: heavy_slot_check imported at module level",
    "tools/planted.py:3: the database-job tripwire is outside main()",
  ]);
  assert.deepEqual(dbEntryProblems("tools/planted.py", "def main():\n    pass\n", "main"), [`tools/planted.py: no ${DB_CALL} call`]);
  const problems = [...DB_MAIN.map((f) => dbEntryProblems(f, read(f), "main")),
                    ...DB_CHILDREN.map((f) => dbEntryProblems(f, read(f), "__main__"))].flat();
  assert.deepEqual(problems, []);
});

test("3 vite.config.ts carries the vitest tripwire", () => {
  assert.equal(viteProblems('import { defineConfig } from "vitest/config";\n').length, 1);
  assert.deepEqual(viteProblems(read("frontend/vite.config.ts")), []);
});

test("4 both conftests open pytest_configure with the heavy-slot require(", () => {
  const planted = 'if os.environ.get("ASSETOPS_TEST_DATABASE_URL"): _heavy_slot_check().require("x", exit_with=pytest.exit)\n\n' +
                  "def pytest_configure(config):\n    config.addinivalue_line('markers', 'slow')\n";
  assert.deepEqual(conftestProblems("backend/tests/conftest.py", planted),
                   ["backend/tests/conftest.py:4: the first statement of pytest_configure is not the heavy-slot require("]);
  assert.deepEqual([...conftestProblems("backend/tests/conftest.py", read("backend/tests/conftest.py")),
                    ...conftestProblems("host/conftest.py", read("host/conftest.py"))], []);
});

test("5 frontend/package.json reinstalls the tsc shim on install", () => {
  assert.equal(JSON.parse(read("frontend/package.json")).scripts?.postinstall, POSTINSTALL);
});

test("6 both container runners call Assert-HeavySlotHeld and the compose file passes the container marker", () => {
  assert.deepEqual(runnerProblems("tools/planted.ps1", "# Assert-HeavySlotHeld is mentioned only\n"), ["tools/planted.ps1: no Assert-HeavySlotHeld call"]);
  assert.deepEqual(RUNNERS.flatMap((f) => runnerProblems(f, read(f))), []);
  const compose = read("docker-compose.test.yml");
  const runner = compose.slice(compose.indexOf("backend-test-runner:"));
  assert.ok(compose.includes("backend-test-runner:") && runner.includes(COMPOSE_LINE), `docker-compose.test.yml: backend-test-runner lacks ${COMPOSE_LINE}`);
});

test("7 the spec §6 documents carry only pooled heavy commands", () => {
  const planted = "Run it:\n`cd frontend && npx vitest run x`\n`tools/heavy-slot.sh -- npx tsc --noEmit`\n" +
                  "An unpooled `npx tsc` is refused.\n## History\n`npx tsc --noEmit`\n## Now\n`node tools/layout-evidence.mjs <url>`\n";
  assert.deepEqual(unpooledLines("planted.md", planted), [
    "planted.md:2: unpooled `npx vitest`: `cd frontend && npx vitest run x`",
    "planted.md:8: unpooled `-evidence.mjs`: `node tools/layout-evidence.mjs <url>`",
  ]);
  assert.deepEqual(DOCS.flatMap((f) => unpooledLines(f, read(f))), []);
});

test("7b the two .claude/agents briefs of spec §6 (pending mid-build question 1)", { todo: "the T1 dispatch forbids .claude/ changes" }, () => {
  assert.deepEqual(DOCS_PENDING.flatMap((f) => unpooledLines(f, read(f))), []);
});
