"""The committed-artifact persistence port (T027, D4). Gated.

A Commit seals a run's eligible stage into one immutable `CommittedArtifact`
(`assetops_contracts.committed_artifact`) and files it here, once per run. The
port speaks artifacts only: no path, file handle or store-specific exception
crosses it.

There is no update and no delete. `create` writes the artifact exclusively and,
if this run already has one, returns the stored artifact UNCHANGED rather than
writing the new one (AC2): the caller decides what a differing stage digest
means. `get` re-reads and re-verifies the stored artifact every time, so a
tampered or truncated file is answered as unreadable, never as an artifact.

The store is built in `create_app` only when the Simulator Lab gate is open,
like the run store: committing is a Lab act. The artifact text itself is a
product contract, so it can be copied out and replayed through ingestion with
no Lab composed at all (AC14/AC15).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from assetops_contracts.committed_artifact import CommittedArtifact


class CommitStoreError(Exception):
    """Base class for the commit store's error vocabulary."""


class CommittedArtifactUnreadable(CommitStoreError):
    """A stored artifact exists and failed its own verification."""


class CommitStoreUnavailable(CommitStoreError):
    """The commit store could not be read or written."""


@runtime_checkable
class CommittedArtifactStore(Protocol):
    def get(self, run_id: str) -> CommittedArtifact | None:
        """The run's committed artifact, re-read and verified, or None.

        Raises:
            CommittedArtifactUnreadable: a stored artifact failed verification.
            CommitStoreUnavailable: the store could not be read.
        """
        ...

    def create(self, artifact: CommittedArtifact) -> CommittedArtifact:
        """File `artifact` once, or return the artifact already filed for its run.

        Never rewrites a stored artifact.

        Raises:
            CommittedArtifactUnreadable: a stored artifact failed verification.
            CommitStoreUnavailable: the store could not be written.
        """
        ...
