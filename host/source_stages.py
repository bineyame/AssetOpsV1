"""Persisted Draft stages under `var/stages`: append-only, atomic, verified.

The leaf's, for the reason the private execution artifacts are the leaf's: a
stage is a Simulator Lab artifact rather than a product record, and the product
reads one only through the execution port, as a verified `SourceStageView`. It
cannot name a file, a directory or a format.

## What a write guarantees

One file per run, written whole: the new text goes to a `.partial` sibling and is
moved over the stage in one `os.replace`. A process that dies mid-write leaves
either the previous complete stage or a `.partial` nobody reads - never a shorter
file that parses. A stage that IS damaged on disk - truncated, edited, or written
by something else - fails `parse_stage_text` and reads as `STAGE_UNREADABLE`.

## What it does not offer

No update, no delete, no rewrite of an envelope. `admit` appends through the
contract's own `admit`, and an unreadable stage is never overwritten: staging
into one raises, so the damaged record stays as evidence of what went wrong.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from assetops_contracts.source_envelope import SourceEnvelope, SourceMappingSet
from assetops_contracts.source_stage import (
    Admission,
    SourceStage,
    StageConflict,
    admit,
    parse_stage_text,
    stage_text,
    with_refusal,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

#: Gitignored user data beside `var/executions`, and like it safe to delete: a
#: run whose stage is gone reads as `NOT_STAGED`.
STAGE_ROOT = REPOSITORY_ROOT / "var" / "stages"


class JsonSourceStages:
    """One canonical JSON document per run."""

    def __init__(self, root: Path = STAGE_ROOT) -> None:
        self._root = root

    def path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def read(self, run_id: str) -> SourceStage | None:
        """The verified stage, `None` when there is none.

        Raises:
            StageUnreadable: a stage exists and fails verification.
        """
        path = self.path(run_id)
        if not path.is_file():
            return None
        return parse_stage_text(path.read_text(encoding="utf-8"), run_id)

    def _write(self, stage: SourceStage) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self.path(stage.run_id)
        partial = path.with_name(path.name + ".partial")
        partial.write_text(stage_text(stage), encoding="utf-8")
        os.replace(partial, path)

    def admit(
        self,
        *,
        run_id: str,
        site_id: str,
        source_id: str,
        gateway_id: str,
        mapping: SourceMappingSet,
        envelopes: Sequence[SourceEnvelope],
        boundaries_total: int = 0,
        published_through: int | None = None,
    ) -> Admission:
        """Append new envelopes; accept identical retries; refuse conflicts.

        A conflict leaves every staged envelope as it was and records the refused
        message id on the stage, so the refusal is visible after a reload and
        blocks release eligibility, and then re-raises it.

        Raises:
            StageConflict: an envelope conflicts with the staged content.
            StageUnreadable: the stage on disk cannot be verified; it is left
                untouched rather than replaced.
        """
        existing = self.read(run_id)
        stage = (
            SourceStage(
                run_id=run_id,
                site_id=site_id,
                source_id=source_id,
                gateway_id=gateway_id,
                mapping=mapping,
                boundaries_total=boundaries_total,
            )
            if existing is None
            else existing
        )
        try:
            admission = admit(
                stage, envelopes, published_through=published_through
            )
        except StageConflict as conflict:
            if existing is not None:
                self._write(with_refusal(existing, conflict))
            raise
        # Written whenever anything changed, the watermark included: a batch
        # that adds nothing but covers one more boundary is still progress, and
        # the watermark is only ever as far as what was WRITTEN.
        if existing is None or admission.stage != existing:
            self._write(admission.stage)
        return admission
