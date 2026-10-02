"""T025g AC3 guardrail: template lineage is run provenance, never a world input.

The run's site binding freezes the Site's template lineage. It must stay out of
`FrozenWorldInputs` and out of `frozen_inputs_identity`, or adding it would
itself change every pinned digest (Architect section 6, revision 3). The
contract-9 gate reproducing unchanged is the end-to-end proof; this is the
direct one, on a Draft built through the product's own setup from the shipped
Kobo template.
"""

from __future__ import annotations

import dataclasses

from kobo import kobo_draft

from assetops_backend.runs.models import FrozenTemplateLineage
from assetops_contracts.trajectory import frozen_inputs_identity
from execution_adapter import frozen_world_inputs


def with_lineage(run, lineage):
    identity = run.deterministic_identity
    return dataclasses.replace(
        run,
        deterministic_identity=dataclasses.replace(
            identity,
            site=dataclasses.replace(identity.site, template_lineage=lineage),
        ),
    )


def identity_of(inputs) -> str:
    return frozen_inputs_identity(
        inputs,
        kernel_version=1,
        model_profile_id="daytime-mini-grid",
        model_profile_version=1,
        numeric_policy="x",
    )


def test_a_kobo_draft_freezes_its_template_lineage() -> None:
    lineage = kobo_draft().deterministic_identity.site.template_lineage

    assert lineage is not None
    assert lineage.template_id == "kobo-mini-grid-60kw"
    assert lineage.template_version is not None


def test_lineage_changes_neither_world_inputs_nor_their_identity() -> None:
    run = kobo_draft()
    variants = [
        run,
        with_lineage(run, None),
        with_lineage(
            run, FrozenTemplateLineage(template_id=None, template_version=None)
        ),
        with_lineage(
            run,
            FrozenTemplateLineage(
                template_id="some-other-template", template_version=99
            ),
        ),
    ]

    inputs = [frozen_world_inputs(variant) for variant in variants]

    assert all(item == inputs[0] for item in inputs)
    assert len({identity_of(item) for item in inputs}) == 1
