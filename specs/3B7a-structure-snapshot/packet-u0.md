# 3B7a unit 0 packet: the inputs seam

Branch `task/3B7a-seam` off `main` 8a2900bc4. Diff: `backend/assetops_backend/structure/read.py` and
`backend/tests/test_3b7a_site_inputs_seam.py` only (+ this file). Mid-build questions: 0.

**Built (spec §2.1, D-3B7A.10).** `SiteInputs` (frozen; `leaves`, `stated` as `MappingProxyType`), `evaluate_inputs`
(registry by key; version mismatch -> `StructureError("STRUCTURE_COMPOSE", key, site_code)`),
`StructureRead.site_inputs` (the old `site` body up to evaluation; same refusals, one read per leaf), and `site` =
`evaluate_inputs(site_inputs(...))`. Both exported in `__all__`.

**Tests first** (6, no database): `evaluate_inputs(site_inputs) == site` for Kobo/Kisiwa/Mto; 31 leaves and the two
stated rows (`revenue`, `fuel_cost`) in registry order; no stated source gives `{}`; one `site_month` call per
`site_inputs` and per `site`; version mismatch raises STRUCTURE_COMPOSE. Seen failing before the code (ImportError).

**Plants, each fails then reverted:** version check removed (1 fail); leaves reversed (3); stated dropped from the
evaluation (first missed by 6 passes, test strengthened, then 3 fail); stated read with no source (1); second read in
`site` (1).

**Runs (no database).** 3B1, 3B3 evaluate and window-price, 4b1, 4b money leaves, 5a targets, seam: 281 passed, 5.5 s.
The Postgres variants were not run (no database touched). Fast check-all: 40 guards passed, 88.9 s wall (3m6s with slot wait).
Interpreter: `/opt/assetecon/AssetOpsV1/.venv`, PYTHONPATH set to this worktree (module paths verified).

**Review:** verification review only; no user review needed.
