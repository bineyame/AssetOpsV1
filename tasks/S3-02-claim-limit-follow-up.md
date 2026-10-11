# S3-02 — Selected-window claim limit

Status: outline; refine after S3-01 review, before activation
USER_REVIEW_REQUIRED: true
Depends on: S3-01 selected assessment, resolved evidence-readiness and dispatch contracts
Branch when activated: task/S3-02-claim-limit

## Visible outcome

The positive `evidence-analysis:2#b` view shows a rule-backed capability and coverage limit for one selected Site/window/assessment. S2's no-conclusion explanation remains its distinct delivered portion.

## Acceptance

- `I-capability-read` uses accepted public coverage for the selected S3 assessment. The complete and missing cases in `I-sim-dispatch-cases` are reusable only when review proves they cover this rule; otherwise add one bounded fixture before activation.
- `I-claim-limit-read` returns the governing rule, limit, selected assessment revision, accepted evidence IDs and missing-role reason. `I-evidence-analysis-claim-limit-ui` shows positive and unavailable states with stable selection after reload.
- Compare the app's `evidence-analysis` panel with v6.9 at desktop and narrow widths, including keyboard selection and Evidence drill-down. Review the exact claim lineage and the distinction from S2 text.

Independent review and the owner checkpoint close this packet. No open path is delivered by this mapping.
