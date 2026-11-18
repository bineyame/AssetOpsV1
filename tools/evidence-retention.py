"""List (and, only on request, delete) evidence older than the retention window (owner O3: 2 weeks).

Evidence lives outside the repo under /opt/assetecon/evidence/ (RULES section 9). An item is:
  - in a folder holding MANIFEST.tsv (path, size, sha256, class, last_commit_date): one group per top-level
    evidence folder of the manifest (e.g. `.agent/post-W6-audit/`) or per root file; its capture date is the newest
    `last_commit_date` of its rows;
  - elsewhere: each `<task>/<run>/` folder (or a file directly under `<task>/`); its capture date is the newest
    file mtime inside it.

  python tools/evidence-retention.py                 # list items older than 14 days and their total size
  python tools/evidence-retention.py --days 30 --today 2026-12-01
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

ROOT = Path("/opt/assetecon/evidence")


def manifest_items(folder: Path) -> list[dict]:
    groups: dict[str, dict] = defaultdict(lambda: {"files": 0, "bytes": 0, "date": "", "paths": []})
    with (folder / "MANIFEST.tsv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            parts = row["path"].split("/")
            key = "/".join(parts[:2]) + "/" if len(parts) > 2 else row["path"]
            g = groups[key]
            if not (folder / row["path"]).exists():
                continue  # already purged; the manifest line stays
            g["files"] += 1
            g["bytes"] += int(row["size"])
            g["date"] = max(g["date"], row["last_commit_date"] or "")
            g["paths"].append(folder / row["path"])
    return [{"item": folder / key, "date": g["date"] or "unknown", "files": g["files"], "bytes": g["bytes"],
             "paths": g["paths"], "source": "manifest"} for key, g in sorted(groups.items()) if g["files"]]


def mtime_item(path: Path) -> dict:
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file() and not p.is_symlink()]
    newest = max((p.stat().st_mtime for p in files), default=path.stat().st_mtime)
    return {"item": path, "date": datetime.fromtimestamp(newest).date().isoformat(), "files": len(files),
            "bytes": sum(p.stat().st_size for p in files), "paths": [path], "source": "mtime"}


def collect(root: Path) -> list[dict]:
    items = []
    for task in sorted(p for p in root.iterdir() if not p.is_symlink()):
        if task.is_file():
            if task.name != "RETENTION-LOG.tsv":
                items.append(mtime_item(task))
        elif (task / "MANIFEST.tsv").is_file():
            items.extend(manifest_items(task))
        else:
            items.extend(mtime_item(run) for run in sorted(task.iterdir()) if not run.is_symlink())
    return items


def remove(item: dict, root: Path) -> None:
    for p in item["paths"]:
        resolved = p.resolve()
        if root.resolve() not in resolved.parents:
            raise SystemExit(f"refusing to delete outside {root}: {p}")
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--today", type=date.fromisoformat, default=date.today())
    ap.add_argument("--delete", action="store_true", help="delete the listed items after a typed confirmation")
    args = ap.parse_args(argv)
    cutoff = (args.today - timedelta(days=args.days)).isoformat()
    old = [i for i in collect(args.root) if i["date"] != "unknown" and i["date"] < cutoff]
    for i in old:
        print(f"{i['date']}\t{i['files']:>6} files\t{i['bytes'] / 1e6:>9.1f} MB\t{i['source']}\t{i['item']}")
    total = sum(i["bytes"] for i in old)
    print(f"{len(old)} items captured before {cutoff} ({args.days} days before {args.today}): "
          f"{sum(i['files'] for i in old)} files, {total / 1e6:.1f} MB")
    if not args.delete or not old:
        return 0
    phrase = f"delete {len(old)} items"
    typed = input(f"Type `{phrase}` to delete them, anything else aborts: ").strip()
    if typed != phrase:
        print("aborted; nothing deleted")
        return 1
    with (args.root / "RETENTION-LOG.tsv").open("a", encoding="utf-8") as log:
        for i in old:
            remove(i, args.root)
            log.write(f"{args.today}\t{i['date']}\t{i['files']}\t{i['bytes']}\t{i['item']}\n")
    print(f"deleted {len(old)} items, {total / 1e6:.1f} MB; logged in {args.root / 'RETENTION-LOG.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
