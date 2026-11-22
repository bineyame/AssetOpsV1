"""T1: the in-tool tripwire, Python half (specs/T1-heavy-tool-slot-pool/spec.md §2 and §5.1).

A heavy tool calls ``require("<tool>")`` before it starts work. Outside a held slot of this machine's pool it
prints the refusal and exits 69 (``exit_with`` when given: the conftests pass ``pytest.exit``). Standard library
only. The contract matches ``tools/heavy_slot_check.cjs``.

D is git's common dir (every GIT_* variable removed), canonical, plus /check-all-slots. ASSETOPS_HEAVY_SLOT_DIR is
never read here: a slot held in a private directory never satisfies a tripwire.

T1b (spec-T1b.md §2-§4): two database lanes, each a lock bound to one base database. ``db=True`` needs exclusive
(both --db markers); ``lane=True`` needs a lane, and its database must be that lane's (``lane_database_refusal``).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

_POOL = "the marker is not a slot of this machine's pool"
_HOLDER = "the slot's holder is not this process or an ancestor"
_DB = "a database job needs --db on the outermost wrapper"
_LANE = "a Postgres test run needs --db-lane (or --db) on the outermost wrapper"

# T1b D-T1.19: lane -> its base database in assetopsv1-postgres-1 (tools/run-host-tests.ps1 holds the same names).
LANE_DATABASES = {"a": "assetops_test", "b": "assetops_b_test"}
_LEAVES = {"slot": r"slot-[12]\.lock", "db": r"db-job\.lock", "dbb": r"db-job-b\.lock", "lane": r"db-job(-b)?\.lock"}
_LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")
_WORKERS = "heavy-slot: refused: a database-lane run uses at most -n 2 (T1b); use --db for more."


def _git_common_dir(start: str) -> str | None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run(["git", "-C", start, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                           env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           text=True, check=False)
    except OSError:
        return None
    out = r.stdout.strip() if r.returncode == 0 else ""
    return out or None


def slot_dir(start: str | None = None) -> str | None:
    """D per spec §2, no override. A git failure from ``start`` is retried from the current directory."""
    common = _git_common_dir(start or os.path.dirname(os.path.abspath(__file__))) or _git_common_dir(os.getcwd())
    if not common or not os.path.exists(common):
        return None
    return os.path.join(os.path.realpath(common), "check-all-slots")


def _same(a: str | None, b: str | None, platform: str) -> bool:
    if not a or not b:
        return False
    return a.lower() == b.lower() if platform == "win32" else a == b


def _owner_pid(lock: str) -> int:
    try:
        with open(lock[: -len(".lock")] + ".owner", encoding="utf-8") as f:
            m = re.search(r"^pid=(\d+)$", f.read(), re.M)
    except OSError:
        return 0
    return int(m.group(1)) if m else 0


def _stat(proc_root: str, pid: int) -> list[str] | None:
    try:
        with open(os.path.join(proc_root, str(pid), "stat"), encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    return text[text.rfind(")") + 2:].split(" ")


def _is_ancestor(holder: int, caller: int, proc_root: str) -> bool:
    own = _stat(proc_root, holder) if holder > 0 else None
    if not own or own[0] == "Z":
        return False
    p = caller
    for _ in range(65):
        if p <= 0:
            return False
        if p == holder:
            return True
        fields = _stat(proc_root, p)
        if not fields:
            return False
        p = int(fields[1])
    return False


def lock_held(lock: str, *, proc_root: str = "/proc", platform: str = sys.platform) -> bool:
    """Someone holds an flock on the file (Linux: /proc/locks lists its device and inode). Never creates it."""
    try:
        st = os.stat(lock)
    except OSError:
        return False
    if platform == "win32":
        try:
            with open(lock, "rb"):
                return False
        except PermissionError:
            return True
        except OSError:
            return False
    want = f"{os.major(st.st_dev):02x}:{os.minor(st.st_dev):02x}:{st.st_ino}"
    try:
        with open(os.path.join(proc_root, "locks"), encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return False
    for line in lines:
        if "->" in line:
            continue
        f = line.split()
        if len(f) > 5 and f[1] == "FLOCK" and f[5] == want:
            return True
    return False


def _marker(value: str | None, name: str, *, slot_dir: str | None, pid: int, proc_root: str,
            platform: str) -> tuple[bool, str]:
    if not value:
        return False, "ASSETOPS_HEAVY_SLOT is not set"
    if not slot_dir:
        return False, _POOL
    leaf = os.path.basename(value)
    if not re.fullmatch(_LEAVES.get(name, _LEAVES["slot"]), leaf):
        return False, _POOL
    parent = os.path.dirname(value)
    if not parent or not os.path.isdir(parent) or not _same(os.path.realpath(parent), slot_dir, platform):
        return False, _POOL
    lock = os.path.join(slot_dir, leaf)
    if platform != "win32" and not _is_ancestor(_owner_pid(lock), pid, proc_root):
        return False, _HOLDER
    if not lock_held(lock, proc_root=proc_root, platform=platform):
        return False, "the slot is not held"
    return True, ""


def _opts(slot_dir: str | None, pid: int | None = None, proc_root: str = "/proc",
          platform: str = sys.platform) -> dict:
    return dict(slot_dir=slot_dir, pid=os.getpid() if pid is None else pid, proc_root=proc_root, platform=platform)


def exclusive(env, **opts) -> bool:
    """T1b §2: a --db holder, both exclusive markers pass (ASSETOPS_HEAVY_DB and ASSETOPS_HEAVY_DB_B)."""
    o = _opts(**opts)
    return _marker(env.get("ASSETOPS_HEAVY_DB"), "db", **o)[0] and _marker(env.get("ASSETOPS_HEAVY_DB_B"), "dbb", **o)[0]


def held_lane(env, **opts) -> str | None:
    """T1b §2: ``"a"`` (exclusive, or ASSETOPS_HEAVY_DB_LANE is db-job.lock), ``"b"`` (db-job-b.lock) or None."""
    if exclusive(env, **opts):
        return "a"
    value = env.get("ASSETOPS_HEAVY_DB_LANE")
    if _marker(value, "lane", **_opts(**opts))[0]:
        return "b" if os.path.basename(value) == "db-job-b.lock" else "a"
    return None


def check_marker(env, *, slot_dir: str | None, pid: int | None = None, proc_root: str = "/proc",
                 platform: str = sys.platform, in_container: bool = False, db: bool = False,
                 lane: bool = False) -> tuple[bool, str]:
    """The tripwire's test; returns ``(ok, reason)``. ``db``: exclusive must pass too; ``lane``: a lane must."""
    if in_container:
        # The container runs on its own server (D-T1.22): `slot` satisfies a lane, only `db` a database job.
        v = env.get("ASSETOPS_HEAVY_SLOT_CONTAINER")
        if v == "db":
            return True, ""
        if v == "slot":
            return (False, _DB) if db else (True, "")
        return False, "in a container without ASSETOPS_HEAVY_SLOT_CONTAINER"
    opts = _opts(slot_dir, pid, proc_root, platform)
    ok, reason = _marker(env.get("ASSETOPS_HEAVY_SLOT"), "slot", **opts)
    if not ok:
        return ok, reason
    if db and not exclusive(env, **opts):
        return False, _DB
    if lane and held_lane(env, **opts) is None:
        return False, _LANE
    return True, ""


def _no(lane: str | None, name: str, why: str) -> str:
    return f"heavy-slot: refused: pytest with Postgres in database lane {lane} may not use {name}: {why}."


def lane_database_refusal(lane: str | None, url: str | None, environ=None) -> str | None:
    """T1b §4 (D-T1.22): the refusal line when a lane run's base URL is not safe for that lane, else None."""
    try:
        from assetops_backend.database_target import DatabaseTargetUnclear, database_target
    except ImportError:
        return _no(lane, "that URL", "assetops_backend does not import")
    try:
        target = database_target(url, environ)
    except DatabaseTargetUnclear as e:
        return _no(lane, "that URL", f"the target is unclear ({e.reason})")
    name = target.name
    if not name.endswith("_test"):
        return _no(lane, name, "its name does not end in _test")
    host = target.host.strip("[]")
    if host not in _LOCAL_HOSTS:
        return _no(lane, name, f"the server is not this machine's development server (host {host})")
    for other, base in LANE_DATABASES.items():
        if other != lane and name == base:
            return _no(lane, name, f"it is lane {other}'s database")
    return None


def _in_container() -> bool:
    return sys.platform != "win32" and os.path.exists("/.dockerenv")


def lane_workers_refusal(numprocesses, env=None) -> str | None:
    """T1b D-T1.25: a lane-only holder (a lane, not exclusive) runs at most ``-n 2``; a string such as auto is over."""
    if _in_container():
        return None
    env = os.environ if env is None else env
    opts = dict(slot_dir=slot_dir())
    if held_lane(env, **opts) is None or exclusive(env, **opts):
        return None
    return None if numprocesses in (None, 0, 1, 2) else _WORKERS


def refusal(tool: str, reason: str, db: bool = False, lane: bool = False) -> str:
    sh = "--db " if db else "--db-lane " if lane else ""
    ps = "-Db " if db else "-DbLane " if lane else ""
    return (f"heavy-slot: refused: {tool} runs only inside the heavy-tool slot pool ({reason}).\n"
            f"Run it as: tools/heavy-slot.sh {sh}-- <your command>   (from frontend/: ../tools/heavy-slot.sh; "
            f"pwsh: pwsh -NoProfile -File tools/heavy-slot.ps1 {ps}-- ...)\n"
            "RULES §7 (T1).")


def require(tool: str, *, db: bool = False, lane: bool = False, exit_with=None) -> None:
    in_container = _in_container()
    sd = None if in_container else slot_dir()
    ok, reason = check_marker(os.environ, slot_dir=sd, in_container=in_container, db=db, lane=lane)
    message = None if ok else refusal(tool, reason, db, lane)
    if ok and lane and not in_container:
        url = os.environ.get("ASSETOPS_TEST_DATABASE_BASE_URL") or os.environ.get("ASSETOPS_TEST_DATABASE_URL")
        message = lane_database_refusal(held_lane(os.environ, slot_dir=sd), url)
    if message is None:
        return
    print(message, file=sys.stderr, flush=True)
    if exit_with is not None:
        exit_with(message, returncode=69)
    sys.exit(69)
