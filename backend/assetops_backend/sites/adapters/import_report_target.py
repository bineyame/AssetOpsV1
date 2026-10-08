"""Where the import comparison report may be written (review m5).

Read-only by construction: this module resolves the Site store roots to
refuse a report target among them, and writes nothing. The report itself is
written by `import_files.write_import_report`.
"""

from __future__ import annotations

from pathlib import Path

from assetops_backend.sites.adapters.yaml_shipped_site_store import SHIPPED_SITE_ROOT
from assetops_backend.sites.adapters.yaml_user_site_store import USER_SITE_STORE_ROOT
from assetops_backend.sites.ports import SiteConfigurationInvalid

REPO_ROOT = Path(__file__).resolve().parents[4]


def _absolute(path_text: str) -> Path:
    path = Path(path_text)
    return (path if path.is_absolute() else Path.cwd() / path).resolve()


def _shown(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def check_report_path(report_text: str, source_text: str) -> None:
    """Refuse a report target that is the source or inside a Site store (review m5).

    The report is review evidence. It may never replace the document being
    imported, nor land among the Site documents the legacy stores read.
    """
    target = _absolute(report_text)
    if target == _absolute(source_text):
        raise SiteConfigurationInvalid(
            f"The report path {report_text} is the import source; the source stays read-only."
        )
    for root in (SHIPPED_SITE_ROOT, USER_SITE_STORE_ROOT):
        resolved = root.resolve()
        if target == resolved or resolved in target.parents:
            raise SiteConfigurationInvalid(
                f"The report path {report_text} is inside the Site store {_shown(resolved)}; "
                "write the report elsewhere (for example .agent/)."
            )


