# S6-03 owner walkthrough - Site Work, Actions list (`sitework:1#a`)

What you are accepting: a new **Work** tab on a Site. Its **Actions** list shows the Actions created at this Site in
the days you choose (at most 31), newest first. Each row opens the Action, the exact Finding version it came from,
and the exact latest recorded step. A window with no Actions says so plainly. If the list cannot be read, or it
changed while you were paging, it says that instead and never shows an empty list. No owner, due date, priority or
"verified" verdict is shown: the system does not record them yet. Incidents and Maintenance are not built.

Wording and visual polish are not part of this check (they are batched into the W1-conclusion copy task). Look at
whether the right things are shown and nothing is invented.

Everything runs in its own private database and folder. Ports: API **8963**, web **5463**.

## 1. Prepare (about 1-2 minutes)

PowerShell window 1:

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review4
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 prepare
```

It should end with `Performance cutover: permitted` and `Prepared.` Then check the data independently:

```powershell
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 attest
```

It prints both windows and ends with `ATTEST OK` (the list's count equals a direct database count: 2 and 0).

## 2. Start the servers

Window 1 (leave it open):

```powershell
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 serve
```

PowerShell window 2:

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review4\frontend
$env:ASSETOPS_API_PORT="8963"; npm.cmd run dev -- --port 5463 --strictPort
```

`serve` prints the exact addresses. They are (the dates come from the stored Actions):

| What | Address |
| --- | --- |
| Positive window (1 Nov 2026) | http://localhost:5463/sites/KOBO-001/work?from=2026-11-01T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z |
| Same, one per page | the address above plus `&limit=1` |
| Empty window (1-31 Oct 2026) | http://localhost:5463/sites/KOBO-001/work?from=2026-10-01T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z |
| No window chosen | http://localhost:5463/sites/KOBO-001/work |

## 3. What to look for

1. **Positive window.** Tab row shows Work selected, then an "Actions" sub-tab. The line under the date picker reads
   "Scoped to Kobo mini-grid · 2 Actions created 1 Nov 2026 to 1 Nov 2026". The table "Actions at this site" has two
   rows, newest first: ACT-000002 (created 00:05, "Accepted · not applied (1 failed attempt)", latest step "Apply
   attempt failed") and ACT-000001 (created 00:00, "Applied · result not checked yet", latest step "Applied to the site
   setup"). No Owner, Due or Verified column. Compare with the mockup screen Site Work
   (`frontend/mockups/v69/index.html#/sitework`): same layout; Owner, Due and Success criterion are left out on purpose.
2. **Links.** Click "Finding, version N": the Finding opens at that exact version. Go back. Click the latest-step
   link: the Action history opens at exactly that step. Go back. Click the Action code: the Action page opens.
3. **Reload.** Press F5: the same two rows come back. Open "What this list is based on": read time, window,
   latest creation and step times, counts ("2 Actions, N recorded steps"), and the record IDs (Action, Finding
   version, step) are here, not in the main reading.
4. **Empty window.** "No Actions created at this site in this window". The basis shows "0 Actions, 0 recorded steps
   (an explicit zero)". The window ends exactly where the first Action was created, so it is a real, checked zero.
5. **No window.** "Choose a window": nothing is listed. Pick 1 Nov 2026 to 1 Nov 2026 and press Show Actions: the
   address gains the dates and the two rows appear. Keyboard: Tab reaches the date fields, the button and every link.
6. **A changed list.** Open the one-per-page address and copy the "Next page" link address (right-click, copy link),
   but do not open it. In PowerShell window 3, record a new step on ACT-000002 (an apply attempt; on today's clock it
   fails and is recorded as a failed attempt):

   ```powershell
   cd C:\Users\assef\Bineyame\AssetOpsV1-review4
   $w = Get-Content var\s603_owner1\walkthrough.json | ConvertFrom-Json
   $a = $w.actions[0].id
   $d = Invoke-RestMethod "http://127.0.0.1:8963/api/sites/KOBO-001/actions/$a"
   $body = @{ expected_foundation_revision_id = $d.application_basis.current_foundation_revision_id; value = "15"; effective_from = "2026-11-02T00:00:00+00:00"; idempotency_key = "owner-step-$(Get-Random)" } | ConvertTo-Json
   try { Invoke-RestMethod -Method Post -ContentType "application/json" -Body $body "http://127.0.0.1:8963/api/sites/KOBO-001/actions/$a/apply" } catch { $_.ErrorDetails.Message }
   ```

   The reply is a refusal that names a FAILED event: that is expected. Now paste the copied "Next page" address:
   the page says "This list changed" with no rows and no count. "Start again from the first page" reloads page one.
7. **Narrow screen.** Make the browser about phone width (390 px, or the browser's device toolbar): the table
   scrolls sideways inside its box; the page itself does not.

## 4. Finish

Stop both servers (Ctrl+C in windows 1 and 2), then:

```powershell
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py --db assetops_s603_owner1 --work var/s603_owner1 drop
```

It prints `dropped database assetops_s603_owner1` and `removed ...var\s603_owner1`.

Screenshots of every step at 1440 and 390 px, with the mockup, were taken by `tools/s603-site-work-evidence.mjs`
during the build (56/56 claims); see the review packet.
