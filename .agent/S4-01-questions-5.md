# S4-01 questions 5 (phase 3, `I-finding-ui`)

Each question has a built default. Every default withholds rather than claims. Route to the Architect only if
a default is wrong.

- **Q25: Dispatch Analysis "finding" unavailable text.** The S3 window body still carries
  `unavailable.finding = "interval assessments are not Findings (S4)"`. The Dispatch Analysis view renders it as
  "Not yet available. interval assessments are not Findings (S4)". Default: leave the S3 backend text unchanged,
  since an assessed period is still not a Finding. The gated panel now says Findings for the day are linked in
  Overview. A later S3 touch can retire the key.
- **Q26: "Repeat not established" wording.** The stored recurrence is `NOT_ESTABLISHED` with reason
  `NO_EARLIER_FINDING` for a first Finding. Default: the page names an unestablished repeat only when an earlier
  Finding exists (any other reason). It never implies an earlier issue that does not exist.
- **Q27: Mock chips.** The mock shows Priority, Confidence (with reasons) and Lens. No priority or confidence
  score is computed by S3/S4. Default: show State, the up-to-date check, the version and the period instead, and
  show no priority or confidence value.
- **Q28: Generic layout tool.** `tools/layout-evidence.mjs` needs the Lab run-setup backend, which the isolated
  walkthrough API does not serve. Run against the walkthrough servers, it stopped at
  `/simulator-lab/scenarios/fuel-loss-event/run-setup` ("submit still disabled after ten seconds"). Default:
  record it as not run to completion. The Finding and Dispatch layout claims (no sideways page scroll at 1440 and
  390, populated sets) are measured by `tools/s4-finding-evidence.mjs` instead.
- **Q29: Screen ledger.** The `finding` row (task "S4-01 + S4-02", "Real with honest gaps") is unchanged. Default:
  no promotion is claimed. Panel 3 ("What to do next") stays the unresolved panel, and the owner checkpoint
  decides.
- **Q30: Block selection in the address.** `?portion=<index>` selects a block within the selected version's
  ordered blocks, and is replaced (not pushed) in history. Default: the index is stable for an exact
  `revision_id`, so a pinned version always reloads to the same block. On the latest-version address, a later
  version may reorder the blocks.
