# S3-01 phase 3b questions (batched; each has its fail-closed default built)

None blocks review. Context: `.agent/S3-01-phase-3b-handoff.md`, `.agent/S3-01-review-packet.md`.

1. **Q17: no list of assessed days.** Without `?day=` the Dispatch screen opens on today (UTC), which usually reads "Not assessed". No route lists assessed days.
   - *Default built:* open on today UTC and say "Not assessed"; never pick a day silently.
   - *Ask:* add a list-of-assessed-days read (and a day-picker default) in S3-02 or later?
2. **Q18: older-rule label and late-evidence history are proven by tests only.** The rebuilt fixture holds no `dispatch-3` run, and the walkthrough does not stage an older-rule result (labelling a 3.1 run "dispatch-3" would be dishonest). The older-rule note and the revision history appear only in `performanceDispatch.test.tsx` and the Postgres read tests.
   - *Default built:* tests only.
   - *Ask:* should the owner walkthrough get a genuine older-model run (fixture regenerated under `dispatch-3`)?
3. **Q19: demonstration notes (answered in the 3b fix round).** The earlier premise was wrong: 6 and 7 Oct are not ambiguous and their window reads carry the fault-fixture annotation. The note now shows on the Overview whenever the day's read carries any, even with no period to select (test in `performanceDispatch.test.tsx`).
   - *Default built:* window notes shown above the result, apart from the records; per-result notes shown in the records panel when not already shown.
   - *Ask:* none.
4. **Q20: staged FAILED and STALE days have no interval.** "Prior result kept" is the window assessment only.
   - *Default built:* state it as such; no invented interval.
   - *Ask:* stage the failure on a day that already has a stored interval?
5. **Q21: committed fixture manifest refreshed.** `.agent/S3-01-dispatch-cases-v1.manifest.json` now matches the producer work-dir manifest and `assetops_s3cases`. Evidence IDs are per run: any new producer run changes them and the committed copy goes stale again.
   - *Default built:* refresh at closeout; the walkthrough tool reads the producer's own manifest.
   - *Ask:* keep committing a per-run manifest, or commit only the stable part (labels, cases, expected ceilings)?
6. **Q22: evidence table cap.** The records drill-down lists at most 60 rows per scope.
   - *Default built:* 60, with the cap stated.
   - *Ask:* none unless a Site needs more.
