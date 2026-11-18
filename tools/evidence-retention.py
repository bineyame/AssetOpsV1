"""List (and, only on request, delete) evidence older than the retention window (owner O3: 2 weeks).

Evidence lives outside the repo under /opt/assetecon/evidence/ (RULES section 9). The tool works only there:
`--root` must be that folder or a folder under it after resolving symlinks, and every listed or deleted path is
checked against the fixed EVIDENCE_ROOT, never against a caller-supplied root.

An item is:
  - in a folder holding MANIFEST.tsv (path, size, sha256, class, last_commit_date): one group per top-level
    evidence folder of the manifest (e.g. `.agent/post-W6-audit/`) or per root file. Its date is
    max(newest last_commit_date of its rows, copied_at), where copied_at is the date in the folder's COPIED_AT file
    (written once, at copy-out). Without COPIED_AT the manifest's own mtime stands in. So a batch copied out of the
    repo is kept two weeks from copy-out even when its commits are older.
  - elsewhere: each `<task>/<run>/` folder (or a file directly under `<task>/`), dated by the newest file mtime.

Capture scripts (*.py, *.mjs, *.sh) in a manifest batch are kept by default: test comments cite them as the
provenance of measured fixtures. `--include-scripts` lists and deletes them too.

  python tools/evidence-retention.py                 # list items past 14 days and their total size
  python tools/evidence-retention.py --days 30 --today 2026-12-20
  python tools/evidence-retention.py --delete        # asks you to type `delete <n> items`; anything else aborts

Nothing is deleted without --delete and the typed confirmation. The coordinator asks the owner before the first
purge. Deleting keeps MANIFEST.tsv unchanged (the manifest line stays) and appends what went to RETENTION-LOG.tsv.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

EVIDENCE_ROOT = Path("/opt/assetecon/evidence")
SCRIPTS = (".py", ".mjs", ".sh")


def inside(path: Path) -> bool:
    """True when path, symlinks resolved, is EVIDENCE_ROOT or below it."""
    base, real = EVIDENCE_ROOT.resolve(), path.resolve()
    return real == base or base in real.parents


def safe_root(root: Path) -> Path:
    if not inside(root):
        raise SystemExit(f"refusing --root {root}: it resolves to {root.resolve()}, outside {EVIDENCE_ROOT}")
    return root.resolve()


def copied_at(folder: Path) -> str:
    stamp = folder / "COPIED_AT"
    if stamp.is_file():
        return date.fromisoformat(stamp.read_text(encoding="utf-8").strip()).isoformat()
    return datetime.fromtimestamp((folder / "MANIFEST.tsv").stat().st_mtime).date().isoformat()


def manifest_items(folder: Path, include_scripts: bool) -> list[dict]:
    copied = copied_at(folder)
    groups: dict[str, dict] = defaultdict(lambda: {"files": 0, "bytes": 0, "date": "", "paths": [], "kept": 0})
    with (folder / "MANIFEST.tsv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            parts = row["path"].split("/")
            key = "/".join(parts[:2]) + "/" if len(parts) > 2 else row["path"]
            g = groups[key]
            path = folder / row["path"]
            if not path.exists() or path.is_symlink():
                continue  # already purged (the manifest line stays), or not a plain copy
            if not include_scripts and path.suffix in SCRIPTS:
                g["kept"] += 1
                continue
            g["files"] += 1
            g["bytes"] += int(row["size"])
            g["date"] = max(g["date"], row["last_commit_date"] or "")
            g["paths"].append(path)
    return [{"item": folder / key, "date": max(g["date"], copied), "files": g["files"], "bytes": g["bytes"],
             "paths": g["paths"], "kept": g["kept"], "source": "manifest"}
            for key, g in sorted(groups.items()) if g["files"] or g["kept"]]


def mtime_item(path: Path) -> dict:
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file() and not p.is_symlink()]
    newest = max((p.stat().st_mtime for p in files), default=path.stat().st_mtime)
    return {"item": path, "date": datetime.fromtimestamp(newest).date().isoformat(), "files": len(files),
            "bytes": sum(p.stat().st_size for p in files), "paths": [path], "kept": 0, "source": "mtime"}


def collect(root: Path, include_scripts: bool) -> list[dict]:
    if (root / "MANIFEST.tsv").is_file():
        return manifest_items(root, include_scripts)
    items = []
    for task in sorted(p for p in root.iterdir() if not p.is_symlink()):
        if task.is_file():
            if task.name != "RETENTION-LOG.tsv":
                items.append(mtime_item(task))
        elif (task / "MANIFEST.tsv").is_file():
            items.extend(manifest_items(task, include_scripts))
        else:
            items.extend(mtime_item(run) for run in sorted(task.iterdir()) if not run.is_symlink())
    return items


def remove(item: dict) -> None:
    for p in item["paths"]:
        if p.is_symlink() or not inside(p) or p.resolve() == EVIDENCE_ROOT.resolve():
            raise SystemExit(f"refusing to delete {p}: not a plain path under {EVIDENCE_ROOT}")
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=EVIDENCE_ROOT, help=f"{EVIDENCE_ROOT} or a folder under it")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--today", type=date.fromisoformat, default=date.today())
    ap.add_argument("--include-scripts", action="store_true", help="also list and delete batch capture scripts")
    ap.add_argument("--delete", action="store_true", help="delete the listed items after a typed confirmation")
    args = ap.parse_args(argv)
    root = safe_root(args.root)
    cutoff = (args.today - timedelta(days=args.days)).isoformat()
    items = collect(root, args.include_scripts)
    old = [i for i in items if i["date"] <= cutoff and i["files"]]  # 14 or more days old
    for i in old:
        print(f"{i['date']}\t{i['files']:>6} files\t{i['bytes'] / 1e6:>9.1f} MB\t{i['source']}\t{i['item']}")
    total = sum(i["bytes"] for i in old)
    kept = sum(i["kept"] for i in items)
    print(f"{len(old)} items dated {cutoff} or earlier ({args.days} days before {args.today}): "
          f"{sum(i['files'] for i in old)} files, {total / 1e6:.1f} MB; {len(items)} items checked; "
          f"{kept} batch capture scripts kept{' (--include-scripts lists them)' if kept else ''}")
    if not args.delete or not old:
        return 0
    phrase = f"delete {len(old)} items"
    typed = input(f"Type `{phrase}` to delete them, anything else aborts: ").strip()
    if typed != phrase:
        print("aborted; nothing deleted")
        return 1
    with (EVIDENCE_ROOT / "RETENTION-LOG.tsv").open("a", encoding="utf-8") as log:
        for i in old:
            remove(i)
            log.write(f"{args.today}\t{i['date']}\t{i['files']}\t{i['bytes']}\t{i['item']}\n")
    print(f"deleted {len(old)} items, {total / 1e6:.1f} MB; logged in {EVIDENCE_ROOT / 'RETENTION-LOG.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
