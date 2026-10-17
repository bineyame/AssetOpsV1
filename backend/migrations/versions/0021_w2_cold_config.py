"""W2-01: cold-chain configuration vocabulary anchor (no SQL change).

`.agent/W2-technical-design-cold.md` migration row `0021_w2_cold_config` and section 3
(`D-2026-10-17-w2-01-answers`).

The cold configuration is held entirely by structures that already exist: the effective Foundation
JSON (`foundation_revision.content`) and immutable binding revisions. The DB site-type CHECK already
admits `COLDCHAIN` (`0001_foundation_identity`). What changes is the closed, code-owned vocabulary in
`assetops_backend.sites` - component types, topology node roles and media, the `event` signal unit,
the `degC` rating unit, the thirteen typed cold properties with their unit ranges, the EVENT role
value kind and the immutable `cold-roles-1` role set. This revision anchors that vocabulary at a
schema version so a database at `0021` is known to be read by code that understands it.

No table, column, constraint or row is created, altered, backfilled or deleted in either direction.
Downgrade is likewise a no-op: stored Foundation and binding rows are untouched, and old-role readers
remain supported.

Revision ID: 0021_w2_cold_config
Revises: 0020_w2_source_event
Create Date: 2026-10-17
"""

from __future__ import annotations

revision = "0021_w2_cold_config"
down_revision = "0020_w2_source_event"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No SQL change: the cold vocabulary is code-owned (see module docstring)."""


def downgrade() -> None:
    """No SQL change and no row touched."""
