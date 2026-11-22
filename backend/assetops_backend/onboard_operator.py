"""ON1 (spec §5; D-ON1.1, D-ON1.4, D-ON1.6, D-ON1.10, D-ON1.15): onboard an operator's tenant from one file.

    python -m assetops_backend.onboard_operator digest --file FILE
    python -m assetops_backend.onboard_operator check --file FILE [--key-dir DIR]
    python -m assetops_backend.onboard_operator apply --file FILE [--key-dir DIR] --confirmed-digest HEX  [--bindings DIR]

`digest` reads and parses the file only and prints its roles digest. `check` prints what would be created and writes
nothing; `apply` creates it and prints the plan as executed. `--key-dir` defaults to `ASSETOPS_PSEUDONYM_KEY_DIR`.
Before any connection: `DATABASE_URL`, the real-data settings (`commercial_upload_settings`, RC4 through RC4-F1) and
the served tenant (`ASSETOPS_TENANT_SLUG`). A refusal prints `<CODE> <where> <sentence>` on standard error and exits 2
(`check`, or `apply` before its first write) or 3 (`apply` after a write). No email, name or password is printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from assetops_backend.accounts.model import AccountRefused
from assetops_backend.config import ConfigurationError, database_url, served_tenant_slug
from assetops_backend.onboarding.operator_file import OnboardRefused, parse_operator_file, roles_digest
from assetops_backend.onboarding.service import OperatorOnboarding

KEY_DIR_ENV = "ASSETOPS_PSEUDONYM_KEY_DIR"

#: Spec §5: one plain sentence per refusal code.
SENTENCES = {
    "ONBOARD_FILE": "The onboarding file cannot be read as JSON.",
    "ONBOARD_FORMAT": "This is not an onboarding file of version 1.",
    "ONBOARD_STRUCTURE": "This part of the file has a missing or unknown field, a field of the wrong kind, or too many or too few entries.",
    "ONBOARD_DATA": '"data" must be "emulated" or "real".',
    "ONBOARD_SLUG": 'The operator code must be lower-case letters, digits and hyphens, and not "demo".',
    "ONBOARD_NAME": "A name must be 1 to 120 characters with no surrounding spaces.",
    "ONBOARD_VERTICAL": "This operator's business type is not onboarded yet.",
    "ONBOARD_SITE_CODE": "A Site code must be upper-case letters, digits and hyphens, and unique.",
    "ONBOARD_SITE_INVALID": "This Site cannot be created as written.",
    "ONBOARD_EMAIL": "This email cannot be used.",
    "ONBOARD_EMAIL_DUPLICATE": "This email appears twice.",
    "ONBOARD_ROLE": "This role is not known.",
    "ONBOARD_ROLE_SITE": "Only a Site manager names a Site, and it must be one of the file's Sites.",
    "ONBOARD_ROLE_DUPLICATE": "This role appears twice for this person.",
    "ONBOARD_EXECUTIVE_COUNT": "Exactly one person must be the operator executive.",
    "ONBOARD_ROLES_MISSING": "At least one finance lead and one analyst are needed to receive exports.",
    "ONBOARD_DATA_MISMATCH": ("Real data is onboarded only into an operator database with real data switched on, and "
                              "emulated data never."),
    "ONBOARD_TENANT_NOT_SERVED": "Set ASSETOPS_TENANT_SLUG to this operator before onboarding it.",
    "ONBOARD_DATABASE_NOT_EMPTY": "An operator database holds one operator only.",
    "ONBOARD_TENANT_DIFFERS": "This operator already exists with another name.",
    "ONBOARD_KEY_ERASED": "This operator's identities were erased; onboard it again as a new operator.",
    "ONBOARD_SITE_CHANGED": "This Site already exists with other details; it is not changed here.",
    "ONBOARD_EMAIL_TAKEN": "This email belongs to another organisation.",
    "ONBOARD_PERSON_DIFFERS": "This person already exists with another name, or is disabled.",
    "ONBOARD_EXECUTIVE_DIFFERS": "This person is in the file as the executive but does not hold that role.",
    "ONBOARD_REAL_AWAITS_APPROVAL": ("A real operator is onboarded once its executive can approve the roles; that step "
                                     "is not built yet."),
    "ONBOARDING_CLOSED": "The executive now grants roles; ask them to grant this one.",
    "ONBOARD_KEY_DIR_REQUIRED": "Name the key directory (--key-dir or ASSETOPS_PSEUDONYM_KEY_DIR).",
    "ONBOARD_KEY_DIR": "The key directory must exist and be readable by its owner only.",
    "ONBOARD_ROLES_SEPARATE": "The person who submits exports cannot also be the finance lead or the executive.",
    "ONBOARD_DIGEST_DIFFERS": "This file is not the one the executive confirmed: its roles digest differs.",
    "DATABASE_URL_REQUIRED": "Set DATABASE_URL to the database to onboard into.",
}


def _refuse(code: str, where: str | None = None, sentence: str | None = None, status: int = 2) -> int:
    parts = [code] + ([where] if where else []) + [SENTENCES.get(code, "") if sentence is None else sentence]
    sys.stderr.write(" ".join(p for p in parts if p) + "\n")
    return status


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.onboard_operator")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("digest").add_argument("--file", required=True)
    for name in ("check", "apply"):
        command = commands.add_parser(name)
        command.add_argument("--file", required=True)
        command.add_argument("--key-dir")
        if name == "apply":
            command.add_argument("--confirmed-digest", required=True)
            command.add_argument("--bindings", metavar="DIR")
    return parser


def _read(path: str):
    try:
        data = Path(path).read_bytes()
    except OSError:
        raise OnboardRefused("ONBOARD_FILE") from None
    return parse_operator_file(data)


def _settings(key_dir: str | None) -> tuple[str, bool, str] | int:
    """Spec §5, before any connection: the key directory, `DATABASE_URL`, the real-data settings, the served tenant."""
    from assetops_backend.commercial.composition import commercial_upload_settings

    if not key_dir:
        return _refuse("ONBOARD_KEY_DIR_REQUIRED")
    url = database_url()
    if url is None:
        return _refuse("DATABASE_URL_REQUIRED")
    try:
        real_data = commercial_upload_settings(url).real_data
        served = served_tenant_slug()
    except ConfigurationError as error:
        return _refuse("CONFIGURATION", sentence=str(error))
    return url, real_data, served


def _compose(url: str, key_dir: str, real_data: bool, served: str) -> OperatorOnboarding:
    from assetops_backend.accounts.composition import build_account_service
    from assetops_backend.commercial.composition import FileKeyFiles
    from assetops_backend.sites.composition import build_foundation_store

    return OperatorOnboarding(build_foundation_store(url), build_account_service(url), FileKeyFiles(key_dir),
                              clock=_now, real_data=real_data, served_slug=served)


def _publish_and_enable(store, f, fixtures: dict[str, Any]) -> int:
    """D-DD.36: per Site, publish its conversion (idempotent), then enable the gateway and each source still disabled."""
    from assetops_backend.evidence import provision_gateway
    from assetops_backend.sites.binding_conversion import ConversionConflict, convert
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.foundation_service import utc_now

    tenant = store.resolve_tenant(f.slug)
    for entry in f.sites:
        fixture = fixtures[entry.code]
        site = store.find_site(tenant.id, entry.code)
        try:
            convert(store, BindingService(store, utc_now), tenant, site, fixture)
        except ConversionConflict as error:
            sys.stderr.write(f"BINDING_CONVERSION bindings/{entry.code} {error}\n")
            return 3
        reg = store.registrations(tenant.id, site.id)
        base = ["--tenant", f.slug, "--site", entry.code, "--actor", "onboarding"]
        for gateway in reg.gateways:
            if gateway.disabled_at is not None:
                code = provision_gateway.main(["enable-gateway", *base, "--gateway", gateway.gateway_external_id])
                if code:
                    return code
        gateway_ids = {g.id: g.gateway_external_id for g in reg.gateways}
        for source in reg.sources:
            if source.disabled_at is not None:
                code = provision_gateway.main(["enable-source", *base, "--gateway", gateway_ids[source.gateway_id],
                                               "--source", source.source_external_id])
                if code:
                    return code
    return 0


def main(argv: Sequence[str] | None = None, *, onboarding: OperatorOnboarding | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = None
    if args.command != "digest" and onboarding is None:
        key_dir = args.key_dir or os.environ.get(KEY_DIR_ENV)
        settings = _settings(key_dir)
        if isinstance(settings, int):
            return settings
    try:
        f = _read(args.file)
    except OnboardRefused as refused:
        return _refuse(refused.code, refused.where)
    if args.command == "digest":
        sys.stdout.write(roles_digest(f) + "\n")
        return 0
    if onboarding is None:
        onboarding = _compose(settings[0], key_dir, settings[1], settings[2])
    from assetops_backend.commercial.composition import KeyDirectoryMissing, KeyErased, KeyExists

    bindings = getattr(args, "bindings", None)
    bindings_fixtures: dict[str, Any] = {}
    if bindings:  # D-DD.36: every Site names its conversion before any write
        for site in f.sites:  # D-DD.47: read and parse every input before the first write
            try:
                bindings_fixtures[site.code] = json.loads(
                    (Path(bindings) / f"{site.code}-bindings.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return _refuse("ONBOARD_SITE_INVALID", f"bindings/{site.code}")
    try:
        if args.command == "check":
            plan = onboarding.check(f)
        else:
            plan = onboarding.apply(f, confirmed_digest=args.confirmed_digest)
            if bindings:
                code = _publish_and_enable(onboarding.foundation, f, bindings_fixtures)
                if code:
                    return code
    except OnboardRefused as refused:
        after = args.command == "apply" and onboarding.wrote
        return _refuse(refused.code, refused.where, status=3 if after else 2)
    except AccountRefused as refused:
        return _refuse(refused.code, sentence="", status=3)
    except (KeyDirectoryMissing, KeyErased, KeyExists) as error:
        return _refuse({KeyDirectoryMissing: "KEY_DIRECTORY_MISSING", KeyErased: "KEY_ERASED",
                        KeyExists: "KEY_EXISTS"}[type(error)], sentence="", status=3)
    sys.stdout.write(json.dumps(plan.as_json(), sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
