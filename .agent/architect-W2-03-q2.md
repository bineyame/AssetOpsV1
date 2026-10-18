# Architect request - W2-03 confirmations (2026-10-18). Brief; edit `.agent/W2-03-build-spec.md` in place; amend `D-2026-10-18-w2-03-answers`. No code.

From the commit-3 implementer (`.agent/W2-03-phase-1-handoff.md`, choices list):
1. Work windows: accepted cold readings grouped within the rules' 10-minute bridge and merged with any assessed window within that bridge (replay gives exactly [19:00,20:05)). Confirm or specify.
2. Finding no longer warranted while the episode is still supported: a SUPPORT_CHANGED or BASIS_REFRESHED revision with lifecycle UNCONFIRMED. Confirm or specify.
3. Staleness in commit 4 reads: the spec's "probe reading under 10 minutes old" rule makes the 2026-10-06 demo replay read STALE_SOURCE today, so every demo cold screen would show stale. The owner's demos rely on replayed data. Specify the freshness reference (wall clock vs the assessed window / replay as-of) so the demo screens are honest and not permanently stale.
4. Also confirm choices 2, 3, 5, 6 in the handoff (labelled simulated clock attestation in tests; split link proven via test double; W2-00 test ignoring cold_chain jobs; excursion replay's start-failure Finding unasserted) or correct them.
Print a 3-line summary.
