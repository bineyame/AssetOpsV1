#!/usr/bin/env python3
"""Register path check (0K4m u23 review H2): every row of derivation-register.md section 3.1 names a manifest leaf.

Each row's first backtick path must resolve in demo-site-scenario-manifest.yaml, or the row must say "removed" in its
disposition column (as M66/M67 do). A row that lists a leaf the manifest no longer has, as if it were live, fails.

Path grammar: dotted keys; `[sel]` on a list picks the element whose id/name/key/item/site/tenant equals sel (or, if
sel is an integer, that index). A text leaf must also match the row's Value cell (see stale()). Usage: python3 check_register_paths.py [--register FILE] [--manifest FILE]
Exit 0 when every row resolves or says removed; 1 otherwise (each failing row printed).
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TOKEN = re.compile(r"([^.\[\]]+)|\[([^\]]*)\]")
MATCH_KEYS = ("id", "name", "key", "item", "site", "tenant", "node", "asset")


MISSING = object()


def resolve(doc, path):
    """The leaf the path names, or MISSING."""
    cur = doc
    toks = TOKEN.findall(path)
    for key, sel in toks:
        if key:
            keys = {str(k): k for k in cur} if isinstance(cur, dict) else {}
            if key not in keys:
                return MISSING
            cur = cur[keys[key]]
        else:
            if isinstance(cur, list):
                if sel.isdigit():
                    i = int(sel)
                    if i >= len(cur):
                        return MISSING
                    cur = cur[i]
                    continue
                hit = [e for e in cur if isinstance(e, dict) and any(str(e.get(k)) == sel for k in MATCH_KEYS)]
                if not hit:
                    return MISSING
                cur = hit[0]
            elif isinstance(cur, dict) and sel in {str(k) for k in cur}:
                cur = cur[{str(k): k for k in cur}[sel]]
            else:
                return MISSING
    return cur


def stale(leaf, value):
    """A text leaf whose row shows other text. The Value cell may be cut at 40 characters, writes `|` as `/`, and may
    end with a "(was ...)" remark; numbers, lists and maps are not compared (their cells use other notations). A path
    ending in a list index names an element by position, which shifts when one before it is removed: this catches it."""
    if not isinstance(leaf, str) or value in ("", "\u2014"):
        return False
    try:
        float(leaf)
        return False
    except ValueError:
        pass
    norm = lambda t: re.sub(r"\s*/$", "", t.replace(" | ", " / ").strip())
    cell = norm(re.sub(r"\s*\(was .*$", "", value).replace("`", ""))
    text = norm(leaf)
    return not (text.startswith(cell) or cell.startswith(text))


def rows(register):
    text = register.read_text(encoding="utf-8").split("\n")
    start = next(i for i, l in enumerate(text) if l.startswith("### 3.1 "))
    end = next(i for i, l in enumerate(text) if i > start and l.startswith("### "))
    for n in range(start, end):
        line = text[n]
        if not re.match(r"^\| M\d+ \|", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        m = re.match(r"`([^`]+)`", cells[1])
        yield n + 1, cells[0], (m.group(1) if m else None), cells[2], cells[3] if len(cells) > 3 else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--register", default=str(HERE / "derivation-register.md"))
    ap.add_argument("--manifest", default=str(HERE / "demo-site-scenario-manifest.yaml"))
    a = ap.parse_args()
    doc = yaml.safe_load(Path(a.manifest).read_text(encoding="utf-8"))
    total = live = removed = 0
    bad = []
    for line, rid, path, value, disp in rows(Path(a.register)):
        total += 1
        says_removed = disp.startswith("removed")
        if path is None:
            bad.append(f"{rid} (line {line}): no backtick path")
        elif (leaf := resolve(doc, path)) is not MISSING:
            live += 1
            if says_removed:
                bad.append(f"{rid} (line {line}): `{path}` resolves, but the row says removed")
            elif stale(leaf, value):
                bad.append(f"{rid} (line {line}): `{path}` is {leaf[:60]!r} in the manifest; the row shows {value[:60]!r}")
        elif says_removed:
            removed += 1
        else:
            bad.append(f"{rid} (line {line}): `{path}` is not in the manifest and the row does not say removed")
    for b in bad:
        print("FAIL", b)
    print(f"register paths: {total} rows in 3.1, {live} resolve, {removed} marked removed, {len(bad)} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
