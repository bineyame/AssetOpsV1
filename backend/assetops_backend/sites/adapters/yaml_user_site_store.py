"""Writable YAML adapter over the user-authored Site store.

This is the only module in the product with a write path to configuration, and
`tools/check-architecture.ps1` enforces that: a write-capable call anywhere
else in the backend fails the build. The shipped roots are read-only at
runtime, so nothing here may name one.

`USER_SITE_STORE_ROOT` is declared here and nowhere else. One owned location
for the writable root is what keeps "outside the shipped configuration roots"
checkable, and the guard fails if a second module declares it.

The write is create-if-absent and never upsert, and it is built so that a
failed create leaves the store byte-identical:

1.  The record is rendered to the document shape and serialized first, before
    anything is touched, so a serialization failure never reaches the store.
2.  The absence of the identity is checked under a lock, so two concurrent
    creates of the same `site_id` cannot both pass the check. The store is
    file-backed and single-host, so a process-level lock is the honest scope
    for this; it is not a distributed-store claim.
3.  The bytes go to a uniquely named temporary file created exclusively, then
    flushed and fsynced.
4.  That temporary file is read back and parsed. The record it yields must
    equal the record that was validated, so what lands in the store is
    provably what passed the parser rather than whatever the writer emitted.
5.  Only then is it moved into place atomically. Any failure at any step
    removes the temporary file, so no partial or stray document is left
    behind and no existing document is disturbed.

The stored file name is the case-folded `site_id`, but identity is never read
back out of a file name: documents are parsed and keyed on the `site_id` they
declare. That is what makes identity independent of whether the host
filesystem happens to be case-sensitive.
"""

from __future__ import annotations

import os
import threading
import uuid
from pathlib import Path

from assetops_backend.sites.adapters.yaml_site_documents import (
    DOCUMENT_SUFFIX,
    read_site_record,
    read_site_records,
    serialize_site_document,
)
from assetops_backend.sites.identity import site_id_key
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteIdentityConflict,
    SiteStoreUnavailable,
)
from assetops_backend.sites.site_parsing import render_site_document

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The writable store for user-authored Site configuration. It lives outside
#: every shipped configuration root and outside version control: `.gitignore`
#: covers it, and `tools/check-architecture.ps1` checks that it does.
USER_SITE_STORE_ROOT = REPO_ROOT / "var" / "sites"

STORE_NAME = "user"


class WritableYamlSiteStore:
    """The user-authored half of the Site identity space."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = USER_SITE_STORE_ROOT if root is None else root
        self._write_lock = threading.Lock()

    @property
    def store_name(self) -> str:
        return STORE_NAME

    def list_sites(self) -> tuple[SiteRecord, ...]:
        return read_site_records(self._root, store_name=STORE_NAME)

    def create_site(self, record: SiteRecord) -> SiteRecord:
        """Write a new Site document, or write nothing at all."""
        payload = serialize_site_document(render_site_document(record))

        with self._write_lock:
            self._ensure_root()

            self._refuse_existing_identity(record.site_id)

            destination = self._root / f"{site_id_key(record.site_id)}{DOCUMENT_SUFFIX}"
            staged = self._root / f".{uuid.uuid4().hex}.staging"
            moved = False

            try:
                self._write_exclusively(staged, payload)

                stored = read_site_record(staged, store_name=STORE_NAME)
                if stored != record:
                    raise SiteConfigurationInvalid(
                        f"The stored document for {record.site_id!r} did not "
                        "match the validated site, so nothing was written."
                    )

                # Re-checked immediately before the move: the absence check
                # above ran before any I/O, and this is the last moment at
                # which an existing document could still be overwritten.
                self._refuse_existing_identity(record.site_id)
                if destination.exists():
                    raise SiteIdentityConflict(
                        f"Site ID {record.site_id!r} is already in use."
                    )

                try:
                    os.replace(staged, destination)
                except OSError as error:
                    raise SiteStoreUnavailable(
                        f"The site {record.site_id!r} could not be written to "
                        "the site store."
                    ) from error
                moved = True
            finally:
                if not moved:
                    try:
                        staged.unlink(missing_ok=True)
                    except OSError:
                        # Removing the staging file is best effort. It carries
                        # no document suffix, so it is never read as a Site.
                        pass

        return record

    def _ensure_root(self) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise SiteStoreUnavailable(
                f"The user site store could not be opened: {self._root}"
            ) from error

    def _refuse_existing_identity(self, site_id: str) -> None:
        key = site_id_key(site_id)
        for existing in self.list_sites():
            if site_id_key(existing.site_id) == key:
                raise SiteIdentityConflict(
                    f"Site ID {site_id!r} is already in use by "
                    f"{existing.site_id!r}."
                )

    def _write_exclusively(self, path: Path, payload: bytes) -> None:
        try:
            descriptor = os.open(
                path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
            )
            try:
                os.write(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as error:
            raise SiteStoreUnavailable(
                f"The site store could not be written: {self._root}"
            ) from error
