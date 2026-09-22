# Declared Capability And What Checks It

Status: **reflection, not a decision.** Nothing here is recorded in
`.ai/DECISIONS.md`, no task file has been touched, and the
`cadence_resolution` rename is on hold pending this. Written by the Architect
on 2026-09-22 at the user's request, after three questions that went
underneath the rename.

Expiry: this document exists because a pattern was visible in three places and
had no name. It goes when the pattern has a name somewhere durable, or when
the user decides it should not have one.

---

## The short answer

**(a) Ownership *is* established at system-logic level, unusually well.**
`runs/profiles.py` makes it structural, with a build guard. The field is a
second, weaker statement of a fact the structure already guarantees, and being
the weaker statement, it is the one that rotted.

**(b) Nothing frozen requires resolution. `cadence_resolution` is not
provenance at all** — it is a derivation of two fields sitting beside it. But
the user's rule as stated would also delete something that should stay, and
the line that actually holds is narrower: *store provenance, derive
derivations.*

**(c) The parser could not have caught it, and is not where this belongs.**
But the question behind the question is the real one, and yes — it is a
family, not an instance.

**One root cause, and the project already owns the rule.**
`.ai/ARCHITECTURE.md` says an expectation is legitimate when being wrong
causes a failure and circular when being wrong causes agreement. That rule was
written about authored scenario expectations. It was never applied to
configuration and provenance, which is the half of the system where all three
of these live.

---

## The concrete picture first

Five places in this codebase where something is **declared in data** and
something else **would have to honour the declaration**. Sorted by whether
anything can fail when the declaration is wrong.

| Declaration | Who would have to honour it | What happens if it is wrong |
| --- | --- | --- |
| `FoundationBinding(component_type="FUEL_TANK", rating_unit="L")` | a Site's Foundation | **Run setup resolves it against the real Site and blocks** with `INITIAL_VALUE_NOT_RESOLVED` |
| `PublicationProfile.device_signal_cadence_minutes` | the profile type itself | **Structurally impossible to be wrong.** The type has the field or it does not, and a build guard stops anything else constructing the record |
| `cadence_resolution: MODEL_PROFILE` | nothing | **Nothing.** It is a label a resolver writes about its own completed act. It was wrong from the day it was written |
| `SupportedState.supported_roles` on `MINIMAL_FUEL_TANK_MODEL` | a causal kernel | **Nothing yet.** No kernel exists to disagree with it |
| OQ3: the model profile owning `fuel-level-reporting-availability` | a model of the reporting path | **Nothing.** The run blocked either way, so the claim was never tested |

The top two are the ones that work. The bottom three are the ones that went
wrong, and they went wrong in the same way.

Notice what the working two have in common, because it is not "more
validation". `FoundationBinding` is checked **against something that exists**
— a real Site, at run setup. `device_signal_cadence_minutes` is not checked at
all; it cannot be wrong, because only one type has the field.

And notice the failure the bottom three share: **nothing could have failed.**

---

## (a) Why is ownership not established at system-logic level?

It is. This is the part of the codebase that already does what the question
asks for, and the module says so in its own words —
`backend/assetops_backend/runs/profiles.py`:

> *"The rule is structural here rather than remembered. This module imports
> nothing from `assetops_backend.sites`, the three resolver functions below
> take only a profile and the scenario's own declared source, and
> `tools/checks/run-setup.ps1` fails the build if a `FrozenObservationBinding`
> or a `FrozenPublicationIdentity` is constructed anywhere else in the
> product."*

That guard is real: `tools/checks/run-setup.ps1:84` names the two records and
fails the build on any construction outside the two resolvers, and it fails
loudly if the scan ever stops reaching outside the run domain. A Site fact
cannot reach a cadence because it cannot reach the module, and nothing outside
the module may build the record a cadence lives in.

So the premise is right and the codebase agrees with it. **The defect is not a
missing structure. It is a redundant restatement of a structure that already
holds.** `PublicationProfile` is the only type with a
`device_signal_cadence_minutes` field; `ModelProfile` has no cadence concept
at all. "Which profile supplied the cadence" has exactly one answer and cannot
have another. Writing that answer into a per-run field presents a settled fact
as a contingent one — and because the field was the weaker of the two
statements, it is the one that drifted.

**The user is right, and the remedy is subtraction, not addition.**

---

## (b) Why does anything frozen require resolution?

Two halves, and the user is right on the first and would over-reach on the
second.

**Right: `cadence_resolution` is not provenance.** It is a derivation. Given
`OBSERVATION_SOURCE_KINDS = {"DEVICE_SIGNAL", "OPERATOR_RECORD"}`, the field is
a total function of the two values beside it:

| `source_kind` | `cadence_minutes` | `cadence_resolution` |
| --- | --- | --- |
| `OPERATOR_RECORD` | absent | `NOT_APPLICABLE` |
| `DEVICE_SIGNAL` | absent | `NOT_RESOLVED` |
| `DEVICE_SIGNAL` | present | `MODEL_PROFILE` |

There is no fourth row. The parser at `runs/parsing.py:1052` then spends
fourteen lines enforcing the biconditional between the third column and the
second — a record is validated against a restatement of itself.

The project has already rejected exactly this, one layer up, in T019.
`backend/tests/test_run_setup.py:1239` suppresses `canonical_value` from the
frozen summary with the reason:

> *"A canonical restatement of the value beside it. One number twice on a
> screen is one number that can disagree with itself."*

`cadence_resolution` is that sentence applied to a record instead of a screen.
It is one fact twice, and the two disagreed.

**Over-reach: "a frozen identity should be values plus a provenance trail" is
the right instinct, but `answered_by` is not the inconsistency you might think
it is.** The codebase already draws a defensible line here, and it is worth
seeing before changing anything:

- `FrozenInitializationInput` **stores** `answered_by` and
  `answered_by_detail` (`runs/models.py:257`). Correct: which of four owners
  answered for an initial value is genuinely contingent — Foundation,
  scenario, run override or model rule could each have answered, and the value
  alone does not say which did.
- `provenance.py` **computes** the row-level answerer for cadence and the two
  publication identities at serve time. Also correct: there is only one
  possible answerer, so there is nothing to record.

That is a coherent rule already in force: **store what was contingent, compute
what follows from the structure.** `cadence_resolution` is the one place that
violates it, by storing the structural case.

So the answer to (b) is not "nothing frozen should carry provenance." It is
that this particular field is not provenance and never was.

**And on the self-describing objection**, which is a real one and worth
answering rather than waving past: a reader with only the YAML and no code
still knows which cadence was frozen (`cadence_minutes: 15`) and which
publication profile the run selected (`publication_profile_id`,
`publication_profile_version`, both in the frozen profile binding). What they
need is one system rule — only a publication profile supplies a cadence — not
a per-record field. Self-describing means *no fact unrecoverable*, not *every
fact restated*. A restatement that can contradict what it restates makes a
record less self-describing, not more, and this one did.

---

## (c) Why did the parser not catch it?

Taken literally, this has a boring answer, and it is worth getting out of the
way so the interesting version is visible.

The parser validates a document: shape, vocabulary membership, cross-field
agreement. "Can the named party supply the thing claimed?" is not a question
about the document — it is a question about the world the document refers to.
The scenario parser has no access to profiles, Sites or kernels **by design**;
that is the parser/service split this codebase names in four places. Asking it
to check effective binding would mean handing it the whole world, and the
thing it would lose is the property that a document is valid or invalid on its
own terms.

There is a second reason this specific field was uncatchable by any layer:
**`cadence_resolution` is written by the resolver, as a label on its own act.**
`resolve_observation_binding` sets it at the moment it reads
`profile.device_signal_cadence_minutes`. No validator downstream can check a
resolver's own label against anything, because the resolver is the authority
for the act it is labelling. A statement nothing can contradict is a statement
nothing can check — which is the argument that it should not be stored at all,
arriving from a different direction.

**But the question behind the question is the important one, and the answer is
yes: this is a family.** The right place for an effective-binding check is not
the parser. It is the *resolver* — and the codebase already has exactly one
that does it properly. `FoundationBinding` declares "a `FUEL_TANK` component
rated in `L` will answer for this", and run setup resolves that claim against
a real Site and blocks when it does not hold. That is a capability declared in
data and checked against the structure that must honour it, and it works.

`supported_states` is the same shape of declaration with no such check.
`MINIMAL_FUEL_TANK_MODEL` declares that `fuel-tank-volume` supports
`CAUSAL_INPUT` and `REPORTED_OBSERVATION`. Nothing in this build can cause or
report anything. The declaration is a promise about a kernel that does not
exist, and `READY` is computed from it, which is precisely what the T019 review
caught.

---

## One root cause, or three?

One. And it can be stated in a sentence someone can apply to the next
vocabulary:

> **A declaration is worth storing only where being wrong causes a failure.
> Where nothing can fail, the declaration is decoration, and decoration
> drifts.**

Test it against all five:

- `FoundationBinding` — wrong, and the run blocks. Earns its place.
- `device_signal_cadence_minutes` — absent, and the run blocks. Earns it.
- `cadence_resolution` — wrong, and the only thing that checks it is the fact
  it restates, so being wrong causes **agreement**. Drifted from the day it
  was written.
- `supported_states` — wrong, and nothing happens **yet**. T021's conformance
  test is exactly the thing that makes being wrong cause a failure.
- OQ3 — the model profile claimed authority over a reporting-path state; the
  run blocked either way, so the claim was never tested. Being wrong caused
  agreement.

**The project already owns this rule.** `.ai/ARCHITECTURE.md`, under Causal
Runtime Authority:

> *"An expectation is legitimate when it occupies a position where being wrong
> causes a failure, and circular when it occupies a position where being wrong
> causes agreement."*

That is the same sentence. It was written about **authored scenario
expectations** — oracles versus consequences — and accepted on 2026-09-21. It
was never applied to **configuration and provenance**, which is where all
three of these live. The rule did not fail; its scope did.

This also explains something that has been treated as a compromise and is
actually the correct move: **the `READY` disclosure.** `supported_states` is a
declaration whose falsifier is scheduled rather than absent. You cannot check
it until a kernel exists. Disclosing what the status does not assert, and
naming the condition that retires the disclosure, is the honest statement of
"this declaration has no falsifier yet." It is the rule being obeyed, not
dodged.

---

## Way forward, and it is small

Three instances, three different stages, and only one of them is work now.

### Now, in T020: delete `cadence_resolution` rather than rename it

This is a smaller change than the rename I recommended, and strictly better on
every axis I checked:

- **The 34 local Drafts survive.** Stored run documents do not reject unknown
  keys — `_parse_observation_binding` reads named keys through `_mapping`,
  and unknown-key rejection exists only on the *setup request* path
  (`REQUEST_KEYS`, `INTERVAL_KEYS`, `PROFILE_KEYS`, `RUN_INPUT_KEYS`). Removing
  the field leaves the key in old documents, harmlessly ignored. **The entire
  store-clearing cost disappears**, which was the only real cost of the rename
  and the thing that made the timing urgent.
- **The parser gets simpler.** The fourteen-line biconditional goes, replaced
  by the rule that was underneath it all along: an `OPERATOR_RECORD` carries no
  cadence, a `DEVICE_SIGNAL` carries one or none.
- **`provenance.py` branches on `(source_kind, cadence_minutes)`** instead of
  on a third vocabulary that has to be kept honest.
- **No new name to get wrong**, and no member to re-examine if a second thing
  ever becomes able to declare a cadence. At that point the field would earn
  its place, and the right moment to add it is then, with something able to
  fail when it is wrong.

Two things to confirm rather than assume, and I have not:

1. This narrows the **run record** shape, not the scenario document shape, so
   under `D-2026-09-22-contract-version-scope` it should not move
   `EXECUTION_CONTRACT_VERSION`. Worth the user confirming that reading rather
   than the Implementer deciding it.
2. `cadence_resolution` sits in the **rendered** half of T019's field audit
   (`test_run_setup.py:1225`), so removing it removes a row from that audit.
   That is the audit working, not breaking.

Surface: the frozenset in `runs/models.py:146`, the writer in
`runs/profiles.py:163`, the reader branch in `runs/provenance.py:266`, two
parser messages, five test assertions, no frontend references.

### Later, in T021: `supported_states` gets its falsifier

Nothing to do now, and this is the honest "it waits for a kernel" answer. The
conformance test deriving `supported_states` from the kernel is the structural
remedy for the largest member of this family, and it cannot exist before the
kernel does. Until then the `READY` disclosure is the correct interim and
`D-2026-09-22-expiry-follows-the-condition` already names its condition.

The one thing worth adding to the record's understanding of T021, whenever the
Planner next touches it: that conformance test is not a quality measure, it is
the falsifier that makes `supported_states` a legitimate declaration rather
than a decorative one. If it is ever descoped, `supported_states` goes back to
being a promise, and `READY` goes back to overreaching.

### Already handled: OQ3

`D-2026-09-22-forcing-state-requirements` moves reporting-path authority to
the publication profile in T020B. That removes the declaration rather than
checking it, which for that instance was the right answer: a model profile
should not have been able to claim a reporting-path state at all.

### Accepted as is

`FoundationBinding` and the profile type structure are the pattern working.
Nothing to change, and they are the reference for what "checked against the
structure that must honour it" looks like in this codebase.

### Optionally durable, and the user's call

Extending the `.ai/ARCHITECTURE.md` sentence's reach from authored
expectations to configuration and provenance — two sentences in the paragraph
that already carries it, not a new section. Three instances is the "repeated
experience" the Change Rule asks for. It could also reasonably wait until
T021, when the pattern has been proved a third time by the conformance test
actually catching something. **I lean toward doing it now**, because the next
vocabulary is cheaper to get right than to fix, and this document exists
precisely because the pattern had no name when it recurred.

---

## What this means for the rename

**It is the wrong first move, and it is now moot.**

The reasoning behind it still holds: `MODEL_PROFILE` is false under every
reading, and a vocabulary of kinds with one party-shaped member is
inconsistent. None of that changes.

But it was a fix to the label on a field that should not exist, and it would
have cost 34 Drafts and a store-clearing window that deletion does not cost at
all. The user was right to stop it. **Delete the field in T020 instead**, and
the rename question never needs answering.

The Planner's holding scope limit keeping `CADENCE_RESOLUTIONS` out of T020
should still be lifted — but for a deletion rather than a rename, and the
lifting is the user's to authorise since this document records no decision.

---

## What I did not do

No decision recorded. No task file touched. No `.ai/ARCHITECTURE.md` change —
the extension above is a recommendation, not an edit. Nothing merged.
