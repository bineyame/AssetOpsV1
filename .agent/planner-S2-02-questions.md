# S2-02 questions for Architect — 2026-10-09

Batch this with `.agent/S2-01c-questions-5.md` and its open R1 publication-gap ruling per the owner's Codex-use instruction. Do not ask the owner to choose technical credential or receipt mechanics.

## Q1 — Registered TLS gateway credential for central upload

S2-01b uses a protected local host-to-gateway IPC credential. `D-2026-10-08-s2-local-gateway-snapshot-transfer` explicitly says it grants no central upload authority. The S2-02 architecture requires registered TLS credentials scoped to tenant/Site/gateway/source for Batch V2 and GatewayDiagnosticsV1, and says secret material must stay outside product rows and the gateway SQLite ledger. It does not choose the concrete pilot credential form or provisioning/revocation behavior. The Implementer needs one form to build an authenticated HTTPS route and repeatable wrong-scope/revoked-credential tests without making the local IPC credential a network credential.

Options:

1. TLS plus a high-entropy bearer credential provisioned per gateway, with only a one-way verifier/reference in Postgres and secret material in protected gateway configuration. The server derives tenant/Site/gateway and permitted sources from the credential; disabled gateway/source immediately refuses upload. Rotation can issue a replacement credential without rewriting sealed batch bytes.
2. Mutual TLS with a client certificate per gateway and a registered certificate fingerprint/identity. This gives a transport-level peer identity but adds pilot certificate issuance, trust-store and local test setup.
3. TLS plus a signed short-lived token issued by a separate authority. This introduces issuance and renewal behavior the current local gateway lacks.

Recommendation: **1** for the simulated pilot, with explicit TLS enforcement, gateway-scoped verifier, source membership check and revocation/disable tests. It satisfies registered gateway authentication without treating `source_mode` or a caller-supplied ID as authority. Please specify whether this is the intended meaning of “registered TLS gateway credentials” for S2-02, and whether source scope is a fixed allowlist on the credential or evaluated from current registration at each request; original historical registration references must still control accepted-as evidence validation.

Can implementation proceed before the answer? **Yes for phase 1**: define an injected authenticated gateway-principal port and implement Postgres decision/receipt semantics against it. Phase 2 external HTTPS credential provisioning and owner demo must wait for the answer. The default is to refuse all network uploads until a registered principal exists; never use the S2-01b local IPC secret or S1 development-tenant snapshot access as a fallback.
