"""The run store reads with libyaml, and what that does and does not change.

`D-2026-09-29-run-store-libyaml` moved the run store's one load point from
PyYAML's pure-Python `SafeLoader` to `CSafeLoader`. That is a change of parser,
not of a scanner, and the two are not lexically equivalent, so this file does
three things and each is stated rather than implied:

1.  **The requirement.** The C extension is present, the adapter uses it, and an
    installation without it fails to import the run store with a message that
    says what is missing and what to do - rather than silently reading with a
    parser that accepts and refuses different documents.
2.  **The compatibility seam.** Every case goes through `read_run_record` on a
    real file, which is the reader the inventory, a single read, the fallback
    scan and the write-time readback all share. Each case is read twice: by the
    shipped reader, and by the same reader with its loader rebound to the
    pure-Python `SafeLoader` (the baseline). Domain records and translated
    refusal TYPES are compared, never low-level YAML exception prose. The
    declared differences assert BOTH sides, so a case that stopped
    discriminating between the parsers would fail rather than pass vacuously.
3.  **The mechanism.** The loader is counted where it is constructed, so the
    number of documents parsed by a canonical hit, an inventory and a create is
    asserted, and so is the fact that every one of those parses used libyaml.

A finite set of probes does not prove two general-purpose parsers equivalent,
and nothing here claims it does. The inherited policies are kept as they were:
an unknown top-level field is ignored, a duplicate YAML key keeps the last value.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

from run_fixtures import (
    FakeRuns,
    FakeScenarios,
    FakeSites,
    model_profile,
    publication_profile,
    scenario,
    setup_request,
    site,
)

from assetops_backend.runs.adapters import yaml_run_documents, yaml_run_store
from assetops_backend.runs.adapters.yaml_run_documents import (
    DOCUMENT_SUFFIX,
    MAX_DOCUMENT_BYTES,
    read_run_record,
    serialize_run_document,
)
from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.parsing import render_run_document
from assetops_backend.runs.ports import (
    RunConfigurationInvalid,
    RunIdentityConflict,
    RunNotFound,
)
from assetops_backend.runs.service import RunSetupService

BACKSLASH = chr(92)
TAB = chr(9)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


def a_run(*, blocked: bool = False, **overrides: Any) -> SimulationRun:
    """One frozen Draft, produced by the real service - READY, or BLOCKED."""
    setup = RunSetupService(
        FakeRuns(),
        FakeSites((site(),)),
        FakeScenarios((scenario(),)),
        model_profiles=(model_profile(),),
        publication_profiles=(
            publication_profile(gateway_id=None) if blocked else publication_profile(),
        ),
        now=lambda: "2026-09-21T09:00:00Z",
    )
    return setup.create_draft_run(setup_request(**overrides))


def stored_text(record: SimulationRun) -> str:
    """The exact text the store writes for `record`."""
    return serialize_run_document(render_run_document(record)).decode("utf-8")


Outcome = tuple[str, Any]


def outcome(path: Path) -> Outcome:
    """A domain record, or the TYPE of the refusal - never exception prose."""
    try:
        return ("record", read_run_record(path))
    except Exception as error:  # noqa: BLE001 - classifying, not handling
        return ("refused", type(error).__name__)


@pytest.fixture
def both_readers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[[bytes], tuple[Outcome, Outcome]]:
    """Read the same bytes with the baseline reader and the shipped one."""
    counter = iter(range(10_000))

    def read(payload: bytes) -> tuple[Outcome, Outcome]:
        path = tmp_path / f"case-{next(counter)}{DOCUMENT_SUFFIX}"
        path.write_bytes(payload)
        with monkeypatch.context() as patch:
            patch.setattr(yaml_run_documents, "CSafeLoader", yaml.SafeLoader)
            baseline = outcome(path)
        candidate = outcome(path)
        return baseline, candidate

    return read


RECORD = ("record",)
INVALID = ("refused", "RunConfigurationInvalid")


def is_record(result: Outcome, expected: SimulationRun) -> bool:
    return result[0] == "record" and result[1] == expected


# --------------------------------------------------------------- requirement


class TestLibyamlIsRequired:
    def test_the_installed_pyyaml_carries_libyaml(self) -> None:
        """The installation/CI check, as a test the suite cannot skip."""
        import yaml._yaml as extension  # noqa: F401 - presence is the assertion

        assert yaml.__with_libyaml__ is True
        assert yaml_run_documents.CSafeLoader is yaml.CSafeLoader
        assert extension.get_version_string()

    def test_the_load_point_names_the_c_loader(self) -> None:
        """Static half of the same rule; the architecture guard holds the rest."""
        source = Path(yaml_run_documents.__file__).read_text(encoding="utf-8")

        assert "yaml.load(text, Loader=CSafeLoader)" in source
        assert "safe_load(" not in source

    def test_an_installation_without_libyaml_cannot_import_the_run_store(
        self,
    ) -> None:
        """The missing-extension diagnostic, exercised for real.

        A child interpreter refuses to import `yaml._yaml` - the compiled
        extension - before PyYAML is first imported, which is exactly the state
        of a PyYAML built without libyaml: `import yaml` succeeds and
        `__with_libyaml__` is False. The run store must then refuse to import
        and say why, and the application entry point with it.
        """
        blocker = (
            "import sys, importlib.abc\n"
            "class NoLibyaml(importlib.abc.MetaPathFinder):\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name == 'yaml._yaml' or name == '_yaml':\n"
            "            raise ImportError('libyaml extension withheld by test')\n"
            "        return None\n"
            "sys.meta_path.insert(0, NoLibyaml())\n"
            "import yaml\n"
            "assert yaml.__with_libyaml__ is False, 'the simulation did not take'\n"
            "assert not hasattr(yaml, 'CSafeLoader')\n"
        )
        for target in (
            "import assetops_backend.runs.adapters.yaml_run_documents",
            "import assetops_backend.main",
        ):
            completed = subprocess.run(
                [sys.executable, "-B", "-c", blocker + target],
                capture_output=True,
                text=True,
                cwd=BACKEND_ROOT,
                timeout=120,
            )

            assert completed.returncode != 0, target
            assert "the simulation did not take" not in completed.stderr
            assert "LibyamlUnavailable" in completed.stderr
            assert "requires PyYAML's libyaml C extension" in completed.stderr
            assert "D-2026-09-29-run-store-libyaml" in completed.stderr
            assert "--only-binary=pyyaml" in completed.stderr

    def test_the_runtime_check_fails_without_libyaml(self) -> None:
        """`tools/run-store-evidence.py runtime` is the install-time check."""
        tool = REPO_ROOT / "tools" / "run-store-evidence.py"
        blocker = (
            "import sys, runpy, importlib.abc\n"
            "class NoLibyaml(importlib.abc.MetaPathFinder):\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name == 'yaml._yaml' or name == '_yaml':\n"
            "            raise ImportError('libyaml extension withheld by test')\n"
            "        return None\n"
            "sys.meta_path.insert(0, NoLibyaml())\n"
            f"sys.argv = [{str(tool)!r}, 'runtime']\n"
            f"runpy.run_path({str(tool)!r}, run_name='__main__')\n"
        )
        env = dict(os.environ, PYTHONWARNINGS="ignore")

        withheld = subprocess.run(
            [sys.executable, "-B", "-c", blocker],
            capture_output=True, text=True, cwd=REPO_ROOT, env=env, timeout=120,
        )
        present = subprocess.run(
            [sys.executable, "-B", str(tool), "runtime"],
            capture_output=True, text=True, cwd=REPO_ROOT, env=env, timeout=120,
        )

        assert withheld.returncode == 1, withheld.stdout + withheld.stderr
        assert "LIBYAML MISSING" in withheld.stdout
        assert "requires PyYAML's libyaml C extension" in withheld.stdout
        assert present.returncode == 0, present.stdout + present.stderr
        assert "libyaml available" in present.stdout


# ----------------------------------------------------- declared differences


class TestTheDeclaredDifferences:
    """The adapter compatibility changes the owner accepted, pinned both ways."""

    def test_a_literal_tab_after_a_colon_is_now_accepted(self, both_readers) -> None:
        record = a_run()
        text = stored_text(record).replace(": ", ":" + TAB, 1)

        baseline, candidate = both_readers(text.encode("utf-8"))

        assert baseline == INVALID
        assert is_record(candidate, record)

    def test_a_tab_inside_a_flow_sequence_is_now_accepted(self, both_readers) -> None:
        record = a_run()
        text = stored_text(record) + "extra_field: [a," + TAB + "b]\n"

        baseline, candidate = both_readers(text.encode("utf-8"))

        assert baseline == INVALID
        assert is_record(candidate, record)

    def test_a_literal_surrogate_escape_is_now_refused(self, both_readers) -> None:
        record = a_run()
        text = stored_text(record) + f'extra_field: "{BACKSLASH}uD800"\n'

        baseline, candidate = both_readers(text.encode("utf-8"))

        assert is_record(baseline, record)
        assert candidate == INVALID

    def test_an_out_of_range_escape_is_now_refused_as_invalid_yaml(
        self, both_readers
    ) -> None:
        """The baseline let a raw `ValueError` cross the seam; this translates."""
        record = a_run()
        text = stored_text(record) + f'extra_field: "{BACKSLASH}U00110000"\n'

        baseline, candidate = both_readers(text.encode("utf-8"))

        assert baseline == ("refused", "ValueError")
        assert candidate == INVALID

    def test_deep_flow_nesting_is_now_the_domains_refusal(
        self, both_readers
    ) -> None:
        """Found by T022B, not by the Architect's probe, and declared here.

        The pure-Python composer recurses per nesting level: a few hundred
        levels exhausted Python's recursion limit and a raw `RecursionError`
        crossed the seam untranslated. libyaml composes it, and the run
        parser's own document bound (nesting depth 12) then refuses it as
        `RunConfigurationInvalid` - in an ignored field and in a validated one
        alike. No readable document is affected.
        """
        record = a_run()
        deep = "[" * 600 + "]" * 600
        ignored = stored_text(record) + f"extra_field: {deep}\n"
        validated = stored_text(record).replace(
            f"run_id: {record.run_id}", f"run_id: {deep}", 1
        )

        for payload in (ignored, validated):
            baseline, candidate = both_readers(payload.encode("utf-8"))
            assert baseline == ("refused", "RecursionError")
            assert candidate == INVALID

    def test_flow_nesting_a_few_thousand_deep_ends_the_process(
        self, tmp_path: Path
    ) -> None:
        """RECORDED, NOT ENDORSED: an open decision, found by T022B.

        PyYAML's compiled `CParser` composes nodes recursively in C without
        consulting Python's recursion limit. Past a depth set by the native
        stack - measured between 2,500 and 3,000 levels on Windows (1 MB main
        thread stack) and between 20,000 and 30,000 on Linux x86-64 (8 MB),
        both far inside `MAX_DOCUMENT_BYTES` - it overflows the native stack
        and the interpreter dies before the domain's depth bound can refuse
        the document. The case below uses 100,000 levels (about 200 KB) so it
        reproduces on both. The baseline raised `RecursionError` and the process
        survived. No document either reader could read is affected: both
        refuse such nesting. But a hand-placed file of this shape in the run
        store now takes down the process serving the inventory rather than
        failing the request.

        Whether to bound nesting before loading is an Architect/owner call -
        it would be a new refusal rule the decision did not approve - so this
        test pins the behaviour as found, in a child process, so that a fix
        changes a test on purpose rather than silently.
        """
        record = a_run()
        path = tmp_path / f"{record.run_id}{DOCUMENT_SUFFIX}"
        deep = "[" * 100_000 + "]" * 100_000
        path.write_text(
            stored_text(record) + f"extra_field: {deep}\n", encoding="utf-8"
        )
        assert path.stat().st_size < MAX_DOCUMENT_BYTES

        def child(baseline: bool) -> subprocess.CompletedProcess[str]:
            script = "\n".join(
                [
                    "import pathlib, yaml",
                    "from assetops_backend.runs.adapters import yaml_run_documents as m",
                    "m.CSafeLoader = yaml.SafeLoader" if baseline else "pass",
                    "try:",
                    f"    m.read_run_record(pathlib.Path({str(path)!r}))",
                    "    print('READ')",
                    "except Exception as error:",
                    "    print('REFUSED', type(error).__name__)",
                ]
            )
            return subprocess.run(
                [sys.executable, "-B", "-c", script],
                capture_output=True, text=True, cwd=BACKEND_ROOT, timeout=120,
            )

        before, after = child(baseline=True), child(baseline=False)

        assert before.returncode == 0, before.stderr
        assert "REFUSED RecursionError" in before.stdout
        assert after.returncode != 0
        assert "READ" not in after.stdout and "REFUSED" not in after.stdout


# ------------------------------------------------------------ equal outcomes


def replace_once(old: str, new: str) -> Callable[[str], str]:
    def edit(text: str) -> str:
        assert old in text, f"fixture no longer contains {old!r}"
        return text.replace(old, new, 1)

    return edit


def append(tail: str) -> Callable[[str], str]:
    return lambda text: text + tail


#: Cases both readers must answer identically. `expected` is the outcome CLASS:
#: "record" (the unmodified record), "changed" (a record, equal between the two
#: readers but not to the original), or a refusal type name.
EQUAL_CASES: list[tuple[str, Callable[[str], str], str]] = [
    ("valid control", lambda text: text, "record"),
    ("unknown top-level field is ignored", append("extra_field: 1\n"), "record"),
    ("same-value duplicate key", lambda t: t + t.splitlines()[0] + "\n", "record"),
    (
        "different-value duplicate key keeps the last",
        append("created_at: '2026-09-21T10:00:00Z'\n"),
        "changed",
    ),
    ("merge key in an ignored field", append("base: &b {x: 1}\nextra_field:\n  <<: *b\n"), "record"),
    ("alias in an ignored field", append("base: &b [1, 2]\nextra_field: *b\n"), "record"),
    ("timestamp-shaped scalar in an ignored field", append("extra_field: 2026-09-21\n"), "record"),
    ("binary scalar in an ignored field", append("extra_field: !!binary AAAA\n"), "record"),
    ("set in an ignored field", append("extra_field: !!set {x}\n"), "record"),
    ("infinity in an ignored field", append("extra_field: .inf\n"), "record"),
    ("byte order mark", lambda text: chr(0xFEFF) + text, "record"),
    ("empty document", lambda text: "", "RunConfigurationInvalid"),
    ("scalar root", lambda text: "just a scalar\n", "RunConfigurationInvalid"),
    ("sequence root", lambda text: "- a\n- b\n", "RunConfigurationInvalid"),
    ("broken flow mapping", append("extra_field: {a: [1, 2}\n"), "RunConfigurationInvalid"),
    ("bad indentation", append("extra_field:\n  a: 1\n b: 2\n"), "RunConfigurationInvalid"),
    ("tab indentation", append("extra_field:\n" + TAB + "a: 1\n"), "RunConfigurationInvalid"),
    ("mapping value where none belongs", lambda text: "this: is: not: a run\n", "RunConfigurationInvalid"),
    ("undefined alias", append("extra_field: *nowhere\n"), "RunConfigurationInvalid"),
    ("unknown tag", append("extra_field: !mystery 1\n"), "RunConfigurationInvalid"),
    ("unsafe python tag", append("extra_field: !!python/object/apply:os.system [echo]\n"), "RunConfigurationInvalid"),
    ("unhashable key", append("? [a, b]\n: 1\n"), "RunConfigurationInvalid"),
    ("unknown escape", append(f'extra_field: "{BACKSLASH}q"\n'), "RunConfigurationInvalid"),
    ("embedded NUL", append("extra_field: a" + chr(0) + "b\n"), "RunConfigurationInvalid"),
    ("two documents", append("---\nextra_field: 1\n"), "RunConfigurationInvalid"),
    ("truncated binary", append("extra_field: !!binary A\n"), "RunConfigurationInvalid"),
    # Wrong domain values: the YAML is fine and the run is not.
    ("status the record contradicts", replace_once("execution_status: READY", "execution_status: BLOCKED"), "RunConfigurationInvalid"),
    ("seed as a quoted string", replace_once("seed: 4242", "seed: '4242'"), "RunConfigurationInvalid"),
    ("seed as a float", replace_once("seed: 4242", "seed: 4242.0"), "RunConfigurationInvalid"),
    ("seed as a boolean", replace_once("seed: 4242", "seed: true"), "RunConfigurationInvalid"),
    ("seed as null", replace_once("seed: 4242", "seed: null"), "RunConfigurationInvalid"),
    ("run_id that is not an identity", lambda t: t.replace(t.splitlines()[0], "run_id: not-a-run", 1), "RunConfigurationInvalid"),
    # Inherited, and the same in both: construction errors PyYAML raises as
    # `ValueError` are not `YAMLError`, so neither reader translates them. They
    # are recorded as equal rather than endorsed; see the review packet.
    ("impossible date in an ignored field", append("extra_field: 2026-02-30\n"), "ValueError"),
    ("integer beyond Python's digit limit", append("extra_field: 1" + "0" * 5000 + "\n"), "ValueError"),
]


class TestTheOutcomesThatDidNotChange:
    @pytest.mark.parametrize(
        ("edit", "expected"),
        [pytest.param(edit, expected, id=name) for name, edit, expected in EQUAL_CASES],
    )
    def test_both_readers_agree(
        self, both_readers, edit: Callable[[str], str], expected: str
    ) -> None:
        record = a_run()
        baseline, candidate = both_readers(edit(stored_text(record)).encode("utf-8"))

        assert baseline == candidate
        if expected == "record":
            assert is_record(candidate, record)
        elif expected == "changed":
            assert candidate[0] == "record" and candidate[1] != record
        else:
            assert candidate == ("refused", expected)

    def test_invalid_utf8_is_refused_before_yaml(self, both_readers) -> None:
        payload = stored_text(a_run()).encode("utf-8") + b"extra_field: \xff\xfe\n"

        baseline, candidate = both_readers(payload)

        assert baseline == candidate == INVALID

    def test_an_oversize_document_is_refused_before_yaml(self, both_readers) -> None:
        payload = stored_text(a_run()).encode("utf-8")
        payload += b"#" * (MAX_DOCUMENT_BYTES + 1 - len(payload))
        assert len(payload) == MAX_DOCUMENT_BYTES + 1

        baseline, candidate = both_readers(payload)

        assert baseline == candidate == INVALID

    @pytest.mark.parametrize("blocked", [False, True], ids=["READY", "BLOCKED"])
    def test_what_the_store_writes_reads_the_same_either_way(
        self, both_readers, blocked: bool
    ) -> None:
        """Generated write/readback, for both execution statuses."""
        record = a_run(blocked=blocked)

        baseline, candidate = both_readers(stored_text(record).encode("utf-8"))

        assert is_record(baseline, record)
        assert is_record(candidate, record)


# ----------------------------------------------------------------- mechanism


class CountingLoaders:
    """Every loader the run store constructs, and which class it was."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.constructed: list[str] = []
        seen = self.constructed

        class Counting(yaml.CSafeLoader):
            def __init__(self, stream: Any) -> None:
                seen.append("CSafeLoader")
                super().__init__(stream)

        monkeypatch.setattr(yaml_run_documents, "CSafeLoader", Counting)


@pytest.fixture
def loads(monkeypatch: pytest.MonkeyPatch) -> CountingLoaders:
    return CountingLoaders(monkeypatch)


def a_store_of(root: Path, count: int) -> tuple[YamlRunStore, tuple[SimulationRun, ...]]:
    store = YamlRunStore(root)
    records = tuple(a_run() for _ in range(count))
    for record in records:
        store.create_run(record)
    return store, records


class TestEveryReadIsOneLibyamlParsePerDocument:
    """Criterion 4: the cost changed per document, not in how many are read."""

    N = 6

    def test_a_canonical_hit_parses_one_document(self, tmp_path, loads) -> None:
        store, records = a_store_of(tmp_path, self.N)
        loads.constructed.clear()

        assert store.get_run(records[2].run_id) == records[2]

        assert loads.constructed == ["CSafeLoader"]

    def test_the_inventory_parses_every_document(self, tmp_path, loads) -> None:
        store, records = a_store_of(tmp_path, self.N)
        loads.constructed.clear()

        assert set(store.list_runs()) == set(records)

        assert loads.constructed == ["CSafeLoader"] * self.N

    def test_a_fallback_read_parses_the_whole_store(self, tmp_path, loads) -> None:
        store, records = a_store_of(tmp_path, self.N)
        moved = records[1]
        (tmp_path / f"{moved.run_id}{DOCUMENT_SUFFIX}").rename(
            tmp_path / f"run-{'e' * 32}{DOCUMENT_SUFFIX}"
        )
        loads.constructed.clear()

        assert store.get_run(moved.run_id) == moved

        assert loads.constructed == ["CSafeLoader"] * self.N

    @pytest.mark.parametrize("existing", [0, 1, 6])
    def test_a_create_into_n_records_parses_two_n_plus_one(
        self, tmp_path, loads, existing: int
    ) -> None:
        """Both identity scans and the staged readback, all through libyaml."""
        store, _ = a_store_of(tmp_path, existing)
        loads.constructed.clear()

        store.create_run(a_run())

        assert loads.constructed == ["CSafeLoader"] * (2 * existing + 1)


# --------------------------------------------- storage guarantees still hold


class TestTheStoreGuaranteesHoldForTheNewRefusals:
    """A document only libyaml refuses behaves like any other invalid document."""

    def corrupt(self, root: Path, record: SimulationRun) -> None:
        path = root / f"{record.run_id}{DOCUMENT_SUFFIX}"
        path.write_text(
            stored_text(record) + f'extra_field: "{BACKSLASH}uD800"\n',
            encoding="utf-8",
        )

    def test_the_inventory_fails_whole(self, tmp_path: Path) -> None:
        store, records = a_store_of(tmp_path, 3)
        self.corrupt(tmp_path, records[1])

        with pytest.raises(RunConfigurationInvalid):
            store.list_runs()

    def test_an_unrelated_canonical_read_still_answers(self, tmp_path: Path) -> None:
        store, records = a_store_of(tmp_path, 3)
        self.corrupt(tmp_path, records[1])

        assert store.get_run(records[0].run_id) == records[0]
        with pytest.raises(RunConfigurationInvalid):
            store.get_run(records[1].run_id)

    def test_an_unknown_identity_is_still_not_found(self, tmp_path: Path) -> None:
        store, _ = a_store_of(tmp_path, 2)

        with pytest.raises(RunNotFound):
            store.get_run("run-" + "0" * 32)

    def test_a_create_into_a_store_it_cannot_read_writes_nothing(
        self, tmp_path: Path
    ) -> None:
        store, records = a_store_of(tmp_path, 2)
        self.corrupt(tmp_path, records[0])
        before = sorted(path.name for path in tmp_path.iterdir())

        with pytest.raises(RunConfigurationInvalid):
            store.create_run(a_run())

        assert sorted(path.name for path in tmp_path.iterdir()) == before

    def test_a_staged_document_libyaml_refuses_is_never_published(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The staged readback runs through the same reader, so it refuses too.

        The emitter is made to append a line only libyaml refuses. The create
        must refuse, and the store must hold exactly what it held before: no
        published record and no staging file.
        """
        store, _ = a_store_of(tmp_path, 1)
        before = sorted(path.name for path in tmp_path.iterdir())
        real = yaml_run_documents.serialize_run_document

        def poisoned(document: dict[str, object]) -> bytes:
            return real(document) + f'extra_field: "{BACKSLASH}uD800"\n'.encode()

        monkeypatch.setattr(yaml_run_store, "serialize_run_document", poisoned)

        with pytest.raises(RunConfigurationInvalid):
            store.create_run(a_run())

        assert sorted(path.name for path in tmp_path.iterdir()) == before

    def test_a_duplicate_identity_is_still_refused(self, tmp_path: Path) -> None:
        store, records = a_store_of(tmp_path, 1)

        with pytest.raises(RunIdentityConflict):
            store.create_run(records[0])
