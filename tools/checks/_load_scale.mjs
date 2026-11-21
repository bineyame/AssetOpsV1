// One rule for wall-time bounds in tests: the bound is scaled by machine load, so a busy host does not fail a test
// that passes alone (owner approval 2026-11-21). factor = clamp(load1 / cpu_count, 1, 4); a bound never shrinks and
// never grows past 4x, so a real slowdown past the scaled bound still fails. Mirrors contracts/tests/load_scale.py.
import os from "node:os";

export const LOAD_SCALE_CAP = 4;

export function loadFactor(load1 = os.loadavg()[0], cpus = os.cpus().length || 1) {
  return Math.min(LOAD_SCALE_CAP, Math.max(1, load1 / cpus));
}

export function scaleWall(ms, load1, cpus) {
  return ms * loadFactor(load1, cpus);
}
