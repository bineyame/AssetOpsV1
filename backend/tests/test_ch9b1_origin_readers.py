"""CH-9b1 (CH9b1-R Q5): the reader audit for the Action origin columns.

Every backend file that names `origin_finding_id`, `origin_finding_revision_id`, `origin_opportunity_id` or
`origin_opportunity_revision_id` is in the committed allowlist with its class and its maximum token count. A new file
or a higher count fails, so a new reader is classified before it lands.

- `action`: a W1 `action` reader, pinned Finding-only; it must not name the opportunity origin.
- `both`: a `domain_action` / chain reader; it must name the opportunity origin (it handles both).
- `finding_fed`: fed only by a Finding-origin read (the MINI rows are excluded upstream); it carries the marker.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "assetops_backend"
TOKEN = re.compile(r"\borigin_(?:finding|opportunity)(?:_revision)?_id\b")
MARKER = "CH-9b1 origin: Finding-only"

ALLOWLIST: dict[str, tuple[str, int]] = {
    "actions/adapters/postgres_action_store.py": ("action", 12),
    "actions/service.py": ("action", 14),
    "actions/site_index.py": ("action", 2),
    "actions/verification.py": ("action", 5),
    "estate/adapters/postgres_estate_read.py": ("action", 3),
    "estate/coverage.py": ("action", 4),
    "estate/portfolio.py": ("action", 2),
    "financials/trial_fuel_comparison.py": ("action", 3),
    "site_outcomes/board.py": ("action", 7),
    "chain/adapters/postgres_chain_read.py": ("both", 4),
    "chain/adapters/postgres_thread_sources.py": ("both", 8),
    "chain/adapters/postgres_thread_store.py": ("both", 4),
    "chain/backfill.py": ("both", 5),
    "chain/lookup.py": ("both", 4),
    "chain/site_chain.py": ("both", 3),
    "chain/threads.py": ("both", 8),
    "work/adapters/postgres_domain_action_index.py": ("both", 7),
    "work/adapters/postgres_domain_intent.py": ("both", 17),
    "work/adapters/postgres_work_read.py": ("both", 39),
    "work/domain_action.py": ("both", 8),
    "work/domain_intent.py": ("both", 10),
    "work/domain_action_index.py": ("finding_fed", 12),
    "work/site_index.py": ("finding_fed", 14),
    "work/adapters/postgres_work_store.py": ("finding_fed", 1),
    "site_outcomes/cold.py": ("finding_fed", 1),
    "site_outcomes/ev.py": ("finding_fed", 3),
}


def scan(root: Path = ROOT) -> dict[str, tuple[int, str]]:
    """`{relative path: (token count, text)}` for every file naming an origin column."""
    out = {}
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        count = len(TOKEN.findall(text))
        if count:
            out[path.relative_to(root).as_posix()] = (count, text)
    return out


def violations(found: dict[str, tuple[int, str]]) -> list[str]:
    out = []
    for rel, (count, text) in found.items():
        entry = ALLOWLIST.get(rel)
        if entry is None:
            out.append(f"{rel}: unlisted origin reader ({count} references); classify it in ALLOWLIST")
            continue
        cls, limit = entry
        if count > limit:
            out.append(f"{rel}: {count} origin references, allowlist {limit}")
        if cls == "action" and "origin_opportunity" in text:
            out.append(f"{rel}: an `action` reader names the opportunity origin (it is Finding-only)")
        if cls == "both" and "origin_opportunity" not in text:
            out.append(f"{rel}: a domain_action reader does not handle the opportunity origin")
        if cls == "finding_fed" and MARKER not in text:
            out.append(f"{rel}: a Finding-fed reader lacks the `{MARKER}` marker")
    return out


def test_every_origin_reader_is_classified() -> None:
    assert violations(scan()) == []


def test_allowlist_has_no_stale_entries() -> None:
    assert sorted(set(ALLOWLIST) - set(scan())) == []


@pytest.mark.parametrize("case", ["new_file", "higher_count", "action_names_opportunity", "both_ignores", "marker"])
def test_guard_is_not_vacuous(case: str) -> None:
    found = dict(scan())
    if case == "new_file":
        found["work/new_reader.py"] = (1, "origin_finding_id")
    elif case == "higher_count":
        count, text = found["chain/lookup.py"]
        found["chain/lookup.py"] = (count + 1, text)
    elif case == "action_names_opportunity":
        count, text = found["actions/service.py"]
        found["actions/service.py"] = (count, text + "\norigin_opportunity_id")
    elif case == "both_ignores":
        count, text = found["chain/site_chain.py"]
        found["chain/site_chain.py"] = (count, text.replace("origin_opportunity", "origin_x"))
    else:
        count, text = found["site_outcomes/cold.py"]
        found["site_outcomes/cold.py"] = (count, text.replace(MARKER, ""))
    assert len(violations(found)) == 1
