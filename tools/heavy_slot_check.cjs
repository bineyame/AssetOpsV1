// T1: the in-tool tripwire, Node half (specs/T1-heavy-tool-slot-pool/spec.md §2 and §5.1).
//
// A heavy tool calls assertHeavySlot("<tool>") before it starts work. Outside a held slot of this machine's pool
// it prints the refusal and exits 69. CommonJS and the Node standard library only, so the tsc shim (CommonJS),
// vite.config.ts (createRequire) and the ESM capture scripts (named import) can all load it.
//
// D is git's common dir (every GIT_* variable removed), canonical, plus /check-all-slots. ASSETOPS_HEAVY_SLOT_DIR is
// never read here: a slot held in a private directory never satisfies a tripwire.
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

function gitCommonDir(from) {
  const env = {};
  for (const [k, v] of Object.entries(process.env)) if (!k.startsWith("GIT_")) env[k] = v;
  try {
    const r = spawnSync("git", ["-C", from, "rev-parse", "--path-format=absolute", "--git-common-dir"], {
      env, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], windowsHide: true,
    });
    const out = r.status === 0 ? String(r.stdout).trim() : "";
    return out || null;
  } catch {
    return null;
  }
}

function canonical(p) {
  try {
    return fs.realpathSync(p);
  } catch {
    return null;
  }
}

// D per spec §2, no override. A git failure from the module's directory is retried from the current directory.
function slotDir({ from } = {}) {
  const common = gitCommonDir(from || __dirname) || gitCommonDir(process.cwd());
  const c = common && canonical(common);
  return c ? path.join(c, "check-all-slots") : null;
}

function samePath(a, b, platform) {
  if (!a || !b) return false;
  return platform === "win32" ? a.toLowerCase() === b.toLowerCase() : a === b;
}

function readOwnerPid(lockPath) {
  try {
    const text = fs.readFileSync(lockPath.replace(/\.lock$/, ".owner"), "utf8");
    const m = /^pid=(\d+)$/m.exec(text);
    return m ? Number(m[1]) : 0;
  } catch {
    return 0;
  }
}

function readStat(procRoot, pid) {
  try {
    const stat = fs.readFileSync(path.join(procRoot, String(pid), "stat"), "utf8");
    return stat.slice(stat.lastIndexOf(")") + 2).split(" ");
  } catch {
    return null;
  }
}

// D-T1.14: the holder is alive and is the caller or an ancestor (4th /proc stat field, at most 64 steps).
function isAncestor(holder, caller, procRoot) {
  const own = holder > 0 ? readStat(procRoot, holder) : null;
  if (!own || own[0] === "Z") return false;
  let p = caller;
  for (let i = 0; i <= 64 && p > 0; i++) {
    if (p === holder) return true;
    const f = readStat(procRoot, p);
    if (!f) return false;
    p = Number(f[1]);
  }
  return false;
}

// Linux: someone holds an flock on the file when /proc/locks lists its device and inode. Never creates the file.
function lockHeld(lockPath, { procRoot = "/proc", platform = process.platform } = {}) {
  let st;
  try {
    st = fs.statSync(lockPath, { bigint: true });
  } catch {
    return false;
  }
  if (platform === "win32") {
    // The pwsh holder opens with FileShare.None, so any open fails while it is held.
    try {
      fs.closeSync(fs.openSync(lockPath, "r"));
      return false;
    } catch (e) {
      return e.code === "EBUSY" || e.code === "EPERM" || e.code === "EACCES";
    }
  }
  const dev = st.dev;
  const major = Number(((dev >> 8n) & 0xfffn) | ((dev >> 32n) & ~0xfffn));
  const minor = Number((dev & 0xffn) | ((dev >> 12n) & ~0xffn));
  const want = `${major.toString(16).padStart(2, "0")}:${minor.toString(16).padStart(2, "0")}:${st.ino}`;
  let text;
  try {
    text = fs.readFileSync(path.join(procRoot, "locks"), "utf8");
  } catch {
    return false;
  }
  for (const line of text.split("\n")) {
    if (line.includes("->")) continue;
    const f = line.trim().split(/\s+/);
    if (f[1] === "FLOCK" && f[5] === want) return true;
  }
  return false;
}

// One marker (spec §2), in order: set; in D with the right name; holder is self or an ancestor (Linux); held.
function markerTest(value, name, { slotDir: dir, pid, procRoot, platform }) {
  if (!value) return { ok: false, reason: "ASSETOPS_HEAVY_SLOT is not set" };
  const pool = { ok: false, reason: "the marker is not a slot of this machine's pool" };
  if (!dir) return pool;
  const leaf = path.basename(value);
  if (!(name === "db" ? /^db-job\.lock$/ : /^slot-[12]\.lock$/).test(leaf)) return pool;
  if (!samePath(canonical(path.dirname(value)), dir, platform)) return pool;
  const lock = path.join(dir, leaf);
  if (platform !== "win32" && !isAncestor(readOwnerPid(lock), pid, procRoot)) {
    return { ok: false, reason: "the slot's holder is not this process or an ancestor" };
  }
  if (!lockHeld(lock, { procRoot, platform })) return { ok: false, reason: "the slot is not held" };
  return { ok: true, reason: "" };
}

// The tripwire's test. `db`: the caller is a database job, so ASSETOPS_HEAVY_DB must pass too.
function checkMarker(env, { slotDir: dir, pid = process.pid, procRoot = "/proc", platform = process.platform,
                           inContainer = false, db = false } = {}) {
  if (inContainer) {
    const v = env.ASSETOPS_HEAVY_SLOT_CONTAINER;
    if (v === "db") return { ok: true, reason: "" };
    if (v === "slot") {
      return db ? { ok: false, reason: "a database job needs --db on the outermost wrapper" } : { ok: true, reason: "" };
    }
    return { ok: false, reason: "in a container without ASSETOPS_HEAVY_SLOT_CONTAINER" };
  }
  const opts = { slotDir: dir, pid, procRoot, platform };
  const slot = markerTest(env.ASSETOPS_HEAVY_SLOT, "slot", opts);
  if (!slot.ok) return slot;
  if (db && !markerTest(env.ASSETOPS_HEAVY_DB, "db", opts).ok) {
    return { ok: false, reason: "a database job needs --db on the outermost wrapper" };
  }
  return { ok: true, reason: "" };
}

function refusal(tool, reason, db) {
  const sh = db ? "--db " : "";
  const ps = db ? "-Db " : "";
  return `heavy-slot: refused: ${tool} runs only inside the heavy-tool slot pool (${reason}).\n` +
    `Run it as: tools/heavy-slot.sh ${sh}-- <your command>   (from frontend/: ../tools/heavy-slot.sh; ` +
    `pwsh: pwsh -NoProfile -File tools/heavy-slot.ps1 ${ps}-- ...)\n` +
    "RULES §7 (T1).";
}

function assertHeavySlot(tool, { db = false } = {}) {
  const inContainer = process.platform !== "win32" && fs.existsSync("/.dockerenv");
  const dir = inContainer ? null : slotDir();
  const r = checkMarker(process.env, { slotDir: dir, inContainer, db });
  if (r.ok) return;
  process.stderr.write(refusal(tool, r.reason, db) + "\n");
  process.exit(69);
}

exports.slotDir = slotDir;
exports.checkMarker = checkMarker;
exports.lockHeld = lockHeld;
exports.refusal = refusal;
exports.assertHeavySlot = assertHeavySlot;
