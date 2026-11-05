"""CH-9 CH9-R4 F1: re-derive the stored `mini-service/1` hours as `mini-service/2`. Enqueue only.

`mini-service/2` (B/mini_depth/store.py `MODEL_VERSIONS`) stores each load row's own `unserved_kwh`, which the
`critical_served` measure reads. For every Site-local hour whose selected `service` head is `mini-service/1`, this
calls the existing 0029/0048 `mini_enqueue_hour(..., 'mini_service', ...)` with a NULL cause (the convention of
`mini_enqueue_configuration`: the work is not caused by one accepted reading) at the migration's transaction time.
The mini-depth worker then derives a `/2` revision and appends its selection as for any other job.

No table, no function, no row rewrite and no change to job semantics: the store stays append-only, and the common
final gate in `mini_enqueue_hour` still decides whether the hour has work. Downgrade is a no-op: jobs are work, not
state, and a `/2` head selected after the upgrade stays a valid, readable head.

Migration order: CH-5c merged first with `0047_chain_response` on `0044_chain_events`; CH-9 re-pointed its two
migrations after it: 0044 -> 0047_chain_response -> 0048_daylight_enqueue -> 0049_mini_service_v2.
"""

from __future__ import annotations

from alembic import op

revision = "0049_mini_service_v2"
down_revision = "0048_daylight_enqueue"
branch_labels = None
depends_on = None

#: The selected `service` head of each hour is the newest selection row for that window (the read's own order).
REENQUEUE_V1_SERVICE = """
SELECT mini_enqueue_hour(h.tenant_id, h.site_id, 'mini_service', h.window_start, h.window_end, NULL, now())
FROM (
        SELECT DISTINCT ON (s.tenant_id, s.site_id, s.window_start)
               s.tenant_id, s.site_id, s.window_start, s.window_end, r.model_version
        FROM mini_depth_selection s JOIN mini_depth_revision r
          ON r.tenant_id = s.tenant_id AND r.site_id = s.site_id AND r.id = s.revision_id
        WHERE s.domain = 'service'
        ORDER BY s.tenant_id, s.site_id, s.window_start, s.selected_at DESC, s.seq DESC
) h
WHERE h.model_version = 'mini-service/1'
ORDER BY h.tenant_id, h.site_id, h.window_start
"""


def upgrade() -> None:
    op.execute(REENQUEUE_V1_SERVICE)


def downgrade() -> None:
    """No-op: the enqueued jobs are work, not state (see the module docstring)."""
