"""D-DD.95: `world_history.py site-inputs` reads `/2` onboarding documents only, a component may have no rating, and a
Site code in two read documents refuses (`F` serves every Site type; C-DD11 reads the on1 directory)."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .conftest import CLI, REPOSITORY_ROOT

ON1 = REPOSITORY_ROOT / "backend/tests/fixtures/on1"
BINDINGS = REPOSITORY_ROOT / "backend/conversions/world"
# Golden: sha256 of `F` built from the `/2` Lakeside file alone, from the branch's /2-only run (no main equivalent).
# D-DD.114: Kobo binds minigrid-roles-5 (was 4e36563d6bc81cccc9dee28b67a69520bab22fef6f865d89e740cb957d6333d9 under roles-4;
# the role-set name and the foundation digest over it are the only changes in the file)
# DD3b merge: the branch's /2 file adds Kisiwa and Mto kit (DD3b2 part 1) on top of main's roles-5
# (742a75d1edbf80a9f6daf8684817a3ad6984c1d4dcf5badb9a4c73167124e0bd on main)
LAKESIDE_ALONE_SHA256 = "7d582e06819c3c9117e9e818b144a92e22dcef7aeb475b5c9e299ec7ee3131ba"


def _run(onboarding: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CLI), "site-inputs", "--onboarding", str(onboarding),
                           "--bindings", str(BINDINGS), "--out", str(out)], capture_output=True, text=True)


def _only(tmp_path: Path, name: str, *files: str) -> Path:
    directory = tmp_path / name
    directory.mkdir()
    for file in files:
        shutil.copy(ON1 / file, directory / file)
    return directory


def test_the_v1_file_is_skipped_and_the_on1_directory_runs(tmp_path: Path) -> None:
    done = _run(ON1, tmp_path / "all.json")
    assert done.returncode == 0, done.stderr
    assert "SKIPPED lakeside-power.v1.onboarding.json assetops.operator-onboarding/1" in done.stderr


def test_lakeside_entries_from_on1_equal_the_v2_file_alone(tmp_path: Path) -> None:
    assert _run(ON1, tmp_path / "all.json").returncode == 0
    alone = _only(tmp_path, "alone", "lakeside-power.onboarding.json")
    assert _run(alone, tmp_path / "alone.json").returncode == 0
    everything = json.loads((tmp_path / "all.json").read_text())
    lakeside = [s for s in everything["sites"] if s["tenant"] == "lakeside-power"]
    only = json.loads((tmp_path / "alone.json").read_text())["sites"]
    assert lakeside == only and len(only) == 3
    assert hashlib.sha256((tmp_path / "alone.json").read_bytes()).hexdigest() == LAKESIDE_ALONE_SHA256


def test_a_component_without_a_rating_passes(tmp_path: Path) -> None:
    document = json.loads((ON1 / "harvest-cold.onboarding.json").read_text())
    stripped = copy.deepcopy(document)
    removed = 0
    for site in stripped["sites"]:
        for component in site["components"]:
            if component.pop("rating", None) is not None:
                removed += 1
    assert removed, "the fixture has ratings to strip"
    directory = tmp_path / "norating"
    directory.mkdir()
    (directory / "harvest-cold.onboarding.json").write_text(json.dumps(stripped))
    # a binding is needed for a Site to be written: join Kobo's file with a cold file that has none is a no-op, so call
    # the pure function with a binding copied for a cold code
    from assetops_simulator.world import telemetry as tel
    binding = json.loads((BINDINGS / "KOBO-001-bindings.json").read_text())
    code = stripped["sites"][0]["code"]
    result = tel.site_inputs(stripped, {code: binding})
    components = result["sites"][0]["foundation"]["components"]
    assert components and all("rating" not in c for c in components)


def test_a_duplicate_site_code_refuses(tmp_path: Path) -> None:
    directory = _only(tmp_path, "dup", "lakeside-power.onboarding.json")
    shutil.copy(ON1 / "lakeside-power.onboarding.json", directory / "copy.onboarding.json")
    done = _run(directory, tmp_path / "dup.json")
    assert done.returncode == 3
    assert done.stderr.startswith("TEL_FOUNDATION KISIWA-001 is in")
