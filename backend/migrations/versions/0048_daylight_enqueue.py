"""CH-9 u1 (build sheet CH-9 §9 R2, §10 CH9-R2 Q4): renewable mini-depth work over measured daylight hours.

The three 0029 enqueue functions are replaced (`CREATE OR REPLACE`, same signatures, same trigger). Renewable work
is enqueued for a Site-local clock hour when an accepted `pv_available_power` reading overlapping that hour is > 0,
and for the local 12:00 hour, as before, when the Site has no `pv_available_power` binding overlapping the hour.
The enqueue is a coarse filter: a dawn or dusk hour is enqueued and assessed, but it is read as daylight only when
`daylight_hours` (B/mini_depth/store.py) finds it fully covered with every value > 0 (§9 R1). Because the test is
on the hour, not on the arriving row, any renewable-role reading landing in such an hour (a late feeder reading)
also enqueues it. `mini_enqueue_hour` refuses a renewable hour that fails the same test.

No table and no writer. Downgrade restores the 0029 bodies (read from that migration's own text) and drops the
one helper function.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from alembic import op

revision = "0048_daylight_enqueue"
down_revision = "0047_chain_response"
branch_labels = None
depends_on = None


def _m0029():
    path = Path(__file__).with_name("0029_w4_mini_depth.py")
    spec = importlib.util.spec_from_file_location("_m0029_w4_mini_depth", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


_M = _m0029()
ROLE_SET_4 = _M.ROLE_SET_4
PV_AVAILABLE = "pv_available_power"
_GATE_LIST = _M._GATE_LIST
_PAIRS = _M._PAIRS
_DOMAIN_LIST = _M._DOMAIN_LIST
RETENTION = _M.RETENTION

#: The one hour test. A numeric reading text is matched before the cast, so a non-numeric value never raises.
RENEWABLE_HOUR = rf"""
CREATE FUNCTION mini_renewable_hour(p_tenant uuid, p_site uuid, p_lo timestamptz, p_hi timestamptz, p_tz text)
    RETURNS boolean
LANGUAGE plpgsql STABLE AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM signal_binding_revision b JOIN signal_binding_set_revision s
          ON s.tenant_id = b.tenant_id AND s.site_id = b.site_id AND s.id = b.binding_set_revision_id
        WHERE b.tenant_id = p_tenant AND b.site_id = p_site AND b.role = '{PV_AVAILABLE}'
          AND s.role_set = '{ROLE_SET_4}' AND s.superseded_at IS NULL AND b.superseded_at IS NULL
          AND b.valid_from < p_hi AND (b.valid_to IS NULL OR b.valid_to > p_lo)) THEN
        RETURN extract(hour FROM (p_lo AT TIME ZONE p_tz)) = 12;
    END IF;
    RETURN EXISTS (
        SELECT 1 FROM accepted_evidence e JOIN ingestion_disposition d
          ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal
        WHERE e.tenant_id = p_tenant AND e.site_id = p_site AND e.role = '{PV_AVAILABLE}'
          AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id
          AND coalesce(e.interval_end, e.source_time + interval '1 microsecond') > p_lo
          AND coalesce(e.interval_start, e.source_time) < p_hi
          AND e.normalized_value_text ~ '^[+-]?([0-9]+[.]?[0-9]*|[.][0-9]+)([eE][+-]?[0-9]+)?$'
          AND e.normalized_value_text::numeric > 0);
END;
$$;
"""

_HOUR_CHECK_0029 = """    IF p_domain = 'mini_renewable' AND extract(hour FROM local_lo) <> 12 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'mini_enqueue_hour: renewable work is the local 12:00 hour only';
    END IF;"""
_HOUR_CHECK_0048 = """    IF p_domain = 'mini_renewable' AND NOT mini_renewable_hour(p_tenant, p_site, p_lo, p_hi, tz) THEN
        RAISE EXCEPTION USING ERRCODE = '22023',
            MESSAGE = 'mini_enqueue_hour: renewable work needs a positive pv_available_power reading in the hour';
    END IF;"""
_LOOP_0029 = "IF m.domain <> 'mini_renewable' OR extract(hour FROM h) = 12 THEN"
_LOOP_0048 = ("IF m.domain <> 'mini_renewable' OR mini_renewable_hour(NEW.tenant_id, NEW.site_id, h AT TIME ZONE tz,\n"
              "                                                                 (h AT TIME ZONE tz) + interval '1 hour', tz) THEN")
_PUB_0029 = "IF d <> 'mini_renewable' OR extract(hour FROM h) = 12 THEN"
_PUB_0048 = ("IF d <> 'mini_renewable' OR mini_renewable_hour(p_tenant, p_site, h AT TIME ZONE tz,\n"
             "                                                       (h AT TIME ZONE tz) + interval '1 hour', tz) THEN")
_TRIGGER = """CREATE CONSTRAINT TRIGGER enqueue_mini_depth AFTER INSERT ON accepted_evidence
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
    EXECUTE FUNCTION mini_enqueue_accepted();
"""


def _functions_0029() -> str:
    """The 0029 function bodies as `CREATE OR REPLACE`, without the trigger (which is unchanged)."""
    body = _M.ENQUEUE
    if body.count(_TRIGGER) != 1:
        raise RuntimeError("0048: the 0029 trigger text was not found once")
    return body.replace(_TRIGGER, "").replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")


def _functions_0048() -> str:
    body = _functions_0029()
    for old, new in ((_HOUR_CHECK_0029, _HOUR_CHECK_0048), (_LOOP_0029, _LOOP_0048), (_PUB_0029, _PUB_0048)):
        if body.count(old) != 1:
            raise RuntimeError(f"0048: expected one 0029 text {old[:40]!r}")
        body = body.replace(old, new)
    return body


def upgrade() -> None:
    op.execute(RENEWABLE_HOUR)
    op.execute(_functions_0048())


def downgrade() -> None:
    op.execute(_functions_0029())
    op.execute("DROP FUNCTION mini_renewable_hour(uuid, uuid, timestamptz, timestamptz, text);")
