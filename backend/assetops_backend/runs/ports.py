"""The SimulationRun persistence port, owned by the product domain.

Modelled on `sites/ports.py` and `scenarios/ports.py`, and holding the same
line for the same reason: the port is the seam that makes storage replaceable,
so its signatures and its errors speak domain records only. No `Path`, no file
handle, no YAML text, no loader `dict`, and no store-specific exception may
cross it.

A third parallel error family, deliberately not a reuse of either existing
one. A missing run, a missing Site and a missing scenario are three different
facts about three different identity spaces, and a caller that caught
`SiteNotFound` around a run lookup has already confused two of them.

Unlike the scenario port, this one writes. T019 is the slice that creates
Drafts, so `create_run` exists and one adapter implements it - and exactly
one, which `tools/checks/configuration-persistence.ps1` holds by registering
the run domain beside the two configuration domains. A run is not
configuration, but the persistence seam it needs is the same one, and a
second write path would be a second set of atomicity guarantees nobody wrote.

There is no update, no delete, and no commit, because nothing in this build
can change a Draft once it exists. A run's frozen inputs are frozen: the whole
point of the record is that it cannot drift out from under a later execution.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from assetops_backend.runs.models import SimulationRun


class RunRepositoryError(Exception):
    """Base class for the run port's error vocabulary."""


class RunNotFound(RunRepositoryError):
    """No run with the requested `run_id` exists."""


class RunIdentityConflict(RunRepositoryError):
    """A `run_id` is already in use.

    Allocation makes this all but impossible, which is exactly why it is
    raised rather than tolerated: if it ever happens, something is allocating
    identities somewhere it should not be, and silently overwriting the first
    run would destroy a record a later execution was bound to.
    """


class RunConfigurationInvalid(RunRepositoryError):
    """A stored run document is not a valid run record.

    Raised by the strict parser and by adapters that meet undecodable or
    unparseable stored content. A run document is written by the product and
    read back by the product, so meeting this means either a defect or a
    hand-edited store; either way the message names what is wrong.
    """


class RunStoreUnavailable(RunRepositoryError):
    """The run store could not be read or written.

    Distinct from `RunConfigurationInvalid`: the content was never reached, so
    nothing is known about whether it is valid. A setup that cannot write must
    say the store could not be reached rather than that the run was refused.
    """


@runtime_checkable
class SimulationRunRepository(Protocol):
    """Persistence for Draft SimulationRuns.

    Three methods. `create_run` is the only write in the domain, and the
    absence of an update or a delete is structural rather than a convention:
    no caller can change a frozen run, because there is no method that could.
    """

    def create_run(self, record: SimulationRun) -> SimulationRun:
        """Persist a new Draft, or write nothing at all.

        Raises:
            RunIdentityConflict: the `run_id` is already in use.
            RunConfigurationInvalid: the record does not survive a round trip
                through the store's own reader.
            RunStoreUnavailable: the store could not be written.
        """
        ...

    def get_run(self, run_id: str) -> SimulationRun:
        """Return one run by identity.

        Raises:
            RunNotFound: no such `run_id`.
            RunConfigurationInvalid: a stored document is invalid.
            RunStoreUnavailable: the store could not be read.
        """
        ...

    def list_runs(self) -> Sequence[SimulationRun]:
        """Return every persisted run.

        Raises:
            RunConfigurationInvalid: a stored document is invalid.
            RunStoreUnavailable: the store could not be read.
        """
        ...
