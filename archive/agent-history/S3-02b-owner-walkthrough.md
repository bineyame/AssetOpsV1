# S3-02b owner walkthrough: what a selected assessment can support (Evidence > Analysis)

You will look at one new section on the Evidence > Analysis page: **"What the selected assessment can support"**. It sits under the existing "How each limit is set" panel. It answers, for one assessed generator run, what the accepted readings allow us to say, and where the readings fall short.

Everything runs on a private copy of the database that the tool creates and deletes. About 15 minutes.

## 1. Prepare (one PowerShell window)

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
.\.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 prepare
```

Takes about a minute. It must end with `Prepared. Next: serve.` and show `evidence: exit 0` and `performance: exit 0` (the two comparisons that release the data) and six `ok` lines.

## 2. Start the two servers

Window 1 (same window as above):

```powershell
.\.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 serve
```

It prints the links you will open (keep this window open; it is the API on port 8932).

Window 2 (a new PowerShell):

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend
$env:ASSETOPS_API_PORT="8932"; npm.cmd run dev -- --port 5442 --strictPort
```

## 3. What to open and what to look for

Open the links window 1 printed (they start with `http://localhost:5442/sites/KOBO-001/evidence?view=analysis`). Scroll to "What the selected assessment can support".

1. **No assessment selected** (first link). The section is there and says "No assessment selected"; nothing is concluded.
2. **Day chosen, no assessment selected**. The day's assessed periods appear as links ("Whole day", "08:00–08:30 UTC"). Using only the keyboard, press Tab until "08:00–08:30 UTC" is highlighted and press Enter. The address now carries `&revision=...` and the section fills in.
3. **Full coverage**. Badge "Current assessment"; the bold sentence says the generator run can be called avoidable for 30 min, with every reading present. The table lists the five readings the conclusion needs, each "30 min of 30 min". Open "7 readings" on any row and click "Reading 1": the reading's detail opens at the top of the page. Reload the browser: the same reading and the same assessment are still shown. Press Back: you return to the assessment.
4. **Missing solar reading**. The sentence says the readings cannot support a conclusion; "Solar power available" shows the missing period.
5. **Unreliable and conflicting readings**. "At most 5 min"; "What limits it" names the unreliable battery readings (08:05–08:20) and conflicting solar reports (08:20–08:30).
6. **Earlier version after a late reading**. Grey badge "Earlier version · audit only"; no current conclusion, only what that version said at the time.
7. **Out of date, being redone**. Grey badge "Out of date · being redone"; no current conclusion.
8. **Refused: revision from another day**. The section says the assessment belongs to a different day and shows nothing else.
9. On any filled-in case, "Technical details — rule, versions and record IDs" is closed. Open it: the rule, IDs, run, cohort and time watermarks are there, not in the main reading.
10. "Open this assessment in Performance › Dispatch" opens the same assessment on the Dispatch page.

**Narrow screen**: make the browser window phone-narrow (or DevTools device mode at 390 px wide). Nothing should run off the right edge; the readings table scrolls sideways inside its own box.

**Mock comparison**: open `frontend\mockups\v69\index.html#/evidence-analysis` in the browser. Its "How a claim limit is set" panel is the model for this section's opening paragraph and plain wording. The app has more here because it shows a real selected assessment.

## 4. A late reading withdraws the current conclusion

Keep the full-coverage link open. In a third PowerShell:

```powershell
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
.\.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 late
```

Reload the full-coverage page. It now says "Out of date · being redone", with no current conclusion; the earlier statement is shown only as "At the time, this version said: ...".

## 5. Stop and clean up

Press Ctrl+C in windows 1 and 2. Then:

```powershell
.\.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 attest
.\.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py --db assetops_s302_owner1 --work var/s302_owner1 drop
```

`attest` must print `ATTEST PASSED`. `drop` deletes the private database and the `var\s302_owner1` folder.

## What to decide

Accept, or name what to change. The wording is not final: the W1-conclusion task will polish it. Please flag anything that reads as wrong or misleading.

## Optional: repeat the measurements

With both servers running, in a third PowerShell at the worktree root:

```powershell
node tools\s302-claim-limit-evidence.mjs http://localhost:5442 var/s302_owner1 var\s302_owner1\shots
```

It must end with `EVIDENCE PASSED`.
