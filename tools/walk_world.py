"""WK (spec `specs/WK-walkthrough-database/spec.md` rev 2; D-WK.1 to D-WK.14): the walkthrough database.

    python tools/walk_world.py copy    --label L            copy the checked L2 world into assetops_polish_walk<L>_test
    python tools/walk_world.py prepare --label L            the two statements and one snapshot rebuild (product commands)
    python tools/walk_world.py check   --label L            W1 to W7: the copy is still clean and good
    python tools/walk_world.py serve   --label L --tree DIR the API and the web on the walk definition's ports
    python tools/walk_world.py smoke   --label L            S1 to S4 over the served pages
    python tools/walk_world.py stop    --label L            stop the serve by recorded PID
    python tools/walk_world.py status  --label L            the manifest and whether each PID is alive
    python tools/walk_world.py drop    --label L            drop the walk database (never forced), then its manifest

Coordinator-only. It never builds, clones, freezes or drops a world rung: those stay with `tools/world.py` (D-WK.1).
Every connection to the walk database goes through `walk_url` (D-WK.11). Exits: 0 done; 2 refused before any change
(`<CODE> <detail>` on stderr); 3 a product step failed; 4 a check or smoke FAIL, or the serve did not start; 5 the cap
was reached; 69 passes through from the heavy-tool slot check. Diagnostics are codes; nothing here is served.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

REPO = Path(__file__).resolve().parents[1]
for _p in ("backend", "contracts", "simulator", "tools"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import world as W  # noqa: E402
from assetops_backend.database_target import DatabaseTargetUnclear, database_target, is_operator_name  # noqa: E402

PROTECTED_DATABASES = ("assetops_polish_walk1113_test",)
PROTECTED_PORTS = (8990, 5490)

WALK_DEFINITION = "backend/conversions/walk-layer4-v1.json"
FORMAT_WALK_DEFINITION = "assetops.walk-definition/1"
FORMAT_WALK_BUILD = "assetops.walk-build/1"
PW_ENV = "/opt/assetecon/tools/pw/env.sh"
EVIDENCE_ROOT = "/opt/assetecon/evidence/WK"
SMOKE_SCRIPT = "tools/walk_world_smoke.cjs"
SERVED = "SERVED"
CONTRIBUTION = "contribution"
LOCAL_HOSTS = ("127.0.0.1", "localhost")
SERVE_WAIT_SECONDS = 120.0
STOP_WAIT_SECONDS = 10.0
IDLE_WAIT_SECONDS = 5.0

_LABEL = re.compile(r"[0-9]{4}[a-z]?", re.ASCII)
_WALK_NAME = re.compile(r"assetops_polish_walk[0-9]{4}[a-z]?_test", re.ASCII)
_AMOUNT = re.compile(r"[0-9]+\.[0-9]{2}", re.ASCII)
_CURRENCY = re.compile(r"[A-Z]{3}", re.ASCII)
_L2 = re.compile(r"[a-z0-9_]{1,40}_audit_l2_[0-9a-f]{12}", re.ASCII)

Refused, StepFailed, CapExceeded = W.Refused, W.StepFailed, W.CapExceeded


class Failed(Exception):
    """Exit 4 with a code (the serve did not start)."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code, self.detail = code, detail


# --- names and the walk URL (§3.1; D-WK.11) --------------------------------------------------------------------------

def walk_name_ok(name: str) -> bool:
    return (isinstance(name, str) and _WALK_NAME.fullmatch(name) is not None and name not in PROTECTED_DATABASES
            and not is_operator_name(name) and not name.startswith("assetops_world"))


def walk_name(label: str) -> str:
    if not isinstance(label, str) or not _LABEL.fullmatch(label):
        raise Refused("WALK_LABEL_INVALID", label if isinstance(label, str) else "")
    name = f"assetops_polish_walk{label}_test"
    if name in PROTECTED_DATABASES:
        raise Refused("WALK_PROTECTED", name)
    if not walk_name_ok(name):
        raise Refused("WALK_NAME_REFUSED", name)
    return name


def walk_url(label: str, environ: Mapping[str, str]) -> str:
    """The only place that builds the walk database's URL (D-WK.11)."""
    name = walk_name(label)
    url = W.rung_url(name, environ)
    try:
        target = database_target(url, environ)
    except DatabaseTargetUnclear as unclear:
        raise Refused("WALK_TARGET_UNCLEAR", unclear.reason) from None
    if target.name != name:
        raise Refused("WALK_TARGET_UNCLEAR", "name")
    if target.host not in LOCAL_HOSTS:
        raise Refused("WALK_TARGET_UNCLEAR", "host")
    try:
        port = int(environ.get("ASSETOPS_PG_PORT", "55432"))
    except ValueError:
        raise Refused("WALK_TARGET_UNCLEAR", "port") from None
    if target.port != port or port in PROTECTED_PORTS:
        raise Refused("WALK_TARGET_UNCLEAR", "port")
    return url


# --- the walk definition (§2) ----------------------------------------------------------------------------------------

@dataclass(frozen=True)
class WalkDefinition:
    raw: dict
    statements: tuple
    rebuild_by: str
    serve: dict
    expect: dict
    pages: tuple


def _bad(where: str) -> Refused:
    return Refused("WALK_DEFINITION_INVALID", where)


def _keys(obj: Any, want: set, where: str) -> None:
    if not isinstance(obj, dict) or set(obj) != want:
        raise _bad(where)


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise _bad(where)
    return value


def _port(value: Any, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1024 <= value <= 65535 or value in PROTECTED_PORTS:
        raise _bad(where)
    return value


def read_walk_definition(path: Path | str, world_definition: W.Definition) -> WalkDefinition:
    from assetops_backend.structure_snapshot.model import BUILT_BY

    try:
        d = json.loads(Path(path).read_bytes())
    except (OSError, ValueError):
        raise _bad("$") from None
    _keys(d, {"format", "world", "statements", "rebuild_by", "serve", "expect", "pages"}, "$")
    if d["format"] != FORMAT_WALK_DEFINITION:
        raise _bad("$.format")
    if d["world"] != world_definition.world:
        raise _bad("$.world")
    slugs = {t.slug for t in world_definition.tenants}
    months = set(world_definition.months)
    if not isinstance(d["statements"], list) or not d["statements"]:
        raise _bad("$.statements")
    for i, s in enumerate(d["statements"]):
        w = f"$.statements[{i}]"
        _keys(s, {"tenant", "as", "period", "currency", "revenue", "fuel_cost", "source_ref"}, w)
        if s["tenant"] not in slugs:
            raise _bad(f"{w}.tenant")
        if s["period"] not in months:
            raise _bad(f"{w}.period")
        if not isinstance(s["currency"], str) or not _CURRENCY.fullmatch(s["currency"]):
            raise _bad(f"{w}.currency")
        for k in ("revenue", "fuel_cost"):
            if not isinstance(s[k], str) or not _AMOUNT.fullmatch(s[k]):
                raise _bad(f"{w}.{k}")
        _text(s["as"], f"{w}.as")
        _text(s["source_ref"], f"{w}.source_ref")
    if not isinstance(d["rebuild_by"], str) or not BUILT_BY.fullmatch(d["rebuild_by"]):
        raise _bad("$.rebuild_by")
    _keys(d["serve"], {"tenant", "port", "web_port"}, "$.serve")
    if d["serve"]["tenant"] not in slugs:
        raise _bad("$.serve.tenant")
    _port(d["serve"]["port"], "$.serve.port")
    _port(d["serve"]["web_port"], "$.serve.web_port")
    if d["serve"]["port"] == d["serve"]["web_port"]:
        raise _bad("$.serve.web_port")
    e = d["expect"]
    _keys(e, {"tenant", "month", "contribution_actual", "contribution_target", "reconciled"}, "$.expect")
    if e["tenant"] not in slugs:
        raise _bad("$.expect.tenant")
    if e["month"] not in months:
        raise _bad("$.expect.month")
    for k in ("contribution_actual", "contribution_target"):
        if not isinstance(e[k], str) or not _AMOUNT.fullmatch(e[k]):
            raise _bad(f"$.expect.{k}")
    if not isinstance(e["reconciled"], bool):
        raise _bad("$.expect.reconciled")
    pages = d["pages"]
    if not isinstance(pages, list) or not pages or not all(isinstance(p, str) and p.startswith("/") for p in pages):
        raise _bad("$.pages")
    if sum(1 for p in pages if "{code}" in p) != 1:
        raise _bad("$.pages")
    return WalkDefinition(d, tuple(d["statements"]), d["rebuild_by"], dict(d["serve"]), dict(e), tuple(pages))


def smoke_pages(walk: WalkDefinition, world_definition: W.Definition) -> list[str]:
    codes = [code for t in world_definition.tenants for code in t.sites]
    out: list[str] = []
    for page in walk.pages:
        out += [page.replace("{code}", c) for c in codes] if "{code}" in page else [page]
    return out


# --- judges (pure) ---------------------------------------------------------------------------------------------------

def expected_census(parent: Mapping[str, int], statements: int, snapshots: Mapping[str, Any]) -> dict:
    want = dict(parent)
    want["commercial_accounts_statement"] = want.get("commercial_accounts_statement", 0) + statements
    want["structure_snapshot"] = want.get("structure_snapshot", 0) + sum(
        1 + len((s or {}).get("sites") or {}) for s in snapshots.values())
    return want


def census_judge(parent: Mapping[str, int], census: Mapping[str, int], statements: int,
                 snapshots: Mapping[str, Any]) -> tuple[bool, str]:
    """W3 and S4: the copy differs from its parent only by the declared rows."""
    want = expected_census(parent, statements, snapshots)
    diff = [f"{t} {want.get(t)} != {census.get(t)}" for t in sorted(set(want) | set(census))
            if want.get(t) != census.get(t)]
    return not diff, "; ".join(diff) or f"{len(census)} tables"


def _iso_z(text: str) -> str:
    return datetime.fromisoformat(text).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def judge_month(body: Any, expect: Mapping[str, Any], as_of: str | None) -> list[str]:
    """W4 and S2: the month is served, current and reconciled as expected, with the expected contribution bar."""
    if not isinstance(body, dict):
        return ["body"]
    if body.get("state") != SERVED:
        return [f"state {body.get('state')}"]
    bad = []
    try:
        if as_of is None or body.get("as_of") != _iso_z(as_of):
            bad.append(f"as_of {body.get('as_of')}")
    except (TypeError, ValueError):
        bad.append("as_of")
    fresh = body.get("fresh") if isinstance(body.get("fresh"), dict) else {}
    if fresh.get("current") is not True:
        bad.append(f"fresh.current {fresh.get('current')}")
    if fresh.get("untracked_text") is not None:
        bad.append("fresh.untracked_text")
    standing = body.get("standing") if isinstance(body.get("standing"), dict) else {}
    if standing.get("reconciled") is not expect["reconciled"]:
        bad.append(f"standing.reconciled {standing.get('reconciled')}")
    tiles = [t for t in body.get("tiles") or [] if isinstance(t, dict) and t.get("key") == CONTRIBUTION]
    bar = tiles[0].get("bar") if len(tiles) == 1 else None
    if not isinstance(bar, dict):
        bad.append("contribution.bar")
    else:
        for k, want in (("actual", expect["contribution_actual"]), ("target", expect["contribution_target"])):
            try:
                ok = Decimal(str(bar.get(k))) == Decimal(want)
            except ArithmeticError:
                ok = False
            if not ok:
                bad.append(f"contribution.{k} {bar.get(k)}")
    return bad


def _line(check: str, ok: bool, detail: Any) -> dict:
    return {"check": check, "state": "PASS" if ok else "FAIL", "detail": detail}


# --- environments (§3.3, §3.5, §3.6) ---------------------------------------------------------------------------------

def _base_env(environ: Mapping[str, str]) -> dict:
    return {k: environ[k] for k in ("PATH", "HOME", "LANG") if k in environ}


def api_env(tree: Path, environ: Mapping[str, str], tenant: str, url: str) -> dict:
    """Built, never inherited: no key folder, no real-data, entry, upload, gateway or live-field switch (D-WK.5)."""
    e = _base_env(environ)
    e["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in ("backend", "contracts", "gateway", "simulator", "host"))
    e["DATABASE_URL"] = url
    e["ASSETOPS_TENANT_SLUG"] = tenant
    for k in ("ASSETOPS_PG_PORT", "ASSETOPS_PG_PASSWORD"):
        if k in environ:
            e[k] = environ[k]
    e["PYTHONUNBUFFERED"] = "1"
    return e


def web_env(environ: Mapping[str, str], port: int) -> dict:
    e = _base_env(environ)
    e["ASSETOPS_API_PORT"] = str(port)
    return e


NODE_FROM_PW = ("PW", "CHROME", "FONTCONFIG_FILE", "AUDIT_LD_LIBRARY_PATH")


def node_env(environ: Mapping[str, str], pw: Mapping[str, str]) -> dict:
    """I3: exactly PATH, HOME, PW, CHROME, FONTCONFIG_FILE and LD_LIBRARY_PATH (the audit library path)."""
    e = {k: environ[k] for k in ("PATH", "HOME") if k in environ}
    e["PW"], e["CHROME"], e["FONTCONFIG_FILE"] = pw["PW"], pw["CHROME"], pw["FONTCONFIG_FILE"]
    e["LD_LIBRARY_PATH"] = pw["AUDIT_LD_LIBRARY_PATH"]
    return e


def pw_values(stdout: str) -> dict:
    values = {}
    for line in (stdout or "").splitlines():
        name, sep, value = line.partition("=")
        if sep and name in NODE_FROM_PW:
            values[name] = value
    return values


def refuse_walk_tree(tree: str) -> Path:
    """R6: the 13 Nov walkthrough tree is never served from (`WALK_TREE_MISMATCH`)."""
    resolved = Path(os.path.realpath(tree))
    if resolved == Path("/opt/assetecon/AssetOpsV1-walk") or resolved.is_relative_to("/opt/assetecon/AssetOpsV1-walk"):
        raise Refused("WALK_TREE_MISMATCH", str(resolved))
    return resolved


# --- dependencies (real ones; tests replace them) --------------------------------------------------------------------

def _real_http(url: str, timeout: float) -> tuple[int, bytes]:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 - 127.0.0.1 only
            return r.status, r.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read() or b""
    except (OSError, ValueError):
        return 0, b""


INTERPRETERS = ("node", "nodejs")


def cmdline_matches(cmdline: Sequence[str] | None, argv: Sequence[str]) -> bool:
    """Secondary check of `/proc/<pid>/cmdline` against a recorded argv, exact on every token (so exact on the port).

    Accepted: the argv itself; the argv run by its interpreter (`node <path>/npm run dev ...`, the script's basename
    equal to `argv[0]`'s, or `npm-cli.js` for `npm`); one retitled string equal to the argv joined, or, for `npm`,
    joined without its `--` (npm 11 sets its title to `npm run dev --port 5491 --strictPort --host 127.0.0.1`). A
    wrapper (`bash -c ...`, `sh -c ...`, `timeout ...`) never matches."""
    if not cmdline or not argv:
        return False
    seen, want = [str(c) for c in cmdline], [str(a) for a in argv]
    if seen == want:
        return True
    if len(seen) == 1:
        title = seen[0].rstrip()
        if title == " ".join(want):
            return True
        if os.path.basename(want[0]) == "npm" and "--" in want:
            cut = want.index("--")
            return title == " ".join(want[:cut] + want[cut + 1:])
        return False
    if os.path.basename(seen[0]) in INTERPRETERS:
        names = {os.path.basename(want[0])} | ({"npm-cli.js"} if os.path.basename(want[0]) == "npm" else set())
        return os.path.basename(seen[1]) in names and seen[2:] == want[1:]
    return False


def _read_proc(path: str) -> bytes | None:
    try:
        return Path(path).read_bytes()
    except (OSError, ValueError):
        return None


def _getpgid(pid: int) -> int | None:
    try:
        return os.getpgid(int(pid))
    except (OSError, ValueError):
        return None


def _list_pids() -> list[int]:
    try:
        return [int(n) for n in os.listdir("/proc") if n.isdigit()]
    except OSError:
        return []


def _killpg(pgid: int, sig: int) -> None:
    try:
        os.killpg(int(pgid), sig)
    except (ProcessLookupError, PermissionError):
        pass


def parse_stat(raw: bytes | None) -> dict | None:
    """`/proc/<pid>/stat`: the fields after `(comm)`; field 5 pgrp, 6 session, 22 starttime (clock ticks since boot)."""
    if not raw:
        return None
    text = raw.decode("utf-8", "replace")
    close = text.rfind(")")
    rest = text[close + 1:].split() if close >= 0 else []
    try:
        return {"pgrp": int(rest[2]), "session": int(rest[3]), "start_time": int(rest[19])}
    except (IndexError, ValueError):
        return None


class Procs:
    """The process table. A child is spawned in its own session and group, and recorded by PID, start time and group.

    Before any signal, all three must hold: `/proc/<pid>` exists with the recorded start time, the PID still leads its
    own group (`getpgid(pid) == pid`), and that group is the recorded one. The cmdline match is secondary. Only then is
    the group signalled. The `/proc` reader, `getpgid`, the PID list, `killpg` and `popen` are injected for tests."""

    def __init__(self, *, read: Callable[[str], bytes | None] = _read_proc,
                 getpgid: Callable[[int], int | None] = _getpgid, pids: Callable[[], list[int]] = _list_pids,
                 killpg: Callable[[int, int], None] = _killpg, popen: Callable[..., Any] = subprocess.Popen) -> None:
        self.read, self.getpgid, self.pids, self._killpg, self.popen = read, getpgid, pids, killpg, popen
        self._children: dict[int, Any] = {}

    def spawn(self, argv: Sequence[str], cwd: str, env: Mapping[str, str], log: Path) -> dict:
        out = open(log, "w", encoding="utf-8")
        try:
            child = self.popen(list(argv), cwd=cwd, env=dict(env), stdout=out, stderr=subprocess.STDOUT,
                               start_new_session=True)
        finally:
            out.close()
        self._children[child.pid] = child
        st = self.stat(child.pid)
        return {"pid": child.pid, "argv": list(argv), "start_time": st["start_time"] if st else None,
                "pgid": self.getpgid(child.pid)}

    def exited(self, pid: int) -> bool:
        child = self._children.get(pid)
        return child is not None and child.poll() is not None

    def stat(self, pid: int) -> dict | None:
        return parse_stat(self.read(f"/proc/{int(pid)}/stat"))

    def cmdline(self, pid: int) -> list[str] | None:
        raw = self.read(f"/proc/{int(pid)}/cmdline")
        if raw is None:
            return None
        return [p.decode("utf-8", "replace") for p in raw.split(b"\0") if p] or None

    def checked(self, rec: Mapping[str, Any]) -> str | None:
        """None when the recorded child is still ours and leads its recorded group; else the failed check, or `gone`."""
        pid, start, pgid = rec.get("pid"), rec.get("start_time"), rec.get("pgid")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (pid, start, pgid)):
            return "unrecorded"
        st = self.stat(pid)
        if st is None:
            return "gone"
        if st["start_time"] != start:
            return "start_time"
        if self.getpgid(pid) != pid:
            return "not_leader"
        if pgid != pid:
            return "pgid"
        if not cmdline_matches(self.cmdline(pid), rec.get("argv") or []):
            return "cmdline"
        return None

    def members(self, rec: Mapping[str, Any]) -> tuple[list[int], list[int]]:
        """L4: the live processes in the recorded group, split into those in the recorded session that started at or
        after the recorded start time (ours: a member cannot predate its leader) and any other (not provably ours)."""
        pgid, start = rec.get("pgid"), rec.get("start_time")
        if not isinstance(pgid, int) or not isinstance(start, int):
            return [], []
        ok, bad = [], []
        for p in self.pids():
            st = self.stat(p)
            if st is None or st["pgrp"] != pgid:
                continue
            (ok if st["session"] == pgid and st["start_time"] >= start else bad).append(p)
        return ok, bad

    def alive(self, rec: Mapping[str, Any]) -> bool:
        reason = self.checked(rec)
        if reason is None:
            return True
        if reason == "gone":
            ok, bad = self.members(rec)
            return bool(ok) and not bad
        return False

    def signal(self, rec: Mapping[str, Any], sig: int) -> str | None:
        """Signal the recorded group only after the checks. With the leader gone (L4), only when every surviving member
        passes the start-time check. Returns None when signalled, `gone` when nothing is left, else the failed check."""
        reason = self.checked(rec)
        if reason == "gone":
            ok, bad = self.members(rec)
            if bad:
                return "group_unverified"
            if not ok:
                return "gone"
            reason = None
        if reason is not None:
            return reason
        self._killpg(rec["pgid"], sig)
        return None

    def port_busy(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(("127.0.0.1", int(port))) == 0


def stop_child(procs: Procs, rec: Mapping[str, Any], clock: Any, first: int = signal.SIGTERM) -> str | None:
    """SIGTERM the recorded group, wait up to 10 s for it to empty, then SIGKILL; each signal is re-checked. A failed
    serve passes `first=SIGKILL` and signals once. Returns None when stopped or already gone, else the check that
    refused the signal."""
    reason = procs.signal(rec, first)
    if reason == "gone":
        return None
    if reason is not None or first == signal.SIGKILL:
        return reason
    end = clock.monotonic() + STOP_WAIT_SECONDS
    while procs.alive(rec) and clock.monotonic() < end:
        clock.sleep(0.25)
    if procs.alive(rec):
        reason = procs.signal(rec, signal.SIGKILL)
        return None if reason == "gone" else reason
    return None


@dataclass
class WalkDeps:
    """I4: the world tool's `Deps`, plus the HTTP getter, the process table and the `World` factory.

    `deep_dive` (url -> (read, dispose)) and `foundation` (url -> the Foundation store) are W4's two reads; tests
    replace them, the real ones are the product's compositions.
    """
    world: W.Deps = field(default_factory=W.Deps)
    http: Callable[[str, float], tuple[int, bytes]] = _real_http
    procs: Any = field(default_factory=Procs)
    world_factory: Callable[[argparse.Namespace, W.Deps], Any] = W.World
    deep_dive: Callable[[str], tuple[Any, Callable[[], None]]] | None = None
    foundation: Callable[[str], Any] | None = None


# --- the run context -------------------------------------------------------------------------------------------------

class Walk:
    def __init__(self, args: argparse.Namespace, deps: WalkDeps) -> None:
        self.args, self.deps = args, deps
        self.world = deps.world_factory(argparse.Namespace(prefix=args.prefix, state=args.state,
                                                           definition=args.definition, cap_seconds=args.cap_seconds),
                                        deps.world)
        self.environ = self.world.environ
        self.admin = self.world.admin
        self.label = args.label
        self.url = walk_url(args.label, self.environ)
        self.name = walk_name(args.label)
        self._walk_def: WalkDefinition | None = None

    def emit(self, obj: Mapping[str, Any]) -> None:
        sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")

    # state
    def state_root(self) -> Path:
        return W._private_dir(Path(self.args.state), "WORLD_STATE_INVALID")

    def walks_dir(self) -> Path:
        d = self.state_root() / "walks"
        if not os.path.lexists(d):
            os.mkdir(d, 0o700)
            os.chmod(d, 0o700)
        st = os.lstat(d)  # L2: an existing folder must be a real, private folder of this user
        if (not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077):
            raise Refused("WORLD_STATE_INVALID", str(d))
        return d

    def manifest_path(self) -> Path:
        return self.walks_dir() / f"{self.name}.json"

    def read_manifest(self) -> dict | None:
        p = self.manifest_path()
        return json.loads(p.read_text()) if p.is_file() else None

    def need_manifest(self) -> dict:
        m = self.read_manifest()
        if m is None:
            raise Refused("WALK_UNKNOWN", self.name)
        return m

    def write_manifest(self, body: Mapping[str, Any]) -> None:
        p = self.manifest_path()
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text(W.canonical(body))
        os.replace(tmp, p)

    # definitions
    def world_definition(self) -> W.Definition:
        if self.world.definition is None:
            rel = self.args.definition
            self.world.definition = W.read_definition(REPO / rel if not Path(rel).is_absolute() else Path(rel))
        return self.world.definition

    def walk_definition(self) -> WalkDefinition:
        if self._walk_def is None:
            rel = self.args.walk_definition
            self._walk_def = read_walk_definition(REPO / rel if not Path(rel).is_absolute() else Path(rel),
                                                  self.world_definition())
        return self._walk_def

    # the walk database: counts and lookups through walk_url's URL only (I2)
    def census(self) -> dict:
        (tables,) = self.deps.world.query(self.url, [W.CENSUS_TABLES])
        names = [t[0] for t in tables]
        counts = self.deps.world.query(self.url, [f'SELECT count(*) FROM "{t}"' for t in names]) if names else []
        return {t: int(c[0][0]) for t, c in zip(names, counts)}

    def tenants(self) -> dict:
        (rows,) = self.deps.world.query(self.url, [W.TENANTS])
        return {str(slug): str(tid) for tid, slug in rows}

    def walk_names(self) -> list[str]:
        rows = self.admin("SELECT datname FROM pg_database WHERE datname LIKE :p ORDER BY datname",
                          {"p": "assetops_polish_walk%"})
        return sorted(str(r[0]) for r in rows if str(r[0]).startswith("assetops_polish_walk"))

    def exists(self) -> bool:
        return bool(self.admin("SELECT 1 FROM pg_database WHERE datname = :n", {"n": self.name}))

    def sessions(self) -> int:
        rows = self.admin("SELECT count(*) FROM pg_stat_activity WHERE datname = :n", {"n": self.name})
        return int(rows[0][0]) if rows else 0

    def step_env(self, tenant: str, key_dir: str | None) -> dict:
        e = self.world.env(None, tenant, key_dir)
        e["DATABASE_URL"] = self.url
        return e

    def serving(self, m: Mapping[str, Any]) -> bool:
        s = m.get("serve")
        if not s:
            return False
        return any(self.deps.procs.alive(s[w]) for w in ("api", "web"))


# --- copy (§3.2) -----------------------------------------------------------------------------------------------------

def cmd_copy(walk: Walk) -> int:
    world = walk.world
    world.prepare()
    l2_name, l2 = world.current_l2()
    passed, stale = world.check_state(l2)
    if stale is not None:
        raise Refused("WALK_CHECK_STALE", stale)
    if passed is None:
        raise Refused("WALK_NOT_CHECKED", l2_name)
    if passed is False:
        raise Refused("WALK_CHECK_FAILED", l2_name)
    if not _L2.fullmatch(l2_name) or not l2_name.startswith(f"{walk.args.prefix}_audit_l2_"):
        raise Refused("WALK_NAME_REFUSED", l2_name)
    walks_before = walk.walk_names()
    if walk.name in walks_before or walk.read_manifest() is not None:
        raise Refused("WALK_EXISTS", walk.name)
    if not world.wait_idle(l2_name):
        raise Refused("WALK_DATABASE_IN_USE", l2_name)
    clock = walk.deps.world.clock
    start = clock.monotonic()
    walk.admin(f'CREATE DATABASE "{walk.name}" TEMPLATE "{l2_name}" STRATEGY FILE_COPY')
    seconds = round(clock.monotonic() - start, 3)
    walk.write_manifest({
        "format": FORMAT_WALK_BUILD, "database": walk.name, "label": walk.label, "parent": l2_name,
        "parent_key": l2["key"], "commit": world.git.head(), "copied_at": W._now_iso(world), "seconds": seconds,
        "tenants": l2.get("tenants"), "key_dir": l2.get("key_dir"), "parent_census": l2.get("census"),
        "parent_snapshots": l2.get("snapshots"), "steps": [], "walks_before": walks_before, "snapshots": None,
        "check": None, "serve": None})
    walk.emit({"database": walk.name, "parent": l2_name, "parent_key12": str(l2["key"])[:12], "seconds": seconds})
    return 0


# --- prepare (§3.3) --------------------------------------------------------------------------------------------------

def statement_argv(s: Mapping[str, str]) -> list[str]:
    return ["-m", "assetops_backend.reconcile_month", "record", "--tenant", s["tenant"], "--as", s["as"],
            "--period", s["period"], "--currency", s["currency"], "--revenue", s["revenue"], "--fuel-cost",
            s["fuel_cost"], "--source-ref", s["source_ref"]]


def snapshot_argv(slug: str, month: str, by: str) -> list[str]:
    return ["-m", "assetops_backend.build_structure_snapshot", "build", "--tenant", slug, "--month", month, "--by", by]


def cmd_prepare(walk: Walk) -> int:
    world = walk.world
    m = walk.need_manifest()
    world.prepare()
    if world.git.head() != m["commit"]:
        raise Refused("WALK_COMMIT_MOVED", m["commit"][:12])
    if m.get("steps"):
        raise Refused("WALK_PREPARED", walk.name)
    wd, d = walk.walk_definition(), walk.world_definition()
    plan = [(f"prepare.statement:{n}", s["tenant"], statement_argv(s), None) for n, s in enumerate(wd.statements)]
    plan += [(f"prepare.snapshot:{t.slug}:{month}", t.slug, snapshot_argv(t.slug, month, wd.rebuild_by),
              f"{t.slug}:{month}") for t in d.tenants for month in d.months]
    snapshots: dict = {}
    for step, tenant, argv, snap_key in plan:
        rc, _, record = world.run_step(walk.name, step, argv, walk.step_env(tenant, m.get("key_dir")), fail=False)
        m["steps"].append(record)
        walk.write_manifest(m)
        if rc != 0:
            raise StepFailed(walk.name, step, rc)
        if snap_key is not None:
            out = record["out"] if isinstance(record["out"], dict) else {}
            snapshots[snap_key] = {k: out.get(k) for k in ("as_of", "portfolio_snapshot_id", "sites", "rules_digest")}
    m["snapshots"] = snapshots
    walk.write_manifest(m)
    walk.emit({"database": walk.name, "steps": len(m["steps"]), "snapshots": sorted(snapshots)})
    return 0


# --- check (§3.4; D-WK.4) --------------------------------------------------------------------------------------------

def _w1(walk: Walk, m: Mapping[str, Any]) -> dict:
    world = walk.world
    l2_name, l2 = world.current_l2()
    bad = []
    if l2_name != m["parent"]:
        bad.append(f"parent {l2_name}")
    if l2.get("key") != m["parent_key"]:
        bad.append("key")
    state = world.check_state(l2)
    if state != (True, None):
        bad.append(f"check_state {state[0]} {state[1]}")
    if world.git.head() != m["commit"]:
        bad.append("commit")
    return _line("W1", not bad, "; ".join(bad) or l2_name)


def _w2(walk: Walk, m: Mapping[str, Any]) -> dict:
    bad = []
    snaps = m.get("snapshots") or {}
    for key_, snap in sorted(snaps.items()):
        slug = key_.split(":")[0]
        argv = ["-m", "assetops_backend.build_structure_snapshot", "verify", "--tenant", slug, "--snapshot",
                str(snap.get("portfolio_snapshot_id"))]
        rc, _, rec = walk.world.run_step(walk.name, f"check.verify:{key_}", argv,
                                         walk.step_env(slug, m.get("key_dir")), fail=False)
        out = rec["out"] if isinstance(rec["out"], dict) else {}
        if rc != 0 or out.get("matches") is not True:
            bad.append(f"{key_} exit={rc}")
    if not snaps:
        bad.append("no snapshots")
    return _line("W2", not bad, "; ".join(bad) or f"{len(snaps)} snapshots match")


def _census_line(walk: Walk, m: Mapping[str, Any], check: str) -> dict:
    ok, detail = census_judge(m.get("parent_census") or {}, walk.census(), len(walk.walk_definition().statements),
                              m.get("snapshots") or {})
    return _line(check, ok, detail)


def _dispose_store(store: Any) -> None:
    engine = getattr(store, "_engine", None)
    if engine is not None:
        engine.dispose()


def month_body(walk: Walk, slug: str, month: str) -> dict:
    """I1: the deep-dive read as the route reads it: the `TenantRef` and the imported Sites' names from the walk
    database's Foundation, the read unpacked and disposed."""
    if walk.deps.foundation is not None:
        store = walk.deps.foundation(walk.url)
    else:
        from assetops_backend.sites.composition import build_foundation_store

        store = build_foundation_store(walk.url)
    try:
        tenant = store.resolve_tenant(slug)
        names = {s.site_code: s.name for s in store.list_sites(tenant.id) if s.import_record is not None}
    finally:
        _dispose_store(store)
    if walk.deps.deep_dive is not None:
        read, dispose = walk.deps.deep_dive(walk.url)
    else:
        from assetops_backend.deep_dive.composition import build_deep_dive_read

        read, dispose = build_deep_dive_read(walk.url)
    held = os.environ.pop("ASSETOPS_TENANT_SLUG", None)
    try:
        body = read.month(tenant, month, names)
    finally:
        if held is not None:
            os.environ["ASSETOPS_TENANT_SLUG"] = held
        dispose()
    return json.loads(json.dumps(body, default=str))


def expected_as_of(m: Mapping[str, Any], expect: Mapping[str, Any]) -> str | None:
    snap = (m.get("snapshots") or {}).get(f"{expect['tenant']}:{expect['month']}") or {}
    return snap.get("as_of")


def _w4(walk: Walk, m: Mapping[str, Any]) -> dict:
    expect = walk.walk_definition().expect
    body = month_body(walk, expect["tenant"], expect["month"])
    bad = judge_month(body, expect, expected_as_of(m, expect))
    return _line("W4", not bad, "; ".join(bad) or f"{expect['tenant']} {expect['month']} served")


def _w5(walk: Walk, m: Mapping[str, Any]) -> dict:
    from uuid import UUID

    from assetops_backend.structure_snapshot import codec

    d = walk.world_definition()
    derived = json.loads((REPO / d.derived_values).read_text())
    if walk.deps.world.snapshots is not None:
        service = walk.deps.world.snapshots(walk.url)
    else:
        from assetops_backend.structure_snapshot.composition import build_structure_snapshot

        service = build_structure_snapshot(walk.url)
    snaps = m.get("snapshots") or {}
    rows: list = []
    try:
        for key_, snap in sorted(snaps.items()):
            slug = key_.split(":")[0]
            tid = UUID((m.get("tenants") or {})[slug])
            ids = [UUID(x) for _, x in sorted((snap.get("sites") or {}).items())]
            rows += [(slug, codec.payload_of(r)) for r in service.store.get(tid, ids)]
    finally:
        service.dispose()
    counts: dict = {}
    for key_ in snaps:
        counts[key_.split(":")[0]] = counts.get(key_.split(":")[0], 0) + 1
    result = W.c4_oracle(rows, d, derived, counts)
    marks = [f["mark"] for f in result["detail"]["fails"]]
    ok = result["state"] == "PASS" and not marks
    return _line("W5", ok, result["detail"] if not ok else f"{len(rows)} Site rows")


def _w6(walk: Walk, m: Mapping[str, Any]) -> dict:
    bad = []
    try:
        walk_url(walk.label, walk.environ)
    except Refused as r:
        bad.append(f"{r.code} {r.detail}")
    rows = walk.admin("SELECT datallowconn FROM pg_database WHERE datname = :n", {"n": m["parent"]})
    if not rows or rows[0][0] is not False:
        bad.append(f"datallowconn {rows[0][0] if rows else None}")
    if walk.tenants() != (m.get("tenants") or {}):
        bad.append("tenants")
    extra = sorted(set(walk.walk_names()) - {walk.name} - set(m.get("walks_before") or []))
    bad += [f"walk {x}" for x in extra]
    return _line("W6", not bad, "; ".join(bad) or walk.name)


def _w7(walk: Walk, m: Mapping[str, Any]) -> dict:
    steps = m.get("steps") or []
    bad = [f"{s.get('step')} exit {s.get('exit')}" for s in steps if s.get("exit") != 0]
    d, wd = walk.world_definition(), walk.walk_definition()
    n_statements = sum(1 for s in steps if str(s.get("step", "")).startswith("prepare.statement:"))
    n_snapshots = sum(1 for s in steps if str(s.get("step", "")).startswith("prepare.snapshot:"))
    if n_statements != len(wd.statements):
        bad.append(f"statements {n_statements} != {len(wd.statements)}")
    if n_snapshots != len(d.tenants) * len(d.months):
        bad.append(f"snapshots {n_snapshots} != {len(d.tenants) * len(d.months)}")
    return _line("W7", not bad, "; ".join(bad) or f"{len(steps)} steps")


def _guard(name: str, fn: Callable[[], dict]) -> dict:
    try:
        return fn()
    except CapExceeded:
        raise
    except Refused as r:  # a refusal inside a check (a stale parent) is that check's FAIL
        return _line(name, False, f"{r.code} {r.detail}".strip())
    except Exception as error:  # a check that raises is a FAIL; the others still run
        return _line(name, False, f"raised {type(error).__name__}")


def cmd_check(walk: Walk) -> int:
    m = walk.need_manifest()
    if not m.get("steps") or m.get("snapshots") is None:
        raise Refused("WALK_NOT_PREPARED", walk.name)
    walk.world.prepare()
    walk.walk_definition()
    lines = [_guard("W1", lambda: _w1(walk, m)), _guard("W2", lambda: _w2(walk, m)),
             _guard("W3", lambda: _census_line(walk, m, "W3")), _guard("W4", lambda: _w4(walk, m)),
             _guard("W5", lambda: _w5(walk, m)), _guard("W6", lambda: _w6(walk, m)), _guard("W7", lambda: _w7(walk, m))]
    passed = all(x["state"] == "PASS" for x in lines)
    m["check"] = {"at": W._now_iso(walk.world), "commit": walk.world.git.head(), "passed": passed, "lines": lines}
    walk.write_manifest(m)
    for x in lines:
        walk.emit(x)
    walk.emit({"check": "ALL", "state": "PASS" if passed else "FAIL"})
    return 0 if passed else 4


# --- serve (§3.5; D-WK.5, D-WK.6) ------------------------------------------------------------------------------------

def _git_head(walk: Walk, tree: Path) -> str:
    done = walk.deps.world.runner(["git", "-C", str(tree), "rev-parse", "HEAD"], str(tree),
                                  _base_env(walk.environ), 30.0)
    return (done.stdout or "").strip() if done.returncode == 0 else ""


def cmd_serve(walk: Walk) -> int:
    tree = refuse_walk_tree(walk.args.tree)
    m = walk.need_manifest()
    check = m.get("check") or {}
    if check.get("passed") is not True or check.get("commit") != m["commit"]:
        raise Refused("WALK_NOT_PASSED", walk.name)
    if _git_head(walk, tree) != m["commit"]:
        raise Refused("WALK_TREE_MISMATCH", str(tree))
    if walk.serving(m):
        raise Refused("WALK_SERVING", walk.name)
    wd = walk.walk_definition()
    port = wd.serve["port"] if walk.args.port is None else walk.args.port
    web_port = wd.serve["web_port"] if walk.args.web_port is None else walk.args.web_port
    for p in (port, web_port):
        if p in PROTECTED_PORTS:
            raise Refused("WALK_PORT_PROTECTED", str(p))
    for p in (port, web_port):  # L1: the definition reader's range, and two different ports
        if not 1024 <= p <= 65535:
            raise Refused("WALK_PORT_INVALID", str(p))
    if port == web_port:
        raise Refused("WALK_PORT_INVALID", f"{port} = {web_port}")
    for p in (port, web_port):
        if walk.deps.procs.port_busy(p):
            raise Refused("WALK_PORT_BUSY", str(p))
    logs = tree / "var" / f"polish_walk{walk.label}" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    api_argv = [walk.deps.world.python, "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)]
    web_argv = ["npm", "run", "dev", "--", "--port", str(web_port), "--strictPort", "--host", "127.0.0.1"]
    api_log, web_log = logs / f"api-{port}.log", logs / f"web-{web_port}.log"
    procs, clock = walk.deps.procs, walk.deps.world.clock
    api_rec = procs.spawn(api_argv, str(tree / "host"), api_env(tree, walk.environ, wd.serve["tenant"], walk.url),
                          api_log)
    try:
        web_rec = procs.spawn(web_argv, str(tree / "frontend"), web_env(walk.environ, port), web_log)
    except OSError as error:  # L3: the API child is stopped (safely), never left running unrecorded
        _report_refused([(api_rec, stop_child(procs, api_rec, clock, signal.SIGKILL))])
        raise Failed("WALK_SERVE_FAILED", f"web spawn {type(error).__name__}") from None
    api, web = api_rec["pid"], web_rec["pid"]
    end = clock.monotonic() + SERVE_WAIT_SECONDS
    failed = None
    while True:
        if procs.exited(api):
            failed = ("api", api_log)
            break
        if procs.exited(web):
            failed = ("web", web_log)
            break
        status, _ = walk.deps.http(f"http://127.0.0.1:{port}/api/health", 2.0)
        if status == 200 and procs.port_busy(web_port):
            break
        if clock.monotonic() >= end:
            failed = ("api", api_log) if status != 200 else ("web", web_log)
            break
        clock.sleep(0.5)
    if failed is not None:
        _report_refused([(rec, stop_child(procs, rec, clock, signal.SIGKILL)) for rec in (api_rec, web_rec)])
        raise Failed("WALK_SERVE_FAILED", f"{failed[0]} {failed[1]}")
    m["serve"] = {"tree": str(tree), "port": port, "web_port": web_port, "api": api_rec, "web": web_rec, "started_at": W._now_iso(walk.world)}
    walk.write_manifest(m)
    walk.emit({"api": f"http://127.0.0.1:{port}", "web": f"http://127.0.0.1:{web_port}", "api_pid": api,
               "web_pid": web})
    return 0


# --- smoke, stop, status, drop (§3.6) --------------------------------------------------------------------------------

def cmd_smoke(walk: Walk) -> int:
    m = walk.need_manifest()
    if not walk.serving(m):
        raise Refused("WALK_NOT_SERVING", walk.name)
    walk.deps.world.require("walk-smoke")  # M2: S3 launches Chromium; this process is the one heavy-slot.sh wraps
    s, wd = m["serve"], walk.walk_definition()
    base = f"http://127.0.0.1:{s['port']}"
    lines = []
    status, _ = walk.deps.http(f"{base}/api/health", 10.0)
    lines.append(_line("S1", status == 200, f"status {status}"))
    expect = wd.expect
    status, raw = walk.deps.http(f"{base}/api/portfolio/month?month={expect['month']}", 60.0)
    try:
        body = json.loads(raw) if status == 200 else None
    except ValueError:
        body = None
    bad = [f"status {status}"] if status != 200 else judge_month(body, expect, expected_as_of(m, expect))
    lines.append(_line("S2", not bad, "; ".join(bad) or f"{expect['tenant']} {expect['month']} served"))
    lines.append(_guard("S3", lambda: _s3(walk, s, wd)))
    lines.append(_guard("S4", lambda: _census_line(walk, m, "S4")))  # D-WK.13: after the pages were walked
    passed = all(x["state"] == "PASS" for x in lines)
    for x in lines:
        walk.emit(x)
    walk.emit({"check": "ALL", "state": "PASS" if passed else "FAIL"})
    return 0 if passed else 4


def _s3(walk: Walk, s: Mapping[str, Any], wd: WalkDefinition) -> dict:
    runner, environ = walk.deps.world.runner, walk.environ
    printed = runner(["bash", "-c", f'. "{PW_ENV}" && for n in {" ".join(NODE_FROM_PW)}; do '
                      'printf "%s=%s\\n" "$n" "${!n}"; done'], str(REPO), _base_env(environ), 30.0)
    if printed.returncode != 0:
        return _line("S3", False, f"env exit {printed.returncode}")
    values = pw_values(printed.stdout)
    missing = [n for n in NODE_FROM_PW if not values.get(n)]
    if missing:
        return _line("S3", False, f"env {missing[0]}")
    env = node_env(environ, values)
    out = Path(EVIDENCE_ROOT) / walk.label
    pages = smoke_pages(wd, walk.world_definition())
    argv = ["node", SMOKE_SCRIPT, "--base", f"http://127.0.0.1:{s['web_port']}", "--pages", json.dumps(pages),
            "--out", f"{out}/"]
    try:
        done = runner(argv, str(REPO), env, float(walk.args.cap_seconds))
    except subprocess.TimeoutExpired:
        return _line("S3", False, "cap")
    return _line("S3", done.returncode == 0, f"exit {done.returncode} {len(pages)} pages {out}/report.json")


def _report_refused(results: Sequence[tuple[Mapping[str, Any], str | None]]) -> list:
    """`WALK_PID_REUSED <pid> <check>` on stderr for each child whose group was not signalled."""
    refused = [rec.get("pid") for rec, reason in results if reason is not None]
    for rec, reason in results:
        if reason is not None:
            sys.stderr.write(f"WALK_PID_REUSED {rec.get('pid')} {reason}\n")
    return refused


def cmd_stop(walk: Walk) -> int:
    m = walk.need_manifest()
    s = m.get("serve")
    procs, clock = walk.deps.procs, walk.deps.world.clock
    results = [(s[w], stop_child(procs, s[w], clock)) for w in ("api", "web")] if s else []
    reused = _report_refused(results)
    m["serve"] = None
    walk.write_manifest(m)
    walk.emit({"database": walk.name, "stopped": bool(s), "reused": reused})
    return 0


def cmd_status(walk: Walk) -> int:
    m = walk.need_manifest()
    s = m.get("serve")
    alive = None
    if s:
        alive = {w: walk.deps.procs.alive(s[w]) for w in ("api", "web")}
    walk.emit({"database": m["database"], "parent": m["parent"], "check_passed": (m.get("check") or {}).get("passed"),
               "serve": s, "alive": alive})
    return 0


def cmd_drop(walk: Walk) -> int:
    m = walk.need_manifest()
    if m.get("serve"):
        raise Refused("WALK_SERVING", walk.name)
    clock = walk.deps.world.clock
    end = clock.monotonic() + IDLE_WAIT_SECONDS
    while walk.sessions() != 0:
        if clock.monotonic() >= end:
            raise Refused("WALK_DATABASE_IN_USE", walk.name)
        clock.sleep(0.25)
    if walk.exists():
        walk.admin(f'DROP DATABASE "{walk.name}"')
    walk.manifest_path().unlink()
    walk.emit({"database": walk.name, "dropped": True})
    return 0


# --- the command line ------------------------------------------------------------------------------------------------

COMMANDS = {"copy": cmd_copy, "prepare": cmd_prepare, "check": cmd_check, "serve": cmd_serve, "smoke": cmd_smoke,
            "stop": cmd_stop, "status": cmd_status, "drop": cmd_drop}
HEAVY = ("copy", "prepare", "check", "drop")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python tools/walk_world.py", description="The walkthrough database.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("--label", required=True)
        p.add_argument("--definition", default=W.DEFINITION)
        p.add_argument("--walk-definition", default=WALK_DEFINITION)
        p.add_argument("--state", default=W.DEFAULT_STATE)
        p.add_argument("--prefix", default=W.DEFAULT_PREFIX)
        p.add_argument("--cap-seconds", type=float, default=900.0)
        if name == "serve":
            p.add_argument("--tree", required=True)
            p.add_argument("--port", type=int, default=None)
            p.add_argument("--web-port", type=int, default=None)
    return parser


def main(argv: Sequence[str] | None = None, *, deps: WalkDeps | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    deps = deps or WalkDeps()
    if args.command in HEAVY:
        deps.world.require("walk", db=True)
    walk = None
    try:
        walk = Walk(args, deps)
        return COMMANDS[args.command](walk)
    except Refused as r:
        sys.stderr.write(f"{r.code} {r.detail}\n")
        return 2
    except StepFailed as f:
        sys.stderr.write(f"STEP_FAILED {f.database} {f.step} {f.exit_code}\n")
        return 3
    except Failed as f:
        sys.stderr.write(f"{f.code} {f.detail}\n")
        return 4
    except CapExceeded as c:
        sys.stderr.write(f"WALK_CAP_EXCEEDED {c.step}\n")
        return 5
    finally:
        if walk is not None and deps.world.admin is None and isinstance(walk.admin, W.Admin):
            walk.admin.dispose()


if __name__ == "__main__":
    sys.exit(main())
