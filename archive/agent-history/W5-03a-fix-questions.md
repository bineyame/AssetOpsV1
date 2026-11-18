# W5-03a fix round: points the rulings do not settle (non-blocking, builder chose the narrowest reading)

1. **Next-evidence sentence for a SCHEDULED window with zero unknown time.** The spec table gives three branches
   (unknown scheduled time, zero declared hours, absent schedule). A scheduled, fully known window matches none.
   Built: only `A telemetry outage does not prove the charging connector was physically unavailable.` (no `Recover ...`
   sentence, no `any unknown scheduled time`). Architect to confirm or give the literal.
2. **Hours formatting scope.** The table says up to two decimal hours "for the status, card notes, bars and prose".
   Built: status and the Known-time card note use `hoursText` (already the case; the review flagged it, the ruling
   keeps it). Chart notes, bound prose and the next-evidence `{duration}` keep `durationText` (`1 h 10 min`), which the
   ruling did not ask to change. Architect to confirm if the prose should also be decimal hours.
3. **Ruling 2 persisted test.** The higher selected-but-failing and unselected rows are real persisted `accepted_evidence`
   clones (test helper `add_import`, cloned row and disposition). If the ledger triggers reject a clone the batch run
   will show it; the fix then stays inside the helper.
4. **`to_real.unresolved_panels`.** Replacing the `GAP:` panel fields (ruling 6) makes `check_v69_ledger.py` require
   `unresolved_panels: []` for `availability` and `energy`; set accordingly (mechanical consequence, no tier change).
