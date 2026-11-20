# 3A2 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Reset for spec rev 2 (handshake round 1 answered, 2026-11-20).

Count: **2** (builder, 2026-11-20). Both are built on the reading below, pending a ruling; nothing else waits.

## Q1. §4 places file I/O where the persistence guard refuses it

- **Section.** §4 code table (`pseudonym.py` holds `FileKeyStore`; `pseudonym_key.py` writes the key;
  `UploadSettings.key_dir: Path | None`; `composition.py` imports `make_url` and the two SQLAlchemy errors) and §8 Q9
  (guard changes limited to the commercial writer block).
- **Conflict.** `tools/checks/configuration-persistence.ps1` rule 8 fails on each: `os.open`/`os.write` outside a
  registered file-writer adapter, `pathlib` or `sqlalchemy` imported in a domain package outside `adapters/`.
- **Built (the evidence-domain precedent, `evidence/adapters/gateway_credential_file.py` via `evidence/composition.py`
  and `provision_gateway.py`):** `commercial/adapters/file_key_store.py` holds `FileKeyStore` and
  `create_key_file` (same checks, same messages); `composition.py` re-exports them; `pseudonym_key.py` calls the
  composition; `pseudonym.py` keeps the port, the two exceptions and the pseudonymiser. `UNAVAILABLE` and
  `database_name(url)` live in the Postgres adapter; `COMMERCIAL_UNAVAILABLE` is re-exported unchanged.
  `UploadSettings.key_dir` is `str | None`. The guard's `commercial` domain entry registers the one file writer
  (`Writer = @(".../file_key_store.py")`), a line outside the commercial writer block.
- **Ask.** Ratify this placement and the domain-entry line (or name another), and amend §4 and Q9.

## Q2. Two word placements the spec does not fix

- **Section.** §5 Shapes and Words.
- **Open.** (a) Where `commercial_upload.summary` is served (no shape names it). (b) Which words the Site path's
  401 `UNAUTHENTICATED` and 403 `SITE_SCOPE_FORBIDDEN` carry ("as reading upload" fixes the codes; reading upload's
  words speak of readings).
- **Built.** (a) Not served; `Preview.words` is `commercial_upload.state.checked`, mirroring `UploadSummary.words`
  (the state's words). (b) `commercial_upload.person_required` and `commercial_upload.role_required`.
- **Ask.** Confirm or name the keys; each is a one-line change.
