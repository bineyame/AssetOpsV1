"""Persisted assessment history (T028 AC13).

A lineage is one assessed generator interval across reassessments. Each
revision keeps its own evidence basis, model version and assessed window, so a
prior assessment stays inspectable after a revision supersedes it. Nothing is
overwritten: a changed basis appends a revision; a lineage no longer matched by
any interval is retired, and keeps its revisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AssessmentRevision:
    revision: int
    assessed_at: str
    model_version: str
    basis_digest: str
    #: The analytic's full payload for this interval at this revision.
    assessment: dict[str, Any]


@dataclass(frozen=True)
class AssessmentLineage:
    #: Stable id of the assessed object; the Finding id when it raises one.
    assessment_id: str
    site_id: str
    analytic_id: str
    finding_type: str
    active: bool
    retired_at: str | None
    revisions: tuple[AssessmentRevision, ...]

    @property
    def latest(self) -> AssessmentRevision:
        return self.revisions[-1]


@dataclass(frozen=True)
class AssessmentHistory:
    site_id: str
    lineages: tuple[AssessmentLineage, ...] = field(default_factory=tuple)
