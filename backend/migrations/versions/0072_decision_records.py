"""6a (`specs/6a-decision-records/spec.md` §2; D-P6.1 to D-P6.29, handshake R4, I5): step 6's records.

A **decision** on a Site's lever for a period, its **options** (always exactly one `no-action`, position 0), the
**one-off** cost a person states for an option, the **evaluation runs** `6c` writes (one `option_evaluation` per
option, with its `option_effect` rows) and the executive's **choice**, which freezes the run they saw.

- One raw `UPGRADE` string (0062 and 0070 style); no column defaults: the adapter writes every column.
- Exactly one no-action option: `decision_option_key_unique` with the `option_key` and pairing checks give at most
  one; the deferred constraint trigger `decision_has_no_action` gives at least one (SQLSTATE 23514).
- Every run covers every option: the deferred constraint trigger `option_evaluation_run_complete` (SQLSTATE 23514).
- Cross-row checks (an evaluation's option in its run's decision, a choice's option and run in its decision, a
  one-off on the evaluation's option) are the adapter's, in its transaction (spec §2, §3.3).
- Every table-level and multi-column CHECK is named `<table>_<rule>`; column checks keep `<table>_<column>_check`.
- Append-only: 0005's `ledger_append_only()` refuses UPDATE and DELETE (row trigger) and TRUNCATE (statement
  trigger) on each of the seven tables.
- `agreed_action_tenant_id_unique` is added so a choice can name its agreed Action within the tenant.

Numbering (spec §0 gate A): `main`'s head was `0071_person_on_actions` at build time. Renumbering at gate B changes
only the file name, `revision` and `down_revision` (the refusal message is built from `revision`).

Revision ID: 0072_decision_records
Revises: 0071_person_on_actions
Create Date: 2026-11-22
"""
from alembic import op

revision = "0072_decision_records"
down_revision = "0071_person_on_actions"
branch_labels = None
depends_on = None

#: Parent to child; the downgrade walks it in reverse.
TABLES = ("decision", "decision_option", "option_one_off", "option_evaluation_run", "option_evaluation",
          "option_effect", "decision_choice")

ID_RE = "'^[a-z][a-z0-9_]{0,63}$'"


def _ws(col: str) -> str:
    """0070's whole-second check."""
    return f"CHECK (date_trunc('second', {col} AT TIME ZONE 'UTC') = {col} AT TIME ZONE 'UTC')"


UPGRADE = f"""
ALTER TABLE agreed_action ADD CONSTRAINT agreed_action_tenant_id_unique UNIQUE (tenant_id, id);

CREATE TABLE decision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NOT NULL,
    structure_key text NOT NULL CHECK (structure_key IN ('MINI_GRID', 'COLD_CHAIN', 'EV_DEPOT_CAPTIVE')),
    lever_id text NOT NULL CHECK (lever_id ~ {ID_RE}),
    purpose_factor_id text NOT NULL CHECK (purpose_factor_id ~ {ID_RE}),
    finding_id uuid NULL,
    period text NOT NULL CHECK (period ~ '^[0-9]{{4}}-(0[1-9]|1[0-2])$'),
    horizon_months integer NOT NULL CHECK (horizon_months BETWEEN 1 AND 60),
    current_settings jsonb NOT NULL CHECK (jsonb_typeof(current_settings) = 'object'),
    rule_version text NOT NULL CHECK (rule_version = 'decision-prepare-1'),
    prepared_by_person_id uuid NOT NULL,
    prepared_role text NOT NULL CHECK (prepared_role = 'ANALYST'),
    prepared_by_script boolean NOT NULL,
    prepared_at timestamptz NOT NULL {_ws('prepared_at')},
    CONSTRAINT decision_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id, finding_id) REFERENCES finding (tenant_id, site_id, id),
    FOREIGN KEY (tenant_id, prepared_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE UNIQUE INDEX decision_once ON decision (tenant_id, site_id, lever_id, period, finding_id) NULLS NOT DISTINCT;
CREATE INDEX decision_tenant ON decision (tenant_id, prepared_at DESC, id DESC);

CREATE TABLE decision_option (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    option_key text NOT NULL CHECK (option_key ~ '^[a-z0-9][a-z0-9-]{{0,63}}$'),
    generator text NOT NULL CHECK (generator IN ('NO_ACTION', 'SETTING_GRID')),
    settings jsonb NOT NULL CHECK (jsonb_typeof(settings) = 'object'),
    position integer NOT NULL CHECK (position >= 0),
    CONSTRAINT decision_option_no_action_key CHECK ((generator = 'NO_ACTION') = (option_key = 'no-action')),
    CONSTRAINT decision_option_no_action_first CHECK ((generator = 'NO_ACTION') = (position = 0)),
    CONSTRAINT decision_option_tenant_id_unique UNIQUE (tenant_id, id),
    CONSTRAINT decision_option_key_unique UNIQUE (decision_id, option_key),
    CONSTRAINT decision_option_position_unique UNIQUE (decision_id, position),
    FOREIGN KEY (tenant_id, decision_id) REFERENCES decision (tenant_id, id)
);

CREATE TABLE option_one_off (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    option_id uuid NOT NULL,
    amount numeric(14, 2) NOT NULL CHECK (amount >= 0),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{{3}}$'),
    crew_visits integer NOT NULL CHECK (crew_visits >= 0),
    basis text NOT NULL CHECK (char_length(basis) BETWEEN 1 AND 200 AND basis = btrim(basis)),
    declared_by_person_id uuid NOT NULL,
    declared_role text NOT NULL CHECK (declared_role IN ('SITE_MANAGER', 'FINANCE_AND_COMMERCIAL_LEAD')),
    declared_by_script boolean NOT NULL,
    declared_at timestamptz NOT NULL {_ws('declared_at')},
    CONSTRAINT option_one_off_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, declared_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX option_one_off_latest ON option_one_off (option_id, declared_at DESC, id DESC);

CREATE TABLE option_evaluation_run (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    evaluator_version text NOT NULL CHECK (evaluator_version ~ '^option-evaluator-[0-9]+$'),
    outcome text NOT NULL CHECK (outcome IN ('RECOMMENDED', 'NO_ACTION_BEST', 'RANKING_INCOMPLETE', 'NOTHING_ADMITTED')),
    study_sha256 text NULL CHECK (study_sha256 IS NULL OR study_sha256 ~ '^[0-9a-f]{{64}}$'),
    study_identity jsonb NULL CHECK (study_identity IS NULL OR jsonb_typeof(study_identity) = 'object'),
    known_at timestamptz NOT NULL {_ws('known_at')},
    run_by_person_id uuid NOT NULL,
    run_role text NOT NULL CHECK (run_role = 'ANALYST'),
    run_by_script boolean NOT NULL,
    run_at timestamptz NOT NULL {_ws('run_at')},
    CONSTRAINT option_evaluation_run_study_pair CHECK ((study_sha256 IS NULL) = (study_identity IS NULL)),
    CONSTRAINT option_evaluation_run_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, decision_id) REFERENCES decision (tenant_id, id),
    FOREIGN KEY (tenant_id, run_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX option_evaluation_run_latest ON option_evaluation_run (decision_id, run_at DESC, id DESC);

CREATE TABLE option_evaluation (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    run_id uuid NOT NULL,
    option_id uuid NOT NULL,
    disposition text NOT NULL
        CHECK (disposition IN ('COMPARISON', 'RECOMMENDED', 'CONDITIONAL', 'ACCEPTABLE', 'DEFERRED', 'REJECTED')),
    reason_code text NULL CHECK (reason_code IS NULL OR reason_code ~ '^[A-Z][A-Z0-9_]{{0,63}}$'),
    rank integer NULL CHECK (rank IS NULL OR rank >= 1),
    monthly_change numeric NULL,
    horizon_change numeric NULL,
    one_off_id uuid NULL,
    value numeric NULL,
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{{3}}$'),
    source_class text NOT NULL CHECK (source_class IN ('SIMULATED', 'EMULATED', 'RECORDED')),
    evidence_class text NOT NULL
        CHECK (evidence_class IN ('RECORDED', 'MEASURED', 'DECLARED', 'DERIVED', 'ESTIMATED', 'MODELLED')),
    missing jsonb NOT NULL CHECK (jsonb_typeof(missing) = 'array'),
    assumed jsonb NOT NULL CHECK (jsonb_typeof(assumed) = 'array'),
    admission jsonb NULL CHECK (admission IS NULL OR jsonb_typeof(admission) = 'object'),
    dawn jsonb NULL CHECK (dawn IS NULL OR jsonb_typeof(dawn) = 'object'),
    CONSTRAINT option_evaluation_value_or_missing CHECK ((value IS NULL) = (jsonb_array_length(missing) > 0)),
    CONSTRAINT option_evaluation_value_currency
        CHECK (value IS NULL OR currency IS NOT NULL OR disposition = 'COMPARISON'),
    CONSTRAINT option_evaluation_comparison
        CHECK (disposition <> 'COMPARISON' OR (value = 0 AND rank IS NULL AND one_off_id IS NULL)),
    CONSTRAINT option_evaluation_recommended_first CHECK (disposition <> 'RECOMMENDED' OR rank = 1),
    CONSTRAINT option_evaluation_tenant_id_unique UNIQUE (tenant_id, id),
    CONSTRAINT option_evaluation_once UNIQUE (run_id, option_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES option_evaluation_run (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, one_off_id) REFERENCES option_one_off (tenant_id, id)
);
CREATE UNIQUE INDEX option_evaluation_one_recommended ON option_evaluation (run_id) WHERE disposition = 'RECOMMENDED';

CREATE TABLE option_effect (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    evaluation_id uuid NOT NULL,
    factor_id text NOT NULL CHECK (factor_id ~ {ID_RE}),
    position integer NOT NULL CHECK (position >= 0),
    change_per_month numeric NULL,
    unit text NOT NULL CHECK (char_length(unit) BETWEEN 1 AND 32),
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{{3}}$'),
    missing jsonb NOT NULL CHECK (jsonb_typeof(missing) = 'array'),
    CONSTRAINT option_effect_change_or_missing CHECK ((change_per_month IS NULL) = (jsonb_array_length(missing) > 0)),
    CONSTRAINT option_effect_once UNIQUE (evaluation_id, factor_id),
    FOREIGN KEY (tenant_id, evaluation_id) REFERENCES option_evaluation (tenant_id, id)
);

CREATE TABLE decision_choice (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    option_id uuid NULL,
    run_id uuid NOT NULL,
    agreed_action_id uuid NULL,
    chosen_by_person_id uuid NOT NULL,
    chosen_role text NOT NULL CHECK (chosen_role = 'OPERATOR_EXECUTIVE'),
    chosen_by_script boolean NOT NULL,
    chosen_at timestamptz NOT NULL {_ws('chosen_at')},
    CONSTRAINT decision_choice_once UNIQUE (decision_id),
    FOREIGN KEY (tenant_id, decision_id) REFERENCES decision (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES option_evaluation_run (tenant_id, id),
    FOREIGN KEY (tenant_id, agreed_action_id) REFERENCES agreed_action (tenant_id, id),
    FOREIGN KEY (tenant_id, chosen_by_person_id) REFERENCES operator_account (tenant_id, id)
);

CREATE FUNCTION decision_has_no_action() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM decision_option WHERE decision_id = NEW.id AND generator = 'NO_ACTION') THEN
        RAISE EXCEPTION 'decision % has no no-action option', NEW.id USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER decision_has_no_action AFTER INSERT ON decision
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION decision_has_no_action();

CREATE FUNCTION run_covers_options() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    evaluated integer;
    offered integer;
BEGIN
    SELECT count(*) INTO evaluated FROM option_evaluation WHERE run_id = NEW.id;
    SELECT count(*) INTO offered FROM decision_option WHERE decision_id = NEW.decision_id;
    IF evaluated <> offered THEN
        RAISE EXCEPTION 'option_evaluation_run % evaluates % of % options', NEW.id, evaluated, offered
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER option_evaluation_run_complete AFTER INSERT ON option_evaluation_run
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION run_covers_options();
""" + "".join(
    f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON {t}\n"
    f"    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n"
    f"CREATE TRIGGER {t}_no_truncate BEFORE TRUNCATE ON {t}\n"
    f"    FOR EACH STATEMENT EXECUTE FUNCTION ledger_append_only();\n"
    for t in TABLES)

DOWNGRADE_REFUSED = f"Downgrade of {revision} refused: decision rows exist"

REFUSE_IF_USED = (
    "".join(f"LOCK TABLE {t} IN ACCESS EXCLUSIVE MODE;\n" for t in TABLES)
    + "DO $$\nBEGIN\n    IF "
    + " OR ".join(f"EXISTS (SELECT 1 FROM {t})" for t in TABLES)
    + f" THEN\n        RAISE EXCEPTION '{DOWNGRADE_REFUSED}';\n    END IF;\nEND;\n$$;\n"
)

#: Reverse order: triggers, both functions, indexes, tables, the agreed_action unique. 0005's
#: `ledger_append_only()` is never dropped.
DOWNGRADE = (
    "".join(f"DROP TRIGGER {t}_no_truncate ON {t};\nDROP TRIGGER {t}_immutable ON {t};\n" for t in reversed(TABLES))
    + "DROP TRIGGER option_evaluation_run_complete ON option_evaluation_run;\n"
    + "DROP TRIGGER decision_has_no_action ON decision;\n"
    + "DROP FUNCTION run_covers_options();\n"
    + "DROP FUNCTION decision_has_no_action();\n"
    + "DROP INDEX option_evaluation_one_recommended;\n"
    + "DROP INDEX option_evaluation_run_latest;\n"
    + "DROP INDEX option_one_off_latest;\n"
    + "DROP INDEX decision_tenant;\n"
    + "DROP INDEX decision_once;\n"
    + "".join(f"DROP TABLE {t};\n" for t in reversed(TABLES))
    + "ALTER TABLE agreed_action DROP CONSTRAINT agreed_action_tenant_id_unique;\n"
)


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
