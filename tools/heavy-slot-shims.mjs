// T1: the tsc tripwire, a shim in node_modules/.bin (specs/T1-heavy-tool-slot-pool/spec.md §5.2).
//
//   node tools/heavy-slot-shims.mjs install <node_modules>   # frontend/package.json "postinstall" runs this
//   node tools/heavy-slot-shims.mjs check <node_modules>     # exit 0 only when .bin/tsc is the shim
//
// install makes <node_modules> canonical first (a worktree's symlink resolves to main's install), writes
// <nm>/.heavy-slot/tsc.cjs and points <nm>/.bin/tsc at it. Idempotent: a second install changes nothing.
// Documented gaps: `node node_modules/typescript/bin/tsc` run directly, and the Windows .cmd shims.
import fs from "node:fs";
import path from "node:path";

const LINK = "../.heavy-slot/tsc.cjs";

function shimText(nm) {
  const check = path.join(fs.realpathSync(path.join(nm, "..", "..")), "tools", "heavy_slot_check.cjs");
  return "#!/usr/bin/env node\n" +
    "// T1 heavy-slot shim (tools/heavy-slot-shims.mjs); the real tsc is ../typescript/bin/tsc\n" +
    `require(${JSON.stringify(check)}).assertHeavySlot("tsc");\n` +
    'require("../typescript/bin/tsc");\n';
}

function install(nmArg) {
  const nm = fs.realpathSync(nmArg);
  const dir = path.join(nm, ".heavy-slot");
  const shim = path.join(dir, "tsc.cjs");
  const text = shimText(nm);
  fs.mkdirSync(dir, { recursive: true });
  let current = null;
  try { current = fs.readFileSync(shim, "utf8"); } catch { /* new */ }
  if (current !== text) fs.writeFileSync(shim, text);
  if ((fs.statSync(shim).mode & 0o777) !== 0o755) fs.chmodSync(shim, 0o755);
  const bin = path.join(nm, ".bin");
  const link = path.join(bin, "tsc");
  let target = null;
  try { target = fs.readlinkSync(link); } catch { /* missing, or not a link */ }
  if (target !== LINK) {
    fs.mkdirSync(bin, { recursive: true });
    fs.rmSync(link, { force: true });
    fs.symlinkSync(LINK, link);
  }
  console.log(`heavy-slot-shims: tsc shim installed in ${nm}`);
}

function check(nmArg) {
  let nm;
  try { nm = fs.realpathSync(nmArg); } catch { return fail(`${nmArg} does not exist`); }
  const shim = path.join(nm, ".heavy-slot", "tsc.cjs");
  let resolved;
  try { resolved = fs.realpathSync(path.join(nm, ".bin", "tsc")); } catch { return fail(`${nm}/.bin/tsc does not resolve`); }
  if (resolved !== shim) return fail(`${nm}/.bin/tsc resolves to ${resolved}, not the T1 shim (run: node tools/heavy-slot-shims.mjs install ${nmArg})`);
  const m = /^require\(("[^"]*")\)\.assertHeavySlot\("tsc"\);$/m.exec(fs.readFileSync(shim, "utf8"));
  if (!m) return fail(`${shim} does not call assertHeavySlot("tsc")`);
  const module = JSON.parse(m[1]);
  if (!fs.existsSync(module)) return fail(`${shim} names ${module}, which does not exist`);
  console.log(`heavy-slot-shims: ${nm}/.bin/tsc is the T1 shim (${module})`);
  return 0;
}

function fail(line) {
  console.log(`heavy-slot-shims: ${line}`);
  return 1;
}

const [cmd, nm] = process.argv.slice(2);
if (cmd === "install" && nm) install(nm);
else if (cmd === "check" && nm) process.exitCode = check(nm);
else {
  console.error("usage: node tools/heavy-slot-shims.mjs install|check <node_modules>");
  process.exitCode = 64;
}
