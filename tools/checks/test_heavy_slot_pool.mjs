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
import { scaleWall } from "./_load_scale.mjs";

const TOOLS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const COPY = ["heavy-slot.sh", "heavy-slot.ps1", "checks/_heavy_slot.ps1", "heavy_slot_check.cjs", "heavy_slot_check.py",
              "heavy-slot-shims.mjs"];
const SCRUB = ["ASSETOPS_HEAVY_SLOT", "ASSETOPS_HEAVY_DB", "ASSETOPS_HEAVY_DB_B", "ASSETOPS_HEAVY_DB_LANE", "ASSETOPS_HEAVY_SLOT_CONTAINER",
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
  return { child, done, out: () => stdout };
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
  if (!Number.isInteger(pid) || pid <= 0) return; // 0 or a negative pid would signal a whole process group
  try { process.kill(pid, sig); } catch { /* gone */ }
}

// A holder of slot <n> (or of a lock path) outside any wrapper, with no owner file: one process (sleep) holds the fd.
async function rawHold(repo, n) {
  fs.mkdirSync(repo.D, { recursive: true });
  const p = typeof n === "number" ? repo.slot(n) : n;
  const h = start("bash", ["-c", 'exec 9>>"$1"; flock -x 9; exec sleep 120', "hold", p]);
  await waitFor(() => held(p), 8000, `raw hold of ${path.basename(p)}`);
  return h;
}

// T1b: a holder through a wrapper whose child prints its three DB markers, then sleeps; resolves once printed.
const MARKERS = 'echo "lane=${ASSETOPS_HEAVY_DB_LANE-} db=${ASSETOPS_HEAVY_DB-} dbb=${ASSETOPS_HEAVY_DB_B-}"; exec sleep 120';
async function markHold(repo, kind, extra) {
  const args = [...extra, "--", "sh", "-c", MARKERS];
  const h = kind === "bash" ? start("bash", [repo.sh, ...args], { cwd: repo.M })
                            : start(PWSH, ["-NoProfile", "-File", repo.ps, ...args], { cwd: repo.M });
  try {
    await waitFor(() => h.out().includes("\n"), 10000, `${kind} ${extra.join(" ")} holder`);
  } catch (e) {
    await stop(h);
    throw e;
  }
  return h;
}

// A pooled holder through a wrapper; resolves once slot <n> is held.
async function wrapHold(repo, kind, n, extra = []) {
  const args = [...extra, "--", "sleep", "120"];
  const h = kind === "bash" ? start("bash", [repo.sh, ...args], { cwd: repo.M })
                            : start(PWSH, ["-NoProfile", "-File", repo.ps, ...args], { cwd: repo.M });
  // Wait on the owner file, never on a lock probe: a probe that coincides with the holder's own try would push it
  // to the next slot (R8a), which is the pool working as designed, not the case under test.
  try {
    await waitFor(() => ownerField(repo.slot(n), "child") !== "", 10000, `${kind} hold of slot-${n}`);
  } catch (e) {
    await stop(h);
    throw e;
  }
  assert.ok(held(repo.slot(n)), `slot-${n} is held by the ${kind} holder`);
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

describe("T1 heavy-slot pool", { concurrency: 4 }, () => {
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
      assert.ok(out.ms >= 3000 && out.ms <= scaleWall(6000), `took ${out.ms} ms`);
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
      assert.ok(out.ms < scaleWall(5000), `took ${out.ms} ms`);
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
      assert.ok(a.ms < scaleWall(5000), `pwsh outer took ${a.ms} ms`);
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
      assert.ok(b.ms < scaleWall(5000), `Enter-HeavySlot outer took ${b.ms} ms`);
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
        assert.ok(out.ms < scaleWall(5000), `took ${out.ms} ms`);
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
        assert.ok(Date.now() - t0 <= scaleWall(6000), `took ${Date.now() - t0} ms`);
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
      assert.ok(Date.now() - t0 <= scaleWall(6000));
      assert.equal(held(r.slot(1)), false);
    } finally { killQuiet(child); killQuiet(h.child.pid); cleanup(r); }
  });

  // D-T1.15a. A python job whose cleanup (a `finally`) takes 9 s; SIGTERM is turned into SystemExit so TERM runs it too.
  const FIN9 = 'import signal, sys, time\nsignal.signal(signal.SIGTERM, lambda *a: sys.exit(143))\n' +
               'try:\n    print("started", flush=True)\n    time.sleep(60)\nfinally:\n    time.sleep(9)\n    print("cleanup ran", flush=True)\n';
  async function finJob(kind) {
    const r = makeRepo();
    const script = path.join(r.root, "fin.py");
    fs.writeFileSync(script, FIN9);
    const h = kind === "bash" ? start("bash", [r.sh, "--", "python3", script], { cwd: r.M, detached: true })
                              : start(PWSH, ["-NoProfile", "-File", r.ps, "--", "python3", script], { cwd: r.M, detached: true });
    await waitFor(() => ownerField(r.slot(1), "child") !== "", 10000, "the child");
    const child = Number(ownerField(r.slot(1), "child"));
    await waitFor(() => h.out().includes("started"), 8000, "python to start");
    return { r, h, child };
  }
  for (const kind of ["bash", "pwsh"]) {
    test(`${kind === "bash" ? "P7c" : "P8c"} Ctrl-C (SIGINT to the group) on the ${kind} wrapper: a 9 s finally finishes, no KILL, the slot frees`, async () => {
      const { r, h, child } = await finJob(kind);
      try {
        process.kill(-h.child.pid, "SIGINT");
        const out = await h.done;
        assert.match(out.stdout, /cleanup ran/, `stdout ${out.stdout} stderr ${out.stderr}`);
        assert.equal(out.code, 130, out.stderr);
        assert.equal(alive(child), false);
        assert.equal(held(r.slot(1)), false);
      } finally { killQuiet(child); killQuiet(h.child.pid); cleanup(r); }
    });
  }

  test("P7d INT to the bash wrapper only: not forwarded (child still running at 5 s); a second INT lets the cleanup finish", async () => {
    const { r, h, child } = await finJob("bash");
    try {
      process.kill(h.child.pid, "SIGINT");
      await new Promise((res) => setTimeout(res, 5000));
      assert.equal(alive(child), true, "the child was stopped by a single INT to the wrapper");
      assert.equal(alive(h.child.pid), true);
      assert.ok(!h.out().includes("cleanup ran"));
      process.kill(h.child.pid, "SIGINT");
      const out = await h.done;
      assert.match(out.stdout, /cleanup ran/, `stdout ${out.stdout} stderr ${out.stderr}`);
      assert.equal(out.code, 130, out.stderr);
      assert.notEqual(out.signal, "SIGKILL");
      assert.equal(held(r.slot(1)), false);
    } finally { killQuiet(child); killQuiet(h.child.pid); cleanup(r); }
  });

  test("P7e TERM to the bash wrapper: the 9 s cleanup finishes inside the 30 s grace, exit is the child's", async () => {
    const { r, h, child } = await finJob("bash");
    try {
      const t0 = Date.now();
      process.kill(h.child.pid, "SIGTERM");
      const out = await h.done;
      assert.match(out.stdout, /cleanup ran/, `stdout ${out.stdout} stderr ${out.stderr}`);
      assert.equal(out.code, 143, out.stderr);
      assert.ok(Date.now() - t0 < scaleWall(30000), `took ${Date.now() - t0} ms`);
      assert.equal(alive(child), false);
      assert.equal(held(r.slot(1)), false);
    } finally { killQuiet(child); killQuiet(h.child.pid); cleanup(r); }
  });

  test("P9 one database job at a time: a second --db entry times out although a slot is free", async () => {
    const r = makeRepo();
    let h;
    try {
      h = await wrapHold(r, "bash", 1, ["--db"]);
      assert.equal(held(path.join(r.D, "db-job.lock")), true);
      // T1b: a --db holder holds both lanes.
      for (const st of [await bashW(r, ["--status"]), await pwshW(r, ["-Status"])]) {
        const lines = st.stdout.trim().split("\n");
        assert.match(lines[2], /^db-job: busy pid=\d+ child=\d+ label=sleep 120 /, st.stdout);
        assert.match(lines[3], /^db-job-b: busy pid=\d+ child=\d+ label=sleep 120 /, st.stdout);
      }
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
      assert.ok(a.ms < scaleWall(3000), `took ${a.ms} ms`);
      const b = await bashW(r, ["--", PWSH, "-NoProfile", "-File", r.ps, "-Db", "-SlotWaitSeconds", "30", "--", "true"]);
      assert.equal(b.code, 69, b.stderr);
      assert.match(b.stderr, line);
      assert.ok(b.ms < scaleWall(5000), `took ${b.ms} ms`);
    } finally { cleanup(r); }
  });

  test("P10 --status: the four lines, free when the file is missing, busy with the owner, holder unknown", async () => {
    const r = makeRepo();
    let h; let x;
    try {
      for (const st of [await bashW(r, ["--status"]), await pwshW(r, ["-Status"])]) {
        assert.equal(st.code, 0, st.stderr);
        assert.deepEqual(st.stdout.trim().split("\n"), ["slot-1: free", "slot-2: free", "db-job: free", "db-job-b: free"]);
      }
      assert.equal(fs.existsSync(path.join(r.D, "db-job.lock")), false, "a status probe never creates a file");
      assert.equal(fs.existsSync(path.join(r.D, "db-job-b.lock")), false, "a status probe never creates a file");
      h = await wrapHold(r, "bash", 1);
      x = await rawHold(r, 2);
      fs.writeFileSync(path.join(r.D, "slot-3.lock"), "");
      for (const st of [await bashW(r, ["--status"]), await pwshW(r, ["-Status"])]) {
        const lines = st.stdout.trim().split("\n");
        assert.match(lines[0], /^slot-1: busy pid=\d+ child=\d+ label=sleep 120 since=\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ cwd=\S+$/);
        assert.equal(lines[1], `slot-2: busy, holder unknown (owner file stale); find it with: fuser -v ${fs.realpathSync(r.D)}/slot-2.lock`);
        assert.equal(lines[2], "slot-3: free");
        assert.equal(lines[3], "db-job: free");
        assert.equal(lines[4], "db-job-b: free");
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

  // ---- T1b (spec-T1b.md §8): two database lanes ----
  const LANES_BUSY = /heavy-slot: both database lanes are busy \(tools\/heavy-slot\.sh --status\); waiting up to 3 s\./;
  const laneOf = (h) => /lane=(\S*)/.exec(h.out())[1];

  test("P16 two --db-lane holders (bash, pwsh) get db-job.lock and db-job-b.lock; a third of each waits and exits 75", async () => {
    const r = makeRepo();
    let a; let b;
    try {
      a = await markHold(r, "bash", ["--db-lane"]);
      const D = fs.realpathSync(r.D);
      b = await markHold(r, "pwsh", ["-DbLane"]);
      assert.equal(laneOf(a), `${D}/db-job.lock`, a.out());
      assert.equal(laneOf(b), `${D}/db-job-b.lock`, b.out());
      assert.match(a.out(), /db= dbb=/, "a lane holder gets no exclusive marker");
      assert.match(b.out(), /db= dbb=/, "a lane holder gets no exclusive marker");
      assert.equal(ownerField(path.join(r.D, "db-job.lock"), "db"), "lane");
      assert.equal(ownerField(path.join(r.D, "db-job-b.lock"), "db"), "lane");
      const [c, d] = await Promise.all([bashW(r, ["--db-lane", "--wait-seconds", "3", "--", "true"]),
                                        pwshW(r, ["-DbLane", "-SlotWaitSeconds", "3", "--", "true"])]);
      for (const out of [c, d]) {
        assert.equal(out.code, 75, out.stderr);
        assert.match(out.stderr, LANES_BUSY);
        assert.match(out.stderr, TIMEOUT_LINE);
      }
    } finally { await stop(a); await stop(b); cleanup(r); }
  });

  test("P17 --db waits on lane b while a --db-lane holds it; --db-lane waits while a --db holds both", async () => {
    const r = makeRepo();
    let x; let lb; let ex;
    try {
      x = await rawHold(r, path.join(r.D, "db-job.lock"));
      lb = await markHold(r, "bash", ["--db-lane"]);
      assert.match(laneOf(lb), /\/db-job-b\.lock$/, lb.out());
      await stop(x); x = null;
      for (const out of await Promise.all([bashW(r, ["--db", "--wait-seconds", "3", "--", "true"]),
                                           pwshW(r, ["-Db", "-SlotWaitSeconds", "3", "--", "true"])])) {
        assert.equal(out.code, 75, out.stderr);
        assert.match(out.stderr, /heavy-slot: another database job holds db-job-b\.lock; waiting up to 3 s\./);
        assert.doesNotMatch(out.stderr, /holds db-job\.lock/);
      }
      assert.equal(held(path.join(r.D, "db-job.lock")), false, "a timed-out --db releases lane a");
      await stop(lb); lb = null;
      ex = await markHold(r, "bash", ["--db"]);
      assert.match(ex.out(), /^lane= db=\S+\/db-job\.lock dbb=\S+\/db-job-b\.lock$/m, ex.out());
      for (const out of await Promise.all([bashW(r, ["--db-lane", "--wait-seconds", "3", "--", "true"]),
                                           pwshW(r, ["-DbLane", "-SlotWaitSeconds", "3", "--", "true"])])) {
        assert.equal(out.code, 75, out.stderr);
        assert.match(out.stderr, LANES_BUSY);
      }
    } finally { await stop(x); await stop(lb); await stop(ex); cleanup(r); }
  });

  test("P18 nesting: --db-lane inside --db takes nothing; --db inside --db-lane and --db-lane inside a slot exit 69; both flags exit 64", async () => {
    const r = makeRepo();
    try {
      const both = "heavy-slot: --db and --db-lane are exclusive; give one.\n";
      for (const out of [await bashW(r, ["--db", "--db-lane", "--", "true"]), await pwshW(r, ["-Db", "-DbLane", "--", "true"])]) {
        assert.equal(out.code, 64, out.stderr);
        assert.equal(out.stderr, both);
      }
      assert.equal(fs.existsSync(path.join(r.D, "db-job-b.lock")), false, "a usage error takes no lock");
      const inner = (flag) => [["bash", r.sh, flag === "db" ? "--db" : "--db-lane", "--wait-seconds", "30", "--", "true"],
                               [PWSH, "-NoProfile", "-File", r.ps, flag === "db" ? "-Db" : "-DbLane", "-SlotWaitSeconds", "30", "--", "true"]];
      for (const argv of inner("lane")) {
        const ok = await bashW(r, ["--db", "--", ...argv]);
        assert.equal(ok.code, 0, ok.stderr);
        assert.ok(ok.ms < scaleWall(argv[0] === "bash" ? 3000 : 5000), `took ${ok.ms} ms`);
      }
      const dbLine = /heavy-slot: refused: --db inside a held slot; put --db on the outermost wrapper\./;
      const laneLine = /heavy-slot: refused: --db-lane inside a held slot; put --db-lane on the outermost wrapper\./;
      for (const [outer, flag, line] of [[["--db-lane"], "db", dbLine], [[], "lane", laneLine]]) {
        for (const argv of inner(flag)) {
          const out = await bashW(r, [...outer, "--", ...argv]);
          assert.equal(out.code, 69, out.stderr);
          assert.match(out.stderr, line);
          assert.ok(out.ms < scaleWall(argv[0] === "bash" ? 3000 : 5000), `took ${out.ms} ms`);
        }
      }
    } finally { cleanup(r); }
  });


});

const REFUSAL = (tool, reason, db = false) =>
  `heavy-slot: refused: ${tool} runs only inside the heavy-tool slot pool (${reason}).\n` +
  `Run it as: tools/heavy-slot.sh ${db ? "--db " : ""}-- <your command>   (from frontend/: ../tools/heavy-slot.sh; ` +
  `pwsh: pwsh -NoProfile -File tools/heavy-slot.ps1 ${db ? "-Db " : ""}-- ...)\nRULES §7 (T1).\n`;
const NOT_SET = "ASSETOPS_HEAVY_SLOT is not set";
const NOT_POOL = "the marker is not a slot of this machine's pool";
const NOT_ANCESTOR = "the slot's holder is not this process or an ancestor";
const DB_REASON = "a database job needs --db on the outermost wrapper";

// The tripwires as their tools call them, run from M/tools: node, python and pwsh.
const nodeTrip = (r, tool, db = false) => ["node", "-e",
  `require(${JSON.stringify(path.join(r.M, "tools", "heavy_slot_check.cjs"))}).assertHeavySlot(${JSON.stringify(tool)}, { db: ${db} }); console.log("PASSED")`];
const pyTrip = (r, tool, db = false) => ["python3", "-c",
  `import sys; sys.path.insert(0, ${JSON.stringify(path.join(r.M, "tools"))}); import heavy_slot_check as h; ` +
  `h.require(${JSON.stringify(tool)}, db=${db ? "True" : "False"}); print("PASSED")`];
const psTrip = (r, tool, db = false) => [PWSH, "-NoProfile", "-Command",
  `. '${r.mod}'; Assert-HeavySlotHeld -Tool '${tool}'${db ? " -Db" : ""}; 'PASSED'`];
const pooled = (r, argv, extra = [], opts = {}) => run("bash", [r.sh, ...extra, "--", ...argv], { cwd: r.M, ...opts });
const unpooled = (r, argv, opts = {}) => run(argv[0], argv.slice(1), { cwd: r.M, ...opts });

function refused(out, tool, reason, db = false) {
  assert.equal(out.code, 69, `${tool}: code ${out.code}; ${out.stdout}${out.stderr}`);
  assert.ok(out.stderr.includes(REFUSAL(tool, reason, db)), `${tool}: stderr was:\n${out.stderr}`);
  assert.doesNotMatch(out.stdout, /PASSED/);
}
function passed(out, what) {
  assert.equal(out.code, 0, `${what}: ${out.stderr}`);
  assert.match(out.stdout, /PASSED/);
}

describe("T1 heavy-slot tripwires", { concurrency: 4 }, () => {
  test("P-T1 node and python: pooled both pass; unpooled both exit 69 with the exact message", async () => {
    const r = makeRepo();
    try {
      for (const trip of [nodeTrip, pyTrip]) {
        passed(await pooled(r, trip(r, "tsc")), "pooled");
        refused(await unpooled(r, trip(r, "tsc")), "tsc", NOT_SET);
        // The container marker means nothing outside a container (reviewer guide R3).
        refused(await unpooled(r, trip(r, "tsc"), { env: { ASSETOPS_HEAVY_SLOT_CONTAINER: "slot" } }), "tsc", NOT_SET);
      }
    } finally { cleanup(r); }
  });

  test("P-T2 a slot in a private ASSETOPS_HEAVY_SLOT_DIR never satisfies a tripwire", async () => {
    const r = makeRepo();
    try {
      const env = { ASSETOPS_HEAVY_SLOT_DIR: path.join(r.root, "private") };
      for (const trip of [nodeTrip, pyTrip]) refused(await pooled(r, trip(r, "vitest"), [], { env }), "vitest", NOT_POOL);
    } finally { cleanup(r); }
  });

  test("P-T3 a forged marker naming another holder's slot is refused", async () => {
    const r = makeRepo();
    let h;
    try {
      h = await wrapHold(r, "bash", 1);
      const env = { ASSETOPS_HEAVY_SLOT: path.join(fs.realpathSync(r.D), "slot-1.lock") };
      for (const trip of [nodeTrip, pyTrip]) refused(await unpooled(r, trip(r, "tsc"), { env }), "tsc", NOT_ANCESTOR);
    } finally { await stop(h); cleanup(r); }
  });

  test("P-T4 database jobs need --db; the container rule (slot, db) by injected inContainer", async () => {
    const r = makeRepo();
    try {
      for (const trip of [nodeTrip, pyTrip]) {
        refused(await pooled(r, trip(r, "database job", true)), "database job", DB_REASON, true);
        passed(await pooled(r, trip(r, "database job", true), ["--db"]), "--db");
      }
      const cjs = JSON.stringify(path.join(r.M, "tools", "heavy_slot_check.cjs"));
      const node = await run("node", ["-e", `const { checkMarker } = require(${cjs});
        const c = (v, db) => checkMarker({ ASSETOPS_HEAVY_SLOT_CONTAINER: v }, { inContainer: true, db });
        console.log(JSON.stringify([c("slot", false), c("slot", true), c("db", false), c("db", true), c(undefined, false)]));`]);
      const py = await run("python3", ["-c", `import sys, json; sys.path.insert(0, ${JSON.stringify(path.join(r.M, "tools"))})
import heavy_slot_check as h
c = lambda v, db: dict(zip(("ok", "reason"), h.check_marker({"ASSETOPS_HEAVY_SLOT_CONTAINER": v} if v else {}, slot_dir=None, in_container=True, db=db)))
print(json.dumps([c("slot", False), c("slot", True), c("db", False), c("db", True), c(None, False)]))`]);
      const want = [{ ok: true, reason: "" }, { ok: false, reason: DB_REASON }, { ok: true, reason: "" }, { ok: true, reason: "" },
                    { ok: false, reason: "in a container without ASSETOPS_HEAVY_SLOT_CONTAINER" }];
      assert.deepEqual(JSON.parse(node.stdout), want, node.stderr);
      assert.deepEqual(JSON.parse(py.stdout), want, py.stderr);
    } finally { cleanup(r); }
  });

  test("P-T4b T1b: db=True needs --db, not a lane; python lane=True passes under either and fails under a plain slot", async () => {
    const r = makeRepo();
    let a;
    try {
      for (const trip of [nodeTrip, pyTrip]) {
        refused(await pooled(r, trip(r, "database job", true), ["--db-lane"]), "database job", DB_REASON, true);
        passed(await pooled(r, trip(r, "database job", true), ["--db"]), "--db");
      }
      const tools = JSON.stringify(path.join(r.M, "tools"));
      const lane = ["python3", "-c", `import sys, os, json; sys.path.insert(0, ${tools}); import heavy_slot_check as h
print(json.dumps([h.check_marker(os.environ, slot_dir=h.slot_dir(), lane=True), h.held_lane(os.environ, slot_dir=h.slot_dir(), pid=os.getpid())]))`];
      const LANE_REASON = "a Postgres test run needs --db-lane (or --db) on the outermost wrapper";
      const ask = async (extra) => JSON.parse((await pooled(r, lane, extra)).stdout);
      assert.deepEqual(await ask(["--db"]), [[true, ""], "a"]);
      assert.deepEqual(await ask(["--db-lane"]), [[true, ""], "a"]);
      assert.deepEqual(await ask([]), [[false, LANE_REASON], null]);
      a = await wrapHold(r, "bash", 1, ["--db-lane"]);
      assert.deepEqual(await ask(["--db-lane"]), [[true, ""], "b"]);
      const py = await run("python3", ["-c", `import sys, json; sys.path.insert(0, ${tools})
import heavy_slot_check as h
c = lambda v: list(h.check_marker({"ASSETOPS_HEAVY_SLOT_CONTAINER": v}, slot_dir=None, in_container=True, lane=True))
print(json.dumps([c("slot"), c("db")]))`]);
      assert.deepEqual(JSON.parse(py.stdout), [[true, ""], [true, ""]], py.stderr);
      // The refusal names the flag to use.
      const out = await pooled(r, ["python3", "-c", `import sys; sys.path.insert(0, ${tools}); import heavy_slot_check as h; h.require("pytest with Postgres", lane=True)`]);
      assert.equal(out.code, 69, out.stderr);
      assert.ok(out.stderr.includes(`(${LANE_REASON}).\nRun it as: tools/heavy-slot.sh --db-lane -- <your command>`), out.stderr);
      assert.ok(out.stderr.includes("tools/heavy-slot.ps1 -DbLane -- ...)"), out.stderr);
    } finally { await stop(a); cleanup(r); }
  });

  test("P-T8 T1b planted shared-DB use: a lane run pointed at the other lane's base, a non-_test or an off-machine URL exits 69", async () => {
    const r = makeRepo();
    let a;
    try {
      // A Python with SQLAlchemy (assetops_backend.database_target needs it): the guard interpreter or the venv.
      const venv = [process.env.ASSETOPS_GUARD_PYTHON, path.join(TOOLS, "..", ".venv", "bin", "python"),
                    "/opt/assetecon/AssetOpsV1/.venv/bin/python"].find((p) => p && fs.existsSync(p));
      assert.ok(venv, "no Python with SQLAlchemy found (set ASSETOPS_GUARD_PYTHON)");
      const tools = JSON.stringify(path.join(r.M, "tools"));
      const probe = [venv, "-c", `import sys; sys.path.insert(0, ${tools}); import heavy_slot_check as h; h.require('pytest with Postgres', lane=True); print("PASSED")`];
      const env = (host, name) => ({ env: { PYTHONPATH: path.join(TOOLS, "..", "backend"), ASSETOPS_TEST_DATABASE_BASE_URL: undefined,
                                            PGHOST: undefined, PGDATABASE: undefined, PGPORT: undefined, PGSERVICE: undefined,
                                            ASSETOPS_TEST_DATABASE_URL: `postgresql+psycopg://u:p@${host}:1/${name}` } });
      const no = (lane, name, why) => `heavy-slot: refused: pytest with Postgres in database lane ${lane} may not use ${name}: ${why}.\n`;
      const refusedWith = (out, line) => {
        assert.equal(out.code, 69, out.stdout + out.stderr);
        assert.ok(out.stderr.includes(line), out.stderr);
        assert.doesNotMatch(out.stdout, /PASSED/);
      };
      a = await wrapHold(r, "bash", 1, ["--db-lane"]);  // lane a is taken, so the next --db-lane is lane b
      refusedWith(await pooled(r, probe, ["--db-lane"], env("127.0.0.1", "assetops_test")), no("b", "assetops_test", "it is lane a's database"));
      passed(await pooled(r, probe, ["--db-lane"], env("127.0.0.1", "assetops_b_test")), "lane b on assetops_b_test");
      refusedWith(await pooled(r, probe, ["--db-lane"], env("10.0.0.9", "assetops_b_test")),
                  no("b", "assetops_b_test", "the server is not this machine's development server (host 10.0.0.9)"));
      await stop(a); a = null;
      refusedWith(await pooled(r, probe, ["--db-lane"], env("127.0.0.1", "assetops_b_test")), no("a", "assetops_b_test", "it is lane b's database"));
      refusedWith(await pooled(r, probe, ["--db-lane"], env("127.0.0.1", "assetops")), no("a", "assetops", "its name does not end in _test"));
      refusedWith(await pooled(r, probe, ["--db"], env("127.0.0.1", "assetops_b_test")), no("a", "assetops_b_test", "it is lane b's database"));
      passed(await pooled(r, probe, ["--db-lane"], env("127.0.0.1", "assetops_test")), "lane a on assetops_test");
    } finally { await stop(a); cleanup(r); }
  });

  test("P-T5 the tsc shim: refused unpooled, the real tsc pooled, check 0 then 1, a second install changes nothing", async () => {
    const r = makeRepo();
    try {
      const nm = path.join(r.M, "frontend", "node_modules");
      fs.mkdirSync(path.join(nm, "typescript", "bin"), { recursive: true });
      fs.mkdirSync(path.join(nm, ".bin"), { recursive: true });
      fs.writeFileSync(path.join(nm, "typescript", "bin", "tsc"), '#!/usr/bin/env node\nconsole.log("REAL TSC " + process.argv.slice(2).join(" "));\n', { mode: 0o755 });
      fs.symlinkSync("../typescript/bin/tsc", path.join(nm, ".bin", "tsc"));
      const shims = path.join(r.M, "tools", "heavy-slot-shims.mjs");
      const install = await run("node", [shims, "install", nm]);
      assert.equal(install.code, 0, install.stderr);
      assert.equal((await run("node", [shims, "check", nm])).code, 0);
      const bin = path.join(nm, ".bin", "tsc");
      const out = await unpooled(r, [bin, "--noEmit"]);
      assert.equal(out.code, 69, out.stderr);
      assert.ok(out.stderr.includes(REFUSAL("tsc", NOT_SET)), out.stderr);
      const ok = await pooled(r, [bin, "--noEmit"]);
      assert.equal(ok.code, 0, ok.stderr);
      assert.equal(ok.stdout.trim(), "REAL TSC --noEmit");
      const shim = path.join(nm, ".heavy-slot", "tsc.cjs");
      const before = [fs.statSync(shim).mtimeMs, fs.readFileSync(shim, "utf8"), fs.readlinkSync(bin), fs.lstatSync(bin).mtimeMs];
      assert.equal((fs.statSync(shim).mode & 0o777).toString(8), "755");
      assert.equal((await run("node", [shims, "install", nm])).code, 0);
      assert.deepEqual([fs.statSync(shim).mtimeMs, fs.readFileSync(shim, "utf8"), fs.readlinkSync(bin), fs.lstatSync(bin).mtimeMs], before);
      fs.rmSync(bin);
      fs.symlinkSync("../typescript/bin/tsc", bin);
      const check = await run("node", [shims, "check", nm]);
      assert.equal(check.code, 1, check.stdout);
      assert.equal(check.stdout.trim().split("\n").length, 1);
    } finally { cleanup(r); }
  });

  test("P-T7 the pwsh Assert-HeavySlotHeld behaves as P-T1 to P-T3", async () => {
    const r = makeRepo();
    let h;
    try {
      const tool = "the container test runner";
      passed(await pooled(r, psTrip(r, tool)), "pooled");
      refused(await unpooled(r, psTrip(r, tool)), tool, NOT_SET);
      refused(await pooled(r, psTrip(r, tool), [], { env: { ASSETOPS_HEAVY_SLOT_DIR: path.join(r.root, "private") } }), tool, NOT_POOL);
      refused(await pooled(r, psTrip(r, tool, true)), tool, DB_REASON, true);
      h = await wrapHold(r, "bash", 1);
      refused(await unpooled(r, psTrip(r, tool), { env: { ASSETOPS_HEAVY_SLOT: path.join(fs.realpathSync(r.D), "slot-1.lock") } }), tool, NOT_ANCESTOR);
    } finally { await stop(h); cleanup(r); }
  });
});

// Measured alone, after the concurrent cases, so the figure is not the load of 8 parallel cases.
describe("T1 heavy-slot pool, timing", () => {
  test("A11 Enter-HeavySlot returns without a poll wait when a slot is free", async () => {
    const r = makeRepo();
    try {
      const out = await pwshScript(r, "a11.ps1", `. '${r.mod}'
$d = Get-HeavySlotDir '${r.M}/tools'
$w = [Diagnostics.Stopwatch]::StartNew()
$h = Enter-HeavySlot -SlotDir $d -WaitSeconds 5 -Label a11
$ms = $w.Elapsed.TotalMilliseconds
Exit-HeavySlot $h
"{0:F1}" -f $ms
`);
      assert.equal(out.code, 0, out.stderr);
      // The wait loop sleeps up to 2000 ms per poll (_heavy_slot.ps1), so a free slot must return well under one poll;
      // 400 ms (1600 ms at the 4x cap) absorbs pwsh start-up jitter and still fails one poll wait.
      assert.ok(Number(out.stdout.trim()) <= scaleWall(400), `Enter-HeavySlot took ${out.stdout.trim()} ms`);
    } finally { cleanup(r); }
  });
});
