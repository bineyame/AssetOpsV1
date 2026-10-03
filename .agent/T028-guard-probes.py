"""Mutation probes for the T028 guards. Each mutation must make the check fail;
every file is restored with git checkout (work is committed first)."""
import pathlib
import subprocess

ROOT = pathlib.Path(r"C:\Users\assef\Bineyame\AssetOpsv1")
A = "backend/assetops_backend/analytics"


def check() -> str:
    done = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "tools/check-architecture.ps1"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return done.stdout + done.stderr


def append(path: str, text: str) -> None:
    p = ROOT / path
    p.write_text(p.read_text(encoding="utf-8") + text, encoding="utf-8")


def replace(path: str, old: str, new: str) -> None:
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    assert old in s, (path, old)
    p.write_text(s.replace(old, new, 1), encoding="utf-8")


def restore(*paths: str) -> None:
    subprocess.run(["git", "checkout", "--", *paths], cwd=ROOT, check=True)


probes = [
    ("import from runs.profiles", lambda: append(f"{A}/dispatch.py", "\nfrom assetops_backend.runs.profiles import MODEL_PROFILES\n"),
     [f"{A}/dispatch.py"], "reaches private or simulator flow"),
    ("name EXECUTION_REQUIREMENTS", lambda: append(f"{A}/service.py", "\n_X = 'EXECUTION_REQUIREMENTS'\n"),
     [f"{A}/service.py"], "reaches private or simulator flow"),
    ("import the simulator", lambda: append("backend/assetops_backend/analytics_api.py", "\nimport assetops_simulator\n"),
     ["backend/assetops_backend/analytics_api.py"], "reaches private or simulator flow"),
    ("declaration lacks model_version", lambda: replace(f"{A}/declaration.py", "    model_version=dispatch.MODEL_VERSION,\n", ""),
     [f"{A}/declaration.py"], "does not declare 'model_version'"),
    ("declaration declares verification", lambda: replace(f"{A}/declaration.py", "    model_version=dispatch.MODEL_VERSION,\n", "    model_version=dispatch.MODEL_VERSION,\n    verification_rules=(),\n"),
     [f"{A}/declaration.py"], "declares verification rules"),
    ("declaration not listed", lambda: replace(f"{A}/declaration.py", "DECLARATIONS: tuple[AnalyticDeclaration, ...] = (DISPATCH,)", "DECLARATIONS: tuple[AnalyticDeclaration, ...] = ()"),
     [f"{A}/declaration.py"], "not listed in DECLARATIONS"),
    ("undeclared analytic module", lambda: (ROOT / f"{A}/fuel.py").write_text('ANALYTIC_ID = "fuel"\n', encoding="utf-8"),
     None, "has no declaration"),
    ("evidence imports analytics", lambda: append("backend/assetops_backend/evidence/overview.py", "\nfrom assetops_backend.analytics import dispatch\n"),
     ["backend/assetops_backend/evidence/overview.py"], "Accepted evidence imports"),
]

assert "Architecture check passed." in check(), "baseline must pass"
for name, mutate, paths, expected in probes:
    mutate()
    out = check()
    if paths:
        restore(*paths)
    else:
        (ROOT / f"{A}/fuel.py").unlink()
    print(("CAUGHT " if expected in out and "failed" in out else "MISSED ") + name)
assert "Architecture check passed." in check(), "restored tree must pass"
print("restored: pass")
