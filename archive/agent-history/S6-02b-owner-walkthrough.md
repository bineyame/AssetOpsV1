# S6-02b owner walkthrough - did the reserve change work?

What you are checking: after a battery-reserve change is applied, the Action now shows its **plan** (what success
means, fixed in advance), its **evidence** (the readings in the two hours compared) and its **verification** (the
result). One Action is a real end-to-end trial on Lab data that reaches "Target met within every limit". Four more
are **test-scoped examples** (built by the test helpers, not Lab runs) that show the other results. You need Docker
Desktop running (the AssetOps Postgres container) and about 15 minutes for the preparation.

## 1. Prepare (once, about 12 minutes)

Open PowerShell:

    cd C:\Users\assef\Bineyame\AssetOpsV1-review5
    C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py --db assetops_s602b_owner --work var\s602b_owner prepare

It ends with `Prepared. Next: serve, then capture.` and, on the way, `replay: VERIFIED ...` and four `case ...` lines.

## 2. Start the two web pages (two more PowerShell windows, leave them open)

    cd C:\Users\assef\Bineyame\AssetOpsV1-review5\frontend
    $env:ASSETOPS_API_PORT="8966"; npm.cmd run dev -- --port 5466 --strictPort

    cd C:\Users\assef\Bineyame\AssetOpsV1-review5\frontend
    $env:ASSETOPS_API_PORT="8967"; npm.cmd run dev -- --port 5467 --strictPort

## 3. Serve (fourth window; Ctrl+C to stop)

    cd C:\Users\assef\Bineyame\AssetOpsV1-review5
    C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py --db assetops_s602b_owner --work var\s602b_owner serve --case guardrail

It prints every link. Port **5466** is the real trial; port **5467** shows ONE test-scoped example at a time. To see
another example, press Ctrl+C and run the same command with `--case target_miss`, `--case inconclusive` or
`--case withdrawn` (the web windows stay open; reload the page).

## 4. What to look for - the real trial (http://localhost:5466, links printed by `serve`)

| Page | Look for |
| --- | --- |
| Verification (current) | "Target met within every limit"; generator time 60 min -> 0 min, target Pass; every limit Pass; source "Registered Lab trial data"; the yellow note: policy trial, no savings or realized benefit; "Resolved" in Resolution activity with "It is not permanent". |
| Verification, exact outcome | A prominent **Historical** label; click **Plan**: the address keeps `outcome_id=`; press F5: it stays. |
| Plan | Success criteria fixed before the later window; the two one-hour windows; old reserve 30 % -> new 25 %; "Dig deeper" holds the IDs. |
| Evidence | Two tables (before / after the change), 12 five-minute slots each, all complete; on a phone-width window the tables scroll sideways inside their box, not the page. |
| Selector conflict | A clear "conflicting selection" message, nothing chosen silently. |
| Recommendation | The accepted proposal stays; "Declare success before evaluating" links the plan. |
| Foundation change | "Later effect" shows the result and says that being applied is not success. |

Honest limit: in this trial the generator ran **unloaded** (0 kW) in the earlier window - the avoided time is
generator running time, not fuel burned; no savings are claimed.

## 5. What to look for - TEST-SCOPED examples (http://localhost:5467)

These are labelled examples, not Lab runs: the source row reads "Authored test data (test-scoped example)" (the
`inconclusive` one reads "Source not established" - its real readings are incomplete).

| `--case` | Verification page shows |
| --- | --- |
| target_miss | "Target not met" (generator time not reduced enough). |
| guardrail | "Trial missed a safety or service limit" with the failed limits, values and evidence beside them. Open the printed "hold" link: the other Finding's recommendation is blocked with the reason and a link to this Action, buttons disabled. |
| inconclusive | "Could not conclude" with what is missing. |
| withdrawn | Current "Could not conclude"; Resolution activity shows Resolved and then **Resolution withdrawn**; Outcome evidence lists the earlier "Target met" as replaced. Open that earlier outcome: it reads **Historical**, never current. The printed "hold" link shows the overlap block. |

## 6. Clean up

Stop the windows (Ctrl+C), then:

    cd C:\Users\assef\Bineyame\AssetOpsV1-review5
    C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py --db assetops_s602b_owner --work var\s602b_owner drop

Record your acceptance (or what to change) for the coordinator; merge is held until you do.
