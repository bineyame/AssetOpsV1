# Architect request: R350 scope for non-domain (W1) Action IDs

W5-EV-Work (branch `task/post-W6-W5-EV-work`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-review10`, head 12ec40c3) built R350 per `.agent/post-W6-W5-rulings.md` ruling 4 and the pre-flight Q2 answer (`.agent/post-W6-W5-EV-preflight.md`): Action section routes `/plan`, `/execution`, `/history`, `/evidence` under a cold or EV Site now show "Page not available / This address is not served" with no read and no redirect. See the packet `.agent/post-W6-W5-EV-packet.md` (residual risk) in that worktree.

Consequence: it applies to every Action ID, so a W1 (battery/mini-grid) Action ID opened at those section routes on a cold or EV Site also becomes "not served" instead of the W1 detail. W1 IDs on cold or EV Sites occur only in tests today.

Decide: (a) accept as built (not-served for all Action IDs on cold/EV Sites), or (b) keep the W1 detail for non-domain IDs (probe returns for non-domain IDs in that branch). If (b), state precisely what must change and whether it blocks merge or goes to the backlog. Also confirm or reject two small extensions the builder made: R348's refused EV window also applies at the bare Action route (no redirect); and Reload shown on 409.

Write `.agent/post-W6-W5-EV-r350-rulings.md`: numbered, short, binding. Do not edit other files. Do not commit.
