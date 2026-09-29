"""Reproducible run-store evidence for T022B (`D-2026-09-29-run-store-libyaml`).

Runnable from any checkout, with no owner data required:

    .venv\\Scripts\\python.exe tools/run-store-evidence.py runtime
    .venv\\Scripts\\python.exe tools/run-store-evidence.py compare-corpus <runs-dir> [--json OUT]
    .venv\\Scripts\\python.exe tools/run-store-evidence.py seed <env-dir> (--runs N | --copy-runs-from DIR)
    .venv\\Scripts\\python.exe tools/run-store-evidence.py measure <env-dir> [--rounds K] [--json OUT]
    .venv\\Scripts\\python.exe tools/run-store-evidence.py serve <env-dir> --port P [--loader baseline|candidate]

`runtime` is the installation check: it prints the OS, Python, PyYAML and libyaml
versions and exits non-zero when the C extension the run store requires is
absent. `compare-corpus` reads a run directory READ-ONLY with both loaders and
compares the domain records they yield; it hashes every file before and after
and fails if anything changed. Everything that writes - `seed`, `measure`,
`serve` - writes only inside the environment directory it is given, which must
not be inside `var/`.

## Baseline and candidate

The candidate is this checkout's reader: `read_run_record` loading with
`CSafeLoader`. The baseline is the same reader with its loader name rebound to
the pure-Python `SafeLoader` for the duration of a sample - the pre-T022B load
policy with every other line of the reader, the store and the application held
fixed. It exists only here; nothing in the product can select it.

## Composition

`measure` and `serve` compose the application exactly as `host/lab_app.py`'s
`build_app` does - `create_app` with the gate open and a `HostLabExecution`
behind it - except that every store root is the environment's: runs, Sites,
scenarios, execution artifacts and stages. `build_app` cannot take those roots
(it builds `HostLabExecution()` over `var/`), and changing it for a benchmark
would change the product's entry point.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import statistics
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[1]
for tree in ("backend", "contracts", "simulator", "host"):
    if str(REPO / tree) not in sys.path:
        sys.path.insert(0, str(REPO / tree))

import yaml  # noqa: E402

API = "/api/simulator-lab"
SITE_ID = "MG-001"
SCENARIO_ID = "fuel-loss-event"
TEMPLATE_ID = "hybrid-mini-grid-100kw"


# --------------------------------------------------------------------- runtime


def runtime_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "os": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": sys.version.split()[0],
        "python_build": sys.version,
        "pyyaml": getattr(yaml, "__version__", None),
        "with_libyaml": bool(getattr(yaml, "__with_libyaml__", False)),
        "libyaml": None,
        "extension": None,
        "run_store_imports": False,
        "diagnostic": None,
    }
    try:
        import yaml._yaml as extension  # type: ignore[import-not-found]

        report["libyaml"] = extension.get_version_string()
        report["extension"] = extension.__file__
    except ImportError as error:
        report["diagnostic"] = str(error)
    try:
        import assetops_backend.runs.adapters.yaml_run_documents  # noqa: F401

        report["run_store_imports"] = True
    except ImportError as error:
        report["diagnostic"] = str(error)
    return report


def command_runtime(_: argparse.Namespace) -> int:
    report = runtime_report()
    for key, value in report.items():
        print(f"{key:18} {value}")
    ok = report["with_libyaml"] and report["run_store_imports"]
    print("RESULT            " + ("libyaml available" if ok else "LIBYAML MISSING"))
    return 0 if ok else 1


# --------------------------------------------------------------------- loaders


def documents_module():
    from assetops_backend.runs.adapters import yaml_run_documents

    return yaml_run_documents


@contextmanager
def loader(name: str) -> Iterator[None]:
    """Rebind the reader's loader for the length of one sample."""
    module = documents_module()
    chosen = {"baseline": yaml.SafeLoader, "candidate": yaml.CSafeLoader}[name]
    previous = module.CSafeLoader
    module.CSafeLoader = chosen
    try:
        yield
    finally:
        module.CSafeLoader = previous


def outcome(path: Path) -> tuple[str, Any]:
    """The domain outcome of reading one document: a record or a refusal type."""
    try:
        return ("record", documents_module().read_run_record(path))
    except Exception as error:  # noqa: BLE001 - classifying, not handling
        return ("refused", type(error).__name__)


def digest_tree(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
        if path.is_file()
    }


def command_compare_corpus(args: argparse.Namespace) -> int:
    root = Path(args.runs_dir).resolve()
    before = digest_tree(root)
    paths = documents_module().document_paths(root)
    total_bytes = sum(path.stat().st_size for path in paths)
    equal = 0
    differences: list[dict[str, Any]] = []
    statuses: dict[str, int] = {}
    versions: dict[str, int] = {}
    for path in paths:
        with loader("baseline"):
            base = outcome(path)
        with loader("candidate"):
            cand = outcome(path)
        if base == cand:
            equal += 1
        else:
            differences.append(
                {"document": path.name, "baseline": str(base)[:200], "candidate": str(cand)[:200]}
            )
        if cand[0] == "record":
            record = cand[1]
            statuses[record.execution_status] = statuses.get(record.execution_status, 0) + 1
            version = str(record.deterministic_identity.profiles.execution_contract_version)
            versions[version] = versions.get(version, 0) + 1
    after = digest_tree(root)
    summary = {
        "runs_dir": str(root),
        "documents": len(paths),
        "bytes": total_bytes,
        "equal_outcomes": equal,
        "differences": differences,
        "execution_status_counts": statuses,
        "execution_contract_version_counts": versions,
        "files_unchanged": before == after,
        "runtime": runtime_report(),
    }
    text = json.dumps(summary, indent=2, default=str)
    print(text)
    if args.json:
        Path(args.json).write_text(text, encoding="utf-8")
    return 0 if (not differences and before == after) else 1


# ------------------------------------------------------------------ composition


def refuse_owner_path(env: Path) -> None:
    var = (REPO / "var").resolve()
    if env.resolve() == var or var in env.resolve().parents:
        raise SystemExit(f"Refusing to use {env}: it is inside the owner's var/.")


def compose(env: Path, run_repository: Any = None):
    """`host/lab_app.build_app`'s composition over the environment's roots."""
    from assetops_backend.config import FeatureFlags
    from assetops_backend.main import create_app
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.scenarios.adapters.composite_scenario_repository import (
        CompositeScenarioRepository,
    )
    from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import (
        ReadOnlyYamlScenarioStore,
    )
    from assetops_backend.scenarios.adapters.yaml_user_scenario_store import (
        UserYamlScenarioStore,
    )
    from assetops_backend.sites.adapters.composite_site_repository import (
        CompositeSiteRepository,
    )
    from assetops_backend.sites.adapters.yaml_shipped_site_store import (
        ReadOnlyYamlSiteStore,
    )
    from assetops_backend.sites.adapters.yaml_user_site_store import (
        WritableYamlSiteStore,
    )
    from lab_execution import HostLabExecution, YamlExecutionArtifacts
    from source_stages import JsonSourceStages

    refuse_owner_path(env)
    return create_app(
        FeatureFlags(simulator_lab_enabled=True),
        site_repository=CompositeSiteRepository(
            shipped=ReadOnlyYamlSiteStore(),
            user=WritableYamlSiteStore(env / "sites"),
        ),
        scenario_repository=CompositeScenarioRepository(
            shipped=ReadOnlyYamlScenarioStore(),
            user=UserYamlScenarioStore(env / "scenarios"),
        ),
        run_repository=(
            YamlRunStore(env / "runs") if run_repository is None else run_repository
        ),
        execution=HostLabExecution(
            artifacts=YamlExecutionArtifacts(env / "executions"),
            stages=JsonSourceStages(env / "stages"),
        ),
    )


def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)


def setup_body(http, index: int) -> dict[str, Any]:
    """A run setup request the product accepts, varied by `index`."""
    scenario = http.get(f"{API}/scenarios/{SCENARIO_ID}").json()["scenario"]
    site = http.get(f"/api/sites/{SITE_ID}").json()
    profiles = http.get(f"{API}/run-profiles").json()
    model = profiles["model_profiles"][0]
    publication = profiles["publication_profiles"][0]
    timesteps = (15, 15, 30, 60, 5)
    days = 1 + index % 3
    return {
        "site_id": SITE_ID,
        "foundation_version": site["foundation"]["version"],
        "scenario_id": SCENARIO_ID,
        "scenario_version": scenario["version"]["scenario_version"],
        "interval": {
            "start_time": "2026-09-21T00:00:00Z",
            "end_time": f"2026-09-{21 + days:02d}T17:00:00Z",
        },
        "timestep_minutes": timesteps[index % len(timesteps)],
        "seed": 20260921 + index,
        "model_profile": {
            "profile_id": model["model_profile_id"],
            "profile_version": model["model_profile_version"],
        },
        "publication_profile": {
            "profile_id": publication["publication_profile_id"],
            "profile_version": publication["publication_profile_version"],
        },
        "run_inputs": [],
    }


class Collecting:
    """A run repository that keeps what setup freezes, for writing in bulk."""

    def __init__(self) -> None:
        self.written: list[Any] = []

    def create_run(self, record):
        self.written.append(record)
        return record

    def get_run(self, run_id):
        from assetops_backend.runs.ports import RunNotFound

        for record in self.written:
            if record.run_id == run_id:
                return record
        raise RunNotFound(run_id)

    def list_runs(self):
        return tuple(self.written)


def command_seed(args: argparse.Namespace) -> int:
    env = Path(args.env).resolve()
    refuse_owner_path(env)
    if env.exists() and any(env.iterdir()):
        raise SystemExit(f"{env} is not empty; seed a fresh directory.")
    for part in ("sites", "scenarios", "runs", "executions", "stages"):
        (env / part).mkdir(parents=True, exist_ok=True)

    http = client(compose(env))
    created = http.post(
        f"{API}/sites",
        json={
            "template_id": TEMPLATE_ID,
            "site_id": SITE_ID,
            "display_name": "Evidence mini-grid",
            "location": {"country": "Uganda", "locality": "Kalangala"},
            "timezone": "Africa/Kampala",
        },
    )
    if created.status_code != 201:
        raise SystemExit(f"Site creation failed: {created.status_code} {created.text}")

    if args.copy_runs_from:
        source = Path(args.copy_runs_from).resolve()
        before = digest_tree(source)
        for path in sorted(source.iterdir()):
            if path.is_file() and path.suffix == ".yaml":
                shutil.copy2(path, env / "runs" / path.name)
        if digest_tree(source) != before:
            raise SystemExit("The source run directory changed during the copy.")
    else:
        from assetops_backend.runs.adapters.yaml_run_documents import (
            serialize_run_document,
        )
        from assetops_backend.runs.identity import run_id_key
        from assetops_backend.runs.parsing import render_run_document

        collecting = Collecting()
        generator = client(compose(env, run_repository=collecting))
        bodies = [setup_body(generator, index) for index in range(min(args.runs, 15))]
        for index in range(args.runs):
            response = generator.post(f"{API}/runs", json=bodies[index % len(bodies)] | {"seed": 20260921 + index})
            if response.status_code != 201:
                raise SystemExit(f"Setup failed: {response.status_code} {response.text}")
        for record in collecting.written:
            path = env / "runs" / f"{run_id_key(record.run_id)}.yaml"
            path.write_bytes(serialize_run_document(render_run_document(record)))

    print(json.dumps(describe(env), indent=2))
    return 0


def describe(env: Path) -> dict[str, Any]:
    runs = sorted((env / "runs").glob("*.yaml"))
    sizes = [path.stat().st_size for path in runs]
    return {
        "env": str(env),
        "runs": len(runs),
        "bytes": sum(sizes),
        "mean_bytes": round(statistics.mean(sizes)) if sizes else 0,
        "min_bytes": min(sizes) if sizes else 0,
        "max_bytes": max(sizes) if sizes else 0,
    }


# -------------------------------------------------------------------- measure


def summarise(samples: list[float]) -> dict[str, Any]:
    return {
        "n": len(samples),
        "median_s": round(statistics.median(samples), 4),
        "min_s": round(min(samples), 4),
        "max_s": round(max(samples), 4),
        "samples_s": [round(sample, 4) for sample in samples],
    }


def command_measure(args: argparse.Namespace) -> int:
    env = Path(args.env).resolve()
    http = client(compose(env))
    body = setup_body(http, 0)
    start = describe(env)
    raw: list[dict[str, Any]] = []
    for round_index in range(args.rounds):
        order = ("baseline", "candidate") if round_index % 2 == 0 else ("candidate", "baseline")
        for name in order:
            with loader(name):
                began = time.perf_counter()
                listed = http.get(f"{API}/runs")
                inventory = time.perf_counter() - began
                if listed.status_code != 200:
                    raise SystemExit(f"Inventory failed: {listed.status_code} {listed.text[:400]}")
                rows = len(listed.json()["runs"])

                setup = None
                if not args.inventory_only:
                    began = time.perf_counter()
                    created = http.post(f"{API}/runs", json=body | {"seed": 90000000 + len(raw)})
                    setup = time.perf_counter() - began
                    if created.status_code != 201:
                        raise SystemExit(f"Setup failed: {created.status_code} {created.text[:400]}")
                    if not args.keep_created:
                        # Hold the store at its measured size, so every sample
                        # reads the same N - and a 2,000-record store is not
                        # pushed past MAX_DOCUMENTS by its own measurement.
                        run_id = created.json()["run"]["run_id"]
                        (env / "runs" / f"{run_id.casefold()}.yaml").unlink()
            raw.append(
                {"round": round_index, "loader": name, "rows": rows,
                 "inventory_s": inventory, "setup_s": setup}
            )
            print(
                f"round {round_index} {name:9} rows {rows:5} inventory {inventory:7.3f} s"
                + ("" if setup is None else f"  setup {setup:7.3f} s"),
                flush=True,
            )

    result: dict[str, Any] = {
        "boundary": "in-process ASGI request through the composed app (TestClient); "
        "inventory = GET /api/simulator-lab/runs, setup = POST /api/simulator-lab/runs",
        "store_held_constant": not args.keep_created,
        "start": start,
        "end": describe(env),
        "runtime": runtime_report(),
        "load": load_snapshot(),
        "samples": raw,
    }
    for name in ("baseline", "candidate"):
        mine = [sample for sample in raw if sample["loader"] == name]
        result[name] = {
            "first_inventory_s": round(mine[0]["inventory_s"], 4),
            "inventory_warm": summarise([s["inventory_s"] for s in mine[1:]] or [mine[0]["inventory_s"]]),
        }
        if not args.inventory_only:
            result[name]["first_setup_s"] = round(mine[0]["setup_s"], 4)
            result[name]["setup_warm"] = summarise([s["setup_s"] for s in mine[1:]] or [mine[0]["setup_s"]])
    text = json.dumps(result, indent=2, default=str)
    print(json.dumps({k: result[k] for k in ("start", "end", "baseline", "candidate")}, indent=2))
    if args.json:
        Path(args.json).write_text(text, encoding="utf-8")
    return 0


def load_snapshot() -> dict[str, Any]:
    """What else the machine was doing, as far as the standard library can say."""
    snapshot: dict[str, Any] = {"taken_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if hasattr(os, "getloadavg"):
        snapshot["loadavg"] = os.getloadavg()
    return snapshot


# ---------------------------------------------------------------------- serve


def command_serve(args: argparse.Namespace) -> int:
    import uvicorn

    env = Path(args.env).resolve()
    app = compose(env)
    module = documents_module()
    if args.loader == "baseline":
        module.CSafeLoader = yaml.SafeLoader
    print(f"serving {env} with the {args.loader} loader on {args.port}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("runtime").set_defaults(run=command_runtime)

    compare = commands.add_parser("compare-corpus")
    compare.add_argument("runs_dir")
    compare.add_argument("--json")
    compare.set_defaults(run=command_compare_corpus)

    seed = commands.add_parser("seed")
    seed.add_argument("env")
    group = seed.add_mutually_exclusive_group(required=True)
    group.add_argument("--runs", type=int)
    group.add_argument("--copy-runs-from")
    seed.set_defaults(run=command_seed)

    measure = commands.add_parser("measure")
    measure.add_argument("env")
    measure.add_argument("--rounds", type=int, default=6)
    measure.add_argument("--inventory-only", action="store_true")
    measure.add_argument(
        "--keep-created", action="store_true",
        help="keep each Draft a setup sample creates (the store then grows by one per sample)",
    )
    measure.add_argument("--json")
    measure.set_defaults(run=command_measure)

    serve = commands.add_parser("serve")
    serve.add_argument("env")
    serve.add_argument("--port", type=int, required=True)
    serve.add_argument("--loader", choices=("baseline", "candidate"), default="candidate")
    serve.set_defaults(run=command_serve)

    args = parser.parse_args()
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
