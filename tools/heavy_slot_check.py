"""T1: the in-tool tripwire, Python half (specs/T1-heavy-tool-slot-pool/spec.md §2 and §5.1).

A heavy tool calls ``require("<tool>")`` before it starts work. Outside a held slot of this machine's pool it
prints the refusal and exits 69 (``exit_with`` when given: the conftests pass ``pytest.exit``). Standard library
only. The contract matches ``tools/heavy_slot_check.cjs``.

D is git's common dir (every GIT_* variable removed), canonical, plus /check-all-slots. ASSETOPS_HEAVY_SLOT_DIR is
never read here: a slot held in a private directory never satisfies a tripwire.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

_POOL = "the marker is not a slot of this machine's pool"
_HOLDER = "the slot's holder is not this process or an ancestor"
_DB = "a database job needs --db on the outermost wrapper"


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
    if not re.fullmatch(r"db-job\.lock" if name == "db" else r"slot-[12]\.lock", leaf):
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


def check_marker(env, *, slot_dir: str | None, pid: int | None = None, proc_root: str = "/proc",
                 platform: str = sys.platform, in_container: bool = False, db: bool = False) -> tuple[bool, str]:
    """The tripwire's test; returns ``(ok, reason)``. ``db``: ASSETOPS_HEAVY_DB must pass too."""
    if in_container:
        v = env.get("ASSETOPS_HEAVY_SLOT_CONTAINER")
        if v == "db":
            return True, ""
        if v == "slot":
            return (False, _DB) if db else (True, "")
        return False, "in a container without ASSETOPS_HEAVY_SLOT_CONTAINER"
    opts = dict(slot_dir=slot_dir, pid=os.getpid() if pid is None else pid, proc_root=proc_root, platform=platform)
    ok, reason = _marker(env.get("ASSETOPS_HEAVY_SLOT"), "slot", **opts)
    if not ok:
        return ok, reason
    if db and not _marker(env.get("ASSETOPS_HEAVY_DB"), "db", **opts)[0]:
        return False, _DB
    return True, ""


def refusal(tool: str, reason: str, db: bool) -> str:
    sh = "--db " if db else ""
    ps = "-Db " if db else ""
    return (f"heavy-slot: refused: {tool} runs only inside the heavy-tool slot pool ({reason}).\n"
            f"Run it as: tools/heavy-slot.sh {sh}-- <your command>   (from frontend/: ../tools/heavy-slot.sh; "
            f"pwsh: pwsh -NoProfile -File tools/heavy-slot.ps1 {ps}-- ...)\n"
            "RULES §7 (T1).")


def require(tool: str, *, db: bool = False, exit_with=None) -> None:
    in_container = sys.platform != "win32" and os.path.exists("/.dockerenv")
    ok, reason = check_marker(os.environ, slot_dir=None if in_container else slot_dir(),
                              in_container=in_container, db=db)
    if ok:
        return
    message = refusal(tool, reason, db)
    print(message, file=sys.stderr, flush=True)
    if exit_with is not None:
        exit_with(message, returncode=69)
    sys.exit(69)
