"""3B7a unit 1 (spec §2.5; D-3B7A.11): the digest of the code that built a snapshot.

`import_closure` parses each module with `ast` (it never imports one) and follows every `Import` and `ImportFrom`
anywhere in the file, function bodies included (the compositions import lazily), resolving relative imports. It keeps
the `assetops_backend` modules whose file exists, and each package `__init__` on the way. `rules_digest` is the
sha256 over "<module> <sha256 of its bytes>" lines in module-name order: any change to a module a build can reach
changes it. It over-reports (a refactor with no value change also marks a snapshot): the honest direction.
"""
from __future__ import annotations

import ast
import functools
import hashlib
from collections.abc import Sequence
from pathlib import Path

ROOT_PACKAGE = "assetops_backend"
RULE_ROOTS = ("assetops_backend.structure_snapshot.composition",)
_PACKAGE_DIR = Path(__file__).resolve().parents[1]


def _file(package_dir: Path, name: str) -> Path | None:
    """The source of module `name` under `package_dir`, or None when it is not a module of the package."""
    parts = name.split(".")
    if parts[0] != ROOT_PACKAGE:
        return None
    base = package_dir.joinpath(*parts[1:])
    if parts[1:] and base.with_suffix(".py").is_file():
        return base.with_suffix(".py")
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    return None


def _package_of(name: str, path: Path) -> str:
    return name if path.name == "__init__.py" else name.rpartition(".")[0]


def _imported(package_dir: Path, name: str, path: Path) -> set[str]:
    tree = ast.parse(path.read_bytes(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = _package_of(name, path).split(".")
                base = base[:len(base) - (node.level - 1)] if node.level > 1 else base
                module = ".".join(base + ([node.module] if node.module else []))
            else:
                module = node.module or ""
            for alias in node.names:
                candidate = f"{module}.{alias.name}"
                found.add(candidate if _file(package_dir, candidate) is not None else module)
    return {n for n in found if n.split(".")[0] == ROOT_PACKAGE}


def import_closure(package_dir: Path, roots: Sequence[str] = RULE_ROOTS) -> tuple[str, ...]:
    package_dir = Path(package_dir)
    seen: set[str] = set()
    todo = list(roots)
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        path = _file(package_dir, name)
        if path is None:
            continue
        seen.add(name)
        parts = name.split(".")
        todo.extend(".".join(parts[:i]) for i in range(1, len(parts)))  # each package __init__ on the way
        todo.extend(_imported(package_dir, name, path))
    return tuple(sorted(seen))


def _digest(package_dir: Path) -> str:
    lines = []
    for name in import_closure(package_dir):
        path = _file(package_dir, name)
        lines.append(f"{name} {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


@functools.lru_cache(maxsize=1)
def _running() -> str:
    return _digest(_PACKAGE_DIR)


def rules_digest(package_dir: Path | None = None) -> str:
    """The digest of the build's code; the running package's is computed once (cached)."""
    if package_dir is None or Path(package_dir).resolve() == _PACKAGE_DIR:
        return _running()
    return _digest(Path(package_dir))


__all__ = ["RULE_ROOTS", "import_closure", "rules_digest"]
