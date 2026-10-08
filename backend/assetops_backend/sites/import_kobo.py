"""One-shot import of a legacy Site document into the product Foundation store.

    python -m assetops_backend.sites.import_kobo --source var/sites/kobo-001.yaml \
        --tenant demo --report .agent/S1-01-import-comparison.md

Run from the repository root with `DATABASE_URL` set and the database
migrated (`alembic upgrade head`). The source document is read, never
written. Re-running against the same path and bytes returns the same UUIDs
and revision; a different same-code source, changed bytes or another tenant
is a conflict that needs explicit reconciliation (exit status 2).

The report compares the source document with what Postgres now holds, so a
reviewer can resolve every value to the original import.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.sites.composition import (
    build_foundation_store,
    check_site_import_report_path,
    legacy_site_documents,
    read_site_import_source,
    write_site_import_report,
)
from assetops_backend.sites.foundation_content import (
    battery_reserve,
    configuration_gaps,
    content_from_record,
    record_at,
    utc_text,
)
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.foundation_service import (
    ImportConflict,
    ImportResult,
    ImportSource,
    import_site,
)
from assetops_backend.sites.ports import SiteRepositoryError


def _row(label: str, fixture: object, stored: object) -> str:
    verdict = "same" if fixture == stored else "DIFFERENT"
    return f"| {label} | {fixture} | {stored} | {verdict} |"


def comparison_report(command: str, source: ImportSource, result: ImportResult) -> str:
    record = source.record
    site = result.site
    revision = result.revision
    regs = result.registrations
    stored_record = record_at(site, revision)
    fixture_content = content_from_record(record)
    reserve = battery_reserve(revision.content)
    lines = [
        "# S1-01 import comparison",
        "",
        f"Command: `{command}`",
        "",
        f"- Source: `{source.path}`",
        f"- Source sha256: `{source.sha256}`",
        f"- Tenant: `{result.tenant.slug}` (`{result.tenant.id}`)",
        f"- Site UUID: `{site.id}`",
        f"- Import registration: `{site.import_record.id}` at {utc_text(site.import_record.imported_at)}",
        f"- Outcome: {'imported' if result.created else 'already imported (idempotent; same UUIDs and revision)'}",
        "",
        "## Identity and version",
        "",
        "| Field | Fixture | Postgres | |",
        "| --- | --- | --- | --- |",
        _row("site code", record.site_id, site.site_code),
        _row("name", record.display_name, site.name),
        _row("site type", record.site_type, site.site_type),
        _row("timezone", record.timezone, site.timezone),
        _row("lifecycle", record.lifecycle_status, site.lifecycle),
        _row("Foundation version", record.foundation.version, revision.version),
        _row("valid_from", record.foundation.valid_from, utc_text(revision.valid_from)),
        _row("valid_to", "(open)", revision.valid_to or "(open)"),
        f"| Foundation content, all sections | fixture | Postgres revision content | {'same' if fixture_content == revision.content else 'DIFFERENT'} |",
        f"| Site record re-parsed from Postgres | fixture record | Postgres record | {'same' if stored_record == record else 'DIFFERENT'} |",
        "",
        f"Revision `{revision.id}`; content sha256 `{revision.content_sha256}`; recorded {utc_text(revision.recorded_at)}.",
        "",
        "## Assets (one per fixture component)",
        "",
        "| asset_code | type | asset UUID | rating |",
        "| --- | --- | --- | --- |",
    ]
    order = {c.component_id: i for i, c in enumerate(record.foundation.components)}
    for asset in sorted(regs.assets, key=lambda row: order.get(row.asset_code, len(order))):
        rating = asset.attributes.get("rating")
        rating_text = "none" if rating is None else f"{rating['value']} {rating['unit']}"
        lines.append(f"| {asset.asset_code} | {asset.asset_type} | `{asset.id}` | {rating_text} |")
    lines += [
        "",
        f"{len(regs.assets)} assets; fixture declares {len(record.foundation.components)} components. "
        "No controller asset is invented; devices are sources, not assets.",
        "",
        "## Gateway and sources (registration metadata only)",
        "",
    ]
    for gateway in regs.gateways:
        lines.append(
            f"- Gateway `{gateway.gateway_external_id}` `{gateway.id}`: mode {gateway.mode} "
            f"(proposed provenance), credential_ref {gateway.credential_ref or 'null (pending)'}, "
            f"disabled_at {utc_text(gateway.disabled_at) if gateway.disabled_at else 'null'}."
        )
    asset_codes = {asset.id: asset.asset_code for asset in regs.assets}
    lines += ["", "| source_external_id (= device_id) | kind | asset | source UUID |", "| --- | --- | --- | --- |"]
    for source_row in regs.sources:
        lines.append(
            f"| {source_row.source_external_id} | {source_row.device_kind} | "
            f"{asset_codes.get(source_row.asset_id)} | `{source_row.id}` |"
        )
    topology = revision.content.get("topology") or {}
    controls = {c["control_key"]: c["members"] for c in revision.content.get("site_controls") or ()}
    lines += [
        "",
        f"{len(regs.sources)} sources; fixture declares {len(record.foundation.devices or ())} devices.",
        "",
        "## Topology and controls",
        "",
        f"- Topology: {len(topology.get('nodes') or ())} nodes, {len(topology.get('connections') or ())} connections (stored verbatim).",
        f"- Battery reserve-state-of-charge: {reserve['value'] if reserve else 'NOT CONFIGURED'} {reserve['unit'] if reserve else ''}".rstrip(),
        f"- source-priority (read-only): {controls.get('source-priority', 'NOT CONFIGURED')}",
        f"- critical-load-priority (read-only): {controls.get('critical-load-priority', 'NOT CONFIGURED')}",
        "- Generator start/stop thresholds: not in the fixture, not imported (the mock's 35% / 90% are layout examples).",
        "",
        "## Omitted binding authority",
        "",
        f"- {len(revision.content.get('signal_mappings') or ())} legacy `signal_mappings` are stored in the revision as "
        "comparison data only. No signal_binding_revision exists; bindings are INCOMPLETE until S1-02; "
        "no acquisition snapshot can be downloaded and no evidence can be uploaded.",
        "",
        "## Configuration gaps",
        "",
    ]
    gaps = configuration_gaps(site, revision, regs)
    lines += [f"- {gap.code} ({gap.subject}): {gap.message}" for gap in gaps] or ["- none"]
    lines += [
        "",
        "Mock values (MG-DEMO-01, Africa/Nairobi, Foundation v4) were not used; every value above comes from the source document.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.sites.import_kobo")
    parser.add_argument("--source", required=True, help="Site YAML document to import (read only)")
    parser.add_argument("--tenant", required=True, help="Tenant slug; must be the configured tenant")
    parser.add_argument("--report", help="Where to write the comparison report (Markdown)")
    args = parser.parse_args(argv)
    command = "python -m assetops_backend.sites.import_kobo " + " ".join(
        sys.argv[1:] if argv is None else argv
    )
    try:
        if args.report:
            check_site_import_report_path(args.report, args.source)
        source = read_site_import_source(args.source)
        result = import_site(
            build_foundation_store(database_url()),
            tenant_slug=args.tenant,
            configured_tenant_slug=DEVELOPMENT_TENANT_SLUG,
            source=source,
            legacy_documents=legacy_site_documents(),
        )
    except ImportConflict as error:
        print(f"IMPORT CONFLICT: {error}", file=sys.stderr)
        return 2
    except (SiteRepositoryError, FoundationStoreError) as error:
        print(f"IMPORT FAILED: {error}", file=sys.stderr)
        return 1
    print(
        f"{'Imported' if result.created else 'Already imported'} {result.site.site_code} "
        f"site={result.site.id} revision={result.revision.id} v{result.revision.version} "
        f"assets={len(result.registrations.assets)} sources={len(result.registrations.sources)} "
        f"sha256={source.sha256}"
    )
    if args.report:
        path = write_site_import_report(
            args.report, comparison_report(command, source, result), source=args.source
        )
        print(f"Report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
