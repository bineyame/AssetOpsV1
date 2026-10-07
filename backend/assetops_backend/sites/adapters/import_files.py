"""File access for the one-shot Site import (S1-01).

Reads a Site source document byte for byte (it is never modified), locates
the documents the legacy YAML Site stores hold so the import and the product
read router can detect a same-code collision, and writes the import
comparison report. The report is review evidence, not Site configuration;
this module never writes a Site document.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from assetops_backend.sites.foundation_service import ImportSource, LegacyDocument
from assetops_backend.sites.ports import SiteConfigurationInvalid, SiteStoreUnavailable
from assetops_backend.sites.site_parsing import parse_site_document

REPO_ROOT = Path(__file__).resolve().parents[4]
MAX_SOURCE_BYTES = 128 * 1024


def canonical_path(path: Path) -> str:
    """Repository-relative POSIX spelling when inside the repo, else absolute."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _read_bytes(path: Path) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise SiteStoreUnavailable(f"{path} could not be read") from error
    if len(payload) > MAX_SOURCE_BYTES:
        raise SiteConfigurationInvalid(f"{path} is above the {MAX_SOURCE_BYTES}-byte limit")
    return payload


def read_import_source(path_text: str) -> ImportSource:
    """Parse one Site document with the strict legacy parser, recording its digest."""
    path = Path(path_text)
    if not path.is_absolute():
        path = Path.cwd() / path
    payload = _read_bytes(path)
    try:
        document = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise SiteConfigurationInvalid(f"{path} is not a readable YAML Site document") from error
    record = parse_site_document(document, source=canonical_path(path))
    return ImportSource(
        path=canonical_path(path),
        sha256=hashlib.sha256(payload).hexdigest(),
        record=record,
    )


def legacy_documents(roots: tuple[Path, ...]) -> tuple[LegacyDocument, ...]:
    """Every legacy Site document's declared code, canonical path and digest.

    Only the `site_id` is read: full validation stays with the legacy stores,
    which already refuse an invalid document on their own read path.
    """
    found: list[LegacyDocument] = []
    for root in roots:
        try:
            if not root.is_dir():
                continue
            paths = sorted(p for p in root.iterdir() if p.suffix == ".yaml")
        except OSError as error:
            raise SiteStoreUnavailable(f"The site store {root} could not be read") from error
        for path in paths:
            payload = _read_bytes(path)
            try:
                document = yaml.safe_load(payload.decode("utf-8"))
            except (UnicodeDecodeError, yaml.YAMLError) as error:
                raise SiteConfigurationInvalid(f"{path.name} is not readable YAML") from error
            code = document.get("site_id") if isinstance(document, dict) else None
            if isinstance(code, str):
                found.append(
                    LegacyDocument(
                        site_code=code,
                        path=canonical_path(path),
                        sha256=hashlib.sha256(payload).hexdigest(),
                    )
                )
    return tuple(found)


def write_import_report(path_text: str, report: str) -> str:
    """Write the comparison report (review evidence only) and return its path."""
    path = Path(path_text)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return canonical_path(path)
