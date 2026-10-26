# Architect request: commercial-capability-readiness.md, iteration 3 (commercial-performance assessment)

You are the AssetOps Architect. The authority for this task is the owner's feedback, word for word, in `.agent/owner-commercial-capability-feedback-2026-10-26.md`. Read all of it. Earlier owner files still apply: `owner-commercial-capability-brief-2026-10-26.md` and `owner-commercial-capability-direction-2026-10-26.md`.

**Scope: edit only `Docs/demo-sprint/commercial-capability-readiness.md`.** Leave `integration-pilot-baseline.md` and `simulation-evolution-assessment.md` unchanged, unless a cross-reference becomes wrong.

Do this in the document:
- **Keep the technical findings.** Keep your evidence boundaries and maturity classifications, and do not promote any partial capability to ready.
- **Add the commercial-performance assessment.** The owner's recapped outcome ranking per vertical is the organising principle, not the implementation inventory. Sections 3–8 of the feedback ask for four things:
  1. **Workflow-level coverage for each leading outcome.** Describe the complete business decision AssetOps could support, the capability chain it needs, and where that chain breaks today.
  2. **A commercial importance × readiness matrix** per vertical, as the owner describes it, kept as two axes rather than one score.
  3. **A sized gap to the commercially significant experience,** with gaps clearly distinguished by kind and size (for example, a missing vehicle/roster join is not the same as a missing UI badge). Name the gaps that need independent business records versus simulated or authored inputs.
  4. **Compare the alternatives the owner names,** using the owner's common question: "What is the smallest credible addition that makes AssetOps materially more valuable to a prospective buyer, while preserving the integrity of the underlying evidence?"
     - **Mini-grid:** the margin-framed experience ("Where is this portfolio failing to achieve its potential margin, and what are the most actionable drivers?"), assessed for productive-use margin, diesel/cost-of-supply reduction and portfolio profitability as lead candidates. Show how headroom, generation cost and the verified technical intervention combine without building a financial management system.
     - **EV:** Option A (post-action technical verification on charger observations) versus Option B (a minimal, explicitly simulated charging-requirement and departure-window join for one constrained fleet-readiness decision). Compare their commercial differentiation per unit of engineering effort.
     - **Cold chain:** an additional thermal verification versus a qualified inventory-exposure valuation, with the buyer distinction shown separately: goods owner versus storage-service provider (occupancy, cost per billable unit).
- **Reflect the owner's hybrid preference.** Reuse the shared workflows, verify fully in mini-grid, and add verification to EV and cold only where a small extension unlocks a compelling outcome.
- **For each comparison, state your recommendation and reasoning.** Then name what still needs the owner, as the owner says: what commercially meaningful proof initial client conversations need, and which assumptions are acceptable in a simulated demonstration.
- **Replace the earlier "lead outcomes" framing where it is implementation-led.** Keep your claim ladder.
- **Update the §11 decision summary.** End with a short list of owner decisions. Lead it with the mini-grid lead-outcome question the owner raised as the next discussion.

Keep it concise and scannable: tables plus short reasoning.

**Limits:** assessment only, with no five-day plan. No product code, test or `.gitignore` edits. Focused tests only, if you need any (project venv, `PYTHONPATH="backend;contracts;simulator;gateway;host;."`). No suites, dev servers or DB creation.
