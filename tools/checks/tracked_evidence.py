"""Commit hygiene guard (declutter step 3; recommendation §5.5): generated evidence and logs are never tracked.

Fails when the git index holds:
  1. a log, err, pid or out file, or a raw session transcript (`*-log.txt`, `*-last.txt`, `*.jsonl` outside fixtures);
  2. a file inside an evidence-shaped folder (`*-captures*`, `*-evidence*`, `*-recapture*`, `*-screens`, `*-shots`,
     `*-wip`, `*-probe`) anywhere in the tree;
  3. an image (png, jpg, jpeg, gif, webp) outside the allowed folders;
  4. a file over MAX_BYTES outside the allowed folders;
  5. under `.agent/`: anything other than a root-level md/html/py/sh file or `.agent/delivery-drafts/*.md`
     (the text that stays tracked until declutter step 4 gives it a home).

Allowed folders (rules 3 and 4): `frontend/mockups/`, `frontend/public/`, `Docs/`, `contract-fixtures/`, and any
`fixtures/` or `__fixtures__/` folder. A test fixture is the only evidence that may be committed, and only there.

MAX_BYTES is 1 MiB. Outside the allowed folders the largest tracked files are a 0.68 MB build sheet and a 0.36 MB
registry JSON, while evidence bulk ranges from 0.1-0.5 MB screenshots (caught by rule 3) to 4.4 MB session
transcripts; 1 MiB leaves about 50% headroom over legitimate text and still catches transcripts and dumps. Lower it
after declutter step 4 moves the large build sheets (review L3). Test data
colocated in `__tests__/` (e.g. frontend/src/shell/__tests__/kobo-degraded-evidence-deltas.json, 1.38 MB) is allowed.

Sizes are read from the index (`git cat-file --batch-check`), so a staged file is checked as committed.
`--self-test` runs the rules on planted paths and exits 1 if any rule fails to fire or a clean path is flagged.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 1 << 20
ALLOWED_PREFIXES = ("frontend/mockups/", "frontend/public/", "Docs/", "contract-fixtures/")
ALLOWED_SEGMENTS = ("fixtures", "__fixtures__")
SIZE_ALLOWED_SEGMENTS = ALLOWED_SEGMENTS + ("__tests__",)
LOG = re.compile(r"\.(log|err|pid|out)$|-(log|last)\.txt$", re.I)
TRANSCRIPT = re.compile(r"\.jsonl$", re.I)
IMAGE = re.compile(r"\.(png|jpe?g|gif|webp)$", re.I)
EVIDENCE_DIR = re.compile(r"-(captures|evidence|recapture)(-.*)?$|-(screens|shots|wip|probe)$", re.I)
AGENT_KEPT = re.compile(r"\.agent/[^/]+\.(md|html|py|sh)$|\.agent/delivery-drafts/[^/]+\.md$")


def allowed(path: str, segments: tuple[str, ...]) -> bool:
    return path.startswith(ALLOWED_PREFIXES) or any(s in segments for s in path.split("/")[:-1])


def problems(entries: list[tuple[str, int]]) -> list[str]:
    out = []
    for path, size in entries:
        dirs = path.split("/")[:-1]
        if LOG.search(path):
            out.append(f"{path}: log/err/pid/out or session transcript")
        elif TRANSCRIPT.search(path) and not allowed(path, ALLOWED_SEGMENTS):
            out.append(f"{path}: jsonl transcript outside a fixtures folder")
        if any(EVIDENCE_DIR.search(d) for d in dirs):
            out.append(f"{path}: inside an evidence folder")
        if IMAGE.search(path) and not allowed(path, ALLOWED_SEGMENTS):
            out.append(f"{path}: image outside frontend/mockups, frontend/public, Docs or a fixtures folder")
        if size > MAX_BYTES and not allowed(path, SIZE_ALLOWED_SEGMENTS):
            out.append(f"{path}: {size} bytes, over the {MAX_BYTES}-byte cap outside fixtures and mocks")
        if path.startswith(".agent/") and not AGENT_KEPT.fullmatch(path):
            out.append(f"{path}: only root md/html/py/sh text is tracked under .agent/ (evidence goes to "
                       "/opt/assetecon/evidence/<task>/<run>/)")
    return out


def tracked(root: Path) -> list[tuple[str, int]]:
    listing = subprocess.run(["git", "-C", str(root), "ls-files", "-s", "-z"], capture_output=True, check=True)
    rows = [r.decode("utf-8", "surrogateescape") for r in listing.stdout.split(b"\0") if r]
    shas, paths = [], []
    for row in rows:
        meta, path = row.split("\t", 1)
        mode, sha, _stage = meta.split()
        if mode == "160000":  # submodule
            continue
        shas.append(sha)
        paths.append(path)
    check = subprocess.run(["git", "-C", str(root), "cat-file", "--batch-check=%(objectsize)"],
                           input="\n".join(shas).encode() + b"\n", capture_output=True, check=True)
    sizes = [int(s) for s in check.stdout.split()]
    return list(zip(paths, sizes))


def self_test() -> int:
    bad = [(".agent/post-W6-audit/run-1/shot.png", 200_000), (".agent/W9-evidence/report.md", 100),
           ("tools/foo-captures/a.json", 10), ("backend/run.log", 10), ("serve.pid", 5), ("x/y.err", 5),
           (".agent/planner-X-log.txt", 4_000_000), ("frontend/src/shot.png", 10), ("notes/session.jsonl", 10),
           (".agent/next-work.json", 10), ("backend/big.json", MAX_BYTES + 1), (".agent/X-wip/a.py", 10)]
    good = [(".agent/packet-declutter-03.md", 9000), (".agent/delivery-drafts/w1-panel-mapping-draft.md", 10),
            ("frontend/mockups/v70/previews/portfolio.png", 307_133), ("Docs/UI Design/Motivation/x.png", 1_747_141),
            ("backend/tests/fixtures/w2/ev-w206-vectors.json", 2_047_695),
            ("frontend/src/shell/__tests__/kobo-degraded-evidence-deltas.json", 1_377_522),
            ("backend/assetops_backend/evidence/__init__.py", 10), ("host/fixtures/diesel-f0/probe-result.json", 10),
            ("tools/layout-evidence.mjs", 285_412), ("frontend/src/shell/__fixtures__/a.png", 10)]
    failures = [f"not flagged: {p}" for p, s in bad if not problems([(p, s)])]
    failures += [f"wrongly flagged: {m}" for p, s in good for m in problems([(p, s)])]
    for f in failures:
        print(f"self-test: {f}")
    print(f"tracked-evidence self-test: {len(bad)} planted violations, {len(good)} clean paths, "
          f"{'FAIL' if failures else 'pass'}")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                               check=True).stdout.strip())
    entries = tracked(root)
    found = problems(entries)
    for line in found[:50]:
        print(line)
    if len(found) > 50:
        print(f"... and {len(found) - 50} more")
    print(f"tracked-evidence guard: {len(entries)} tracked files, {len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
