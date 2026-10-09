# Owner draft (verbatim, 2026-10-09)

Owner's message: "also, [draft below] I would like the architect to consider the following draft and turn it into a proper decision i can review and confirm: D-2026-10-09-owner-delivery-strategy"

---

## 2026-10-09

Decision: `D-2026-10-09-owner-delivery-strategy`. Owner product decision on
delivery order, fidelity target, prioritisation method and autonomy. This is
not an Architect contract, task activation or slice acceptance. It supersedes
no technical decision; product choices never satisfy a technical gate.

**Goal.** A demo application faithful to the v6.9 mock
(`frontend/mockups/v69/index.html`), built from persisted source-to-claim data.
No mock value becomes product data. Unsupported content stays honestly
unavailable until it is real.

**Delivery order: story-first waves.** Build a thin version across all three
domains first, then the estate layer once, then deepen. Do not finish one domain
before starting the next.

1. W1, mini-grid spine: the S1–S7 queue as planned, plus V-01 visual fidelity
   as a standing check on every screen slice.
2. W2, thin cold-chain and EV spines: one Site per domain, built on the
   S2–S4 backbone. Foundation, evidence, one assessment, one Finding and its
   bounded consequence each. Cold chain: temperature excursion and backup
   response. EV: interrupted session. Includes each domain's simulated data
   world and fixtures.
3. W3, estate layer with all three domains present: Portfolio, the global
   Findings (Cost/Risks/Opportunities), Actions, Evidence and Financials.
   Built once, with no single-domain interim version.
4. W4 onward, deepen by score: the remaining mini-grid objectives, domain
   work views, Incident/Maintenance (after the Findings they link to), the
   Asset root, onboarding and Settings.

The Architect proposes each wave's exact manifest IDs at wave start; I approve
them.

**Fidelity tiers.** Each wave targets `Real with honest gaps`, with core panels
I approve at wave start. `Real` (every panel real or owner-approved withheld,
plus interaction, navigation and V-01 acceptance) is the end state for every
screen not dropped. Screens explicitly dropped: ‹none yet / list›. Screens
deferred without a wave: ‹none yet / list›.

**Prioritisation.** Within the active wave, order work by a weighted score
published beside its raw facts (ready-now, closure-unlock, reach, distance,
effort):
- demo value ‹0.4›: owner-set 1–5 per screen at wave start
- panels unlocked ‹0.3›
- reach ‹0.2›
- effort ‹−0.1› (S=1, M=3, L=5)
- tie-break: lower distance, then lower effort

`priority` on product nodes records the wave ID. Recompute after every
recorded decision, accepted task or closed fixture.

**Autonomy.** After my wave-start input, the coordinator runs the cycle without
asking:

> closeout → recalculate → select top candidate → refine → build → review → merge

Architecture decisions for later-wave consumers of shared contracts
(FindingIndex, CapabilityReadiness, SourceHealth, money comparability, routes,
actor identity) may be pulled forward, so shared screens are designed for all
three domains. Implementation stays inside the active wave.

**Owner gates.** The loop stops for me only at:
- wave start: confirm IDs, core panels and demo values
- withholding a panel
- the S2, S4, S6 and S7 review checkpoints and each wave exit
- dropping a screen
- a contested ranking: top candidates within ‹10%›, or one exceeding ‹L›
- a change to scoring weights

It also stops on a checker failure, a second review rejection of the same task,
or any claim marked real without lineage evidence.

**Prerequisites (route to the Architect before the loop starts).**
1. Reconcile the registry with merged S1, S2-01a and S2-01b, including S1-03.
2. Add a `delivery_plan` block to the registry and extend the checker with
   the weighted score, a `next-work` report, a staleness guard and a task list
   read from the queue README.
3. Split `P-work-cases` per domain, and move the EV screens assigned to the
   Evidence area into the EV wave.
4. Add the closeout step and its owning role to `.ai/WORKFLOW.md`.
5. Run the checkers in the normal check path.
6. Write the coordinator loop instruction.

**Product nodes.** Record W1's product nodes as `Real with honest gaps`,
priority `W1`, with core panels approved at W1 confirmation. Leave the other
product nodes `pending owner` with planned wave noted until their wave starts.
