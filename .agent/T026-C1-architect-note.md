# T026 C1 - are scenario control overrides operator commands? (Architect note)

Produced by Claude under the ROLE_CONFIG exception (Architect bound to Claude
until the Codex reset 2026-10-03 21:23). A recommendation; the owner decides.

## Question

Profile 5 publishes every scenario forcing of `generator-stop-soc-threshold` or
`battery-reserve-state-of-charge` as an `OVERRIDE_COMMAND` record, actor
`OPERATOR` (`host/execution_adapter.py:853`, `runs/service.py` `OVERRIDE_COMMAND_STATES`).
`kobo-mini-grid-stop-60` v2 says its override is "a scenario event over the Site's
baseline ... not operator evidence", and its purpose calls it "a different policy".
Which is right: (a) operator, reword stop-60; (b) not operator, stop publishing;
(c) defer to T028.

## The fact that settles it

stop-60's `stop-threshold-override` and degraded-evidence's are byte-for-byte the
same shape (EVENT, category EQUIPMENT, FORCING_INPUT, same state key, WINDOW).
Only the prose differs: one says "an operator overrides", the other "not operator
evidence". So the code is not wrong about either scenario by reading them; it
INFERS who issued the change from which state is forced. In the modelled world a
stop threshold can change by operator command, by a controller configuration
change, or by a Site policy revision. Who issued it is a fact about what
happened, so by the swap test (`D-2026-09-21-physical-property-ownership`) it is
the scenario's to say; the publication profile only decides how the installation
reports it. Inferring it from the state key puts a world fact in the publication
layer. And actor provenance is exactly what AC4 asks the record to carry.

## Options and consequences

(a) All such overrides are operator commands; reword stop-60. Makes the
inference a modelling rule: no scenario can ever express a policy revision or a
config change of a control, and stop-60's own story (a changed policy) becomes
an operator story. C on stop-60 would gain "an operator commanded 60 %",
evidence the author never intended. Cost: stop-60 v3 under the fingerprint guard
(new pin, header + purpose), T026 slice. Contract 9 unaffected.

(b) As literally posed - none are operator commands, profile 5 stops publishing
them. Wrong for degraded-evidence, whose override IS an operator command and
whose missing record is T028's absent case (AC4). Loses the family T026 exists
to introduce.

(b') Recommended refinement of (b): an override is an operator command only when
its scenario entry declares it. Add an explicit, optional declaration on the
event entry (e.g. `issued_by: OPERATOR`; absent = not operator-commanded, no
override record). Profile 5 publishes a record only for declared entries;
degraded-evidence declares it, stop-60 does not and is left untouched.
Consequence for C: on stop-60 nothing claims an operator acted, which is what
its author said; on degraded-evidence the present/missing record cases stand.
`An absent override record never establishes that no override occurred` still
holds - an undeclared change is simply not commanded evidence.

(c) Carry to T028. T028 would inherit a record family whose actor field is
derived rather than declared, and any profile-5 Draft of stop-60 made before
then freezes an OPERATOR record the author disclaimed. Fixing it later means
changing published record content under existing runs. Deferral saves nothing:
the fix is the same size now and larger later.

## Recommendation: (b'), in T026 before merge

Why: it moves provenance to the layer that owns it, keeps both shipped
scenarios true to their headers, and keeps the AC4 family T028 needs.

Cost, in T026 (fix round 2, before the owner's hands-on check freezes a
profile-5 Draft):
- scenario parser: one optional enum field on EVENT entries, refused on any
  state outside the two CONTROL keys; the host and backend sets read the
  declaration instead of the state key (the existing agreement test stays).
- degraded-evidence v1 gains the declaration. It is NEW_SINCE_T025G and
  unmerged, so its pin is re-taken in-branch, no version bump.
- stop-60: no change, no bump, pin unchanged.
- Contract 9: stays 9. The declaration changes what is published, never the
  world trajectory or controller decisions (same physical inputs, same run);
  the contract-9 gate remains unedited.

Not in scope here: whether stop-60's policy change should surface under
profile 5 as a policy record (version, effective interval, source - AC3) rather
than nothing. That is a T028 question; note it on the T028 entry.
