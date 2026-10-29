"""Summarise py-spy raw profiles from tools/profile-tests-in-container.ps1 (PERF-01).

    python tools/profile-summary.py --cpu <on-CPU run dir> --wall <idle-included run dir> [--out <file.md>]

py-spy samples at 100 Hz with --threads and --subprocesses, so every line starts with its process (children nest
under the pytest process) and thread. Groups:
    test thread     the pytest MainThread while a test runs (stacks under pytest_runtest_protocol; collection and
                    imports are left out, they are paid once per worker, not per test)
    in-process app  the other threads of the pytest process: Starlette TestClient portal / AnyIO workers, where
                    the in-process central app ingests the gateway's uploads and serves reads
    gateway child   `python -m assetops_gateway serve` processes
    other child     any other child process
--wall (idle samples included) gives the test thread's wall time by what it was doing or waiting on.
--cpu (on-CPU samples only) gives where CPU went in every group, by leaf category and by AssetOps function.
"""

from __future__ import annotations

import argparse
import collections
import re
from pathlib import Path

FRAME = re.compile(r"^(?P<func>.*?) \((?P<path>[^()]*?)(?::(?P<line>\d+))?\)$")


def split_frame(frame: str):
    m = FRAME.match(frame)
    return (m.group("func"), m.group("path") or "") if m else (frame, "")


def is_assetops(path: str) -> bool:
    return ("site-packages" not in path and "_pytest" not in path and
            any(k in path for k in ("assetops_", "host/", "tests/", "simulator/", "gateway/", "lab_", "gateway_")))


def leaf(frames) -> str:
    """Category of the innermost frame that tells what the thread was doing."""
    for frame in reversed(frames):
        func, p = split_frame(frame)
        if func == "sleep":
            return "sleep"
        if "assetops_gateway/ipc.py" in p:
            return "gateway IPC (waiting on / talking to the gateway child)"
        if "subprocess" in p and func in ("wait", "_wait", "_try_wait", "communicate", "_communicate"):
            return "waiting on a child process"
        if ("threading" in p or "queue" in p or "concurrent/futures" in p) and func in ("wait", "acquire", "get",
                                                                                       "result", "_wait_for_tstate_lock"):
            return "waiting on another thread (in-process app)"
        if "anyio/from_thread" in p or "starlette/testclient" in p:
            return "HTTP / ASGI stack (TestClient)"
        if "psycopg" in p:
            return "database driver (psycopg: round trip + Python)"
        if "sqlalchemy" in p:
            return "SQLAlchemy (Python)"
        if "alembic" in p:
            return "migrations (alembic)"
        if "pydantic" in p:
            return "validation (pydantic)"
        if "yaml" in p:
            return "YAML parsing"
        if p.startswith("json/") or "/json/" in p:
            return "JSON"
        if "hashlib" in p or "hmac" in p:
            return "hashing"
        if any(k in p for k in ("starlette", "fastapi", "anyio", "httpx", "h11", "httpcore", "asyncio", "ssl.py",
                                "http/client", "urllib", "socket.py", "selectors")):
            return "HTTP / ASGI / socket stack"
        if any(k in p for k in ("datetime", "decimal", "_strptime", "zoneinfo")):
            return "datetime / decimal"
        if p.startswith("re/") or "sre_" in p:
            return "regex"
        if "copy.py" in p:
            return "copy / deepcopy"
        if "importlib" in p or "<frozen" in p:
            return "imports"
        if is_assetops(p):
            parts = p.split("/")
            return "AssetOps: " + "/".join(parts[:2] if len(parts) > 2 else parts)
    return "other"


def parse_line(line: str):
    stack, _, count = line.rstrip().rpartition(" ")
    frames = stack.split(";")
    procs = [f for f in frames if f.startswith("process ")]
    thread_index = max((i for i, f in enumerate(frames) if f.startswith("thread (")), default=-1)
    thread = frames[thread_index] if thread_index >= 0 else ""
    code = [f for f in frames[thread_index + 1:] if not f.startswith(("process ", "thread ("))]
    last = procs[-1] if procs else ""
    if "assetops_gateway" in last:
        group = "gateway child"
    elif len(procs) > 1:
        group = "other child"
    elif "MainThread" in thread:
        group = "test thread" if any("pytest_runtest_protocol" in f for f in code) else "collection / start-up"
    else:
        group = "in-process app"
    return group, code, int(count)


def read(run: Path, name: str):
    path = run / f"{name}.raw"
    groups = collections.Counter()
    cats = collections.defaultdict(collections.Counter)
    funcs = collections.defaultdict(collections.Counter)
    if not path.exists():
        return groups, cats, funcs
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        group, code, n = parse_line(line)
        groups[group] += n
        cats[group][leaf(code)] += n
        seen = set()
        for frame in code:
            func, p = split_frame(frame)
            if is_assetops(p):
                key = f"{func} ({p})"
                if key not in seen:
                    seen.add(key)
                    funcs[group][key] += n
    return groups, cats, funcs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu", type=Path, required=True)
    parser.add_argument("--wall", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    names = sorted(p.stem for p in args.cpu.glob("*.raw"))
    out = ["# PERF-01 site-build profiles (py-spy 0.4.0, 100 Hz, --threads --subprocesses)", "",
           f"- on-CPU run: `{args.cpu.name}`; wall run (idle included): `{args.wall.name}`", ""]
    for name in names:
        wg, wc, _ = read(args.wall, name)
        cg, cc, cf = read(args.cpu, name)
        wall = wg["test thread"]
        out += [f"## {name}", "",
                f"Test thread wall (test phases only): {wall / 100:.1f} s. On-CPU seconds: " +
                ", ".join(f"{g} {cg[g] / 100:.1f}" for g in ("test thread", "in-process app", "gateway child",
                                                               "other child", "collection / start-up")), "",
                "Test thread wall by activity:", "", "| activity | s | share |", "| --- | ---: | ---: |"]
        out += [f"| {k} | {v / 100:.1f} | {100 * v / wall:.1f}% |" for k, v in wc["test thread"].most_common(16)]
        for group in ("test thread", "in-process app", "gateway child"):
            total = cg[group]
            if not total:
                continue
            out += ["", f"On-CPU in {group} ({total / 100:.1f} s) by leaf:", "", "| category | s | share |",
                    "| --- | ---: | ---: |"]
            out += [f"| {k} | {v / 100:.1f} | {100 * v / total:.1f}% |" for k, v in cc[group].most_common(14)]
            out += ["", f"Top AssetOps functions on-CPU in {group} (inclusive):", "", "| s | function |",
                    "| ---: | --- |"]
            out += [f"| {v / 100:.1f} | `{k}` |" for k, v in cf[group].most_common(18)]
        out.append("")
    text = "\n".join(out) + "\n"
    (args.out or (args.cpu / "profile-summary.md")).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
