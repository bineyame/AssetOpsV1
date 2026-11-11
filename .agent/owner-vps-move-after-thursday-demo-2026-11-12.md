# Owner — VPS move timing (2026-11-12, ~02:30)

Context: coordinator recommended Wed 18 Nov (after the client demo), alternative Sat 14 20:00.

Owner, verbatim:

> i'd like the move to be tomorrow, after the demo

Coordinator reading: Thursday 12 Nov after the 14:00 technical demo (the owner has not slept since the 11th; "tomorrow's demo" = the 14:00 one). This supersedes option B's "hold until everything is merged" for timing. Follow-up question (coordinator): "I'm reading 'tomorrow, after the demo' as this afternoon, after the 14:00 demo — correct? … How should those [unmerged pieces] carry over to the VPS?" Options: Push their branches (Recommended) / Main only / Friday, not today.

Owner answer, verbatim: "Push their branches (Recommended)" — option text: "Thursday ~16:00: merge what has passed review, push main AND the unfinished task branches to the private GitHub repo. Git only, no file copying; nothing lost; the VPS continues each branch where it stopped."

=> Authorization: at the Thursday ~16:00 cutover, push `main` and the unfinished task branches to git@github.com:bineyame/AssetOpsV1.git. Was open: how unmerged in-flight branches travel (owner earlier: "no separate file transfer of code").
