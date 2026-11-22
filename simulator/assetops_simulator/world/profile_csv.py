"""DD2.3/DD2.4 (spec `specs/DD-demo-data/spec.md` §3, §5.2, §5.3; D-DD.24, D-DD.49): emulated files in a source
profile's own format.

The profile file (`backend/conversions/profiles/<id>.profile.json`) is the one definition of the format: this module
compiles it with the contract's `compile_profile` and writes each record as one CSV row through its columns, the
inverse of `read_rows`. A record the profile cannot carry exactly raises `EMU_PROFILE <id> <path>` (an emulator bug).
`render_layout` refuses profile-shaped layouts on purpose (3A6: the contract renders illustrative layouts only), so
the emulator owns this writer; the round trip through `read_layout` is its test.

Cells are written in the profile's own canonical forms: numbers and dates as their canonical text (the profiles use
`.` decimals, no thousands mark, ISO dates and months), datetimes as ISO instants (kept as text by the reader), a coded
or bool path through its map, an absent value as an empty cell.

Standard library and `assetops_contracts.native` only.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Mapping, Sequence

from assetops_contracts.native import compile_profile
from assetops_contracts.native.layouts_v1 import Layout

#: The repository's profile folder (D-DD.24). Read as data; nothing of the backend is imported.
PROFILES_DIR = Path(__file__).resolve().parents[3] / "backend" / "conversions" / "profiles"


def load_profile(profile_id: str, profiles_dir: Path = PROFILES_DIR) -> tuple[dict, Layout]:
    """The profile object and its compiled layout (version 1)."""
    obj = json.loads((profiles_dir / f"{profile_id}.profile.json").read_text(encoding="utf-8"))
    return obj, compile_profile(obj, 1)


def _get(record: Mapping, path: str) -> object:
    node: object = record
    for part in path.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return None
        node = node[part]
    return node


def _text(value: object, layout: Layout, path: str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if not isinstance(value, str):
        raise ValueError(f"EMU_PROFILE {layout.id} {path}")
    return value


def _cell(layout: Layout, column, record: Mapping) -> str:
    first = column.paths[0]
    value = _get(record, first)
    if value is None:
        cell = ""
    elif first in column.maps:
        inverse = {v: k for k, v in column.maps[first].items()}
        text = _text(value, layout, first)
        if text not in inverse:
            raise ValueError(f"EMU_PROFILE {layout.id} {first}")
        cell = inverse[text]
    else:
        cell = _text(value, layout, first)
    for path in column.paths[1:]:  # every other path of the column must read back the same value
        found = _get(record, path)
        if cell == "":
            want = None
        elif path in column.maps:
            want = column.maps[path].get(cell)
        else:
            want = cell
        if found is None and want is None:
            continue
        if found is None or _text(found, layout, path) != want:
            raise ValueError(f"EMU_PROFILE {layout.id} {path}")
    return cell


def row_digest(layout: Layout, record: Mapping) -> str:
    """`read_rows`' `row_digest` source version, from the record's own canonical values (3A6)."""
    values = []
    for column in layout.columns:
        if not column.paths:
            continue
        value = _get(record, column.paths[0])
        values.append("" if value is None else _text(value, layout, column.paths[0]))
    return "r" + hashlib.sha256("\x1f".join(values).encode("utf-8")).hexdigest()[:16]


def render_profile(layout: Layout, records: Sequence[Mapping]) -> bytes:
    """The header row, then one row per record in order (CSV, comma, UTF-8, `\\n`)."""
    if layout.file.format != "csv" or layout.file.delimiter != "," or layout.file.header_row != 1:
        raise ValueError(f"EMU_PROFILE {layout.id} file")
    out = io.StringIO()
    writer = csv.writer(out, dialect="excel", lineterminator="\n")
    writer.writerow([c.header for c in layout.columns])
    for record in records:
        for path, value in layout.constants.items():
            found = _get(record, path)
            if found is None or found != value:
                raise ValueError(f"EMU_PROFILE {layout.id} {path}")
        if layout.version_digest and record.get("source_version") != row_digest(layout, record):
            raise ValueError(f"EMU_PROFILE {layout.id} source_version")
        writer.writerow([_cell(layout, column, record) if column.paths else "" for column in layout.columns])
    return out.getvalue().encode("utf-8")
