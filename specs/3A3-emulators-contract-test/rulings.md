# 3A3 rulings

Architect (Claude), 2026-11-20. Each ruling is applied by `spec.md` rev 1. D-3A3.1, D-3A3.6 and D-3A3.8 settle three of
the four residuals that 3A2's review and packet left open (`specs/3A2-commercial-file-intake/review.md` "Residual
risk", handshake answer R4); the fourth (a recreated key) is `ON1`'s, D-ON1.7.

## D-3A3.1 Every commercial record enters through 3A2's intake; emulators write files, never the store

- **Ruling.** No emulator, seed, bootstrap or bulk loader calls `CommercialRecords.ingest`. Emulators write native
  files; a loader submits them through `CommercialUploads` (read, check, pseudonymise, submit, accept). The class test
  S1 holds the seam: `CommercialRecords(` is built only in `commercial/composition.py`, `.ingest(` is called only by
  `commercial/uploads.py`, and `build_commercial_uploads(` has two callers (`main.py`, `load_emulated_exports.py`).
  `build_commercial_records` is deleted (no caller on `main`). This binds `DS3` too: it loads the generated world's
  canonical files through the same loader (it accepts `<tenant>.<source_type>.json`).
- **Why.** The review found that a direct 3A1 writer keeps raw refs while 3A2 stores pseudonyms, so one customer
  would not link across the two paths and the same version sent both ways ends in `INTAKE_VERSION_CONFLICT`.
  Pseudonymising in a second place would copy the key rule and the field table; routing through the one service
  keeps one rule, one acceptance record and one refusal vocabulary. The integration design already says emulators
  "write native-shape files into the same authenticated intake" (§7.2, §7.3). Volumes are small (D-3A1 Q2), so the
  in-process path costs nothing.
- **Sweep (W6).** `grep -rn "\.ingest(\|CommercialRecords(\|build_commercial_records"` over product, tools, host and
  simulator on `main` 6db81330a: the only product caller is `commercial/uploads.py`; `build_commercial_records` has
  none; the rest are tests. Nothing else to change.

## D-3A3.2 Native layouts are data in the neutral contracts package, read and rendered by one engine

- **Ruling.** `assetops_contracts.native` holds `Column`, `Layout`, `read_layout`, `render_layout` and the four
  illustrative layouts. The simulator renders with it; the backend reads with it through `LayoutReader`. `3A6` adds
  loading `Layout` values from profile files and the transforms; it does not change the engine's contract.
- **Why.** The simulator may not import the backend (protected seam), and the emulator and the reader must share one
  definition of the native shape, so the definition sits where both may import it, as 2a's format does. A layout as a
  value (not a parser per source) is what makes `3A6` "only transport and profile change" (§7.2). Independence (W2):
  the contract test's goldens and expected records are hand-written, so a shared engine cannot pass its own mistake.

## D-3A3.3 A reader gets the upload's context and may refuse a row

- **Ruling.** `SourceReader.read(data, *, context)` with `ReadContext(tenant_code, received_at)`; `ReadResult.refused`
  maps record indexes to a native code and path. A reader refusal wins over 2a's verdict for that row.
- **Why.** A native export names no tenant and no production time; the uploader's tenant and the receipt time are the
  honest values. A map miss or a short row must be refused with its own words ("this value is not one this layout
  knows") rather than whatever 2a says about a placeholder; letting an unmapped budget line through as a lower-case
  factor would store a heading nobody declared.

## D-3A3.4 What the emulators write

- **Ruling.** October only (the accounting period), mini-grid tenants only (RC5), from the manifest's October `actual`,
  `plan`, `coverage` and tenant `prices`; DS1b's records reused for O&M, staff and its budget lines. Forty customers
  per Site, kWh split evenly with the remainder to the first customers; receipts pay customers in order; fuel in
  400-litre deliveries. Totals must equal the manifest per Site or the emulator stops (`EMU_REVENUE`,
  `EMU_COLLECTIONS`, `EMU_FUEL`). ESTIMATED coverage writes nothing (GAP-1, D-DS1B.7).
- **Why.** The deep-dive month is October and the gate is Kobo's −562.00; history months would need derived figures
  the manifest does not state, so emulating them would invent. Even splits are plain and checkable by hand (W2); the
  replacement rule allows values "derived from the manifest" and nothing a real export lacks.

## D-3A3.5 The contract test admits readers

- **Ruling.** One parametrised suite (C1 to C10) over `CONTRACT_CASES`; `READERS` may hold a reader only when it has a
  case (S2). It checks kinds, required fields, numbers, clocks, the idempotency key (DUP-1, CONF-1), the late month,
  plain-word refusals at file and row level, pseudonymisation and the provenance cap.
- **Why.** §7.3: "a real adapter is admitted only when it passes". Tying registration to a case makes the admission
  mechanical for `3A6` and every later profile, instead of a reviewer's memory.

## D-3A3.6 Emulated loading refuses operator databases (handshake R4 of 3A2)

- **Ruling.** `refuse_operator_database(url)` refuses a database whose name, lower-cased, starts with `assetops_op`, or
  that has no name, before any connection. The loader calls it first; any future non-app caller of
  `build_commercial_uploads` must too (S1's allowlist makes adding one a reviewed change).
- **Why.** RC4: an operator database holds only that operator's real data. 3A2's provenance cap already refuses
  `source-emulated` there, but a loader that fails late has already connected and read the people; refusing by name
  first matches 3A2's broad detection (D-3A2.6) and keeps the rehearsal tooling off real data entirely.

## D-3A3.7 One path per source type per tenant

- **Ruling.** A tenant takes a source type either as DS1b canonical files or as emulated native files, never both; the
  loader refuses a directory holding both for one source type (`EXPORT_PATHS_MIXED`). Across runs, the runbooks keep
  the walkthrough tenants (`DS3`) and the rehearsal tenant (`DDR`) apart.
- **Why.** A record's identity includes its source system (D-3A1.2), and the two paths name different systems, so the
  same O&M line loaded both ways would be two records and the month would count it twice.

## D-3A3.8 The finance lead's list across Sites comes with the upload screen, not now

- **Ruling.** No cross-Site "waiting" read in this fortnight. When the upload list screen is built (next fortnight,
  beside `3C0b`), it adds `uploads_waiting(tenant_id, limit)` over every Site and the organisation for the finance lead
  and the executive.
- **Why.** The deep-dive path has no upload screen (RC7: the owner presents; `3C0b` moved out), and the rehearsal
  submits on the organisation path, which already lists everything it sent. A read with no screen would be reviewed
  twice. Recorded so the screen unit cannot miss it (owner queue Q2).
