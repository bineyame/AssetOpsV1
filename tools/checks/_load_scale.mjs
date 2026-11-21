// One rule for wall-time bounds in tests: the bound is scaled by machine load, so a busy host does not fail a test
// that passes alone (owner approval 2026-11-21). factor = clamp(load / cpu_count, 1, 4), load = max(1-minute average, runnable tasks now - 1); a bound never shrinks and
// never grows past 4x (the runnable count catches a burst the lagging average has not seen), so a real slowdown past the scaled bound still fails. Mirrors contracts/tests/load_scale.py.
import fs from "node:fs";
import os from "node:os";

export const LOAD_SCALE_CAP = 4;

function currentLoad() {
  let load = os.loadavg()[0];
  try {
    const running = Number(fs.readFileSync("/proc/loadavg", "utf8").split(/\s+/)[3].split("/")[0]);
    if (Number.isFinite(running)) load = Math.max(load, running - 1);
  } catch { /* not Linux: the average alone */ }
  return load;
}

export function loadFactor(load1 = currentLoad(), cpus = os.cpus().length || 1) {
  return Math.min(LOAD_SCALE_CAP, Math.max(1, load1 / cpus));
}

export function scaleWall(ms, load1, cpus) {
  return ms * loadFactor(load1, cpus);
}
