# T1 review, round 3 (verification of fix round 2, W5/W6)

Reviewer: fresh Claude reviewer, 2026-11-19. Diff `8e4ea2e7d..80ece8e5c` (`b5fa23c1e`, `d29f1a36f`, `80ece8e5c`).

## Summary

- **Verdict: ACCEPT.** M2 is fixed. No cleanup was cut short in any case I reproduced, on either wrapper.
- I reproduced every case by hand in a scratch repo. The job was a `python3` script whose `finally` sleeps
  9 s, and in a second set 40 s. The wrapper ran as a session leader with SIGINT at its default.
- No High or Medium findings. Two Lows, which do not block.
- Regressions: the pooled self-test gave 35 pass, 0 fail (28.8 s). The inventory test gave 7 pass, 1 todo
  (`7b`), 0 fail.
- After every case, `--status` showed all slots free and `ps` showed no leftover job processes.

## Reproduction (bash and pwsh wrappers, Linux)

| Case | bash | pwsh |
|---|---|---|
| Group INT, 9 s `finally` | cleanup ran, rc 130, 9.0 s | cleanup ran, rc 130, 9.1 s |
| Group INT, 40 s `finally` (longer than the 30 s TERM grace) | cleanup ran, rc 130, 40.1 s | cleanup ran, rc 130, 40.1 s |
| INT to the wrapper only, then a second INT 5 s later | child alive at 5 s; cleanup ran; rc 130, 14.1 s | the same |
| HUP to the wrapper only, twice | first not forwarded (wrapper and child alive at 5 s); rc 129 | the same |
| TERM, which the job turns into its `finally` | cleanup ran, rc 143, 9.1 s | cleanup ran, rc 143, 9.1 s |
| TERM, which the job ignores | KILL at 30.2 s, rc 137 | KILL at 30.1 s, rc 137 |

- **Plant.** I changed the bash wrapper to forward the first INT, in a scratch copy. P7c and P7d then fail
  and P7e passes, as the packet claims.
- **Harness note.** If you launch the wrapper with `&` from a non-interactive script, it inherits SIGINT as
  ignored. Bash cannot trap that signal or reset it, so INT does nothing. An unpooled job behaves the same
  way, so this is not a finding. It does mean a manual reproduction must reset SIGINT first.

## Findings

### L-c (Low). An INT between the trap install and the fork is absorbed

- **Where:** `tools/heavy-slot.sh:283-298`.
- **What happens:** a Ctrl-C in this window is counted as the first INT. No child exists yet to receive it,
  so the job then runs to completion. This is a millisecond window, and a second Ctrl-C still works.
- **Optional fix:** reset `hs_nsig` when `hs_child` is set, or exit 130 if `hs_nsig > 0` at the fork.

### L-d (Low, documents). The Windows Ctrl-C statements disagree

- **What the code and packet say:** the code (`tools/heavy-slot.ps1:77` and `:146-147`) and the packet
  (`packet.md:143`) say a Windows Ctrl-C kills the child's tree at once.
- **What the spec says:** `spec.md:197` says the child gets the console event and the wrapper waits.
- **Why it matters:** if the code is right, a Windows Ctrl-C cuts a cleanup short. I cannot verify this on
  Linux, and Windows is not the agents' platform, so this is a residual risk only.
- **Fix:** make the spec line match the code. Or record the Windows behaviour as a §5.2 gap.

## Checks run

- Pooled: `node --test tools/checks/test_heavy_slot_pool.mjs` gave 35/35 pass.
  `node --test tools/checks/test_heavy_slot_inventory.mjs` gave 7 pass and 1 todo.
- I ran the reproductions above, then `--status` and `pgrep` after each one. The two `/tmp/t1-pool-*`
  directories date from 16:10. They predate this round (L6), and I left them alone.
- I could not verify Windows behaviour.
