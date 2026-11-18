# Architect request: W2-05a review r1 rulings

You are the AssetOps Architect. Read `.ai/ROLE_CONFIG.md` (the sections "Mockup drives the design; implementers never decide" and "Token Efficiency"), `.agent/W2-05a-build-spec.md` (`D-2026-10-18-w2-05-buildspec`), `.agent/W2-technical-design-ev.md`, and the review `.agent/W2-05a-review-r1.md`. The code is on branch `task/W2-05a-ev-foundation`; read it with `git show task/W2-05a-ev-foundation:<path>`. The v69 EV mock is authoritative.

Give an exact, implementer-proof ruling for every finding: files, behaviour, copy, and tests.

- **H1.** The ev-sld renders one feeder per declared charger. The fixture EV-LAB-001 declares one charger, but the mock and spec QN have three feeder slots (including Charger 2). Rule the fixture and/or rendering: should the fixture declare a second charger, or should the slot render as configured-missing, and with what exact labels? Also rule the monitoring-rail ordering key (c1 before c2).
- **M1.** Financials, Assumptions and Health are live links on EV views, and they open the mini-grid screens. Confirm the spec's unavailable-entry treatment and the exact copy and placement.
- **M2.** `validate_bindings` lets an EV binding set publish with no connector, so the site-import cadence can be null. Give the exact validation rule and refusal reason.
- **M3.** Q8 says power/controller channels carry the connector, but the W2-00 v4 parser (`source_envelope_v4.py:269-270`) and the 0020 CHECK forbid it. Rule which one is right, and the exact change. 05a adds no further migration beyond 0024, so say whether 0024 must change.
- **M4.** `ev_lab.py:61` records the ev-lab binding set five minutes in the future (copied from `cold_lab`). The spec doesn't require it, and bindings read as empty for five minutes after install. Ratify it with a reason, or remove it.
- **Lows.** Rule each one:
  - "Not available yet" via the tab/chip exemption rather than `<MissingClaim>`;
  - missing `UNIT_RANGES` for `s`/`kWh`;
  - unruled "power sharing" wording: give the final string;
  - missing-role readiness at 1.31x: accept or compact.
- **Writer-guard probes.** The `writer_guard_probes.py` run did not finish, and no guard or SQL writer code changed. Waive it, or require it.

Append "Run 8 rulings (review r1)" to `.agent/W2-05a-build-spec.md`. If any ruling changes W2-05b, amend `.agent/W2-05b-build-spec.md` too. Do an implementer dry-read and a copy dry-read. Write nothing else. Do not commit.
