OUT-E E5 captures (product e18c6e22). Producer: tools/s602b_verification_walkthrough.py prepare (DBs assetops_s602b_oute_audit
and _{target_miss,guardrail,inconclusive,withdrawn,estate,verified}; walkthrough CASES gained `verified`), OUT-D demo objectives
declared into the verified DB (logs/verified-declare.log), served with --case on API 8986/8987, Vite 5487.
Tool: capture-oute.mjs (OUT-D tool plus `earlier` and per-target `expect`/`forbid` board-text claims), targets-verified.json.

Result: the Kobo Overview at 1440 and 390 (shots/) renders "Awaiting evidence migration": the s602b case DBs have no passing S2
comparison (the OUT-B4 Addendum 1/6 condition; OUT-B4 tests use an S2 stand-in, the served producer does not), so the overview
read is 409 and the board is not rendered. 16/18 claims: the two failures are the expected Assure-line text on that page.
No page overflow. The board itself was therefore recorded as API JSON per case (board-reads/, board-reads.ps1), 2026-11-02:
- verified: PARTIAL; ACT-000001 under Protect "Verified on test data · linked finding outside this view", detail null (R595);
  Assure "ACT-000001 verified on test data · modelled change 0.042–0.046 USD less per kWh of feeder demand".
- inconclusive: Protect "Not determined · ...", detail null; Assure "ACT-000001 result not determined".
- target_miss / guardrail: "Did not fix it", detail null; Assure "did not meet its target". withdrawn: "Not determined", detail null.
- Residual risk (review): no modelled-change, "not realised savings" or PRICE_MISSING text in target_miss, guardrail, withdrawn
  or inconclusive (each holds a PRICE_MISSING or OUTCOME_INCONCLUSIVE revision). verified has exactly one modelled-change line.
board-*.json were saved by Invoke-WebRequest, which decoded UTF-8 as Latin-1 (the en dash shows as mojibake in the files);
the API itself served the en dash (checked with curl before the loop).
Cleanup: every server stopped by PID (serve wrappers, uvicorn on 8986/8987, Vite 5487); all 7 DBs dropped; var/s602b_oute removed.
