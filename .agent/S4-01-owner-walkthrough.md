# S4-01 owner walkthrough: the generator-support Finding

What you will see: AssetOps opening a Finding when the generator stayed on while solar power and the battery
reported enough capacity for the site's demand, keeping the same Finding as later records arrive, and saying
plainly when the conclusion is limited, out of date, not confirmed or no longer supported.

## What this is, and what it is not

- The records are demonstration data for the Kobo mini-grid (KOBO-001), not field evidence. Each Finding's
  "Records behind this version" panel says which kind:
  - **Ordinary gateway path** (2 Oct): records sealed by the site's registered gateway and delivered the
    normal way. This day still used the site template's positive minimum generator on-time; from 3 Oct the
    prepared test cases set that minimum to zero. The two bases are kept separate.
  - **Prepared test cases** (6 to 21 Oct): records sent with the gateway's own credential to create
    situations on purpose, such as late records, gaps and stops. This is not the ordinary delivery path.
- Access is the pilot's development access. Nobody signs in yet; the refusals for "sign in" and "no access" are
  tested in code but not live.
- No fuel, money, recommendation or Action is shown. Those panels say "Not yet available". The full History and
  Evidence tabs and the Site's Findings list come in later slices (S4-02 to S4-04, S6).
- Rule upgrade (F07) was proven with a test-only rule version. There is no reviewed later rule, so no live
  upgraded Finding exists.
- A short stop (20 minutes or less) joins two parts into one Finding only when the generator reported off at
  both ends and nothing contrary arrived in between. If few reports arrive during a stop, that joining rests on
  the two off reports. The page says so where it applies (2026-10-08/09).

## Start (about 6 minutes, nothing on your usual servers is touched)

From the repository root, in PowerShell:

```
.venv\Scripts\python.exe tools\s4_finding_cases.py run          # about 4 minutes; ends with VERIFY PASSED
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py prepare
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py links    # prints the addresses below with this run's IDs
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py serve    # leave open; Ctrl+C stops it
```

In a second window, from `frontend\`:

```
$env:ASSETOPS_API_PORT="8840"; npm.cmd run dev -- --port 5340 --strictPort
```

Uses its own database (`assetops_s4walk`, a copy of the fixture output) and ports 8840 and 5340. The
walkthrough also marks 9 Oct as waiting for reassessment, so you can see an "Out of date" Finding.
`tools\s4_finding_walkthrough.py recover` clears that.

## Steps (use the addresses `links` printed)

1. **Open Finding (F01).** You should see the heading "Generator support merits review", the status "Open" and "Up to date", and the
   cards "Possibly avoidable 45 min", "Needed 15 min" and "Cannot determine 0 min". The coloured bar shows each
   block. Select a block with the mouse, or Tab to it and press Enter. Its times appear with "See this block on
   the Dispatch day". Reload, and the same block is still selected. "Where to look next" links the Dispatch day;
   the Dispatch day links back under "Findings".
2. **Same Finding after a late earlier record (F04).** Open the latest version, then the "version 1" address.
   The address keeps `?revision_id=`. Version 1 is labelled "Earlier version 1 of 3" and links to the latest
   version. Both versions have the same Finding address; only the version differs.
3. **Repeat after a recorded stop (F03 recurrence).** "What limits this conclusion" says this happened before,
   links the earlier Finding, and says the link does not mean the earlier one is still open.
4. **Not confirmed, then no longer supported (F05).** The version 2 address (`links` prints every version) reads "Not confirmed". It says no records are missing;
   it could not decide because the generator may be within the configured minimum runtime (it cites the 20 % battery
   reserve), and that this is not a new issue. The latest version reads "No longer supported". It says
   this does not mean the generator was repaired or that money was saved.
5. **Out of date (F02, across midnight 8 to 9 Oct).** The status reads "Out of date" and the recorded version
   stays visible. It reads "ran between ... with one short stop", links both Dispatch days and names the stop.
6. **Joined Findings (F06 merged).** The joined Finding leads with "Joined into an earlier Finding" and links
   the one that now carries the review. Its own versions still open.
7. **One record's lineage.** On any Finding open **Analysis**. It lists every cited record with its delivery
   batch, gateway, source and sequence, the assessment revisions and passes used, the site settings revisions,
   and every version's ID. On the Dispatch day, select the same block to see the same records.
8. **Days without a Finding.** Use the three Dispatch day addresses `links` prints. 19 Oct reads "could not decide, so this is not a no-Finding result".
   7 Oct reads "No assessment exists for this day". The fixture has no fully assessed day with no Finding; the
   tests cover that wording ("fully assessed and has no Finding").

## Mock comparison

`node tools/s4-finding-evidence.mjs http://localhost:5340 <folder>` (with both servers running) captures the
v6.9 mock `#/finding` and the app at 1440 and 390 pixels. It checks interaction and reload, and prints 36
measured claims. Last run: 36/36. The screenshots are in `%LOCALAPPDATA%\AssetOps\s4-finding-walkthrough\evidence`.

| Mock `finding` | App |
| --- | --- |
| What happened: sentence, segment bar, metric cards | Same, with the measured minutes; the fuel/cost card says "Not yet available" |
| What limits this conclusion | Record gaps, joined stops, repeat links, access basis |
| What to do next (recommendation, ACT link) | "Not yet available" (S6) |
| Where to look next: Analysis, Evidence, Alternatives, linked action | Dispatch days, accepted records, related Findings; History, money and actions not yet available |
| Priority, Confidence and Lens chips | State, up-to-date check, version, period (no priority or confidence score is computed) |
| Tabs Overview, Analysis, Evidence, Alternatives, Recommendation, History | Overview and Analysis; versions listed on the page |

Stop: Ctrl+C in both windows.
