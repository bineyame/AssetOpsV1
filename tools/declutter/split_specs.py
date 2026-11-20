"""Declutter step 4: split each over-cap spec (over the 15k-token cap, about 60 KB) by its own headings.

The sheet moved verbatim to `specs/<ID>/spec.md` first (move_step4.py). This script cuts that file at
its level-1/2 headings (outside code fences; a section still over the cap is cut again at its level-3
headings) and puts every section, unchanged and in its original order, into one of:

- `spec.md`    the binding text: the first section and every section that is not a ruling or a review;
- `rulings.md` a section whose heading names a ruling, closure, amendment, answer, pre-flight, revision,
               stop or question round (`(q3)`, `Q-C3-1`) or a ruling tag (`DD1a1-R2`), or starts with a
               decision ID (`D-SR.12`) or `R4`; a level-3 piece of an over-cap section keeps its parent's kind;
- `review.md`  a section whose heading starts with Review / Re-review / Verdict or names a review round
               (and is not a ruling).

Each kind is packed into parts of at most LIMIT bytes in order (`rulings.md`, `rulings-2.md`, ...); one
section larger than LIMIT is its own part. `specs/<ID>/README.md` lists every section in original order
with its old line range, its part and its line range there: the reassembly map.

Usage: python tools/declutter/split_specs.py [--dry-run]   # split every over-cap spec.md not yet split
       python tools/declutter/split_specs.py --verify      # reassemble each split sheet from its parts
                                                           # and compare bytes with the BASE original
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step4_map import BASE, SPECS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 60 * 1024
RUL = re.compile(r"ruling|closure|amendment|answer|pre-?flight|follow-?up|correction|revision|\brev\b|"
                 r"\(q\d|\(r\d|\bQ-?[A-Z]*\d|\bstop\b|[A-Za-z0-9]-R\d*\b", re.I)
REV = re.compile(r"^(review|re-?review|verdict)\b|\breview (round|r\d+\b|findings)", re.I)
ROW = re.compile(r"^\| (\d+) \| (\d+)-(\d+) \| `([^`]+)` \| (\d+)-(\d+) \|")


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


def heading_starts(lines: list[str], lo: int, hi: int, pattern: str) -> list[int]:
    out, fence = [], False
    for i in range(lo, hi):
        if lines[i].startswith(("```", "~~~")):
            fence = not fence
        elif not fence and re.match(pattern, lines[i]):
            out.append(i)
    return out


def sections(lines: list[str]) -> list[tuple[int, int, int]]:
    """(first, end, parent): a level-3 piece of an over-cap section keeps its parent's start line."""
    starts = heading_starts(lines, 0, len(lines), r"#{1,2} ")
    if not starts or starts[0] != 0:
        starts = [0] + starts
    cuts = list(zip(starts, starts[1:] + [len(lines)]))
    out = []
    for a, b in cuts:
        if sum(len(x.encode()) for x in lines[a:b]) > LIMIT:
            subs = [s for s in heading_starts(lines, a + 1, b, r"### ")]
            edges = [a] + subs + [b]
            out += [(x, y, a) for x, y in zip(edges, edges[1:])]
        else:
            out.append((a, b, a))
    return out


def kind(text: str, first: bool) -> str:
    title = re.sub(r"^#+\s*", "", text).strip()
    if first:
        return "spec"
    if RUL.search(title) or title.startswith("D-") or re.match(r"R\d", title):
        return "rulings"
    if REV.search(title):
        return "review"
    return "spec"


def plan(lines: list[str]):
    secs = sections(lines)
    kinds = [kind(lines[parent], i == 0) for i, (a, b, parent) in enumerate(secs)]
    parts: dict[int, str] = {}  # section index -> part file name
    for k in ("spec", "rulings", "review"):
        n, size = 1, 0
        for i, (a, b, _) in enumerate(secs):
            if kinds[i] != k:
                continue
            sz = sum(len(x.encode()) for x in lines[a:b])
            if size and size + sz > LIMIT:
                n, size = n + 1, 0
            parts[i] = f"{k}.md" if n == 1 else f"{k}-{n}.md"
            size += sz
    return secs, kinds, parts


def part_order(name: str) -> tuple[int, int]:
    kind_, _, n = name[:-3].partition("-")
    return (("spec", "rulings", "review").index(kind_), int(n or 1))


def split_one(spec_id: str, dry: bool) -> str | None:
    folder = ROOT / "specs" / spec_id
    src = folder / "spec.md"
    if (folder / "README.md").is_file() or src.stat().st_size <= LIMIT:
        return None
    data = src.read_bytes()
    lines = data.decode("utf-8").splitlines(keepends=True)
    secs, kinds, parts = plan(lines)
    bodies: dict[str, list[str]] = {}
    rows = []
    for i, (a, b, _) in enumerate(secs):
        part = parts[i]
        have = bodies.setdefault(part, [])
        p0 = len(have) + 1
        have.extend(lines[a:b])
        title = re.sub(r"^#+\s*", "", lines[a]).strip().replace("|", "/")
        title = title if len(title) <= 70 else title[:67] + "..."
        rows.append(f"| {i + 1} | {a + 1}-{b} | `{part}` | {p0}-{len(have)} | {title} |")
    old = next(k for k, v in SPECS.items() if v == spec_id)
    summary = ", ".join(f"`{p}` {sum(len(x.encode()) for x in v) // 1024} KB" for p, v in sorted(bodies.items(), key=lambda kv: part_order(kv[0])))
    readme = (
        f"# {spec_id}: split map\n\n"
        f"`.agent/{old}` ({len(data) // 1024} KB, {len(lines)} lines, sha256 `{hashlib.sha256(data).hexdigest()[:16]}`) "
        f"moved here on 2026-11-18 (declutter step 4) and was split by its own headings, verbatim and in order, "
        f"into {summary}. Open the part a citation names; an old `file:line` citation maps through the table "
        f"(old lines -> part lines). Proof: `python tools/declutter/split_specs.py --verify`.\n\n"
        "| # | Old lines | Part | Part lines | Section |\n| --- | --- | --- | --- | --- |\n"
        + "\n".join(rows) + "\n")
    if dry:
        print(f"{spec_id}: {len(secs)} sections -> {summary}")
        return spec_id
    src.unlink()
    for part, body in bodies.items():
        (folder / part).write_bytes("".join(body).encode("utf-8"))
    (folder / "README.md").write_text(readme, encoding="utf-8")
    print(f"{spec_id}: {len(secs)} sections -> {summary}")
    return spec_id


def line_map(spec_id: str) -> list[tuple[int, int, str, int]] | None:
    """[(old_first, old_last, part, part_first)] for a split sheet, else None."""
    readme = ROOT / "specs" / spec_id / "README.md"
    if not readme.is_file():
        return None
    out = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            out.append((int(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5))))
    return out


def verify() -> int:
    bad, n = [], 0
    for old, spec_id in SPECS.items():
        rows = line_map(spec_id)
        if rows is None:
            continue
        n += 1
        folder = ROOT / "specs" / spec_id
        original = git_bytes("show", f"{BASE}:.agent/{old}")
        parts = {p: (folder / p).read_bytes().decode("utf-8").splitlines(keepends=True) for p in {r[2] for r in rows}}
        used = {p: 0 for p in parts}
        out, expect_old = [], 1
        for a, b, p, p0 in rows:
            count = b - a + 1
            if a != expect_old or p0 != used[p] + 1:
                bad.append(f"{spec_id}: row {a}-{b} is out of order or leaves a gap")
            out.extend(parts[p][p0 - 1:p0 - 1 + count])
            used[p] += count
            expect_old = b + 1
        extra = [p for p in parts if used[p] != len(parts[p])]
        if extra:
            bad.append(f"{spec_id}: part(s) {extra} hold lines the map does not list")
        if "".join(out).encode("utf-8") != original:
            bad.append(f"{spec_id}: reassembled bytes differ from {BASE}:.agent/{old}")
        else:
            print(f"ok {spec_id}: {len(parts)} parts reassemble to {BASE}:.agent/{old} "
                  f"({len(original)} bytes, sha256 {hashlib.sha256(original).hexdigest()[:16]})")
    for b in bad:
        print(f"FAIL {b}")
    print(f"split specs: {n} verified, {len(bad)} problem(s)")
    return 1 if bad or n == 0 else 0


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(verify())
    done = [s for s in (split_one(i, "--dry-run" in sys.argv) for i in SPECS.values()) if s]
    print(f"{len(done)} spec(s) {'would be ' if '--dry-run' in sys.argv else ''}split")
