# S4-03 owner walkthrough: a Finding's Evidence and History

This walkthrough shows three things. You can open the records one exact version of a Finding cites, and follow one record to its stored original message. You can list every version of the Finding and see how a late reading added a new version without changing the old one. You can go back to an old version's evidence after a reload.

## What this is, and what it is not

- **The data is demonstration data for KOBO-001.** It is the same S4-01 fixture. The 2 Oct Finding came the ordinary way, through the site's registered gateway. The 6-21 Oct Findings come from prepared test cases. Evidence labels this "Kind of data" and adds a note supplied with the demonstration data.
- **Nothing here changes a Finding.** Evidence and History only read stored versions.
- **History does not let you view the Finding "as of" an earlier moment.** It shows each version exactly as it was recorded.
- **Not shown:**
  - Recommendations, Actions and money (S4-02, S6).
  - The mock's "Alternatives" and "Recommendation" tabs.
  - The mock's "Recommendation prepared" history row.
- **Two parts of the Evidence measurement summary say "not available yet".** They are Coverage and Use.
- **Development access only.** The sign-in and no-access refusals are covered by tests, not by this walkthrough.

## Start

Run these from the repository root in PowerShell. They use their own database and folder, so your usual servers are untouched. The first step needs the S4-01 producer output (`tools\s4_finding_cases.py run`, about 4 minutes). Skip it if `%LOCALAPPDATA%\AssetOps\s4-finding-cases\s4-finding-cases-run.json` already exists.

```
$db = "assetops_s403_owner_walk"; $work = "$env:TEMP\s403-owner-walk"
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db --work $work prepare
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db --work $work links --web-port 5366
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db --work $work serve --port 8866 --web-port 5366   # leave open
```

`prepare` refuses a work folder that already exists and that it did not create. If that happens, pick a new folder name.

In a second window, from `frontend\`:

```
$env:ASSETOPS_API_PORT="8866"; npm.cmd run dev -- --port 5366 --strictPort
```

To show the "assessments not released" states (step 6), use a second copy on ports 8867 and 5367:

```
$db2 = "assetops_s403_owner_closed"; $work2 = "$env:TEMP\s403-owner-closed"
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db2 --work $work2 prepare
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db2 --work $work2 close-gate
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db2 --work $work2 serve --port 8867 --web-port 5367
# second window, from frontend\:  $env:ASSETOPS_API_PORT="8867"; npm.cmd run dev -- --port 5367 --strictPort
```

## Steps

Use the addresses that `links` printed.

1. **Finding, then Evidence (F01, ordinary gateway path, 2 Oct).**
   - Open the Finding. Under it, the section links read **Finding · Evidence · History**.
   - Open **Evidence**. It reads "Latest version at the time of reading", with a "Keep this exact version" link.
   - It says the version cites **102** accepted records, out of the **263** the analysis read.
   - "Cited records by measurement" counts all 102 records, not only the 50 on the page.
   - Select a record with the mouse, or Tab to it and press Enter. Its full trail appears: source, delivery batch, the stored message fingerprint, the site setup it was accepted under, and the assessment that cites it.
   - "Open the stored record and its original message" opens the Site Evidence inspector for that exact record.
   - Reload. The same record stays selected.
2. **History of the Finding with a late reading (F04).**
   - Open **History** for F04. It reads "All 3 recorded versions are listed, oldest first".
   - Version 2 says "Cites readings accepted after version 1 was recorded. Version 1 keeps the records it cited."
   - Version 1 cites 42 records. Versions 2 and 3 cite 78.
   - Version 3 is marked **Latest**. On an unpinned address it is also **Selected**.
3. **Old → new → Evidence → old.**
   - Open the "version 1 History" address. It leads with "Version 1 is selected. It is an earlier version".
   - Select version 3. The address changes to version 3's ID.
   - Click **Evidence** in the section links. It is the same version 3 ID.
   - Press Back twice. You are on version 1 again, and the address shows version 1's exact ID.
   - Reload. Version 1 is still selected.
   - Press Forward. Version 3 is back.
   - Open version 1's evidence: 42 records, with an "Earlier version 1" notice. Use "See version 1 in the Finding's history" to return.
4. **Single version, closed and joined Findings.**
   - A one-version Finding reads "No earlier versions: this Finding has one recorded version."
   - F05's History leads with "No longer supported", and says this does not mean the generator was repaired.
   - F06's History lists the joined Finding as a link to that Finding's own history.
5. **Wrong version.** Change the `revision_id` in a History or Evidence address to an unknown ID. The page says no such version exists. It keeps your address and offers the latest version only as a link.
6. **Assessments not released (second copy).**
   - History and Evidence without `revision_id` say the assessments are not released.
   - A version address still opens, led by "Record only". Evidence shows no Dispatch links there.
7. **Old assessment-keyed Evidence tab.** This is listed only for completeness. On this fixture, KOBO-001 has no older assessment page to open. The day-level list "Findings recorded for this day / these days" is covered by tests only.

## Mock comparison

With the servers running:

```
$env:ASSETOPS_S4_WALK_WORK=$work; node tools\s4-finding-evidence.mjs http://localhost:5366 $env:TEMP\s403-owner-evidence
```

This captures mock `#/finding-evidence`, `#/finding-history` and the app at 1440 and 390 pixels.

| Mock | App |
| --- | --- |
| Evidence bundle: Input / Source / Coverage / Use rows (illustrative devices) | The real cited records by measurement and source. Coverage and Use read "not available yet". |
| Inspect source lineage | The selected record's full trail, plus a link to the stored message |
| History: one compact table (Time / Event / Basis), 3 rows | One block per stored version, with its times, amounts, cited count and links. Late acceptance is noted on the version it affected. |
| "Recommendation prepared" history row | Not shown (S6 / G-04) |
| Tabs: Alternatives, Recommendation | Not shown (G-04) |

Visual question for you: the mock's History is a compact three-column table, while the app shows a longer block per version. Is that acceptable?

## Stop and clean up

1. Press Ctrl+C in every server window.
2. Drop each copy. `drop` removes the work folder only if `prepare` created it:

```
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db --work $work drop
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py --db $db2 --work $work2 drop
```
