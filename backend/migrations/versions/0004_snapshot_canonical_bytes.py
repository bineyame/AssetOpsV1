"""S1-02 fix round: keep each pinned snapshot's canonical bytes (review M1).

Decision `D-2026-10-08-s1-bindings-roles-and-snapshot` Q6 requires the exact
historical bytes to stay available, or reproducible from immutable inputs. The
`assetops.acquisition-snapshot/1` serializer reads registration fields - the
Site code, the gateway's external ID and mode, the sources' external IDs - that
the schema does not make immutable, so rebuilding at download time cannot
promise the published bytes. This migration stores them instead:

* `snapshot_canonical` holds the canonical bytes hashed at publication. It is
  NOT NULL and a CHECK ties it to `snapshot_sha256`, so the database refuses a
  row whose bytes do not hash to its pinned SHA-256.
* The 0003 immutability trigger compares whole rows (`to_jsonb(NEW) -
  'superseded_at'`), so the new column is immutable without changing it.
* Binding set revisions published before this migration are backfilled by
  re-running the preserved v1 serializer over the stored rows. A rebuilt body
  is written only when it reproduces the SHA-256 pinned at publication, which
  makes it the published body. If any row does not reproduce - a registration
  identity field changed after publication - the migration refuses rather than
  pinning different bytes or recomputing the hash.

Credential and disabled status stay mutable: the serializer never read them.

Revision ID: 0004_snapshot_canonical_bytes
Revises: 0003_pinned_binding_snapshots
Create Date: 2026-10-08
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

from alembic import op
from sqlalchemy import text

revision = "0004_snapshot_canonical_bytes"
down_revision = "0003_pinned_binding_snapshots"
branch_labels = None
depends_on = None


ENFORCE = r"""
ALTER TABLE signal_binding_set_revision
    ALTER COLUMN snapshot_canonical SET NOT NULL,
    ADD CONSTRAINT binding_set_snapshot_canonical_hashed
        CHECK (encode(sha256(snapshot_canonical), 'hex') = snapshot_sha256);
"""


def _backfill(bind) -> None:
    # The preserved v1 serializer is pure; it reads only the attributes selected
    # below, so this migration hands it plain rows rather than the adapter's.
    from assetops_backend.sites.binding_alignment import SERIALIZERS, snapshot_bytes

    def rows(sql: str, **params):
        return bind.execute(text(sql), params).all()

    refused: list[str] = []
    bodies: list[tuple[object, object, bytes]] = []
    for scope in rows("SELECT DISTINCT tenant_id, site_id FROM signal_binding_set_revision ORDER BY 1, 2"):
        t, s = scope.tenant_id, scope.site_id
        site = rows("SELECT id, site_code FROM site WHERE tenant_id = :t AND id = :s", t=t, s=s)[0]
        registrations = SimpleNamespace(
            gateways=rows("SELECT id, gateway_external_id, mode FROM gateway WHERE tenant_id = :t AND site_id = :s",
                          t=t, s=s),
            sources=rows("SELECT id, source_external_id FROM source WHERE tenant_id = :t AND site_id = :s", t=t, s=s),
        )
        foundations = {
            r.id: r
            for r in rows(
                "SELECT id, version, valid_from, valid_to, content_sha256 FROM foundation_revision "
                "WHERE tenant_id = :t AND site_id = :s", t=t, s=s,
            )
        }
        bindings: dict[object, list] = {}
        for b in rows(
            "SELECT id, binding_set_revision_id, gateway_id, source_id, device_id, signal_id, asset_id, role, "
            "source_unit, canonical_unit, conversion FROM signal_binding_revision "
            "WHERE tenant_id = :t AND site_id = :s", t=t, s=s,
        ):
            bindings.setdefault(b.binding_set_revision_id, []).append(b)
        for row in rows(
            "SELECT id, binding_set_id, version, role_set, valid_from, valid_to, bindings_sha256, "
            "foundation_revision_id, gateway_id, snapshot_schema, snapshot_sha256 "
            "FROM signal_binding_set_revision WHERE tenant_id = :t AND site_id = :s ORDER BY version", t=t, s=s,
        ):
            label = f"{site.site_code} binding v{row.version} ({row.id})"
            if row.snapshot_schema not in SERIALIZERS:
                refused.append(f"{label}: no serializer for {row.snapshot_schema!r}")
                continue
            binding_set = SimpleNamespace(**row._asdict(), bindings=tuple(bindings.get(row.id, ())))
            body = snapshot_bytes(
                row.snapshot_schema, t, site, registrations, foundations[row.foundation_revision_id], binding_set
            )
            if hashlib.sha256(body).hexdigest() != row.snapshot_sha256:
                refused.append(f"{label}: the current registrations no longer reproduce the pinned SHA-256")
                continue
            bodies.append((t, row.id, body))
    if refused:
        raise RuntimeError(
            "Migration 0004 cannot recover the published snapshot bytes of "
            f"{len(refused)} binding set revision(s), and will not pin different bytes or "
            "recompute a published hash: " + "; ".join(refused)
        )
    op.execute("ALTER TABLE signal_binding_set_revision DISABLE TRIGGER binding_set_revision_immutable")
    for tenant_id, row_id, body in bodies:
        bind.execute(
            text(
                "UPDATE signal_binding_set_revision SET snapshot_canonical = :body "
                "WHERE tenant_id = :tenant_id AND id = :id AND snapshot_canonical IS NULL"
            ),
            {"body": body, "tenant_id": tenant_id, "id": row_id},
        )
    op.execute("ALTER TABLE signal_binding_set_revision ENABLE TRIGGER binding_set_revision_immutable")


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("ALTER TABLE signal_binding_set_revision ADD COLUMN snapshot_canonical bytea NULL")
    if bind.execute(text("SELECT count(*) FROM signal_binding_set_revision")).scalar_one():
        _backfill(bind)
    op.execute(ENFORCE)


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE signal_binding_set_revision
            DROP CONSTRAINT IF EXISTS binding_set_snapshot_canonical_hashed,
            DROP COLUMN IF EXISTS snapshot_canonical;
        """
    )
