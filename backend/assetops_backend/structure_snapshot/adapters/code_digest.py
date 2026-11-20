"""3B7a unit 1 (spec §2.5; D-3B7A.11): the digest of the code that built a snapshot.

`import_closure` parses each module with `ast` (it never imports one) and follows every `Import` and `ImportFrom`
anywhere in the file, function bodies included (the compositions import lazily), resolving relative imports. It keeps
the modules of the first-party packages (`assetops_backend` and `assetops_contracts`, D-3B7A.11 as applied by the
review of round 1, F1) whose file exists, and each package `__init__` on the way. `rules_digest` is the
sha256 over "<module> <sha256 of its bytes>" lines in module-name order: any change to a module a build can reach
changes it. It over-reports (a refactor with no value change also marks a snapshot): the honest direction.
"""
from __future__ import annotations

import ast
import functools
import hashlib
import importlib.util
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT_PACKAGE = "assetops_backend"
PACKAGES = ("assetops_backend", "assetops_contracts")  # every first-party package the build imports
RULE_ROOTS = ("assetops_backend.structure_snapshot.composition",)
_PACKAGE_DIR = Path(__file__).resolve().parents[2]


def _contracts_dir() -> Path:
    spec = importlib.util.find_spec("assetops_contracts")  # locates the package; runs none of its code
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("assetops_contracts is not importable: the code digest cannot cover it")
    return Path(next(iter(spec.submodule_search_locations))).resolve()


def _dirs(package_dir: Path, contracts_dir: Path | None) -> dict[str, Path]:
    return {"assetops_backend": Path(package_dir),
            "assetops_contracts": Path(contracts_dir) if contracts_dir is not None else _contracts_dir()}


def _file(dirs: Mapping[str, Path], name: str) -> Path | None:
    """The source of module `name` under its package's directory, or None when it is not a first-party module."""
    parts = name.split(".")
    if parts[0] not in dirs:
        return None
    base = dirs[parts[0]].joinpath(*parts[1:])
    if parts[1:] and base.with_suffix(".py").is_file():
        return base.with_suffix(".py")
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    return None


def _package_of(name: str, path: Path) -> str:
    return name if path.name == "__init__.py" else name.rpartition(".")[0]


def _imported(dirs: Mapping[str, Path], name: str, path: Path) -> set[str]:
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
                found.add(candidate if _file(dirs, candidate) is not None else module)
    return {n for n in found if n.split(".")[0] in dirs}


def import_closure(package_dir: Path, roots: Sequence[str] = RULE_ROOTS,
                   contracts_dir: Path | None = None) -> tuple[str, ...]:
    dirs = _dirs(package_dir, contracts_dir)
    seen: set[str] = set()
    todo = list(roots)
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        path = _file(dirs, name)
        if path is None:
            continue
        seen.add(name)
        parts = name.split(".")
        todo.extend(".".join(parts[:i]) for i in range(1, len(parts)))  # each package __init__ on the way
        todo.extend(_imported(dirs, name, path))
    return tuple(sorted(seen))


def _digest(package_dir: Path, contracts_dir: Path | None = None) -> str:
    dirs = _dirs(package_dir, contracts_dir)
    lines = []
    for name in import_closure(package_dir, contracts_dir=contracts_dir):
        path = _file(dirs, name)
        lines.append(f"{name} {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


@functools.lru_cache(maxsize=1)
def _running() -> str:
    return _digest(_PACKAGE_DIR)


def rules_digest(package_dir: Path | None = None, contracts_dir: Path | None = None) -> str:
    """The digest of the build's code; the running packages' is computed once (cached)."""
    if (package_dir is None or Path(package_dir).resolve() == _PACKAGE_DIR) and contracts_dir is None:
        return _running()
    return _digest(Path(package_dir) if package_dir is not None else _PACKAGE_DIR, contracts_dir)


__all__ = ["PACKAGES", "RULE_ROOTS", "import_closure", "rules_digest"]
