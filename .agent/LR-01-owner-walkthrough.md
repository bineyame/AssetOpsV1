# LR-01 owner walkthrough: late reading, series limit and the money limit

Merge checkpoint for `tasks/LR-01-late-reading-series-and-money-limit.md` (USER_REVIEW_REQUIRED). Everything runs in a
private database (`assetops_lr01_owner`) and its own folder (`%LOCALAPPDATA%\AssetOps\assetops_lr01_owner`, the
same root the tool already uses). No schedule is installed: each "tick" below is one explicit command. Run the
commands from the repository root in PowerShell, on the branch `task/LR-01-late-reading-series-and-money-limit`.

The demonstration data is the authored late-power case (`s4-power-late-demo-cases-v1`): a generator ran
06:05-08:00 on 2026-10-24 with one 5-minute reading (07:00-07:05) delivered late. Clock proof is a labelled
**simulated** attestation recorded by the system only; it is not proof for a real source.

## 1. Run 1 withheld (about 5 minutes)

```powershell
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py run --db assetops_lr01_owner
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py serve --db assetops_lr01_owner --api-port 8921 --web-port 5421
```

The `run` delivers the readings, accepts the late one numbered on arrival (how this project's gateway numbers a
late reading), ticks once, runs the Performance comparison that opens the source gate, and ends with
`0 failed checks`. The `serve` command prints the links below with the real IDs. In a second window:

```powershell
cd frontend; $env:ASSETOPS_API_PORT="8921"; npm.cmd run dev -- --port 5421 --strictPort
```

Open `http://localhost:5421/sites/KOBO-001/financials?finding_id=<finding id from serve>`. Look for:

- Cost: **"Withheld: the generator records are not in a proven time order"**, and no amount at the top.
- One list item (one per refused span and kind, even when the selected window repeats it): "The order of generator records from 2026-10-24 07:05 UTC to 2026-10-24 08:00 UTC is not proven: they
  arrived before an earlier reading and their clock is not proven. The finding ends before them and that time is not judged."
  (The span is the unordered block, not the late reading itself, which is the 07:00-07:05 mean.)
- The link "Open the recorded fuel cost of this finding version". It opens fuel cost version 1, **0.00 to 7.57
  USD**, marked "kept for the record". Nothing on the page is called the current fuel cost.
- The Finding page (`/sites/KOBO-001/findings/<finding id>`), under "What limits this conclusion": "This finding
  ends at 2026-10-24 07:00 UTC because the generator records after that could not be put in a proven time order".

This is also the "simulated data without attestation stays limited" case: nothing orders these readings until a
clock attestation is recorded.

## 2. Record the simulated clock attestation, then see "being reassessed"

Leave both servers running. In a third window:

```powershell
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py attest --db assetops_lr01_owner
```

Reload Financials. Look for: **"Being reassessed: no current cost yet"**, the reassessment sentence, still no
amount, and the same "Open the recorded fuel cost" link to the same 7.57 USD version.

## 3. Tick, then see the full episode and the current cost

```powershell
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py tick --db assetops_lr01_owner
```

Reload Financials. Look for:

- The headline **"Modelled potential fuel-cost exposure" 0.00 to 15.82 USD**, with the finding now 06:05 to 08:00.
- The **"Demonstration data"** label and its statement beside the finding (P02-power-late, same wording as the
  earlier demonstration case). It is absent in the withheld state only if the page hides it for withheld money; if it is
  missing here, report it.
- A new finding version and a new fuel cost version (new IDs).
- The Finding page no longer has the "ends at 07:00" sentence.
- The earlier 7.57 USD record is still there: use the finding's version history to open the earlier version
  (`...financials?finding_id=<id>&revision_id=<withheld revision>&consequence_revision_id=<recorded consequence>`;
  `serve` prints this link once you restart it). It reads "Earlier finding version: kept for the record".

## 4. The on-time-numbered variant

Stop both servers (Ctrl+C), then:

```powershell
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py run --db assetops_lr01_owner_ontime --variant on-time
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py serve --db assetops_lr01_owner_ontime --api-port 8921 --web-port 5421
```

Restart the frontend command from step 1. Financials shows 0.00 to 15.82 USD directly, with the same "Demonstration data" label: the reading was numbered when
taken and the clock attestation covers it.

## 5. Clean up

```powershell
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py drop --db assetops_lr01_owner
.venv\Scripts\python.exe tools\s402c_late_power_walkthrough.py drop --db assetops_lr01_owner_ontime
```

Notes: money is judged on the Financials bridge; the Finding page shows only the series-limit statement and its
evidence link. Residual risk: a generator refusal in a neighbouring bracket day can withhold a Finding it does not
touch (fail closed) until that refusal is resolved.

`serve`, `attest` and `tick` refuse any database not named `assetops_lr01*`. Screenshots of every state at
1440 and 390 px are in `.agent/LR-01-browser-evidence/`.
