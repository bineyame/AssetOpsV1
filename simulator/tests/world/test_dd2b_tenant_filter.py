"""DD2b fix round 8 (D-DD.74): `world_history.py exports --tenant SLUG` keeps only the named tenants' files."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .books_support import MANIFEST
from .conftest import CLI

LAKESIDE, COLD, EV = "lakeside-power", "harvest-cold", "metro-bus"


def _run(tmp_path: Path, name: str, *tenants: str, extras: bool = False) -> tuple[subprocess.CompletedProcess, Path, Path]:
    out, extra = tmp_path / name, tmp_path / f"{name}-extras"
    argv = [sys.executable, str(CLI), "exports", "--manifest", str(MANIFEST), "--out", str(out)]
    for slug in tenants:
        argv += ["--tenant", slug]
    if extras:
        argv += ["--extras", str(extra)]
    return subprocess.run(argv, capture_output=True, text=True, timeout=300), out, extra


def _starts(directory: Path, slug: str) -> list[str]:
    return sorted(p.name for p in directory.iterdir() if p.name.startswith(f"{slug}."))


def test_t1_one_tenant_writes_no_other_tenants_file_and_the_same_lakeside_bytes(tmp_path: Path) -> None:
    full, full_out, full_extra = _run(tmp_path, "full", extras=True)
    one, one_out, one_extra = _run(tmp_path, "one", LAKESIDE, extras=True)
    assert full.returncode == one.returncode == 0, (full.stderr, one.stderr)
    assert _starts(full_out, COLD) and _starts(full_out, EV)  # the unfiltered run does carry them
    for directory in (one_out, one_extra):
        assert {p.name.split(".")[0] for p in directory.iterdir()} <= {LAKESIDE, "unwritten"}
    lakeside = _starts(full_out, LAKESIDE)
    assert lakeside and _starts(one_out, LAKESIDE) == lakeside
    assert all((one_out / n).read_bytes() == (full_out / n).read_bytes() for n in lakeside)
    assert (one_out / "unwritten.json").read_bytes() == (full_out / "unwritten.json").read_bytes()
    assert _starts(one_extra, LAKESIDE) == _starts(full_extra, LAKESIDE) != []


def test_t2_two_flags_write_both_tenants(tmp_path: Path) -> None:
    run, out, _ = _run(tmp_path, "two", LAKESIDE, COLD)
    assert run.returncode == 0, run.stderr
    assert _starts(out, LAKESIDE) and _starts(out, COLD) and not _starts(out, EV)


def test_t3_an_unknown_slug_is_refused(tmp_path: Path) -> None:
    run, _, _ = _run(tmp_path, "bad", "nobody")
    assert run.returncode == 3 and "EMU_TENANT_UNKNOWN nobody" in run.stderr
