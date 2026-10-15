# S5-01 owner walkthrough - selected-day Site Overview

What you are accepting: Site > Overview for an imported Site (KOBO-001) now shows **one UTC day**: whether the day was
assessed, its operating objective, a day timeline, the accepted readings, and at most **one** Finding's potential
fuel-cost exposure. An amount appears only when every gate passes. Every other case names why there is no amount.
The day and the selected Finding version stay in the address, so a reload shows the same thing.

Packet: `tasks/S5-01-site-overview.md`. Review packet: `.agent/S5-01-review-packet.md`. Merge is held until you
record acceptance or feedback below.

## Setup (once, about 6 minutes)

From the repository root (PowerShell). The tool uses only its own database and folder, and refuses any other.

```powershell
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py prepare --db assetops_s501_owner --work var/s501_owner
```

It ends with `prepare finished ... with 0 failed checks`. If any day does not read as expected, it stops with
exit 1 and lists the failed checks instead of promising an amount that is not there.

Terminal 1 (keep it open):

```powershell
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py serve --db assetops_s501_owner --work var/s501_owner
```

Terminal 2 (keep it open), from `frontend\`:

```powershell
$env:ASSETOPS_API_PORT="8925"; npm.cmd run dev -- --port 5425 --strictPort
```

Terminal 3 runs the step commands below.

**Five-minute rule.** No schedule is installed on this machine; the tool runs one schedule pass when you ask it to
(`tick`). The product treats a schedule with no pass in the last 5 minutes as **stopped** and then shows no amount
anywhere (this is the real production threshold, not a demo setting). If an amount you expect is missing and the
"This day" panel says "Out of date" with `SCHEDULE_STOPPED`, run the tick command and reload.

The exact tick command (Terminal 3):

```powershell
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py tick --db assetops_s501_owner --work var/s501_owner
```

- Run it **right before steps 1 and 4**, and before any other step that expects "Current" or an amount (step 5 too).
- **Never tick between `attest` (step 6) and the reload of P02 and P01 in steps 6 and 7.** A tick there settles the
  reassessment and hides the "Pending reassessment" state you are meant to see. Tick only at step 8. If the last tick is over 5 minutes old when you reach step 6, tick *before* running `attest`, not after.
- If more than 5 minutes pass between a tick and the step you are on, tick again, except as above.

## Steps

| # | Do | What you should see |
| --- | --- | --- |
| 1 | **Tick first.** Open `http://localhost:5425/sites/KOBO-001?date=2026-10-02` | Ordinary gateway day. "This day: Current". Money card: **No current amount**, "Fuel quantity unavailable". Findings: one Finding link; "Unavailable until the Site Finding index is delivered." |
| 2 | Open `?date=2026-11-10` | Nothing was delivered for this day. "This day: **Unknown**"; objective "Unknown"; no amount ("Day not assessed"). |
| 3 | Open `?date=2026-10-07` | A deliberately failed assessment. "This day: **Failed**"; objective "Reassessment failed"; no amount ("Upstream failed"). |
| 4 | **Tick first**, then open `?date=2026-10-23` (P01) | Blue "Demonstration data" note, then **0.00 to 15.82 USD**, "Current amount", money gate "Eligible". The address gains `finding_id` and `finding_revision_id`. Links: "Fuel cost for this Finding version" opens Financials pinned to the exact fuel-cost version; price assumption, assessment and record links open the exact versions. |
| 5 | Open `?date=2026-10-24` (P02) (within 5 minutes of the step 4 tick, else tick again) | A late generator reading was accepted. **No current amount**, "Withheld: generator power series"; money gate "Withheld: generator power series". Note the Finding version in the address. |
| 6 | Terminal 3: `.venv\Scripts\python.exe tools\s5_overview_walkthrough.py attest --db assetops_s501_owner --work var/s501_owner` then reload P02 immediately; **do not tick** | Same Finding, same version in the address, **no amount**. Two separate facts are shown, on purpose: the card's state is **"Upstream out of date"** (the attestation queued a reassessment of the day, so the day's assessment is now out of date), while the line "Money gate" says **"Pending reassessment"**. The upstream state is checked first, so it is the one the card names. |
| 7 | Reload P01 (`?date=2026-10-23`) now; still **do not tick** | P01 may also show **no amount** ("Upstream out of date") until the next tick. This is expected and safe: P02's day falls inside the six-hour range P01's day depends on, so the pending reassessment there briefly blocks P01's amount too (it fails closed rather than showing a figure on an unsettled basis). |
| 8 | Run the tick command (the first tick since `attest`), reload P02 | Money gate "Eligible", **0.00 to 15.82 USD**, a **new** Finding version in the address and a new fuel-cost version in the link, and the "Demonstration data" note (P02 is authored demonstration data too). P01 shows its amount again. |
| 9 | `... stop-schedule --db assetops_s501_owner --work var/s501_owner`, reload P02 | No amount, "Upstream out of date"; open "Why, and the exact read basis": `SCHEDULE_STOPPED`. The money gate still says "Eligible": the stopped schedule blocks the amount separately. |
| 10 | `... gate --close --db assetops_s501_owner --work var/s501_owner`, reload P02 | "The Performance source is closed"; objective "Closed"; money **"Source closed"**, no amount; the Finding version from the address is kept, marked "kept for audit; not current". |
| 11 | `... gate --open ...`, then `... start-schedule ...`, then `... tick ...`, reload P02 | Back to the current amount (step 8), only after every gate has settled. |
| 12 | Press **Next day** (or pick another date) and reload | The address keeps the new date; the old Finding pin is dropped, because it belongs to another day. |

Unsupported v6.9 `mini` panels (Site totals, savings, battery or service health, fuel balance, renewable
opportunity, recommendations) are **absent** by design: there is no source for them yet.

## Evidence already captured

`.agent/S5-01-evidence/` (claims per stage and the step log with API IDs/watermarks) and, on the implementer's
machine, `var/s501-evidence/` (screenshots at 1440 and 390 px), from
`node tools/s5-overview-evidence.mjs http://localhost:5425 <initial|pending|eligible|stopped|closed> var/s501-evidence [finding-id revision-id]`.
The review packet lists the claim counts and the API IDs/watermarks.

## Clean up

```powershell
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py drop --db assetops_s501_owner --work var/s501_owner
```

## Owner record

- Date:
- Accepted / feedback:
