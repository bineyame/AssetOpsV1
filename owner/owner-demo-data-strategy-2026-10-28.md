# Owner request (verbatim), 2026-10-28

Let the architect create a well illustrated demo data strategy and ustilize it instead of waiting for me to bring customer export before outreach and discussion, i can only have it after demo during pilot talks:

# AssetOps — Evidence-Grounded Demo Data Plan

Develop a **practical, implementation-ready demo data strategy** for AssetOps across **mini-grid, EV fleet/charging, and cold-chain** verticals.

## 1. Guiding principles

- **Real data first:** Maximize use of authentic operational datasets. Use realistic synthetic data only when actual measurements are unavailable, incomplete, inaccessible, or unsuitable.
- **Physical and commercial consistency:** Reconstruct missing telemetry using defensible physics, operating constraints, asset specifications, and economic models. Avoid arbitrary random generation.
- **Commercial outcomes drive the design:** Data must support the high-value operational and financial outcomes defined in our existing commercial capability specifications, not merely populate dashboards or validate ingestion.
- **Preserve traceability:** Explicitly distinguish observed, derived, modeled, and fault-injected data. Never present synthetic measurements as authentic field observations.
- **Build on existing work:** Review the current simulators, site models, commercial analytics, scenarios, and integration plans. Extend and reuse them rather than create competing machinery.
- **Pilot relevance:** Prefer African operating conditions, realistic asset configurations, and telemetry corresponding to equipment and integrations we might encounter in initial pilots.

## 2. Dataset research and selection

Investigate accessibility, licensing, coverage, granularity, quality, and relevance of the following starting points:

| Vertical | Priority sources |
|---|---|
| Mini-grid | Renewvia African mini-grid dataset (access restricted), NREL African microgrid load profiles, NREL PVDAQ |
| EV | KU Leuven BEV Energy Dynamics, DOE EV Charging Data, Caltech ACN-Data, electric-bus fleet research datasets |
| Cold-chain | Hohenheim cold-storage monitoring (Zenodo), industrial refrigeration telemetry (Zenodo) |

Use the URLs and descriptions from our prior dataset research. Verify sources independently, identify stronger alternatives where available, and distinguish downloadable data from access-restricted datasets.

**Do not assume any source contains signals that have not been verified.**

## 3. Demo data architecture and scenarios

For each vertical:

1. Define 1–3 representative African operating sites, including asset configuration, operational context, and commercial model.
2. Map prioritized commercial outcomes to required telemetry, contextual information, financial inputs, and evidence.
3. Identify which signals can be sourced directly, derived, reconstructed, or must be generated synthetically.
4. Design physically consistent 30–90-day operational histories with normal behavior, meaningful variability, and realistic operating constraints.
5. Include representative failure modes and inefficiencies with identifiable root causes, measurable impacts, credible counterfactuals, and corrective actions.
6. Ensure scenarios support site-level findings, portfolio prioritization, economic reconciliation, and defensible value calculations without double-counting.
7. Design replay through the existing telemetry ingestion and integration architecture, including protocol emulation where appropriate.

Maintain a shared cross-vertical data framework while respecting vertical-specific physical systems, commercial models, and operational workflows.

## 4. Integration and validation

Specify how datasets and reconstructed signals will exercise the actual AssetOps pipeline, not merely prepopulate application tables.

Include:

- Time-series alignment, units, sampling intervals, missing values, and data-quality handling.
- Asset and signal mapping to the existing canonical telemetry model.
- Physically constrained simulation and deterministic, reproducible fault injection.
- Integration emulator and BeagleBone Black replay opportunities.
- Validation of energy balances, operating constraints, asset behavior, and financial calculations.
- Acceptance criteria ensuring defects are detectable, recommendations are justified, and estimated outcomes are evidence-backed.

Synthetic faults must not be treated as observed real-world incidents.

## 5. Required deliverables

Produce a concise, actionable plan containing:

1. **Dataset inventory and selection matrix:** verified sources, URLs, accessibility, coverage, limitations, and intended use.
2. **Per-vertical coverage and gap matrix:** required signals and their proposed real/derived/modeled/synthetic origins.
3. **Demo site and scenario specifications:** prioritized by commercial value and demonstration credibility.
4. **Unified data preparation and replay architecture:** reuse of existing simulator, telemetry ingestion, and economic analytics.
5. **Implementation backlog:** sequenced, dependency-aware tasks suitable for coding agents, with clear acceptance tests.
6. **Residual gaps and pilot data requests:** what cannot be credibly validated without actual operator data.

## 6. Execution constraints

- **Plan first; do not begin implementing until the plan is reviewed.**
- Inspect the codebase and existing specifications before proposing changes.
- Prefer freely downloadable, reusable datasets; do not make restricted sources critical-path dependencies.
- Prioritize improvements to the existing demo over unnecessary infrastructure or simulator rewrites.
- Explicitly distinguish **validated reality, modeled approximations, and unverified assumptions**.
- Optimize for a commercially compelling, technically credible demo that can evolve directly into pilot integrations.

**Success criterion:** AssetOps demonstrates commercially meaningful findings across all three verticals using the strongest available real-world evidence, with synthetic data filling only justified gaps. The resulting scenarios must withstand reasonable technical, operational, and financial scrutiny from prospective operators and investors.
