// T1: the heavy-tool slot pool and its tripwires, end to end (specs/T1-heavy-tool-slot-pool/spec.md §7.1).
//
//   node --test tools/checks/test_heavy_slot_pool.mjs
//
// Every case builds its own temp git repository M (one commit) with a worktree W, and copies the pool files into
// both M/tools and W/tools. D is then M/.git/check-all-slots: the real pool of that repository, never this
// machine's. Cases run concurrently. Every spawn scrubs the T1 variables unless the case sets them (I10).
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { describe, test } from "node:test";
import { fileURLToPath } from "node:url";

const TOOLS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const COPY = ["heavy-slot.sh", "heavy-slot.ps1", "checks/_heavy_slot.ps1", "heavy_slot_check.cjs", "heavy_slot_check.py",
              "heavy-slot-shims.mjs"];
const SCRUB = ["ASSETOPS_HEAVY_SLOT", "ASSETOPS_HEAVY_DB", "ASSETOPS_HEAVY_SLOT_CONTAINER",
               "DOTNET_SYSTEM_IO_DISABLEFILELOCKING", "ASSETOPS_HEAVY_SLOT_DIR"];
const PWSH = "pwsh";
const live = new Set();

function envWith(extra = {}) {
  const env = {};
  for (const [k, v] of Object.entries(process.env)) if (!SCRUB.includes(k) && !k.startsWith("GIT_")) env[k] = v;
  for (const [k, v] of Object.entries(extra)) if (v === undefined) delete env[k]; else env[k] = v;
  return env;
}

function git(cwd, ...args) {
  const r = spawnSync("git", ["-c", "user.name=t1", "-c", "user.email=t1@example.invalid", ...args],
                      { cwd, env: envWith(), encoding: "utf8" });
  if (r.status !== 0) throw new Error(`git ${args.join(" ")}: ${r.stderr}`);
  return r.stdout.trim();
}

function makeRepo() {
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "t1-pool-")));
  const M = path.join(root, "M");
  const W = path.join(root, "W");
  fs.mkdirSync(M);
  git(M, "init", "-q");
  git(M, "commit", "-q", "--allow-empty", "-m", "t1");
  git(M, "worktree", "add", "-q", "--detach", W);
  for (const top of [M, W]) {
    fs.mkdirSync(path.join(top, "tools", "checks"), { recursive: true });
    for (const f of COPY) {
      if (fs.existsSync(path.join(TOOLS, f))) fs.copyFileSync(path.join(TOOLS, f), path.join(top, "tools", f));
    }
    fs.chmodSync(path.join(top, "tools", "heavy-slot.sh"), 0o755);
  }
  const D = path.join(M, ".git", "check-all-slots");
  return { root, M, W, D, sh: path.join(M, "tools", "heavy-slot.sh"), ps: path.join(M, "tools", "heavy-slot.ps1"),
           mod: path.join(M, "tools", "checks", "_heavy_slot.ps1"), slot: (n) => path.join(D, `slot-${n}.lock`) };
}

function cleanup(repo) {
  fs.rmSync(repo.root, { recursive: true, force: true });
}

// Start a process; `done` resolves to { code, signal, stdout, stderr, ms }.
function start(cmd, args, { cwd, env = {}, input, detached = false } = {}) {
  const t0 = Date.now();
  const child = spawn(cmd, args, { cwd, env: envWith(env), detached, stdio: ["pipe", "pipe", "pipe"] });
  live.add(child);
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (d) => { stdout += d; });
  child.stderr.on("data", (d) => { stderr += d; });
  if (input !== undefined) child.stdin.end(input); else child.stdin.end();
  const done = new Promise((resolve) => {
    child.on("close", (code, signal) => { live.delete(child); resolve({ code, signal, stdout, stderr, ms: Date.now() - t0 }); });
  });
  return { child, done };
}
const run = (cmd, args, opts) => start(cmd, args, opts).done;
const bashW = (repo, args, opts = {}) => run("bash", [opts.via || repo.sh, ...args], { cwd: repo.M, ...opts });
const pwshW = (repo, args, opts = {}) => run(PWSH, ["-NoProfile", "-File", opts.via || repo.ps, ...args], { cwd: repo.M, ...opts });
const pwshScript = (repo, file, text, opts = {}) => {
  const p = path.join(repo.root, file);
  fs.writeFileSync(p, text);
  return run(PWSH, ["-NoProfile", "-File", p], { cwd: repo.M, ...opts });
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitFor(pred, ms = 8000, what = "condition") {
  const t0 = Date.now();
  while (!pred()) {
    if (Date.now() - t0 > ms) throw new Error(`timed out waiting for ${what}`);
    await sleep(50);
  }
}

// A probe for the test only: a shared flock would block while anyone holds the exclusive lock.
function held(p) {
  if (!fs.existsSync(p)) return false;
  return spawnSync("flock", ["-n", "-s", "-E", "99", p, "true"]).status === 99;
}

function ownerField(lock, field) {
  try {
    const m = new RegExp(`^${field}=(.*)$`, "m").exec(fs.readFileSync(lock.replace(/\.lock$/, ".owner"), "utf8"));
    return m ? m[1] : "";
  } catch {
    return "";
  }
}

function alive(pid) {
  try {
    const s = fs.readFileSync(`/proc/${pid}/stat`, "utf8");
    return s.slice(s.lastIndexOf(")") + 2)[0] !== "Z";
  } catch {
    return false;
  }
}

function tree(pid) {
  const out = [pid];
  let dirs = [];
  try { dirs = fs.readdirSync(`/proc/${pid}/task`); } catch { return out; }
  for (const t of dirs) {
    let kids = "";
    try { kids = fs.readFileSync(`/proc/${pid}/task/${t}/children`, "utf8"); } catch { continue; }
    for (const k of kids.trim().split(/\s+/).filter(Boolean)) out.push(...tree(Number(k)));
  }
  return out;
}

function killQuiet(pid, sig = "SIGKILL") {
  try { process.kill(pid, sig); } catch { /* gone */ }
}

// A holder of slot <n> outside any wrapper, with no owner file: one process (sleep) holds the flocked fd.
async function rawHold(repo, n) {
  fs.mkdirSync(repo.D, { recursive: true });
  const h = start("bash", ["-c", 'exec 9>>"$1"; flock -x 9; exec sleep 120', "hold", repo.slot(n)]);
  await waitFor(() => held(repo.slot(n)), 8000, `raw hold of slot-${n}`);
  return h;
}

// A pooled holder through a wrapper; resolves once slot <n> is held.
async function wrapHold(repo, kind, n, extra = []) {
  const args = [...extra, "--", "sleep", "120"];
  const h = kind === "bash" ? start("bash", [repo.sh, ...args], { cwd: repo.M })
                            : start(PWSH, ["-NoProfile", "-File", repo.ps, ...args], { cwd: repo.M });
  await waitFor(() => held(repo.slot(n)) && ownerField(repo.slot(n), "child") !== "", 10000, `${kind} hold of slot-${n}`);
  return h;
}

async function stop(h) {
  if (!h) return;
  killQuiet(h.child.pid, "SIGTERM");
  const timer = setTimeout(() => killQuiet(h.child.pid), 6000);
  await h.done;
  clearTimeout(timer);
}

process.on("exit", () => { for (const c of live) killQuiet(c.pid); });

const TIMEOUT_LINE = /heavy-slot: no slot came free in 3 s \((--wait-seconds|-SlotWaitSeconds)\)\./;

describe("T1 heavy-slot pool", { concurrency: 8 }, () => {
  test("P1 a pooled command gets the canonical slot-1 marker; its exit code passes through; the slot frees", async () => {
    const r = makeRepo();
    try {
      const out = await bashW(r, ["--", "sh", "-c", 'echo "$ASSETOPS_HEAVY_SLOT"; exit 7']);
      assert.equal(out.code, 7, out.stderr);
      assert.equal(out.stdout.trim(), fs.realpathSync(r.D) + "/slot-1.lock");
      assert.equal(held(r.slot(1)), false);
    } finally { cleanup(r); }
  });

  test("P2 bash waits for two pwsh holders, then exits 75 with the timeout line", async () => {
    const r = makeRepo();
    let a; let b;
    try {
      a = await wrapHold(r, "pwsh", 1);
      b = await wrapHold(r, "pwsh", 2);
      const out = await bashW(r, ["--wait-seconds", "3", "--", "true"]);
      assert.equal(out.code, 75, out.stderr);
      assert.ok(out.ms >= 3000 && out.ms <= 6000, `took ${out.ms} ms`);
      assert.match(out.stderr, TIMEOUT_LINE);
      assert.match(out.stderr, /both heavy slots are busy \(tools\/heavy-slot\.sh --status\); waiting up to 3 s\./);
    } finally { await stop(a); await stop(b); cleanup(r); }
  });

  test("P2c a bash entry and a pwsh entry racing for one free slot: exactly one wins, 20 times", async () => {
    const lanes = 5;
    const per = 4;
    await Promise.all(Array.from({ length: lanes }, async (_, lane) => {
      const r = makeRepo();
      let x;
      try {
        x = await rawHold(r, 1);
        for (let i = 0; i < per; i++) {
          // The winner holds until the loser has finished, so the two always overlap: two winners never exit.
          const release = path.join(r.root, `release-${i}`);
          const hold = ["--", "sh", "-c", 'while [ ! -e "$1" ]; do sleep 0.05; done', "hold", release];
          const delay = 700 + ((lane * per + i) * 47) % 900; // spread around pwsh's start-up time
          const p = pwshW(r, ["-SlotWaitSeconds", "0", ...hold]);
          await sleep(delay);
          const b = bashW(r, ["--wait-seconds", "0", ...hold]);
          let timer;
          const first = await Promise.race([p, b, new Promise((res) => { timer = setTimeout(() => res(null), 15000); })]);
          clearTimeout(timer);
          fs.writeFileSync(release, "");
          const codes = (await Promise.all([p, b])).map((o) => o.code).sort();
          assert.ok(first && first.code === 75, `lane ${lane} iteration ${i}: the first to finish must be the loser`);
          assert.deepEqual(codes, [0, 75], `lane ${lane} iteration ${i} (bash after ${delay} ms)`);
        }
      } finally { await stop(x); cleanup(r); }
    }));
  });

  test("P3 pwsh waits for two bash holders, then exits 75; Test-HeavyLockHeld sees both", async () => {
    const r = makeRepo();
    let a; let b;
    try {
      a = await wrapHold(r, "bash", 1);
      b = await wrapHold(r, "bash", 2);
      const out = await pwshW(r, ["-SlotWaitSeconds", "3", "--", "true"]);
      assert.equal(out.code, 75, out.stderr);
      assert.match(out.stderr, TIMEOUT_LINE);
      const probe = await run(PWSH, ["-NoProfile", "-Command",
        `. '${r.mod}'; Test-HeavyLockHeld '${r.slot(1)}'; Test-HeavyLockHeld '${r.slot(2)}'`]);
      assert.deepEqual(probe.stdout.trim().split(/\s+/), ["True", "True"], probe.stderr);
    } finally { await stop(a); await stop(b); cleanup(r); }
  });

  test("P4 nested bash and pwsh entries inside a bash slot take nothing", async () => {
    const r = makeRepo();
    let x;
    try {
      x = await rawHold(r, 2);
      const out = await bashW(r, ["--", "sh", "-c",
        `bash '${r.sh}' --wait-seconds 8 -- true && ${PWSH} -NoProfile -File '${r.ps}' -SlotWaitSeconds 8 -- true`]);
      assert.equal(out.code, 0, out.stderr);
      assert.ok(out.ms < 5000, `took ${out.ms} ms`);
      assert.doesNotMatch(out.stderr, /ignoring stale|busy/);
    } finally { await stop(x); cleanup(r); }
  });

  test("P4b nested bash inside a pwsh wrapper and inside the Enter-HeavySlot (check-all) path", async () => {
    const r = makeRepo();
    let x;
    try {
      x = await rawHold(r, 2);
      const a = await pwshW(r, ["--", "bash", r.sh, "--wait-seconds", "8", "--", "true"]);
      assert.equal(a.code, 0, a.stderr);
      assert.ok(a.ms < 5000, `pwsh outer took ${a.ms} ms`);
      const b = await pwshScript(r, "p4b.ps1", `
. '${r.mod}'
$h = Enter-HeavySlot -SlotDir (Get-HeavySlotDir '${r.M}/tools') -WaitSeconds 5 -Label p4b
if (-not $h -or $h.Nested) { exit 3 }
$env:ASSETOPS_HEAVY_SLOT = $h.SlotPath
& bash '${r.sh}' --wait-seconds 8 -- true
$c = $LASTEXITCODE
Exit-HeavySlot $h
exit $c
`);
      assert.equal(b.code, 0, b.stderr);
      assert.ok(b.ms < 5000, `Enter-HeavySlot outer took ${b.ms} ms`);
      assert.doesNotMatch(a.stderr + b.stderr, /ignoring stale|busy/);
    } finally { await stop(x); cleanup(r); }
  });

  test("P4c nesting holds across the main checkout, a worktree and a symlinked path", async () => {
    const r = makeRepo();
    let x;
    try {
      x = await rawHold(r, 2);
      const link = path.join(r.root, "Mlink");
      fs.symlinkSync(r.M, link);
      const shW = path.join(r.W, "tools", "heavy-slot.sh");
      const shL = path.join(link, "tools", "heavy-slot.sh");
      for (const [outer, inner, cwd] of [[r.sh, shW, r.M], [shW, r.sh, r.W], [shL, shW, link]]) {
        const out = await run("bash", [outer, "--", "bash", inner, "--wait-seconds", "8", "--", "sh", "-c", 'echo "$ASSETOPS_HEAVY_SLOT"'], { cwd });
        assert.equal(out.code, 0, `${outer} -> ${inner}: ${out.stderr}`);
        assert.equal(out.stdout.trim(), fs.realpathSync(r.D) + "/slot-1.lock");
        assert.doesNotMatch(out.stderr, /ignoring stale|busy/);
        assert.ok(out.ms < 5000, `took ${out.ms} ms`);
      }
    } finally { await stop(x); cleanup(r); }
  });

  for (const kind of ["bash", "pwsh"]) {
    test(`P5 stale markers are ignored with their reason and the entry acquires normally (${kind})`, async () => {
      const r = makeRepo();
      let h;
      try {
        const D = fs.realpathSync(path.join(r.M, ".git")) + "/check-all-slots";
        fs.mkdirSync(D, { recursive: true });
        const cmd = ["sh", "-c", 'echo "$ASSETOPS_HEAVY_SLOT"'];
        const go = (marker) => (kind === "bash" ? bashW(r, ["--wait-seconds", "5", "--", ...cmd], { env: { ASSETOPS_HEAVY_SLOT: marker } })
                                                : pwshW(r, ["-SlotWaitSeconds", "5", "--", ...cmd], { env: { ASSETOPS_HEAVY_SLOT: marker } }));
        // (a) names a free slot
        const a = await go(`${D}/slot-1.lock`);
        assert.equal(a.code, 0, a.stderr);
        assert.match(a.stderr, new RegExp(`ignoring stale ASSETOPS_HEAVY_SLOT=${D}/slot-1.lock \\((the slot's holder is not this process or an ancestor|the slot is not held)\\)`));
        assert.equal(a.stdout.trim(), `${D}/slot-1.lock`);
        // (b) another directory
        const b = await go("/tmp/x/slot-1.lock");
        assert.equal(b.code, 0, b.stderr);
        assert.match(b.stderr, /ignoring stale ASSETOPS_HEAVY_SLOT=\/tmp\/x\/slot-1\.lock \(the marker is not a slot of this machine's pool\)/);
        // (c) a held slot whose holder is not an ancestor (R5)
        h = await wrapHold(r, "bash", 1);
        const c = await go(`${D}/slot-1.lock`);
        assert.equal(c.code, 0, c.stderr);
        assert.match(c.stderr, /ignoring stale .*\(the slot's holder is not this process or an ancestor\)/);
        assert.equal(c.stdout.trim(), `${D}/slot-2.lock`);
      } finally { await stop(h); cleanup(r); }
    });
  }

  test("P5b GIT_DIR and GIT_COMMON_DIR do not move the pool (both wrappers)", async () => {
    const r = makeRepo();
    try {
      const env = { GIT_DIR: "/tmp/x", GIT_COMMON_DIR: "/tmp/x" };
      const cmd = ["--", "sh", "-c", 'echo "$ASSETOPS_HEAVY_SLOT"'];
      const want = fs.realpathSync(r.M) + "/.git/check-all-slots/slot-1.lock";
      const a = await bashW(r, cmd, { env });
      const b = await pwshW(r, cmd, { env });
      assert.equal(a.stdout.trim(), want, a.stderr);
      assert.equal(b.stdout.trim(), want, b.stderr);
    } finally { cleanup(r); }
  });

  for (const kind of ["bash", "pwsh"]) {
    test(`P6${kind === "pwsh" ? "b" : ""} kill -9 of the ${kind} wrapper frees the slot at once`, async () => {
      const r = makeRepo();
      let h;
      let orphan = 0;
      try {
        h = await wrapHold(r, kind, 1);
        orphan = Number(ownerField(r.slot(1), "child"));
        assert.ok(alive(orphan), "the child runs");
        killQuiet(h.child.pid, "SIGKILL");
        await waitFor(() => !held(r.slot(1)), 3000, "the slot to free after kill -9");
        assert.ok(alive(orphan), "the orphan runs on unpooled (accepted, D-T1.2)");
      } finally { killQuiet(orphan); if (h) await h.done; cleanup(r); }
    });
  }

  test("P6c kill -9 of a pwsh process in Enter-HeavySlot with a child: the slot frees, the child holds no lock fd", async () => {
    const r = makeRepo();
    const pidFile = path.join(os.tmpdir(), `t1-p6c-${process.pid}-${Date.now()}`);
    let sleeper = 0;
    let h;
    try {
      const script = path.join(r.root, "p6c.ps1");
      fs.writeFileSync(script, `
. '${r.mod}'
$h = Enter-HeavySlot -SlotDir (Get-HeavySlotDir '${r.M}/tools') -WaitSeconds 5 -Label p6c
$s = Start-Process sleep -ArgumentList 120 -PassThru
Set-Content -LiteralPath '${pidFile}' -Value $s.Id
Start-Sleep -Seconds 120
`);
      h = start(PWSH, ["-NoProfile", "-File", script], { cwd: r.M });
      await waitFor(() => fs.existsSync(pidFile) && fs.readFileSync(pidFile, "utf8").trim() !== "" && held(r.slot(1)), 10000, "p6c holder");
      sleeper = Number(fs.readFileSync(pidFile, "utf8").trim());
      killQuiet(h.child.pid, "SIGKILL");
      await waitFor(() => !held(r.slot(1)), 3000, "the slot to free");
      const fds = fs.readdirSync(`/proc/${sleeper}/fd`).map((f) => { try { return fs.readlinkSync(`/proc/${sleeper}/fd/${f}`); } catch { return ""; } });
      assert.deepEqual(fds.filter((t) => t.includes("check-all-slots")), []);
    } finally { killQuiet(sleeper); if (h) await h.done; fs.rmSync(pidFile, { force: true }); cleanup(r); }
  });

  for (const kind of ["bash", "pwsh"]) {
    test(`P${kind === "bash" ? "7" : "8"} TERM to the ${kind} wrapper: exit 143, the whole tree gone, the slot free`, async () => {
      const r = makeRepo();
      const args = ["--", "sh", "-c", "sleep 30 & wait"];
      const h = kind === "bash" ? start("bash", [r.sh, ...args], { cwd: r.M })
                                : start(PWSH, ["-NoProfile", "-File", r.ps, ...args], { cwd: r.M });
      let pids = [];
      try {
        await waitFor(() => ownerField(r.slot(1), "child") !== "", 10000, "the child");
        const child = Number(ownerField(r.slot(1), "child"));
        await waitFor(() => tree(child).length >= 2, 5000, "the sleep");
        pids = tree(child);
        const t0 = Date.now();
        killQuiet(h.child.pid, "SIGTERM");
        const out = await h.done;
        assert.equal(out.code, 143, out.stderr);
        assert.ok(Date.now() - t0 <= 6000, `took ${Date.now() - t0} ms`);
        await waitFor(() => pids.every((p) => !alive(p)), 2000, "the tree to go");
        assert.equal(held(r.slot(1)), false);
      } finally { for (const p of pids) killQuiet(p); killQuiet(h.child.pid); cleanup(r); }
    });
  }

  test("P7b TERM to the bash wrapper's process group stops the wrapper and its child together", async () => {
    const r = makeRepo();
    const h = start("bash", [r.sh, "--", "sleep", "60"], { cwd: r.M, detached: true });
    let child = 0;
    try {
      await waitFor(() => ownerField(r.slot(1), "child") !== "", 10000, "the child");
      child = Number(ownerField(r.slot(1), "child"));
      const t0 = Date.now();
      process.kill(-h.child.pid, "SIGTERM");
      const out = await h.done;
      assert.ok(out.code === 143 || out.signal === "SIGTERM", `wrapper: code ${out.code} signal ${out.signal}`);
      await waitFor(() => !alive(child), 2000, "the child to stop");
      assert.ok(Date.now() - t0 <= 6000);
      assert.equal(held(r.slot(1)), false);
    } finally { killQuiet(child); killQuiet(h.child.pid); cleanup(r); }
  });

  test("P9 one database job at a time: a second --db entry times out although a slot is free", async () => {
    const r = makeRepo();
    let h;
    try {
      h = await wrapHold(r, "bash", 1, ["--db"]);
      assert.equal(held(path.join(r.D, "db-job.lock")), true);
      const [db2, plain] = await Promise.all([
        bashW(r, ["--db", "--wait-seconds", "3", "--", "true"]),
        bashW(r, ["--wait-seconds", "3", "--", "true"]),
      ]);
      assert.equal(db2.code, 75, db2.stderr);
      assert.match(db2.stderr, /another database job holds db-job\.lock; waiting up to 3 s\./);
      assert.equal(plain.code, 0, plain.stderr);
      const pdb = await pwshW(r, ["-Db", "-SlotWaitSeconds", "3", "--", "true"]);
      assert.equal(pdb.code, 75, pdb.stderr);
    } finally { await stop(h); cleanup(r); }
  });

  test("P9b a nested --db inside a non-DB slot is refused at once (exit 69)", async () => {
    const r = makeRepo();
    try {
      const line = /heavy-slot: refused: --db inside a held slot; put --db on the outermost wrapper\./;
      const a = await bashW(r, ["--", "bash", r.sh, "--db", "--wait-seconds", "30", "--", "true"]);
      assert.equal(a.code, 69, a.stderr);
      assert.match(a.stderr, line);
      assert.ok(a.ms < 3000, `took ${a.ms} ms`);
      const b = await bashW(r, ["--", PWSH, "-NoProfile", "-File", r.ps, "-Db", "-SlotWaitSeconds", "30", "--", "true"]);
      assert.equal(b.code, 69, b.stderr);
      assert.match(b.stderr, line);
      assert.ok(b.ms < 5000, `took ${b.ms} ms`);
    } finally { cleanup(r); }
  });

  test("P10 --status: the three lines, free when the file is missing, busy with the owner, holder unknown", async () => {
    const r = makeRepo();
    let h; let x;
    try {
      for (const st of [await bashW(r, ["--status"]), await pwshW(r, ["-Status"])]) {
        assert.equal(st.code, 0, st.stderr);
        assert.deepEqual(st.stdout.trim().split("\n"), ["slot-1: free", "slot-2: free", "db-job: free"]);
      }
      assert.equal(fs.existsSync(path.join(r.D, "db-job.lock")), false, "a status probe never creates a file");
      h = await wrapHold(r, "bash", 1);
      x = await rawHold(r, 2);
      fs.writeFileSync(path.join(r.D, "slot-3.lock"), "");
      for (const st of [await bashW(r, ["--status"]), await pwshW(r, ["-Status"])]) {
        const lines = st.stdout.trim().split("\n");
        assert.match(lines[0], /^slot-1: busy pid=\d+ child=\d+ label=sleep 120 since=\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ cwd=\S+$/);
        assert.equal(lines[1], `slot-2: busy, holder unknown (owner file stale); find it with: fuser -v ${fs.realpathSync(r.D)}/slot-2.lock`);
        assert.equal(lines[2], "slot-3: free");
        assert.equal(lines[3], "db-job: free");
      }
    } finally { await stop(h); await stop(x); cleanup(r); }
  });

  test("P11 locking disabled: both wrappers refuse with exit 69", async () => {
    const r = makeRepo();
    try {
      const env = { DOTNET_SYSTEM_IO_DISABLEFILELOCKING: "1" };
      for (const out of [await bashW(r, ["--", "true"], { env }), await pwshW(r, ["--", "true"], { env })]) {
        assert.equal(out.code, 69, out.stderr);
        assert.match(out.stderr, /heavy-slot: refused: DOTNET_SYSTEM_IO_DISABLEFILELOCKING is set; the slot locks would not hold\./);
      }
    } finally { cleanup(r); }
  });

  test("P12 a missing -- and a wrapped setsid exit 64 (both wrappers)", async () => {
    const r = makeRepo();
    try {
      const outs = [await bashW(r, ["npx", "tsc"]), await bashW(r, ["--", "setsid", "x"]),
                    await pwshW(r, ["npx", "tsc"]), await pwshW(r, ["--", "setsid", "x"])];
      for (const out of outs) assert.equal(out.code, 64, out.stderr);
      assert.match(outs[1].stderr + outs[3].stderr, /put setsid\/nohup before the wrapper/);
    } finally { cleanup(r); }
  });

  test("P13 the child keeps stdin (R6)", async () => {
    const r = makeRepo();
    try {
      const out = await bashW(r, ["--", "sh", "-c", 'read x; echo "$x"'], { input: "y\n" });
      assert.equal(out.code, 0, out.stderr);
      assert.equal(out.stdout.trim(), "y");
    } finally { cleanup(r); }
  });

  test("P14 a .ps1 command gets its arguments and its exit code passes through (I2)", async () => {
    const r = makeRepo();
    try {
      const script = path.join(r.root, "x.ps1");
      fs.writeFileSync(script, '"[" + ($args -join "|") + "]"\nexit 5\n');
      const out = await pwshW(r, ["--", script, "a", "b"]);
      assert.equal(out.code, 5, out.stderr);
      assert.equal(out.stdout.trim(), "[a|b]");
    } finally { cleanup(r); }
  });

  test("P15 Enter-HeavySlot refuses -Slots 3 (R8c)", async () => {
    const r = makeRepo();
    try {
      const out = await pwshScript(r, "p15.ps1", `. '${r.mod}'\n$h = Enter-HeavySlot -SlotDir (Get-HeavySlotDir '${r.M}/tools') -Slots 3 -WaitSeconds 1\nexit 0\n`);
      assert.equal(out.code, 64, out.stderr);
      assert.match(out.stderr, /the shared pool has 2 slots \(T1\)/);
    } finally { cleanup(r); }
  });


});

// Measured alone, after the concurrent cases, so the figure is not the load of 8 parallel cases.
describe("T1 heavy-slot pool, timing", () => {
  test("A11 Enter-HeavySlot returns within 0.1 s when a slot is free", async () => {
    const r = makeRepo();
    try {
      const out = await pwshScript(r, "a11.ps1", `. '${r.mod}'
$d = Get-HeavySlotDir '${r.M}/tools'
$w = [Diagnostics.Stopwatch]::StartNew()
$h = Enter-HeavySlot -SlotDir $d -WaitSeconds 5 -Label a11
$ms = $w.Elapsed.TotalMilliseconds
Exit-HeavySlot $h
"{0:N1}" -f $ms
`);
      assert.equal(out.code, 0, out.stderr);
      assert.ok(Number(out.stdout.trim()) <= 100, `Enter-HeavySlot took ${out.stdout.trim()} ms`);
    } finally { cleanup(r); }
  });
});
