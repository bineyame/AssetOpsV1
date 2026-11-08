"""DIESEL-K6a (build sheet DIESEL-1 §9m.2, ruling DIESEL-1-R3m): the fuel Finding as a domain-Action origin, and the
fuel verification family's plan arm.

- `domain_action_domain_chk` admits `FUEL_BALANCE` (the 0035/0051 precedent). `domain_action_mini_origin`,
  `domain_action_one_origin`, the FKs and the code-collision trigger are not touched: unchanged, they force a
  `FUEL_BALANCE` row to carry the Finding pair.
- `verification_plan` admits the `fuel-residual-within-band-1` rule with the `fuel-residual-verification-1` plan
  version. `verification_plan_family` keeps 0052's two arms verbatim and gains a fuel arm: a domain Action plan that
  cites its origin Finding revision (`origin_finding_revision_id`, its 0019 FK to `finding_revision`), is APPLIED by a
  work event, has no other reserve column, no supersession, the `fuel-seal-dip-sensor-power@1` fixture, a nonempty
  baseline wholly before a 14-day later range. 0019's `verification_plan_window_order` applies unchanged.
- Nothing changes on `verification_evaluation_request`, `verification_outcome`, `verification_metric` or the 0044
  producer (0052 made them domain-capable).

Downgrade locks the tables, refuses while any `FUEL_BALANCE` Action or fuel verification plan exists, then restores
0052's three CHECKs and 0051's domain CHECK.

Revision ID: 0057_fuel_verification
Revises: 0056_unexplained_fuel_finding
Create Date: 2026-11-08
"""

from alembic import op
from sqlalchemy import text

revision = "0057_fuel_verification"
down_revision = "0056_unexplained_fuel_finding"
branch_labels = None
depends_on = None

RESERVE, MIDDAY, FUEL = "reserve-trial-1", "midday-productive-shift-1", "fuel-residual-within-band-1"
RESERVE_PLAN, MIDDAY_PLAN = "reserve-trial-verification-1", "midday-productive-shift-verification-1"
FUEL_PLAN = "fuel-residual-verification-1"
MIDDAY_FIXTURE, FUEL_FIXTURE = "productive-load-midday@1", "fuel-seal-dip-sensor-power@1"
RESERVE_COLUMNS = ("action_id", "origin_finding_revision_id", "applied_event_id", "change_id",
                   "old_foundation_revision_id", "new_foundation_revision_id", "battery_asset_id", "field",
                   "baseline_candidate_seconds")
REFUSED = "0057 downgrade requires no fuel-balance Actions or fuel verification plans"
LOCKED = ("verification_metric", "verification_outcome", "verification_evaluation_request", "verification_plan",
          "domain_action_case_link", "domain_action_intent", "domain_action")


def _all(columns, test: str) -> str:
    return " AND ".join(f"{c} {test}" for c in columns)


# 0052's `_FAMILY`, verbatim (both arms); the downgrade restores it.
FAMILY_0052 = f"""(
    (rule_id = '{RESERVE}' AND plan_version = '{RESERVE_PLAN}' AND {_all(RESERVE_COLUMNS, 'IS NOT NULL')}
     AND {_all(('domain_action_id', 'origin_opportunity_revision_id', 'applied_work_event_id'), 'IS NULL')})
    OR (rule_id = '{MIDDAY}' AND plan_version = '{MIDDAY_PLAN}' AND {_all(RESERVE_COLUMNS, 'IS NULL')}
     AND {_all(('domain_action_id', 'origin_opportunity_revision_id', 'applied_work_event_id'), 'IS NOT NULL')}
     AND supersedes_plan_id IS NULL AND triggering_fixture = '{MIDDAY_FIXTURE}'
     AND baseline_end - baseline_start = interval '14 days' AND later_end - later_start = interval '14 days'
     AND baseline_end <= later_start))"""

# The fuel arm: the reserve columns are NULL except the origin Finding revision, which the plan cites.
_FUEL_ARM = f"""(rule_id = '{FUEL}' AND plan_version = '{FUEL_PLAN}'
     AND {_all(tuple(c for c in RESERVE_COLUMNS if c != 'origin_finding_revision_id'), 'IS NULL')}
     AND {_all(('domain_action_id', 'origin_finding_revision_id', 'applied_work_event_id'), 'IS NOT NULL')}
     AND origin_opportunity_revision_id IS NULL AND supersedes_plan_id IS NULL
     AND triggering_fixture = '{FUEL_FIXTURE}' AND baseline_start < baseline_end
     AND later_end - later_start = interval '14 days' AND baseline_end <= later_start)"""
FAMILY_0057 = f"({FAMILY_0052[1:-1]}\n    OR {_FUEL_ARM})"

PLAN_VERSION_CHK_0052 = f"CHECK (plan_version IN ('{RESERVE_PLAN}', '{MIDDAY_PLAN}'))"
RULE_ID_CHK_0052 = f"CHECK (rule_id IN ('{RESERVE}', '{MIDDAY}'))"
PLAN_VERSION_CHK_0057 = f"CHECK (plan_version IN ('{RESERVE_PLAN}', '{MIDDAY_PLAN}', '{FUEL_PLAN}'))"
RULE_ID_CHK_0057 = f"CHECK (rule_id IN ('{RESERVE}', '{MIDDAY}', '{FUEL}'))"
DOMAIN_CHK_0051 = "CHECK (domain IN ('COLDCHAIN', 'EV_CHARGING', 'MINI'))"
DOMAIN_CHK_0057 = "CHECK (domain IN ('COLDCHAIN', 'EV_CHARGING', 'MINI', 'FUEL_BALANCE'))"


def _plan(plan_version: str, rule_id: str, family: str) -> str:
    return f"""
ALTER TABLE verification_plan
    DROP CONSTRAINT verification_plan_plan_version_check,
    DROP CONSTRAINT verification_plan_rule_id_check,
    DROP CONSTRAINT verification_plan_family,
    ADD CONSTRAINT verification_plan_plan_version_check {plan_version},
    ADD CONSTRAINT verification_plan_rule_id_check {rule_id},
    ADD CONSTRAINT verification_plan_family CHECK {family};
"""


def _domain(check: str) -> str:
    return (f"ALTER TABLE domain_action DROP CONSTRAINT domain_action_domain_chk, "
            f"ADD CONSTRAINT domain_action_domain_chk {check};\n")


UPGRADE = _domain(DOMAIN_CHK_0057) + _plan(PLAN_VERSION_CHK_0057, RULE_ID_CHK_0057, FAMILY_0057)
RESTORE = _plan(PLAN_VERSION_CHK_0052, RULE_ID_CHK_0052, FAMILY_0052) + _domain(DOMAIN_CHK_0051)


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text(f"LOCK TABLE {', '.join(LOCKED)} IN ACCESS EXCLUSIVE MODE"))
    used = bind.execute(text(
        "SELECT EXISTS (SELECT 1 FROM domain_action WHERE domain = 'FUEL_BALANCE') "
        f"OR EXISTS (SELECT 1 FROM verification_plan WHERE rule_id = '{FUEL}')")).scalar()
    if used:
        raise RuntimeError(REFUSED)
    op.execute(RESTORE)
