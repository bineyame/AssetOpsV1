"""Publish an imported Site's first signal binding set from an explicit fixture (S1-02).

    python -m assetops_backend.sites.convert_kobo_bindings \
        --fixture backend/conversions/kobo-001-bindings.json --tenant demo

Run from the repository root with `DATABASE_URL` set and the database
migrated. The fixture states every role, unit and conversion; the legacy
`signal_mappings` in the imported Foundation are compared, never edited. The
first run publishes one atomic Foundation-plus-binding change; a rerun prints
the comparison and writes nothing. A fixture that does not match the imported
Site exits with status 2 and writes nothing.

The comparison is printed (Markdown) for the review packet; this command
writes no file.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.sites.binding_conversion import ConversionConflict, ConversionResult, convert
from assetops_backend.sites.binding_service import BindingService
from assetops_backend.sites.composition import build_foundation_store, read_binding_conversion_fixture
from assetops_backend.sites.foundation_content import utc_text
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.foundation_service import FoundationService, utc_now
from assetops_backend.sites.ports import SiteRepositoryError


def report(result: ConversionResult, fixture_path: str, fixture_sha: str, site_code: str) -> str:
    lines = [
        f"# {site_code} signal binding conversion",
        "",
        f"Fixture: `{fixture_path}` (sha256 `{fixture_sha}`). Effective from {utc_text(result.effective_from)}.",
        "Published now." if result.created else "Already converted: nothing was written.",
        "",
        "| Legacy mapping | Channel | Legacy component | Asset | Role | Units | Conversion |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            f"| {row.legacy_mapping_id or '(declared jointly)'} | {row.device_id} / {row.signal_id} | "
            f"{row.legacy_component or '-'} | {row.asset_code} | {row.role} | {row.units} | {row.conversion_kind} |"
        )
    if result.published is not None:
        changed = result.published.changed
        plan = result.published.plan
        lines += [
            "",
            f"Binding set {changed.binding_set_id} v{changed.version} "
            f"(revision {changed.id}, bindings sha256 `{changed.bindings_sha256}`).",
            f"Foundation revisions inserted: {', '.join(f'v{r.version}' for r in plan.revision_inserts) or 'none'}; "
            f"superseded: {len(plan.supersede_revision_ids)}.",
        ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    try:
        fixture, fixture_path, fixture_sha = read_binding_conversion_fixture(args.fixture)
        store = build_foundation_store(database_url())
        foundation = FoundationService(store, DEVELOPMENT_TENANT_SLUG, utc_now)
        tenant = foundation.tenant()
        site = foundation.site(tenant, str(fixture.get("site_code", "")))
        if site is None:
            print(f"Site {fixture.get('site_code')!r} is not imported in tenant {args.tenant!r}.", file=sys.stderr)
            return 2
        result = convert(store, BindingService(store, utc_now), tenant, site, fixture)
    except ConversionConflict as error:
        print(f"Conversion refused; nothing was written. {error}", file=sys.stderr)
        return 2
    except (FoundationStoreError, SiteRepositoryError) as error:
        print(f"Conversion failed: {error}", file=sys.stderr)
        return 1
    sys.stdout.write(report(result, fixture_path, fixture_sha, site.site_code))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
