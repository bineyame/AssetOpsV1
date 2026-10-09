# S2-02 owner walkthrough - registered gateway to Site Evidence

This is the first S2 owner checkpoint: a completed simulated Kobo run is committed, the separate gateway uploads its sealed batches over HTTPS, the server records every reading in Postgres, and Site Evidence shows them with their receipts. Everything below is simulated input. Recorded output of one full scripted run: `.agent/S2-02-demo-run-output.txt`; layout measurements: `.agent/S2-02-layout-evidence.txt`.

## What you need running

The demo runs on its own copy, so your usual servers and data are not used or changed.

| Thing | Value |
| --- | --- |
| Database | `assetops_s2demo` on the usual local Postgres (127.0.0.1:55432). Your developer database `assetops` is not touched. |
| Lab and product API | http://127.0.0.1:8610 |
| Secure upload server (gateway only) | https://127.0.0.1:8643, using a certificate generated for this demo, not the test certificate in the repository |
| Frontend | http://localhost:5310 |
| Demo files | `%LOCALAPPDATA%\AssetOps\s2-demo` (code copy, its own `var/`, gateway ledger, credential files, logs) |

1. From the repository root, build the demo once (about 6 minutes; it stops everything it starts when done):
   `.venv\Scripts\python.exe tools\s2_demo_walkthrough.py run`
   It recreates `assetops_s2demo`, imports KOBO-001, generates the certificate, issues the gateway credential, runs two Lab runs, uploads, and prints each step.
2. Reopen it for the browser: `.venv\Scripts\python.exe tools\s2_demo_walkthrough.py serve` (Ctrl+C stops it). In a second window, from `frontend\`: `$env:ASSETOPS_API_PORT="8610"; npm run dev -- --port 5310 --strictPort`.
3. Run IDs and the reading link from the last run are in `%LOCALAPPDATA%\AssetOps\s2-demo\demo-result.json`.

## Steps and what to look at

1. **Site > Evidence for KOBO-001.** Open `http://localhost:5310/sites/KOBO-001/evidence?from=2026-09-30T03:00:00Z&to=2026-09-30T15:00:01Z`. The page reads from Postgres. "What arrived" should say readings were accepted. The period is source time, start included and end excluded. The analysis is marked stale. That means the queued analysis has not been computed yet, because computing it is S3 work. It does not mean the site is unhealthy.
2. **Gateway contact** on the same page. CURRENT means the server received a gateway report within two declared cadences (2 x 60 s). Stop `serve`, wait over two minutes, start it again, and reload before the gateway's next report: you will see "not heard from recently" (STALE). The scripted run recorded UNKNOWN before the first report, then CURRENT, STALE after 125 s of silence, and CURRENT again after restart. This status is about the gateway reporting in. It is not a statement about the health of any device or asset.
3. **Analysis view** (`&view=analysis`):
   - Each time is labelled with its clock. Source time and publication time are the run's virtual clock. Received time is the server's real clock. The two kinds of clock are never subtracted from each other.
   - Deliveries lists the batches.
   - "Earlier store comparison" says the old file store held nothing for KOBO-001, so nothing was carried over and nothing is claimed to match.
   - The refused-readings list holds exactly one item: the **fault fixture's** invalid sibling (kind `BINDING_NOT_REGISTERED`, signal `fault-fixture-unbound-signal`). It is test input the script built on purpose; the ordinary sealing gateway never sends an invalid reading. Its valid sibling in the same batch was accepted and appears among the readings. Reload the page: both stay.
4. **One reading.** Open the `link` from `demo-result.json`; it goes to one 15:00:00Z reading. The page shows:
   - the value as reported and in site units;
   - the Foundation and binding revision IDs it was accepted under;
   - the delivery receipt: batch, position, first received and decided times;
   - the exact message text.

   Reload the page: the reading stays selected.
5. **Lab Commit panel.** Open `http://localhost:5310/simulator-lab/runs/<main_run>`:
   - The Commit panel says the run is fully released.
   - "Batches and receipts" lists all 246 batches, each one acknowledged with its server receipt.
   - Committing does not write Evidence itself. It releases the sealed batches to the gateway, and the gateway uploads them.
6. **Terminal gap.** Open `/simulator-lab/runs/<gap_run>`. In this run the gateway's clock was forced past a boundary the run had not yet published. The panel shows "Incomplete for good" (TERMINAL_GAP) and never "Fully released". Its 20 sealed batches did upload. The later publish attempt was refused, and nothing moved.

## What the scripted run showed (from the recorded output)

| Case | Result |
| --- | --- |
| Scale | After run-to-end the gateway held 245 sealed batches (292 readings), the earlier proof's count. Advancing the run's publication clock to 15:10 released the one delayed closing report of publication profile v2 (battery state of charge, source time 15:00:00Z, published 15:10:00Z) as one more batch, giving 246 batches (293 readings). The script prints that added batch. They uploaded in 10 bounded passes of up to 25 batches, with progress printed. |
| Fault fixture (labelled) | The script posted a separate test batch over the normal secure upload with two readings: one valid, one naming a signal no binding maps. The server answered 200 with one ACCEPTED and one REJECTED (`BINDING_NOT_REGISTERED`, field `source.signal_id`). After reload, the Site rejection route shows the rejected one and Site Evidence lists the batch. |
| Comparison binding | The comparison report now also records which local evidence and commit stores it was made over (a fingerprint, not a path). A report copied to another workspace pointed at the same database keeps that workspace's Evidence closed until it runs its own comparison. The demo copy made its own. |
| Outage | With the server down, the first attempt failed with `CONNECTION_FAILED` and the batch stayed ready. After restart, the same bytes were sent again. The server's stored digest equals the gateway's sealed digest. |
| Identical bytes again | 200 with the stored receipt. The ledger row counts are unchanged. |
| Same batch ID, changed bytes | One reading's value was changed and the batch was resealed as a valid batch. The server answered 409 `BATCH_ID_CONFLICT`. The stored batch is unchanged and one audit refusal row was added. |
| Wrong credential / plain HTTP | 401 / 426. |
| Credential rotation | A new credential file was written beside the old one, readable only by you. The old credential stopped working at once (401). The gateway config was switched to the new file and the gateway restarted. The same receipt reads back and nothing was resealed. |
| Closing-boundary reading | The 15:00 readings came due after the run ended. They were released by advancing the run's virtual clock to 15:10. The server accepted 6 of them, because their binding period does not end at 15:00. |
| Two runs over the same hours | The gap run's readings sit beside the main run's readings as separate accepted readings with different message IDs. They are not duplicates. |

## Limits - what this checkpoint does not show

- **No historical KOBO replay.** KOBO-001 had no older file-backed Evidence, so the comparison is an explicitly empty set. It proves there was nothing to migrate, not that old and new records match. Old-format parsing is covered only by test fixtures.
- **No S3 analysis.** Accepted readings queue recompute jobs. No analysis, dispatch, capability or healthy-service conclusion is computed or shown.
- **No physical-device proof.** All input comes from the simulator through the simulated gateway. Real protocols and devices are the first-pilot gate.
- **Shown by Postgres tests, not live (labelled test evidence):**
  - a server crash in the middle of a batch, then resume (202 in progress);
  - a closing-boundary reading rejected as outside its period.

  Neither has a product test switch. The live closing readings were accepted because their configuration periods are open (Architect Q32, Q36). The rejected-sibling case is now live, through the labelled fault fixture above.
- **Unconfigured claims:** generator status and the two newer capability channels are not configured in this demo, and no claim is made about them.
- **Your usual server on port 8000:** the developer KOBO-001 comparison was regenerated again in fix round 1 as schema v3 (store-root bound). A server still running older code reads it as "another schema" and answers "awaiting evidence migration" until it is restarted on this branch (`.agent/S2-02-questions-7.md` Q39). Earlier, it also answered "awaiting evidence migration" for KOBO-001 after the comparison was regenerated. A backend started on the current code with `DATABASE_URL` set (port 8620) served KOBO-001 Evidence from Postgres on the developer database. It showed an empty set there, because no gateway has uploaded to that database. Restarting your 8000 server on this branch with `DATABASE_URL` set should do the same.
