"""CH-5c (CH5c-R3 R7, amended by CH5c-R4 W1-W4): the watermark of a stored route response.

The watermark is one statement: the count of `chain_input_change` rows (migration 0047) for the tenant whose Site
is one of the request's Sites or NULL (a tenant-wide change). The log is DB append-only and every write to a
watermark input table commits at least one row in the writer's own transaction, so between two snapshots the
count is equal exactly when no input change committed between them, whatever the commit order (W1). The count is
not filtered by `known_at`: a late change to a historical row moves it too (W2, W4). A change with a NULL tenant
(a TRUNCATE, or a table without a tenant column) moves every tenant's count: over-invalidation, the safe
direction.

`code_version` (Q5, CH5c-R4) hashes the alembic head, every backend source file and every `config/` file, each by
relative path and content (the file list is hashed, so an edited, added or deleted file changes it), and every
environment setting a composer of a stored route reads (`COMPOSER_ENV`: the value's sha, and for a manifest path
the file's content too). Not hashed: `DATABASE_URL` (the store lives in that database) and `ASSETOPS_SERVER_TIMING`
(a response header, never body bytes).

CH5c-R6: the SQL (`read_watermark`) and the file reads (`code_version`) live below the port, in
`chain/adapters/postgres_response_store.py` and `chain/adapters/file_code_version.py`; this module keeps the rule
and the setting lists.
"""
from __future__ import annotations

#: Q5 survey (`grep os.environ backend/assetops_backend`): the settings that can change a stored body's bytes.
COMPOSER_ENV = (
    "ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX",  # the Portfolio `next_cursor` MAC (estate/scope.py)
    "ASSETOPS_WORK_CURSOR_KEY_HEX",  # the work index cursor MAC (work/global_index.py)
    "ASSETOPS_ACTION_DEMO_GRANTS",  # Action admission (actions/composition.py)
    "ASSETOPS_DEMO_FIXTURE_MANIFEST",  # the dispatch and Finding read manifests (main.py)
    "ASSETOPS_FINDING_CASES_MANIFEST",
)
MANIFEST_ENV = ("ASSETOPS_DEMO_FIXTURE_MANIFEST", "ASSETOPS_FINDING_CASES_MANIFEST")

#: CH5c-R6: the cursor keys a server needs to serve (`tools/demo_combined.KEY_NAMES`; an L0 test keeps them equal).
#: A pre-build in a process without all of them stores nothing (`SKIPPED_NO_SERVE_ENV`): its `code_version` could
#: never equal a serving process's, so its rows would never be hit.
SERVE_KEYS = ("ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX", "ASSETOPS_WORK_CURSOR_KEY_HEX")
