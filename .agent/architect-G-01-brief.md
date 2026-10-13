# Architect brief: G-01 questions batch (2026-10-13)

Role: Architect (Codex). Branch `task/G-01-mock-gap-catalogue-and-guard`. G-01 is built; fresh review RETURN fixed (duplicate-placement guard); narrow re-review in progress; owner walkthrough pending. Do not edit code or commit (Codex cannot write .git). Write only `.agent/architect-G-01-answers.md`.

Read: `.agent/G-01-questions-1.md` (Q1-Q4, defaults shipped), `.agent/G-01-review.md` (carries C1-C7, especially C5), `tasks/G-01-mock-gap-catalogue-and-guard.md`, `tasks/G-02-v01a-gap-pilot.md`, decisions `D-2026-10-12-mock-gap-closure-mechanism` and `D-2026-10-13-g-gap-packet-activation`.

Answer:
1. Q1-Q4: ratify the shipped default or rule otherwise; for each say whether anything must change before owner walkthrough/merge, or is a G-02 carry. (Reviewer judged all four reasonable.)
2. C5: `GATEWAY_NOT_AVAILABLE_YET` still bundles three claims (uptime trend, expected-vs-delivered completeness, signal strength) in one sentence. Must G-02 split it per claim into separate placements, or may one rendered element carry several gap IDs? The scan now rejects reusing one placement twice.
3. C7: the phrase list ("not available yet", "not yet available", "no reviewed source") is narrow; should G-02 widen it (e.g. "not tracked yet", "not recorded" in specific contexts)?
4. Anything the owner must decide.
If a recorded decision is warranted, draft its DECISIONS.md entry text inside the answers file.
