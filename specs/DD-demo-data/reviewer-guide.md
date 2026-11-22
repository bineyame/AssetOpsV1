# DD reviewer guide

For the Reviewer of each DD part, DD1 to DD6. Spec: `spec.md`, rev 2. Rulings: D-DD.1 to D-DD.16 (`spec.md` §9) and
D-DD.17 to D-DD.34 (`rulings.md`). The handshake is answered in `handshake.md`. Each part gets a discovery review (W5:
a new mechanism, a protected seam, money-bearing records). Before any code, read `spec.md` §A, §0, §1, §4.0 and §8,
`rulings.md`, and the part's cards in §7. Put any new question to the Architect in one batch.

## What to check, every part

1. **The seam.**
   - No generator module reads `oracle` (C-DD12), and no product code reads the manifest.
   - Every write into a world goes through a product command run as a subprocess (D-DS4.3).
   - `tools/dd_check.py` shares no module, list or expected figure with the generators (grep its imports).
   - The private parameters of cold-thermal 2 (load terms, `f_m`) and the declared tank draw never reach a Foundation
     property or a product table.
2. **One figure per quantity, loyal to the operating world** (the class rule, `rulings.md` head; `spec.md` §4.0).
   - Inputs are scaled to the books or manifest. Outputs (generator state, litres, tank level, SOC, chamber
     temperature, meter kWh, charger power, band kWh, departures met) are never scaled, clipped or tuned. Search the
     writer for any rescale of an output series or any parameter derived from a target output; one is **High**.
   - Measured books (cold bill, EV invoice, departure log) are written from `measured.json` only.
   - Decided books are never read back from readings.
   - `p_m` and `f_m` are taken as declared, never solved for.
3. **Labels.**
   - Books read *Emulated*; readings read SIMULATED / "Simulated".
   - A MANUFACTURER_DATASHEET basis reads "Declared, from the manufacturer data sheet (…)".
   - DATASHEET_FIT and GENERIC_DEFAULT bases read "Assumed: …" with their basis.
   - No path can make any of them read *Recorded*, and no unpublished value reads Declared.
4. **Range rule.** The same span (1 Jul to 6 Nov 06:00 local) and one cadence per signal family at every Site of a
   type; no evidence-window-only days. A "No monthly figures yet" row or a 31-day window is not output (D-DD.26).
5. **Each check can fail.** For every C-DD check the part makes live, the packet shows a plant that fails it: a
   one-line edit, then reverted. Examples:
   - drop one Site-day's readings (C-DD5);
   - shift Thika's failure by an hour (C-DD6);
   - add 1 kWh to one bill row (C-DD7);
   - add 1 L/h to Kobo's no-load rate (C-DD8, C-DD17);
   - read `oracle` in the writer (C-DD12);
   - change one v9 rounding (C-DD19);
   - set Kirinyaga's `f_m` to 1 for September (C-DD20).
6. **Copy.** The only new strings are DD1.1's refusal sentence (in `onboard_operator._SENTENCES`) and the
   `component_property.basis` statement (SC-1).
7. **Guards and machine.** Test databases only (`*_test`, `<prefix>_audit*`); heavy work in the slot pool; no port
   5490, 8990 or 8992; evidence outside the tree; scratch deleted.

## Per part

- **DD1.**
  - `/1` onboarding files digest byte for byte as before. The three verticals map to MINIGRID, COLDCHAIN and
    EV_CHARGING; anything else refuses.
  - `valid_from` is 2026-06-30T21:00:00Z everywhere.
  - After an emulated apply, each of the nine Sites has `edge-<code>` **enabled**, its sources enabled and one
    published binding set. A second apply changes nothing.
  - The (person, role, Site) triples match `demo_workflow`.
  - C-DD1 and C-DD13 are live, and the checker pins `history.json` by its golden sha256.
- **DD2.**
  - History months come from `history.json` leaves and October from `period`; the totals stop the emulator on any
    miss.
  - Mini-grid billed kWh, revenue, collected, litres and fuel cost, and cold revenue and received, are the structure's
    nodes evaluated on the month's leaves (D-DD.48, D-DD.50). The node table matches `M` by a parity test, October's
    evaluated nodes equal `period`'s (`EMU_NODE`, with a plant), and no exporter reads a node field such as
    `s.a["billed_kwh"]`.
  - Cold and EV budgets are the two budget profiles. `contracts/` is untouched outside DD2.2, and no cold or EV
    expense row is ENERGY or PENALTY (D-DD.49).
  - Kobo's October notes are 400 L on 26 Oct, 400 L on 1 Oct and 380 L on 8 Oct (D-DD.53).
  - Every DS1b record lands in exactly one exported file, one staged JSON or `unwritten.json` (D-DD.54).
  - C-DD4's node clause uses the checker's own evaluator, which shares no code with the exporter (D-DD.55).
  - The `bool` type has its four contract tests, and a map on any other non-coded path still refuses.
  - Each profile's columns match `spec.md` §5.2 and §5.3 exactly, pass `run_probes` on the sample, and are admitted
    with `--expected` and `--as`.
  - No ENERGY expense line exists for cold or EV.
  - Statements are sums of emitted rows, never typed.
  - C-DD2 to C-DD4 are live.
- **DD3.**
  - Determinism holds across processes (C-DD11), and readings files carry no UUID.
  - Kobo's `/2` values equal §6's table (36, 0.2917, 0.62 or the owner's Q7 answer, 30, 191.5, 95) with their `-basis`
    values. The tool's residuals are printed.
  - The pure run of D-DD.19 is in the packet with Kobo at both no-load values, and commit 2 follows the Q7 relay.
  - Every regenerated figure is listed, and none is hand-edited.
  - Template v3 is untouched.
  - v9 with one unit each equals v8 byte for byte on Kobo's October.
  - Kisiwa's and Mto's failures act on their own units.
  - C-DD8 (pure), C-DD11, C-DD12, C-DD16, C-DD17 (pure) and C-DD19 (mini) are live.
- **DD4.**
  - cold-thermal 2 with zero terms equals v1 byte for byte.
  - The load parameters, `f_m` and ambient are exactly §4.4's.
  - The depot load manager uses the pack's round-robin across chargers, and `p_m` is as declared.
  - Bills, invoices and departures equal the meters exactly (C-DD7).
  - Every C-DD20 direction holds, or the packet stops for the Architect.
  - C-DD5 to C-DD7, C-DD19 (cold) and C-DD20 are live.
- **DD5.**
  - Cold and EV parity tests pass before `BULK_SITE_TYPE_UNPROVEN` is lifted, in the same commit.
  - The sealed batches are written for C6.
  - Each disorder test runs as §5.5's table says.
  - `/1` definitions still read and build as before.
  - The inputs digest covers every input file.
  - C-DD8 (store) and C-DD14 are live.
- **DD6.**
  - C8 runs the checker.
  - WK `prepare` makes choices and Actions only through commands, and lists the pending ones.
  - WK serves one tenant and switches by PID.
  - Rung seconds, and cold and EV seconds per Site-day, are in the packet beside the 4.4 h projection. Past 8 h the
    build stops (D-DD.15).
  - The pending C-DD9 cells are listed with their units (Q11, Q12).
  - C-DD18 is answered per tenant.

## Done means

Every question of `spec.md` §10 is answered yes with evidence by path. On DD6's first build, §10 Q2 and Q7 may instead
list their pending cells with the unit that closes each. Every plant is shown failing. The mid-build question count is
0; a count above zero is a spec defect, so report it.
