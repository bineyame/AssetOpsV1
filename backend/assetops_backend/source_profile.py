"""3A6 (spec `specs/3A6-source-profiles/spec.md` §2.7; D-3A6.2, D-3A6.10, D-3A6.17): check, admit and list a tenant's
source profiles.

    python -m assetops_backend.source_profile check --tenant SLUG --profile P --sample S --expected E
    python -m assetops_backend.source_profile admit --tenant SLUG --profile P --sample S --expected E --as EMAIL
    python -m assetops_backend.source_profile list  --tenant SLUG

`check` runs admission steps 1 to 6 and writes nothing; `admit` runs them and writes the admitted version, named for
the person (`commercial.profile_admit`: the analyst or the finance lead). Onboarding a new export layout is a profile
file and this command: no code change.

Operator databases are not refused here: a pinned profile is admitted where its real data lives (RC4); the settings
switch (`commercial_upload_settings`) already refuses a real-data run on a non-operator database and the reverse.
Nothing of the sample is printed or kept but its SHA-256 and row count.

One JSON line per answer on stdout. Exit 0 done; 2 refused before admission (`<CODE> <sentence>` on stderr); 3 the
profile, sample or expected file refused (`{"state": "REFUSED", "code", "params", "text"}` on stdout).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

from assetops_backend.accounts.composition import build_account_service
from assetops_backend.accounts.permissions import roles_of
from assetops_backend.commercial.composition import build_source_profiles, commercial_upload_settings
from assetops_backend.commercial.profiles import AdmissionReport, ProfileRefused
from assetops_backend.commercial.uploads import Actor
from assetops_backend.config import ConfigurationError
from assetops_backend.i18n import render

COMMAND = "commercial.profile_admit"
_SENTENCES = {
    "DATABASE_URL_REQUIRED": "Set DATABASE_URL to the database to admit into.",
    "FILE_UNREADABLE": "That file cannot be read.",
    "TENANT_NOT_FOUND": "No organisation has that slug.",
    "PERSON_NOT_FOUND": "No active person of this organisation has that email.",
    "PERSON_ROLE_REQUIRED": "That person's role cannot do this.",
}


class _Stop(Exception):
    def __init__(self, code: str, detail: str | None = None, sentence: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.sentence = sentence if sentence is not None else _SENTENCES.get(code, "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.source_profile",
                                     description="Check, admit or list a tenant's source profiles.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "admit", "list"):
        sub = commands.add_parser(name)
        sub.add_argument("--tenant", required=True, help="the tenant's slug")
        if name != "list":
            sub.add_argument("--profile", required=True, help="the profile file (JSON)")
            sub.add_argument("--sample", required=True, help="the operator's sample export")
            sub.add_argument("--expected", required=True, help="the hand-written expected records (JSON)")
        if name == "admit":
            sub.add_argument("--as", dest="as_email", required=True, help="email of the person who admits")
    return parser


def _write_line(line: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(line, sort_keys=False) + "\n")


def _read(arg: str) -> bytes:
    path = Path(arg)
    if path.is_symlink() or not path.is_file():
        raise _Stop("FILE_UNREADABLE", arg)
    try:
        return path.read_bytes()
    except OSError:
        raise _Stop("FILE_UNREADABLE", arg) from None


def _person(accounts: Any, email: str, slug: str):
    """3A3 §2.6 step 5: the person and the first role of the command they hold."""
    person = accounts.onboard_person(email)
    if person is None or person.tenant_slug != slug or not person.active:
        raise _Stop("PERSON_NOT_FOUND")
    held = {role for role, _ in person.roles}
    role = next((r for r in roles_of(COMMAND) if r in held), None)
    if role is None:
        raise _Stop("PERSON_ROLE_REQUIRED")
    return person, role


def _report(state: str, r: AdmissionReport | Any) -> dict[str, Any]:
    return {"state": state, "reader": r.reader, "version": r.version, "sample_rows": r.sample_rows,
            "profile_sha256": r.profile_sha256, "sample_sha256": r.sample_sha256,
            "expected_sha256": r.expected_sha256}


def _run(args: argparse.Namespace, profiles: Any, accounts: Any) -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise _Stop("DATABASE_URL_REQUIRED")
    try:
        commercial_upload_settings(url)  # before any connection; the real-data switch follows the database
    except ConfigurationError as error:
        raise _Stop("CONFIGURATION", None, str(error)) from None
    files = None if args.command == "list" else (_read(args.profile), _read(args.sample), _read(args.expected))
    dispose = None
    if profiles is None:
        profiles, dispose = build_source_profiles(url)
    if accounts is None:
        accounts = build_account_service(url)
    try:
        tenant_id = accounts.tenant_by_slug(args.tenant)
        if tenant_id is None:
            raise _Stop("TENANT_NOT_FOUND")
        if args.command == "list":
            for row in profiles.latest(tenant_id):
                _write_line({"profile_id": row.profile_id, "reader": row.reader, "status": row.status,
                             "source_type": row.source_type, "source_system": row.source_system,
                             "admitted_at": row.admitted_at.isoformat(), "admitted_by": str(row.admitted_by)})
            return 0
        actor = None
        if args.command == "admit":
            person, role = _person(accounts, args.as_email, args.tenant)
            actor = Actor(person.person_id, role)
        try:
            if actor is None:
                report = profiles.check(tenant_id, *files)
                _write_line(_report("ALREADY_ADMITTED" if report.already is not None else "ADMISSIBLE", report))
            else:
                before = profiles.check(tenant_id, *files)
                row = profiles.admit(tenant_id, actor, *files)
                state = "ALREADY_ADMITTED" if before.already is not None else "ADMITTED"
                _write_line(_report(state, row))
        except ProfileRefused as refused:
            _write_line({"state": "REFUSED", "code": refused.code, "params": refused.params,
                         "text": render(refused.words)})
            return 3
        return 0
    finally:
        if dispose is not None:
            dispose()


def main(argv: Sequence[str] | None = None, *, profiles: Any = None, accounts: Any = None) -> int:
    """Injected services (tests) skip the composition; the URL, settings and file checks always run."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return _run(args, profiles, accounts)
    except _Stop as stop:
        detail = f" {stop.detail}" if stop.detail else ""
        sys.stderr.write(f"{stop.code}{detail} {stop.sentence}".rstrip() + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
