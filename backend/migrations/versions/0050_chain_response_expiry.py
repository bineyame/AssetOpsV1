"""CH-5c2 (CH5c-R7 H2 C2, L4; CH5c2-R1 forced deviation): stored-response expiry and a TRUNCATE-proof change log.

0047 is merged, so the two §8.6 edits to it land here instead:

- `chain_response.valid_until` (NULL = never expires: a historical body). A live body is a miss once the clock
  passes it (`chain/adapters/postgres_response_store.py` `_LOOKUP`).
- L4: a BEFORE TRUNCATE refusal on `chain_input_change`. Row deletes and updates are already refused
  (`ledger_append_only`, 0047); a TRUNCATE would reset every watermark count and break W5 monotonicity. The W5
  harness reset runs under `session_replication_role = replica`, where ordinary triggers do not fire.
"""
from __future__ import annotations

from alembic import op

revision = "0050_chain_response_expiry"
down_revision = "0049_mini_service_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE chain_response ADD COLUMN valid_until timestamptz")
    op.execute("CREATE TRIGGER chain_input_change_no_truncate BEFORE TRUNCATE ON chain_input_change "
               "FOR EACH STATEMENT EXECUTE FUNCTION ledger_append_only()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS chain_input_change_no_truncate ON chain_input_change")
    op.execute("ALTER TABLE chain_response DROP COLUMN valid_until")
