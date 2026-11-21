# 0K1 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

**R1 (done). §3 and §4 T1, plant P2.** P2 is "load series matched by position, not `load_id` (request loads
reversed)", but T1 takes its request from `recorded_request`, whose load order is whatever the kernel's measurements
give (very likely already sorted, so the same order as the plant's sorted loads). A positional-match defect would then
pass T1. Expected: T1 (and T2) pass `loads` in reverse sorted order, so a positional match changes the result and P2
fails T1 as the guide says; the guide's P2 row names that explicitly.

**R2 (done). §3 K-RES and its anchor.** "The replay of the same series at reserve 30 has `running_steps > 0`" does not
say whether that is no reserve setting (baseline 30) or `reserve_soc_pct=Fraction(30)` (a forcing of 30). Expected: no
setting, so it also shows the baseline path; and K-RES's own replay (setting 25) is compared with the kernel run whose
baseline is 25, where only the step fields, not `reserve_source`, can match the kernel. State which, and that
`reserve_source == "SETTING"` is asserted from the request, not read from the kernel.

**R3 (done). §6 question 1, §2.3 `REPLAY_MODELS`.** v6 is admitted but no test replays it (T1 runs v5 and v7). A
replay-affecting difference in v6 (the charge-request measurement) would go unproven. Expected: T1 runs v5, v6 and v7,
or `REPLAY_MODELS` drops v6 until a test covers it. Pick one.

**R4. "What it is" and §1 versus §3.** The summary says "four shipped Kobo runs"; §3 has five cases from three shipped
scenarios (prolonged, stop-60, reserve-trial), two of them edited by `document_edit`, and a fourth (overcast) used only
for the reserve pin. Expected: reword to "five cases on three shipped scenarios", so the review counts the right thing.

**R5. §2.5 `fuel_burned_l`.** The tank identity (start - end + increases - decreases) holds only if the tank never
hits its capacity bound mid-run (a refill clipped at 400 L would be spilled and break it). No Kobo case here has a
cause at the tank (`causes` is empty in the print), so the identity is unproven against a refill. Expected: a ruling
that a refill-bearing run is out of 0K1's proof (0K2's concern) and a one-line note in the docstring, not a test.

## Implementer pre-flight questions

Pre-flight run on `main` (`e844e9d18`) through the slot pool: `kobo_draft` then `frozen_world_inputs` on
prolonged v5, stop-60 v5 and overcast (all READY). The addresses, state keys, units, dimensions, `WINDOW`, `REQUIRED`
of the six plant numbers, the load addresses and both override rows match §2.3. Differences below.

**I1 (done). §3 component ids.** The spec says the template's ids are `inverter`, `battery`, `generator`, `fuel-tank`,
`load-res`, `load-clinic`, `load-mill`. The print shows the PV array is `pv-array`, the inverter `pv-inverter`, the PCS
`battery-pcs` (battery, generator, fuel-tank and the three loads are right). So the test reader's
`pv-available-power@inverter` is wrong; I expect `pv-available-power@pv-inverter` (the kernel keys the measurement by
the inverter component, `mini_grid.py:1063`), and the pre-flight must confirm it by printing the boundary's
interval-measurement keys. Expected: §3 fixed to the printed ids; the reader takes the id from the print.

**I2 (done). §2.3 reserve pin versus the overcast run.** `RESERVE_OVERRIDE_FIELDS` is pinned to a row of a
`daytime-mini-grid` run (event `evening-reserve-override`, `%`, `FRACTION`, `WINDOW`, `REQUIRED`), while the override is
applied to `mini-grid` v5 to v7. The fields do match, but T10 proves only that two rows agree; that the mini-grid
models accept the row is proven by T4 alone. Expected: say so (T4 is the acceptance proof; T10 only guards drift), or
pin to the reserve-trial run if it carries a reserve forcing row (it does not in its shipped document; only overcast
does).

**I3 (done). §2.3 stop and reserve windows `[0, duration)`.** `_stop_threshold_at` (`mini_grid.py:358-405`) refuses an
override whose window is not aligned to the step it is read in, and `_reserve_at` reads the window at the step start.
The shipped stop-60 run has one 480-minute window at 5-minute steps and runs, so a whole-interval window is accepted.
Confirm that is the case for a 5-minute step with `duration` 480 and that a request on a 15-minute run (not tested) is
out of scope. Expected: confirmed; T10 keeps the stop-60 anchor.

**I4. §0 test commands.** `tools/run-host-tests.ps1` is documented for `backend/tests/...` files and a host file; the
contracts test is named as run "by the same wrapper". I did not run it. Expected: confirm in the first commit that
`contracts/tests/test_0k1_forward_replay_contract.py` and `backend/tests/test_0k1_replay_port_seam.py` run under it
without a database (the backend conftest routes only Postgres tests); if the wrapper cannot reach `contracts/tests`,
the packet records the interpreter command used instead, and that is not a mid-build question.

**I5. §2.1 `generator_state` not checked at construction.** Consistent with step 9, but the contract test list has no
case for it. Expected: the contract test asserts `ReplayStartState(..., generator_state="RUNNING")` constructs and the
adapter test T6 refuses it, so both halves are pinned.

## Answers (round 1)

All ten answered in `rulings.md` "Handshake answers (round 1)": R1 D-0K1.10, R2 D-0K1.11, R3 D-0K1.12, R4 D-0K1.13,
R5 D-0K1.14, I1 D-0K1.15, I2 D-0K1.16, I3 D-0K1.17, I4 and I5 D-0K1.18. Spec rev 2 and guide rev 2 apply them. No question
is open; coding may start.
