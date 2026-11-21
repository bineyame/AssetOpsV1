# 3A7 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **2** (reset at spec rev 2, 2026-11-20).

## Q1 (commit 1, 2026-11-21): the owner file is read through a port, not by the service

- **Section.** §2.4, §2.6 (`set_tolerance(tenant_id, tolerance, owner_ref)` checks a file under the owner root).
- **Conflict.** The persistence guard (`tools/checks/configuration-persistence.ps1`, "storage technology above the
  adapter layer") refuses `pathlib` in `commercial/reconciliation.py`, so the service cannot open the file itself.
- **Built (default applied, nothing stopped).** `CommercialReconciliation(months, store, *, owner_file=None)`:
  `owner_file(owner_ref) -> bytes | None` returns the file's bytes under the owner root, or None when absent. The
  service keeps every rule of §2.4 (pattern, existence, slug and figure as whole tokens, SHA-256 of the bytes);
  `owner_file` None means no tolerance can be set (1% stands), which is spec's "deployment without the owner root".
  The tenant's slug comes from `store.tenant_slug`. Commit 2's composition builds `owner_file` from the owner root
  (`main(..., owner_root=...)` unchanged for the command and tests).
- **Asked.** Confirm the port (default), or name another home for the file read (e.g. the command passing the bytes).

## Q2 (commit 1, 2026-11-21, High): the service cannot live in `commercial/`

- **Section.** §3 (`backend/assetops_backend/commercial/reconciliation.py`) with §2.1 (import `COST_STATUSES`,
  `ORIGIN_ORDER`, `SITE_TYPE_TO_STRUCTURE` from `structure`).
- **Conflict.** D-3A4.8: nothing under `commercial/` imports `structure`. Enforced by
  `test_3a4_commercial_months.py::test_12_no_float_and_no_structure_import` and
  `test_4b_money_leaves.py::test_11a_no_float_and_no_structure_import_under_commercial` (both failed with the module
  at the spec's path; those files may not be edited). The same applies to commit 2's
  `commercial/composition.py::build_commercial_reconciliation` (handshake P4 assumed only a digest change).
- **Built (default applied).** The module is `backend/assetops_backend/structure/reconciliation.py` (structure already
  reads commercial: `structure/money.py`). Everything else unchanged; V2 still fails R7 because the import stands.
- **Asked.** Confirm the path, and where commit 2's builder goes (default: beside it in `structure/`, e.g.
  `structure/reconciliation_composition.py`, or the command builds it), since `commercial/composition.py` cannot import it.
