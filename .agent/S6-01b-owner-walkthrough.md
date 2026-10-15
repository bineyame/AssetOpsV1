# S6-01b owner walkthrough: Recommendation, Action and Foundation change

These steps let you view the screens in a browser at desktop (1440) and phone (390) widths, and then record whether you accept them. Nothing here touches your own databases or any other walkthrough's databases.

## Start

From the worktree, run in PowerShell:

```powershell
$py = "C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe"
& $py tools\s601b_action_walkthrough.py --db assetops_s601b_owner --work var\s601b_owner prepare
& $py tools\s601b_action_walkthrough.py --db assetops_s601b_owner --work var\s601b_owner serve
# second window, from frontend\
$env:ASSETOPS_API_PORT="8961"; npm.cmd run dev -- --port 5461 --strictPort
```

What `prepare` does:

- It builds the S6-01a demonstration records in a private database through the real stores and API. These are the same records that produce the frontend test contract.
- It writes a grants file. The file allows the three SYSTEM demonstration commands, for this database's Site and the fixture Findings only.

What `serve` does:

- It prints every address used below, with this database's real IDs. You can print them again at any time with `links`.

Ports:

- API: 8961.
- Web: 5461.
- Browser evidence: CDP 9461.

When you are done:

1. Stop both servers.
2. Run `... drop`. It removes the database and `var\s601b_owner`, and nothing else.

## What to look at, in order

1. **Recommendation, accepted snapshot.** Open the "recommendation:1#a accepted snapshot + live status" address.
   - The accepted proposal reads "Battery reserve 20% to 15%". Beside it are the stored Finding, Foundation and assessment IDs and a link to `ACT-000001`.
   - A separate "Live recomputation" panel says there is no proposal on the current inputs, because a newer Finding version exists. The accepted proposal stays visible.
   - The "Trial only" box says the trial tests whether the reserve setting matters. It does not diagnose, predict generator time, or claim a saving or safety effect.
   - "Money" is a link to the Finding's own money view. It shows no amount for the trial.
2. **Recommendation, ineligible Finding.** This shows the typed reason `SOC_NOT_ABOVE_HEADROOM` and no control.
3. **Action Overview** (`ACT-000001`).
   - The origin Finding version is shown beside the latest Finding version.
   - It shows the pinned basis and the pending outcome.
   - The "Foundation change" panel has two links: "Application event" and "Open the Foundation change".
   - Only Overview, Application and History are offered. One sentence says that plan, evidence and verification belong to the verification step.
4. **Application.**
   - Accepted, the backdated observation, three failed attempts (stale Foundation, invalid value, back-dated time), then Applied.
   - Each row shows SYSTEM demonstration, its service and job, the new Foundation version, and the change record as a link.
   - There is no Apply control: it says "Applied; there is nothing more to apply."
5. **History.**
   - The observation row shows both times and is marked "(recorded later than it happened)".
   - "This event" and "Through this time" select an exact event or a recorded cutoff. Switch to Application and reload: the selection is kept.
   - The "selector conflict" address shows the typed refusal `ACTION_SELECTOR_CONFLICT` and does not choose one selector for you.
   - An unknown `event_id` says "Selected event not found" and offers "Open the latest record of this Action".
6. **Foundation change** (`changes:1#a`). Open it from the Action, or from its printed address. It shows:
   - battery reserve 20% before and 15% after, the battery ID, "effective from 2026-11-02 00:00 UTC onward" and the recorded time;
   - Foundation versions 9 (replaced), 10 (split) and 11 (new), with their origins PUBLISH, SPLIT and PUBLISH;
   - the signal assignment versions that were replaced and written;
   - the Action and the exact application event, as links;
   - the three failed attempts, each changing nothing;
   - "Pending. Nothing has been verified yet". The page makes no effect judgement.

   The Foundation tab is current. No Foundation view row appears, because Changes is not a Foundation view.
7. **Bare `/foundation/changes`.** This says there is no list of changes yet, with "Back to the Foundation".
8. **Second Action** (F02, `ACT-000002`). Its failed `ACTION_NO_CHANGE` attempt leaves it pending. Because the grants file covers it, the control "Apply trial (SYSTEM demonstration)" is offered.
   - **Do not press it unless you want a real write** to this private database. The write is labelled SYSTEM demonstration and is undone by `drop`.

## Things to know before judging

- **The latest Finding version reopens the recommendation.** The Recommendation for the newer F01 Finding version does not mention the Action accepted on the earlier version.
  - In the recorded S6-01a contract (server clock 2026-11-01), that newer version reads AVAILABLE, so you could accept it again.
  - In this served walkthrough the server uses today's clock, and it reads unavailable with `FOUNDATION_BASIS_STALE`.
  - Both are the S6-01a server's behaviour, shown faithfully. The screen does not say "already acted on" for a newer version, because the server does not provide that link. This is worth a decision: should the server link earlier Actions on the same Finding?
- **Dates and clocks.** The records carry the fixture's clock, 2026-10-29 to 2026-11-01. The served API uses the real clock, so the "as read at" times and the default effective time on a pending Action use today's date.
- **Nothing changes on the Site.** Nothing on these screens says the Site now behaves differently, or claims an effect or a saving. Verification is S6-02.

## Evidence already captured

`node tools/s601b-action-evidence.mjs http://localhost:5461 <dir>` checked 56 claims across the two widths, and all 56 passed. It saves app and mock screenshots for each named screen, plus `comparison.md`, which sets the mock's headings beside the app's. The review packet cites the run.

## Your acceptance

Record it here or in the coordinator thread:

- accepted at 1440: yes / no;
- accepted at 390: yes / no;
- notes.

The merge stays held until you accept, and until S6-01a merges.
