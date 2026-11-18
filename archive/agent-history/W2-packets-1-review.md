# W2-00 / W2-01 packet review (plan review, round 1)

Reviewer: fresh independent Claude reviewer. Revision: `e62cc4af`, read-only. No suites run (per dispatch).
Authority checked: `.agent/W2-technical-design-cold.md` (§1, §2 0020/0021 + collision order, §3, §6 cold-foundation/readiness/sld rows, §7 rule 8 + cases), `.agent/architect-W2-design.md:59-73`, `.agent/architect-W1-fidelity.md`, owner W1 verdict.

## Verdicts

- **W2-00: RETURN** (one Medium).
- **W2-01: ACCEPT** (Lows only).

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: "Registry valid: 241 nodes, 11 linked pilot panels", rc 0.
- Registry diff in `e62cc4af`: only `task:"W2-01"` added to `A-cold-role-set`, `I-configuration-breadth-store`, `D-configuration-variants`; all stay `open`. That matches the packet.
- Spot checks: migration head is `0019_verification_core` (correct). `v69-rendered-panels.json` gives cold-foundation 2, cold-readiness 4 and cold-sld 2 panels, with titles matching design :124-131. `ledger_reads.py:232` and `:376` still filter `== "MESSAGE_CONFLICT"`, and `:233` counts `!= MESSAGE_CONFLICT` as rejected, so these lines must change as the design says. `$ledgerConflictAllowed` at `tools/checks/configuration-persistence.ps1:700` already has the three message-family targets. `sites/models.py:26,50,262` matches. The design's citation `binding_roles.py:17-27,117-130` has drifted: the registries are now at `:99` and `:103`.

## W2-00 findings

**M1 (Medium, acceptance gap): the rule-8 writer-guard contract is not sequenced or tested.** Location: `tasks/W2-00-source-events.md:7` (binding-design cites) and `:17` (test 3).
- What is wrong: The packet cites design :5-23, :25-31, :36-38, :91 and :191-193, but not §7 :164-168. Test 3 only says to *run* `tools/writer_guard_probes.py`. The design requires W2-00 to *add* probes:
  - pass probes for the ledger as sole owner of event evidence/rejection/disposition, and for the message-target conflict;
  - fail probes for the event partial-index conflict target, `DO UPDATE` and a foreign writer;
  - double-collision probes, where message+event must choose message, and event+session with a free message must choose event.
- The design also requires `ledger_reads.py` to use `kind IN ('MESSAGE_CONFLICT','EVENT_ID_CONFLICT','SESSION_ID_CONFLICT')` at both receipt count locations. This includes the `rejected` complement at `:233`, which would otherwise count the new conflicts as rejected.
- Why it matters: rule 8 is how the project proves who writes and which conflict targets are allowed. As written, an implementer can pass test 3 with zero new probes, and an event partial-index `ON CONFLICT` target would go unguarded. That is a contract gap, not a preference.
- Fix:
  - Cite `.agent/W2-technical-design-cold.md:164-168` in Binding design.
  - Add to test 3: "add the §7 W2-00 pass/fail and double-collision probes to `tools/writer_guard_probes.py`; `configuration-persistence.ps1` counts them and fails closed; `$ledgerConflictAllowed` keeps exactly the three message-family targets."
  - Add to test 2: "both `ledger_reads.py` count sites (conflicts and rejected complement) use the three-kind set; existing MESSAGE_CONFLICT objects/bytes unchanged."

**L1 (Low).** Make a few design items explicit in test 1/3 rather than implied by "rows/reads":
- v3 mapping snapshots parse without the new mapping keys;
- the four EV codes are `REJECTED` with a null conflict reference;
- the `/evidence/records` family/kind filters work, and old records serialize nulls.

## W2-01 findings

All coverage is present:
- §3 roles, topology and validation; the line-111 read; the 0021 no-op and its downgrade;
- the per-route panel-structure test against `v69-rendered-panels.json` for all three routes, in stocked and empty/refused states;
- 1440/390 side-by-side captures, with structure mismatch as High;
- the W1-F1 dependency, stated at `:3` and `:8`;
- the registry note.

**L2 (Low).** Phase 1 builds `0021` on `0020`, so W2-00 must merge first. Only the migration order implies this. State it beside the W1-F1 dependency.

**L3 (Low).** Architect :73 requires a plain-language scan per UI phase, and the fidelity gate asks the capture log to record app URL, mock hash, selection/revision, viewport and image paths. Name both in the phase 2 acceptance.

**L4 (Low, design hygiene).** Tell the implementer the binding_roles citation is stale (`:99`, `:103`).

## Residual risk

- W1-F1 has no task file at this revision. Phase 2 cannot start until it exists and merges, which the packet acknowledges.
- The approved dynamic titles for cold-readiness:2 and cold-sld:1 come from design :127 and :130, not from the five substitutions in the fidelity contract. The reviewer should accept them as Architect-amended.
