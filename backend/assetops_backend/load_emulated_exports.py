"""3A3 (spec `specs/3A3-emulators-contract-test/spec.md` §2.6; D-3A3.1, D-3A3.6, D-3A3.7, D-3A3.11): load emulated
exports through 3A2's intake.

    python -m assetops_backend.load_emulated_exports --dir DIR --tenant SLUG --submit-as EMAIL [--accept-as EMAIL]

`DIR` holds one tenant's files: native CSVs `<SLUG>.<key>.csv` (`key` in `KEYS`, read by the illustrative layout
readers) or DS1b canonical batches `<SLUG>.<source_type>.json` (read by `canonical-json-v1`), plus an optional
`unwritten.json`. Each file is submitted on the organisation path by the named person and, with `--accept-as`,
accepted by another named person; nothing is written any other way (D-3A3.1). A rerun is idempotent.

Before anything else the database is checked by name (RC4, D-3A3.6): a URL that does not name one database plainly
(RC4-F1) or that names an operator's database (`assetops_op*`, any case) is refused before any connection. Emulated
exports are never loaded into an operator's database.

3A6 (spec §2.8; D-3A6.10): the directory may also hold `<SLUG>.profile.<profile_id>.csv` or `.xlsx`, read by the
tenant's latest admitted version of that source profile (`PROFILE_NOT_ADMITTED` when there is none). Two files of one
source type are `EXPORT_PATHS_MIXED`; a file whose source type the tenant already holds from another source system
is `EXPORT_PATH_SWITCHED` (the intake's per-Site rule is the authority).

One JSON line per file on stdout: `{"file", "upload_id", "state", "counts"}`. Exit 0 done; 2 refused before any
submission; 3 a submission or decision refused (files before it stay as they are). Refusals print `<CODE> <one
sentence>` on stderr.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Sequence

from assetops_backend.accounts.composition import build_account_service
from assetops_backend.accounts.permissions import roles_of
from assetops_backend.commercial.composition import (OperatorDatabaseRefused, build_commercial_uploads,
                                                     build_source_profiles, commercial_upload_settings,
                                                     refuse_operator_database)
from assetops_backend.commercial.readers import DEFAULT_READER, MEDIA_TYPES, READERS
from assetops_backend.commercial.uploads import Actor, UploadRefused, UploadScope
from assetops_backend.config import ConfigurationError
from assetops_backend.database_target import DatabaseTargetUnclear
from assetops_backend.i18n import render
from assetops_contracts.canonical import SOURCE_TYPES

#: The emulated native files, in submission order; each is read by the layout `<key>-illustrative-1`.
KEYS = ("billing", "collections", "expenses", "budget")
UNWRITTEN = "unwritten.json"
ORGANISATION = UploadScope(None, None)
#: 3A6: `<SLUG>.profile.<profile_id>.<format>`.
_PROFILE_FILE = re.compile(r"profile\.([a-z][a-z0-9-]{0,47})\.(csv|xlsx)", re.ASCII)
_SENTENCES = {
    "DATABASE_URL_REQUIRED": "Set DATABASE_URL to the database to load into.",
    "DATABASE_URL_UNCLEAR": "The database URL must name one database plainly.",
    "EMULATED_ON_OPERATOR_DATABASE": "Emulated exports are never loaded into an operator's database.",
    "COMMERCIAL_UPLOAD_OFF": "Set ASSETOPS_PSEUDONYM_KEY_DIR: commercial uploads are off on this database.",
    "EXPORT_FILE_UNKNOWN": "The directory holds a file this loader does not read.",
    "EXPORT_PATHS_MIXED": "The directory holds two files for one source type.",
    "PROFILE_NOT_ADMITTED": "No admitted source profile of this organisation reads that file.",
    "PERSON_NOT_FOUND": "No active person of this organisation has that email.",
    "PERSON_ROLE_REQUIRED": "That person's role cannot do this.",
    "PERSON_SAME_FOR_BOTH": "The person who accepts must not be the person who submits.",
    "EXPORT_PATH_SWITCHED": "This organisation already holds this source type from another source system.",
}


class _Stop(Exception):
    def __init__(self, exit_code: int, code: str, detail: str | None = None, sentence: str | None = None) -> None:
        super().__init__(code)
        self.exit_code = exit_code
        self.code = code
        self.detail = detail
        self.sentence = sentence if sentence is not None else _SENTENCES.get(code, "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.load_emulated_exports",
                                     description="Load one tenant's emulated exports through the upload intake.")
    parser.add_argument("--dir", required=True, type=Path, help="one tenant's export directory")
    parser.add_argument("--tenant", required=True, help="the tenant's slug")
    parser.add_argument("--submit-as", required=True, help="email of the person who submits (analyst or finance)")
    parser.add_argument("--accept-as", default=None, help="email of another person who accepts (finance or executive)")
    return parser


def _files(directory: Path, slug: str) -> list[tuple[str, Path, str | None, str | None]]:
    """Step 4: (name, path, reader id, source type) in submission order: CSVs in `KEYS` order, then profile files by
    name, then JSONs by name. A profile file's reader and source type are None until step 5c resolves them; the
    mixed check here covers the other files."""
    if not directory.is_dir():
        raise _Stop(2, "EXPORT_FILE_UNKNOWN", str(directory))
    csvs: dict[str, tuple[str, Path, str, str]] = {}
    jsons: list[tuple[str, Path, str, str]] = []
    profiled: list[tuple[str, Path, None, None]] = []
    native = {f"{slug}.{key}.csv": key for key in KEYS}
    canonical = {f"{slug}.{source_type}.json": source_type for source_type in SOURCE_TYPES}
    for path in sorted(directory.iterdir(), key=lambda p: p.name):
        name = path.name
        if path.is_symlink() or not path.is_file():
            raise _Stop(2, "EXPORT_FILE_UNKNOWN", name)
        if name == UNWRITTEN:
            continue
        if name in native:
            key = native[name]
            reader_id = f"{key}-illustrative-1"
            csvs[key] = (name, path, reader_id, READERS[reader_id].layout.source_type)
        elif name in canonical:
            jsons.append((name, path, DEFAULT_READER, canonical[name]))
        elif name.startswith(f"{slug}.") and _PROFILE_FILE.fullmatch(name[len(slug) + 1:]):
            profiled.append((name, path, None, None))
        else:
            raise _Stop(2, "EXPORT_FILE_UNKNOWN", name)
    ordered = [csvs[key] for key in KEYS if key in csvs] + profiled + jsons
    _mixed(f for f in ordered if f[3] is not None)
    return ordered


def _mixed(files) -> None:
    """Two files of one source type, whatever their readers, are `EXPORT_PATHS_MIXED`."""
    seen: set[str] = set()
    for _, _, _, source_type in files:
        if source_type in seen:
            raise _Stop(2, "EXPORT_PATHS_MIXED", source_type)
        seen.add(source_type)


def _resolve_profiles(files, profiles: Any, tenant_id) -> tuple[list[tuple[str, Path, str, str]], dict[str, Any]]:
    """Step 5c: each profile file read by the tenant's latest admitted version (`PROFILE_NOT_ADMITTED` else); the
    admitted rows by reader id."""
    latest = {} if profiles is None else {row.profile_id: row for row in profiles.latest(tenant_id)}
    out, rows = [], {}
    for name, path, reader_id, source_type in files:
        if reader_id is None:
            row = latest.get(_PROFILE_FILE.fullmatch(name.split(".", 1)[1])[1])
            if row is None:
                raise _Stop(2, "PROFILE_NOT_ADMITTED", name)
            reader_id, source_type = row.reader, row.source_type
            rows[reader_id] = row
        out.append((name, path, reader_id, source_type))
    return out, rows


def _source_system(path: Path, reader_id: str, rows: dict[str, Any]) -> str | None:
    """Step 5b: the file's source system (None for a JSON batch that does not read; the submission refuses it)."""
    if reader_id in rows:
        return rows[reader_id].source_system
    if reader_id != DEFAULT_READER:
        return READERS[reader_id].layout.source_system
    try:
        batch = json.loads(path.read_bytes())
    except ValueError:
        return None
    system = batch.get("source_system") if isinstance(batch, dict) else None
    return system if isinstance(system, str) else None


def _person(accounts: Any, email: str, slug: str, command: str):
    """Step 5: the person and the first role of `command` they hold."""
    person = accounts.onboard_person(email)
    if person is None or person.tenant_slug != slug or not person.active:
        raise _Stop(2, "PERSON_NOT_FOUND")
    held = {role for role, _ in person.roles}
    role = next((r for r in roles_of(command) if r in held), None)
    if role is None:
        raise _Stop(2, "PERSON_ROLE_REQUIRED")
    return person, role


def _counts(answer: dict[str, Any]) -> dict[str, Any] | None:
    counts = answer.get("preview")
    return None if counts is None else {k: v for k, v in counts.items() if k not in ("words", "text")}


def _write_line(line: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(line, sort_keys=False) + "\n")


def _run(args: argparse.Namespace, uploads: Any, accounts: Any, profiles: Any = None) -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise _Stop(2, "DATABASE_URL_REQUIRED")
    try:
        refuse_operator_database(url)  # step 2: before any connection
    except DatabaseTargetUnclear as unclear:
        raise _Stop(2, "DATABASE_URL_UNCLEAR", unclear.reason) from None
    except OperatorDatabaseRefused:
        raise _Stop(2, "EMULATED_ON_OPERATOR_DATABASE") from None
    if uploads is None or accounts is None:
        try:
            settings = commercial_upload_settings(url)
        except ConfigurationError as error:
            raise _Stop(2, "CONFIGURATION", None, str(error)) from None
        if settings.key_dir is None:
            raise _Stop(2, "COMMERCIAL_UPLOAD_OFF")
        uploads = uploads if uploads is not None else build_commercial_uploads(url, settings)
        accounts = accounts if accounts is not None else build_account_service(url)
        if profiles is None:
            profiles = build_source_profiles(url)[0]
    files = _files(args.dir, args.tenant)
    submitter, submit_role = _person(accounts, args.submit_as, args.tenant, "commercial.upload")
    acceptor = None
    if args.accept_as is not None:
        acceptor, accept_role = _person(accounts, args.accept_as, args.tenant, "commercial.upload_decision")
        if acceptor.person_id == submitter.person_id:
            raise _Stop(2, "PERSON_SAME_FOR_BOTH")
    tenant_id = submitter.tenant_id
    files, profile_rows = _resolve_profiles(files, profiles, tenant_id)  # step 5c
    _mixed(files)  # handshake P7: over every file, its source type now known
    held = uploads.held(tenant_id)  # step 5b: one read
    for _, path, reader_id, source_type in files:
        system = _source_system(path, reader_id, profile_rows)
        if system is not None and any(h.source_type == source_type and h.source_system != system for h in held):
            raise _Stop(2, "EXPORT_PATH_SWITCHED", source_type)
    waiting = {h.file_sha256: h for h in held if h.waiting}
    if acceptor is not None:  # D-3A3.14: across runs, the submitter is never the acceptor
        digests = {hashlib.sha256(path.read_bytes()).hexdigest() for _, path, _, _ in files}
        if any(h.submitted_by == acceptor.person_id for sha, h in waiting.items() if sha in digests):
            raise _Stop(2, "PERSON_SAME_FOR_BOTH")
    actor = Actor(submitter.person_id, submit_role)
    for name, path, reader_id, _ in files:
        data = path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        try:
            if sha256 in waiting:
                upload_id = str(waiting[sha256].upload_id)
                answer = uploads.get(tenant_id, ORGANISATION, upload_id)
                state = "ALREADY_WAITING"
            else:
                if reader_id in profile_rows:  # the profile's format names its media type
                    media_type = sorted(MEDIA_TYPES[profile_rows[reader_id].file_format])[0]
                else:
                    media_type = "application/json" if reader_id == DEFAULT_READER else "text/csv"
                try:
                    answer = uploads.submit(tenant_id, ORGANISATION, actor, data, file_name=name, reader_id=reader_id,
                                            media_type=media_type)
                except UploadRefused as refused:
                    if refused.code != "UPLOAD_NOTHING_NEW":
                        raise
                    _write_line({"file": name, "upload_id": None, "state": "NOTHING_NEW", "counts": None})
                    continue
                upload_id, state = answer["upload_id"], answer["state"]
            line = {"file": name, "upload_id": upload_id, "state": state, "counts": _counts(answer)}
            if acceptor is not None:
                decided = uploads.decide(tenant_id, ORGANISATION, Actor(acceptor.person_id, accept_role), upload_id,
                                         "ACCEPT")
                line["state"] = decided["state"]
                line["decided_by_script"] = True
        except UploadRefused as refused:
            raise _Stop(3, refused.code, None, render(refused.words)) from None
        _write_line(line)
    return 0


def main(argv: Sequence[str] | None = None, *, uploads: Any = None, accounts: Any = None,
         profiles: Any = None) -> int:
    """Injected services (tests) skip step 3 and the composition; steps 1, 2 and 4 always run."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, uploads, accounts, profiles)
    except _Stop as stop:
        detail = f" {stop.detail}" if stop.detail else ""
        sys.stderr.write(f"{stop.code}{detail} {stop.sentence}".rstrip() + "\n")
        return stop.exit_code


if __name__ == "__main__":
    sys.exit(main())
