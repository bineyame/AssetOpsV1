"""3C0a (spec `specs/3C0a-operator-accounts/spec.md` §2; D-3C0A.2, D-3C0A.11): operator accounts, credentials,
statuses, role grants, sessions and sign-in attempts.

- Current state is derived, never stored: the password is the latest `account_credential` row by (set_at, id), the
  status the latest `account_status` row, and a grant is held while its GRANTED `role_grant` row has no REMOVED row
  naming it (`grant_id`). The four record tables are append-only (the 0005 `ledger_append_only()` trigger).
- `operator_session` stores only the token's SHA-256; the one change allowed is setting `revoked_at` once.
- `sign_in_attempt` stores the SHA-256 of the normalised email key, a person only on a success, and is
  insert-and-purge (every insert purges rows older than 30 days; UPDATE is refused).
- The adapter writes every timestamp itself; there are no column defaults.

Numbering: follows UP-1's `0061_reading_upload`; renumbered at merge if another migration reaches main first.

Revision ID: 0062_operator_accounts
Revises: 0061_reading_upload
Create Date: 2026-11-20
"""
from alembic import op

revision = "0062_operator_accounts"
down_revision = "0061_reading_upload"
branch_labels = None
depends_on = None

TABLES = ("operator_account", "account_credential", "account_status", "role_grant", "operator_session",
          "sign_in_attempt")

UPGRADE = r"""
CREATE TABLE operator_account (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    email text NOT NULL CHECK (char_length(email) BETWEEN 3 AND 320 AND email = btrim(email)),
    email_key text NOT NULL UNIQUE CHECK (email_key = lower(email)),
    display_name text NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120 AND display_name = btrim(display_name)),
    created_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    UNIQUE (tenant_id, id)
);
CREATE TABLE account_credential (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    password_hash text NOT NULL CHECK (password_hash ~ '^scrypt\$32768\$8\$1\$[A-Za-z0-9_-]{22}\$[A-Za-z0-9_-]{43}$'),
    set_at timestamptz NOT NULL,
    set_by text NOT NULL CHECK (set_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX account_credential_person ON account_credential (person_id, set_at DESC, id);
CREATE TABLE account_status (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('ACTIVE', 'DISABLED')),
    reason text NULL CHECK (reason IS NULL OR char_length(reason) BETWEEN 1 AND 500),
    set_at timestamptz NOT NULL,
    set_by text NOT NULL CHECK (set_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX account_status_person ON account_status (person_id, set_at DESC, id);
CREATE TABLE role_grant (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    role text NOT NULL CHECK (role IN ('OPERATOR_EXECUTIVE', 'FINANCE_AND_COMMERCIAL_LEAD', 'SITE_MANAGER',
                                       'FIELD_TECHNICIAN', 'ANALYST')),
    site_id uuid NULL,
    action text NOT NULL CHECK (action IN ('GRANTED', 'REMOVED')),
    grant_id uuid NULL REFERENCES role_grant (id),
    by_person_id uuid NULL,
    by_service text NULL CHECK (by_service IS NULL OR by_service ~ '^service:[a-z][a-z0-9-]{0,62}$'),
    at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, by_person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK ((role = 'SITE_MANAGER') = (site_id IS NOT NULL)),
    CHECK ((action = 'REMOVED') = (grant_id IS NOT NULL)),
    CHECK ((by_person_id IS NULL) <> (by_service IS NULL))
);
CREATE UNIQUE INDEX role_grant_one_removal ON role_grant (grant_id) WHERE action = 'REMOVED';
CREATE INDEX role_grant_tenant_at ON role_grant (tenant_id, at DESC, id);
CREATE INDEX role_grant_person ON role_grant (tenant_id, person_id);
CREATE FUNCTION role_grant_removal_matches() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.action = 'REMOVED' AND NOT EXISTS (
        SELECT 1 FROM role_grant g
        WHERE g.id = NEW.grant_id AND g.action = 'GRANTED' AND g.tenant_id = NEW.tenant_id
          AND g.person_id = NEW.person_id AND g.role = NEW.role AND g.site_id IS NOT DISTINCT FROM NEW.site_id) THEN
        RAISE EXCEPTION 'role_grant removal % does not match a granted row', NEW.id;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER role_grant_removal_check BEFORE INSERT ON role_grant
    FOR EACH ROW EXECUTE FUNCTION role_grant_removal_matches();
CREATE TABLE operator_session (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    token_sha256 text NOT NULL UNIQUE CHECK (token_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz NULL,
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id),
    CHECK (expires_at > created_at),
    CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);
CREATE INDEX operator_session_person ON operator_session (person_id, created_at DESC);
CREATE FUNCTION operator_session_revoke_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'operator_session rows are never deleted';
    END IF;
    IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL
       OR (NEW.id, NEW.tenant_id, NEW.person_id, NEW.token_sha256, NEW.created_at, NEW.expires_at)
          IS DISTINCT FROM (OLD.id, OLD.tenant_id, OLD.person_id, OLD.token_sha256, OLD.created_at, OLD.expires_at) THEN
        RAISE EXCEPTION 'operator_session allows only setting revoked_at once';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER operator_session_revoke BEFORE UPDATE OR DELETE ON operator_session
    FOR EACH ROW EXECUTE FUNCTION operator_session_revoke_only();
CREATE TABLE sign_in_attempt (
    id uuid PRIMARY KEY,
    email_key_sha256 text NOT NULL CHECK (email_key_sha256 ~ '^[0-9a-f]{64}$'),
    at timestamptz NOT NULL,
    succeeded boolean NOT NULL,
    person_id uuid NULL REFERENCES operator_account (id),
    CHECK (succeeded = (person_id IS NOT NULL))
);
CREATE INDEX sign_in_attempt_email ON sign_in_attempt (email_key_sha256, at DESC);
CREATE INDEX sign_in_attempt_at ON sign_in_attempt (at);
CREATE FUNCTION sign_in_attempt_no_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'sign_in_attempt rows are inserted and purged, never updated';
END;
$$;
CREATE TRIGGER sign_in_attempt_no_update BEFORE UPDATE ON sign_in_attempt
    FOR EACH ROW EXECUTE FUNCTION sign_in_attempt_no_update();
CREATE TRIGGER operator_account_immutable BEFORE UPDATE OR DELETE ON operator_account
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER account_credential_immutable BEFORE UPDATE OR DELETE ON account_credential
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER account_status_immutable BEFORE UPDATE OR DELETE ON account_status
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER role_grant_immutable BEFORE UPDATE OR DELETE ON role_grant
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

REFUSE_IF_USED = (
    "LOCK TABLE " + ", ".join(TABLES) + " IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n"
    "    IF EXISTS (SELECT 1 FROM operator_account) THEN\n"
    "        RAISE EXCEPTION 'Downgrade of 0062_operator_accounts refused: accounts exist';\n"
    "    END IF;\nEND;\n$$;\n"
)

#: Reverse order. Exactly the three 0062 functions are dropped, never 0005's `ledger_append_only()` (R11).
DOWNGRADE = """
DROP TRIGGER sign_in_attempt_no_update ON sign_in_attempt;
DROP INDEX sign_in_attempt_at;
DROP INDEX sign_in_attempt_email;
DROP TABLE sign_in_attempt;
DROP FUNCTION sign_in_attempt_no_update();
DROP TRIGGER operator_session_revoke ON operator_session;
DROP INDEX operator_session_person;
DROP TABLE operator_session;
DROP FUNCTION operator_session_revoke_only();
DROP TRIGGER role_grant_immutable ON role_grant;
DROP TRIGGER role_grant_removal_check ON role_grant;
DROP INDEX role_grant_person;
DROP INDEX role_grant_tenant_at;
DROP INDEX role_grant_one_removal;
DROP TABLE role_grant;
DROP FUNCTION role_grant_removal_matches();
DROP TRIGGER account_status_immutable ON account_status;
DROP INDEX account_status_person;
DROP TABLE account_status;
DROP TRIGGER account_credential_immutable ON account_credential;
DROP INDEX account_credential_person;
DROP TABLE account_credential;
DROP TRIGGER operator_account_immutable ON operator_account;
DROP TABLE operator_account;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DOWNGRADE)
