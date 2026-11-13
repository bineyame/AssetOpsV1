"""MB-1 (rev 7 section 7.6, D-17N.6): live Modbus readings on the demo stack, through the Kobo edge gateway UP-1 shares.

    python tools/demo_live_field.py start  --work <work> --site KOBO-001 [--from <Z>] [--hours N]
    python tools/demo_live_field.py status --work <work>
    python tools/demo_live_field.py stop   --work <work>
    python tools/demo_live_field.py check  --work <work>

`tools/demo_combined.py live-field` runs these in the demo tree with the serve environment (DATABASE_URL set).

- Switch: `ASSETOPS_LIVE_FIELD_SITES` must name the Site (off by default). `serve` starts the Kobo edge gateway and the
  TLS central when this switch or UP-1's is set (D-UP.2: one edge gateway, never a second one for Kobo).
- Readings: the registered `kobo-mini-grid-prolonged` simulator run over the live window `[from, from + hours]`
  (at most 8 hours), generated in memory (`field_observation_fixtures.generate_live_window`); no draft run is written
  to the demo DB. The GX-shaped emulator replays it at real time (rate 1, source time = wall time) on 127.0.0.1:5020.
- The poller (`assetops_field.modbus_poller`, profile `gx-system-illustrative-2`, wall clock) reads it over Modbus
  TCP and admits to the edge gateway over its IPC link; the gateway uploads over TLS to `serve_tls` every 60 s.
- Overlap rule: `start` refuses when any profile source already holds accepted evidence after `from` (a UP-1 file or
  a story day); `check` is the finish check: no overlapping (Site, source signal, interval) where either row came through
  the edge gateway's epoch.
- The profile's sources that are still disabled are enabled through `provision_gateway enable-source` (the
  credential is not re-issued, so UP-1's upload credential stays valid).
- Both children run in their own session and outlive this command; `stop` kills them by PID.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import demo_upload_gateway as ug

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "field" / "profiles" / "gx-system-illustrative-2.json"
EMULATOR = ROOT / "field" / "tests" / "field_emulators" / "gx_server.py"
SWITCH_ENV = "ASSETOPS_LIVE_FIELD_SITES"
SITE = ug.SITE
ACTOR = "service:demo-live-field"
EMULATOR_HOST, EMULATOR_PORT = "127.0.0.1", 5020
MAX_HOURS = 8  # field_observation_fixtures.LIVE_WINDOW_MAX_HOURS: one prolonged run
STEP = timedelta(minutes=5)
LIVE_REL = Path("live-field")
PIDS, EXPECT = "pids.json", "expect-identity.json"


class LiveFieldRefused(Exception):
    pass


def live_dir(work: Path) -> Path:
    return work / LIVE_REL


def switched_sites(environ: Mapping[str, str] = os.environ) -> set[str]:
    return {s.strip() for s in (environ.get(SWITCH_ENV) or "").split(",") if s.strip()}


def live_switched_on(environ: Mapping[str, str] = os.environ) -> bool:
    return SITE in switched_sites(environ)  # only KOBO-001 starts the shared gateway (as UP-1's switch does)


def zulu(instant: datetime) -> str:
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_zulu(text: str) -> datetime:
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise LiveFieldRefused(f"--from {text!r} is not a UTC instant like 2026-11-17T09:00:00Z") from None


def live_window(from_text: str | None, hours: int, now: datetime) -> tuple[datetime, datetime]:
    """`[start, end]`: `--from` (default now) floored to 5 minutes, for `hours` (1..8, one simulator run)."""
    if not 1 <= hours <= MAX_HOURS:
        raise LiveFieldRefused(f"--hours must be 1..{MAX_HOURS} (one simulator run)")
    base = parse_zulu(from_text) if from_text else now.astimezone(timezone.utc).replace(microsecond=0)
    start = base - timedelta(minutes=base.minute % 5, seconds=base.second)
    end = start + timedelta(hours=hours)
    if end <= now:
        raise LiveFieldRefused(f"the window {zulu(start)}..{zulu(end)} is already over; nothing would be read")
    return start, end


def overlap_refusal(latest: Mapping[str, datetime], start: datetime) -> list[str]:
    """The profile signals whose latest accepted reading lies after `start`: MB-1 would overlap them."""
    return sorted(signal for signal, at in latest.items() if at > start)


def child_env(root: Path, base: Mapping[str, str] = os.environ) -> dict[str, str]:
    env = dict(base)
    env["PYTHONPATH"] = os.pathsep.join(str(root / p) for p in ("contracts", "gateway", "field", "field/tests"))
    env["PYTHONUNBUFFERED"] = "1"
    return env


def emulator_argv(python: str, jsonl: Path, start: datetime, end: datetime, port: int = EMULATOR_PORT) -> list[str]:
    """Rate 1 with the wall epoch equal to the replay start: the emulator's source time is the wall clock."""
    return [python, str(EMULATOR), "--jsonl", str(jsonl), "--profile", str(PROFILE), "--host", EMULATOR_HOST,
            "--port", str(port), "--replay-start", zulu(start), "--replay-rate", "1", "--replay-wall-epoch",
            zulu(start), "--stop-at", zulu(end + timedelta(minutes=1))]


def poller_argv(python: str, gateway: Mapping[str, str], expect: Path, state: Path, end: datetime,
                port: int = EMULATOR_PORT) -> list[str]:
    """The wall-clock poller (no replay arguments), stopping at the window's end."""
    return [python, "-m", "assetops_field.modbus_poller", "--profile", str(PROFILE), "--host", EMULATOR_HOST,
            "--port", str(port), "--gateway-address", gateway["gateway_address"], "--ipc-credential",
            gateway["ipc_credential"], "--snapshot-sha256", gateway["snapshot_sha256"], "--expect-identity",
            str(expect), "--state-dir", str(state), "--stop-at", zulu(end)]


def profile_expect(state: Path) -> dict[str, Any]:
    """The poller's expected identity for profile -2 on the edge gateway (its basis and its one epoch)."""
    import field_bench

    basis = json.loads((state / ug.BASIS_FILE).read_text(encoding="utf-8"))
    epoch = (state / ug.EPOCH_FILE).read_text(encoding="utf-8").strip()
    return field_bench.expect_identity_from_snapshot(basis["snapshot_text"],
                                                    json.loads(PROFILE.read_text(encoding="utf-8")), epoch)


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def is_ours(pid: int, name: str) -> bool:
    """The PID still names the process we started (Linux /proc cmdline), not a reused one. Where /proc is absent the
    check cannot be made, so liveness alone decides."""
    marker = "gx_server" if name == "emulator" else "modbus_poller"
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "replace")
    except FileNotFoundError:
        return not Path("/proc/self").exists()
    except OSError:
        return False
    return marker in cmdline


def read_pids(folder: Path) -> dict[str, Any] | None:
    path = folder / PIDS
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def stop(work: Path, kill: Callable[[int, int], None] = os.killpg, is_alive: Callable[[int], bool] = alive,
         ours: Callable[[int, str], bool] = is_ours) -> dict:
    folder = live_dir(work)
    pids = read_pids(folder)
    if pids is None:
        return {"stopped": []}
    stopped = []
    for name in ("poller", "emulator"):
        pid = pids.get(name)
        if pid and is_alive(pid) and ours(pid, name):
            try:
                kill(pid, signal.SIGTERM)  # its own session: the group is the child alone
                stopped.append({name: pid})
            except ProcessLookupError:
                pass
    (folder / PIDS).unlink(missing_ok=True)
    return {"stopped": stopped}


# ---- the database reads (backend imports inside; run with DATABASE_URL) -------------------------------------------
def _engine():
    from sqlalchemy import create_engine

    from assetops_backend.config import database_url

    return create_engine(database_url())


def latest_accepted(expect: Mapping[str, Any]) -> dict[str, datetime]:
    from sqlalchemy import text

    names: dict[str, list[str]] = {}
    for signal, source in expect["row_sources"].items():
        names.setdefault(source, []).append(signal)
    engine = _engine()
    try:
        with engine.connect() as c:
            rows = c.execute(text("SELECT source_id::text AS s, max(source_time) AS latest FROM accepted_evidence "
                                  "WHERE tenant_id = :t AND site_id = :site AND source_id::text = ANY(:ids) "
                                  "GROUP BY source_id"),
                             {"t": expect["tenant_id"], "site": expect["site_id"], "ids": list(names)}).all()
    finally:
        engine.dispose()
    return {signal: r.latest for r in rows for signal in names[r.s]}


def disabled_sources(expect: Mapping[str, Any]) -> list[str]:
    from sqlalchemy import text

    engine = _engine()
    try:
        with engine.connect() as c:
            rows = c.execute(text("SELECT source_external_id FROM source WHERE id::text = ANY(:ids) "
                                  "AND disabled_at IS NOT NULL ORDER BY source_external_id"),
                             {"ids": sorted(set(expect["row_sources"].values()))}).all()
    finally:
        engine.dispose()
    return [r.source_external_id for r in rows]


OVERLAP_SQL = (
    "SELECT a.device_id, a.signal_id, a.role, count(*) AS pairs FROM accepted_evidence a JOIN accepted_evidence b "
    "ON b.tenant_id = a.tenant_id AND b.site_id = a.site_id AND b.source_id = a.source_id "
    "AND b.device_id = a.device_id AND b.signal_id = a.signal_id AND b.id <> a.id "
    "AND ((a.interval_start IS NOT NULL AND b.interval_start IS NOT NULL "
    "      AND a.interval_start < b.interval_end AND b.interval_start < a.interval_end) "
    "  OR (a.interval_start IS NULL AND b.interval_start IS NULL AND a.source_time = b.source_time)) "
    "WHERE a.tenant_id = :t AND a.site_id = :site AND a.sequence_epoch = :epoch "
    "AND b.source_time >= :lo GROUP BY a.device_id, a.signal_id, a.role ORDER BY 1, 2"
)


def check(work: Path) -> dict:
    """The finish check: no (Site, source, interval) holds two accepted readings where one came through the edge
    gateway (UP-1's file or MB-1's live feed)."""
    from sqlalchemy import text

    state = ug.state_dir(work)
    expect = profile_expect(state)
    engine = _engine()
    try:
        with engine.connect() as c:
            lo = c.execute(text("SELECT min(source_time) FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s "
                                "AND sequence_epoch = :e"), {"t": expect["tenant_id"], "s": expect["site_id"],
                                                             "e": expect["sequence_epoch"]}).scalar_one()
            rows = [] if lo is None else c.execute(text(OVERLAP_SQL), {
                "t": expect["tenant_id"], "site": expect["site_id"], "epoch": expect["sequence_epoch"],
                "lo": lo - timedelta(days=1)}).mappings().all()
    finally:
        engine.dispose()
    return {"ok": not rows, "edge_epoch": expect["sequence_epoch"], "overlaps": [dict(r) for r in rows]}


# ---- start / status --------------------------------------------------------------------------------------------
def _enable(gateway_external_id: str, sources: list[str], run: Callable[..., Any] = subprocess.run) -> None:
    for source in sources:
        done = run([sys.executable, "-m", "assetops_backend.evidence.provision_gateway", "enable-source",
                    "--tenant", ug.TENANT, "--site", SITE, "--gateway", gateway_external_id, "--source", source,
                    "--actor", ACTOR], capture_output=True, text=True)
        if done.returncode != 0:
            raise LiveFieldRefused(f"enable-source {source} failed: {(done.stderr or '')[-400:]}")


def _spawn(argv: list[str], log: Path, env: dict[str, str]) -> subprocess.Popen:
    with open(log, "w", encoding="utf-8") as out:
        return subprocess.Popen(argv, cwd=str(ROOT), env=env, stdout=out, stderr=subprocess.STDOUT,
                                start_new_session=True)


def start(work: Path, site: str, from_text: str | None, hours: int, *, environ: Mapping[str, str] = os.environ,
          now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> dict:
    if site != SITE:
        raise LiveFieldRefused(f"live Modbus is built for {SITE} only")
    if site not in switched_sites(environ):
        raise LiveFieldRefused(f"{SWITCH_ENV} does not name {site}: live Modbus is off")
    gateway_file = work / ug.GATEWAY_FILE
    if not gateway_file.is_file():
        raise LiveFieldRefused(f"{gateway_file} is missing: start `demo_combined.py serve` with {SWITCH_ENV} set "
                               "first (it starts and activates the Kobo edge gateway)")
    folder = live_dir(work)
    running = read_pids(folder)
    if running and any(alive(p) and is_ours(p, k) for k, p in running.items() if k in ("poller", "emulator")):
        raise LiveFieldRefused(f"live Modbus is already running ({running}); `stop` it first")
    start_at, end_at = live_window(from_text, hours, now())
    state = ug.state_dir(work)
    expect = profile_expect(state)
    late = overlap_refusal(latest_accepted(expect), start_at)
    if late:
        raise LiveFieldRefused(f"already recorded after {zulu(start_at)} for {', '.join(late)}: choose a later --from")
    gateway = json.loads(gateway_file.read_text(encoding="utf-8"))
    snapshot = json.loads(json.loads((state / ug.BASIS_FILE).read_text(encoding="utf-8"))["snapshot_text"])
    enabled = disabled_sources(expect)
    _enable(snapshot["gateway"]["gateway_external_id"], enabled)
    folder.mkdir(parents=True, exist_ok=True)
    ug.write_json(folder / EXPECT, expect)
    import field_observation_fixtures as fixtures

    # the scenario is placed over a whole 8-hour run; `--hours` only stops the emulator and poller earlier
    manifest = fixtures.generate_live_window(folder / "readings", zulu(start_at),
                                             zulu(start_at + timedelta(hours=MAX_HOURS)))
    env = child_env(ROOT, environ)
    python = sys.executable
    logs = work / "logs"
    logs.mkdir(exist_ok=True)
    emulator = _spawn(emulator_argv(python, folder / "readings" / "observations.jsonl", start_at, end_at),
                      logs / "live-field-emulator.log", env)
    pids = {"emulator": emulator.pid, "window": [zulu(start_at), zulu(end_at)]}
    ug.write_json(folder / PIDS, pids)
    try:
        ug.wait_for_line(logs / "live-field-emulator.log", "READY", lambda: emulator.poll() is None, timeout=30)
        poller = _spawn(poller_argv(python, gateway, folder / EXPECT, folder / "poller", end_at),
                        logs / "live-field-poller.log", env)
        pids["poller"] = poller.pid
        ug.write_json(folder / PIDS, pids)
        ug.wait_for_line(logs / "live-field-poller.log", "FIELD-POLLER START", lambda: poller.poll() is None,
                         timeout=60)
    except Exception:  # a start that fails stops what it started (never leaves the emulator or poller behind)
        stop(work)
        raise
    return {**pids, "enabled_sources": enabled, "observations": manifest["observation_count"],
            "readings_sha256": manifest["sha256"]}


def status(work: Path) -> dict:
    from assetops_gateway.ipc import GatewayLink, GatewayUnavailable

    folder = live_dir(work)
    pids = read_pids(folder) or {}
    out: dict[str, Any] = {"running": {k: alive(v) for k, v in pids.items() if k in ("poller", "emulator")},
                           "window": pids.get("window")}
    status_file = folder / "poller" / "status.json"
    if status_file.is_file():
        poller = json.loads(status_file.read_text(encoding="utf-8"))
        out["poller"] = {k: poller.get(k) for k in ("session_start", "counters", "admissions", "holds_by_kind")}
    gateway_file = work / ug.GATEWAY_FILE
    if gateway_file.is_file():
        doc = json.loads(gateway_file.read_text(encoding="utf-8"))
        try:
            out["gateway_queue"] = GatewayLink(doc["gateway_address"], doc["ipc_credential"]).call("diagnostics")["queue"]
        except GatewayUnavailable as error:
            out["gateway_queue"] = f"unavailable: {error}"
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="demo_live_field")
    parser.add_argument("step", choices=["start", "status", "stop", "check"])
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--site", default=SITE)
    parser.add_argument("--from", dest="from_text", default=None, help="UTC ...Z; default now (floored to 5 min)")
    parser.add_argument("--hours", type=int, default=MAX_HOURS)
    args = parser.parse_args(argv)
    try:
        if args.step == "start":
            out = start(args.work, args.site, args.from_text, args.hours)
        elif args.step == "stop":
            out = stop(args.work)
        elif args.step == "check":
            out = check(args.work)
        else:
            out = status(args.work)
    except (LiveFieldRefused, ug.GatewayPrepareRefused) as refused:
        print(json.dumps({"ok": False, "error": str(refused)}))
        return 2
    print(json.dumps({"ok": out.get("ok", True), args.step: out}, default=str))
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
