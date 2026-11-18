# S2-01b questions for Architect — 2026-10-08

## Q1 — Authorized frozen-snapshot transfer to the separate simulated gateway

S2-01a freezes the exact registered snapshot bytes/hash and revision IDs on a private Lab Draft. S1's `GET /api/sites/{id}/foundation/snapshot` is scoped only to the development tenant and explicitly says gateway authentication is pending. S2-01b must run acquisition in a separate process using that frozen basis; S2-02 later owns registered TLS credentials for central batch upload. A gateway that directly calls the S1 route, or accepts an unauthenticated caller's claimed Site/hash, would misrepresent the source boundary.

Options:

1. The gated Lab host sends the pinned snapshot and public reports over a local IPC channel with OS/process-level access control and a narrow gateway identity; the gateway verifies hash, immutable references and scope before activating it. No new public configuration endpoint is exposed in S2-01b.
2. Bring forward a registered gateway credential and authenticated snapshot-download endpoint in S2-01b, separate from the S2-02 batch-upload permission; the gateway fetches the selected version itself. This adds credential provisioning and server API work to this slice.
3. Pass the snapshot by a local file/command argument at process launch, protected by file permissions and gateway identity checks. This is simpler for a single local demo but needs an explicit safe refresh/restart story.

Recommendation: **1** for the simulated-only S2-01b demo, with a narrowly scoped local channel and a gateway-side hash/identity check. S2-02 can add the network credential boundary without changing sealed bytes. Please specify whether this local trust boundary satisfies the architecture's “authenticated channel” requirement for S2-01b and what identity the gateway should verify independently of the host's run ID. The packet must not treat the S1 development-tenant route or a Lab run reference as gateway authorization.

Can implementation proceed before the answer? **Phase 1 can:** wire contracts, SQLite ledger and fixtures have no transport dependency. Phase 2 process integration must wait for the decision; a local-only prototype may use option 1 behind an explicit interface but cannot claim the gateway transfer AC closed until the Architect approves its scope.
