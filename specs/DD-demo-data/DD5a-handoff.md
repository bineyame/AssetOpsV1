# DD5a handoff (complete; in_review)

Branch `task/DD5a-load`, worktree `/opt/assetecon/AssetOpsV1-dd5a`. Packet `packet-DD5a.md`. Evidence
`/opt/assetecon/evidence/DD5a/`.

## Done
- Units 1-4 and EV session events (D-DD.161), plants (a), (b) at load level, (c) and the D-DD.161 Lab plant; reach set
  once at the end (`reach-final.log`).

## Next (not DD5a)
- DD4b follow-up: `"session": {"session_id", "connector_id"}` on in-session connector rows (packet deviation 6).
- Architect: EV connector event outside a session takes `connector_id` from `component_id` (deviation 7).
- DD5b: `world.env` per tenant, C6 over `*/sealed/*.batch.json`, C-DD8 on the store, C5 runs both parity files.
