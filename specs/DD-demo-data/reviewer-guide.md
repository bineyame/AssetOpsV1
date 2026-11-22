# DD reviewer guide

For the Reviewer of each DD part (DD1 to DD4). Spec: `spec.md` (rev 1). Rulings D-DD.1 to D-DD.16 (`spec.md` §9).
Discovery review per part (W5: a new mechanism, a protected seam, money-bearing records). Before any code: read `spec.md`
§A, §0, §1, §8 and the part's cards in §7, and put every question to the Architect in one batch (the handshake, with
the Implementer's pre-flight; answers go to `rulings.md` in this folder).

## What to check, every part

1. **The seam.** No generator module reads `oracle` (C-DD12). No product code reads the manifest. Every write into a
   world goes through a product command run as a subprocess (D-DS4.3). The checker `tools/dd_check.py` shares no
   module, list or expected figure with the generator (grep its imports).
2. **One figure, loyal to the operating world.** Inputs are scaled to manifest totals; outputs (generator state,
   litres, SOC, chamber temperature, charger power) are never scaled, clipped or tuned. Search the writer for any
   rescale of an output series; one is High.
3. **Labels.** Books *Emulated*, readings SIMULATED / "Simulated", data-sheet values "Declared, from the manufacturer
   data sheet (...)", assumed values "Assumed" with basis. No path can make any of them read *Recorded*.
4. **Range rule.** Same span (1 Jul to 6 Nov 06:00) and one cadence per signal family at every Site of a type; no
   evidence-window-only days.
5. **Each check can fail.** For every C-DD check the part makes live, the packet shows a plant that fails it (a one-line
   edit, reverted): e.g. drop one Site-day's readings (C-DD5), shift Thika's failed start by an hour (C-DD6), scale an EV
   session (C-DD7), add 1 L/h to the no-load rate so Kobo's balance turns (C-DD8), read `oracle` in the writer (C-DD12).
6. **Copy.** Only DD1.1's refusal message and the DATASHEET label are new strings, both through the SC-1 catalogue.
7. **Guards and machine.** Test DBs only (`*_test`, `<prefix>_audit*`); heavy work in the slot pool; no port 5490, 8990,
   8992; evidence outside the tree; scratch deleted.

## Per part

- **DD1.** `/1` onboarding files digest byte for byte as before. Three verticals map to MINIGRID, COLDCHAIN,
  EV_CHARGING; anything else refuses. After an emulated apply each of the nine Sites has `edge-<code>`, its sources and
  one published binding set; a second apply publishes nothing. 21 people, one executive, finance lead and analyst per
  operator. C-DD1 and C-DD13 live.
- **DD2.** History months come from `history.json` leaves, October from `period`; totals stop the emulator on any miss.
  Each new profile passes `run_probes` on its sample and is admitted by command. Statements are sums of emitted rows,
  never typed. Eight disorder tests planted and listed. C-DD2 to C-DD4, C-DD14 live.
- **DD3.** Determinism across processes (C-DD11). Readings files carry no UUID. Kobo's template v4 values equal
  `spec.md` §6's table exactly (36, 0.2917, 0.62, 30 Assumed, 191.5, 95 Assumed); the tool's residuals printed; the
  fingerprint pin moved; the manifest's Kobo `physical` changed with derived moves listed, none hand-edited. Cold and
  EV parity tests pass before `BULK_SITE_TYPE_UNPROVEN` is lifted, in the same commit. C-DD5 to C-DD8, C-DD16 live.
- **DD4.** `/1` definitions still read as before (the old world builds). `snapshot_months` governs L2 per tenant. C8
  runs the checker. WK serves one tenant, switch by PID. The build's seconds per rung are in the packet beside the 4.4 h
  projection; past 8 h the build stops (D-DD.15).

## Done means

Every question of `spec.md` §10 answered yes with evidence by path; every plant shown failing; mid-build question count
0 (a count above zero is a spec defect: report it).
