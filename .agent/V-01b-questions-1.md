# V-01b questions batch 1 (for the Architect; fail-closed defaults shipped)

Each question is new: the V-01a rulings do not answer it. V-01b builds the default and continues.

## Q1. Lab Stage says "Upload pending" after central receipts exist

For a registered run the Stage read (`simulator_lab_api.py:1827`) always returns `upload_state: PENDING` and
"Upload pending: no batch has been sent and no receipt exists." This comes from an S2-01b constant
(`contracts/assetops_contracts/gateway_stage.py:59-61`: "Until S2-02 adds authenticated upload, every registered
batch is pending"). On the walkthrough run the Commit read shows 198 batches with central receipts.
**Default:** no backend change in a visual gate. In the Lab's primary layer, the delivery state comes only from the
Commit read's central receipts (`lab:3`). The Stage's upload line stays as-is under Advanced details, with a visible
label saying it is the gateway's local Stage statement and that central receipt is shown under Release and
ingestion. **Ask:** should a backend slice derive Stage `upload_state` from the gateway ledger's receipts (or drop
the field)? Record as a backlog carry until ruled.

## Q2. Page headings: app "Evidence" / "Draft run" versus mock Site name / "Kobo · Gateway & Ingestion"

V-01a kept the app's "Foundation" h1 by owner choice (Q2 there). **Default:** keep the "Evidence" h1 with the Site
name in the subtitle. Rename the run page to the mock's purpose, "Gateway & Ingestion", only if existing tests and
guards allow it without loosening; otherwise keep "Draft run" and show "Gateway & Ingestion" as the first section
heading. **Ask:** owner preference at the V-01b checkpoint.

## Q3. Evidence status bar badge

The mock's "Evidence limited" badge is a capability judgement (registry `evidence:1#b`, unmapped).
**Default:** the status bar shows only window facts (accepted readings, sources reporting, not accepted) and a
neutral "No capability conclusion yet" badge. It never shows "Evidence limited", "Full" or any score.
