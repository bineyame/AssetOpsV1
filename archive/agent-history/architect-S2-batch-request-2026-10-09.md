# Architect request: batched S2-01c ruling and S2-02 planning question (2026-10-09)

Owner instructions (verbatim): 2026-10-08 "start from and .agent/coordinator-handoff.md and let the architect and  planner plan S2-0* and implementer proceed. Open questions should be forwarded to architect." 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use"

One batched call, three inputs:

1. **S2-01c re-review block R1** — `.agent/S2-01c-fix-rereview.md` (fresh Claude re-review of the fix round `fb4edae..84a71e6`): after a failed pass and host restart, the stored-schedule-only post-run advance releases delayed reports past an ordinary-publication gap and permanently closes it with no visible trace (reproduced: 115 of 293 envelopes). The reviewer names two fix directions (refuse with a typed kind before the clock moves, or release and expose the gap in the advance answer, schedule read and UI) and says the choice is yours. Also confirm the N1/N2 carries.
2. **S2-01c open implementer questions** — `.agent/S2-01c-questions-5.md` (Q1 per-boundary sealing gives 245 batches for 292 envelopes, which S2-02 ingests; Q2 a passed boundary stops ordinary publication permanently with no repair; Q3-Q5), each built on a fail-closed default.
3. **S2-02 planning question** — `.agent/planner-S2-02-questions.md` (Q1 registered TLS gateway credential for central upload). The refined packet is `tasks/S2-02-ingestion-site-evidence.md` (planning commit is HEAD of `task/S2-01c-gateway-diagnostics-faults`); also flag anything in it that would mislead an Implementer.

Please rule on all of them in one pass, record material decisions in `.ai/DECISIONS.md`, amend the S2-01c/S2-02 packets as needed, and write `.agent/architect-S2-batch-answers-2026-10-09.md` with (a) the exact S2-01c fix-round list and (b) any S2-02 packet changes. Say whether you want the owner to weigh in. No product code; leave edits uncommitted (the coordinator commits).
