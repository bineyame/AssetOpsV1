# Planner brief: one mapping pass for the pre-loop gates (2026-10-11)

Role: Planner (Codex). Branch `plan/pre-S3-startup`. One bounded pass (owner Codex-usage rule, verbatim 2026-10-09: "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use").

Authoritative instructions: `.agent/architect-batch-answers-5.md` (read fully) and its decision in `.ai/DECISIONS.md`.

Do, as tracked edits (no product code; the coordinator commits):
1. **37 proposed-only paths:** apply "One Planner mapping pass for the 37 proposed-only paths" exactly — real node IDs, owner packets, layer, S/M/L effort, technical `requires`, acceptance target, `status:open`; reuse resolved S1/S2 nodes; separate positive/Unknown variants; no node resolved and no panel Real by mapping. Keep `reviewed_mapping:false` for these (an independent reviewer checks them next).
2. **Packets/sections** the mapping needs: `S3-02` claim-limit follow-up; the S4 Site Finding index/history follow-up; packet sections/owners for the moved W1 Finding/Action screens in S4/S6 packets; `PRE-S3-04-readiness-truthfulness` (Q8, small corrective slice, authorized now, outside ranking).
3. **V-01 split (Q1):** `V-01a` (sites, foundation, readiness, sld) and `V-01b` (lab, evidence, evidence-analysis), each L with its own packet and owner checkpoint; V-01 becomes an umbrella index; move the S3 `dispatch` visual increment into S3-01's acceptance; update `delivery_plan.visual_gates`.
4. Q6 wording fix for `A-money-comparability`; Q3/Q4 variant handling; update `tasks/README.md` queue for the new packets.
Do NOT touch `frontend/docs/architecture/delivery_next_work.cjs` or `test_delivery_next_work.cjs` (a Sonnet implementer is fixing F1 there concurrently), and do not do the C1–C3/Q9 review-citation edits or C5 (an implementer does those next). Run the registry checker, ledger, workflow and architecture checks and the live `--next-work` report; report honestly whether it still refuses and why. Questions: `.agent/planner-mapping-questions.md` (fail-closed defaults). Do not commit. End with a short summary.
