# PRE-S3-04 — Foundation Readiness truthfulness

Status: in_review
USER_REVIEW_REQUIRED: false
Depends on: merged S1 Foundation/Readiness and S2 Evidence/central diagnostics
Branch when activated: task/PRE-S3-04-readiness-truthfulness

## Visible outcome

Foundation Readiness reports configuration without stale claims that no accepted Evidence exists or that a registered gateway is awaiting credentials and not sending data.

## Acceptance

- Remove or dynamically qualify the hardcoded “No accepted evidence is linked” and “awaiting credentials, not sending data” copy. Registration alone does not establish contact or credential state.
- If this view has no central Evidence/diagnostic read, say that operational status is not assessed here and link to Site Evidence or central diagnostics where useful. Do not invent a new status value.
- Independently review populated and missing post-S2 states in the app and read API. `readiness:1#a` stays delivered with its recorded caveat until this correction closes; `readiness:2/3#a` remain unpromoted meanwhile.

This correction is outside competitive ranking and closes before loop activation. Run focused backend/frontend checks plus workflow, architecture, registry and ledger guards.
