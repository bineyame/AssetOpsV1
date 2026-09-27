"""The contract's own arithmetic, and the cycle this kernel runs it in.

Two things are protected here.

The two dispatch formulas, against the worked examples their own statements
name. `window-overlap` says a two-minute window concerns one step when it lies
inside one and two when a step boundary falls inside it, and `window-ramp` says
`[1499, 1501)` at a fifteen-minute timestep is half and half so a declared 120
litres moves 60 in each. Those sentences were prose until this slice; here they
are numbers.

The boundary cycle, as the contract's declared order rather than this kernel's
layout. `declared_phase_order` reads `BOUNDARY_CYCLE.sequence`, and a phase in
the contract with no implementation raises rather than being skipped.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from assetops_contracts.execution_contract import (
    BOUNDARY_CYCLE,
    NUMERIC_POLICY,
    canonical_fraction,
    normalize_authored_float,
    overlap_minutes,
    point_due_at,
    step_concerns_window,
    steps_concerning_window,
    window_share_of_step,
)
from assetops_simulator.kernel.execute import _PHASES, declared_phase_order


class TestWhichStepsAWindowConcerns:
    def test_an_aligned_window_selects_the_steps_starting_inside_it(
        self,
    ) -> None:
        """The shipped removal, at the timestep the demonstration uses."""
        assert steps_concerning_window(2460, 15, 1500, 45) == (
            1500,
            1515,
            1530,
        )

    def test_the_step_beginning_at_the_end_of_a_window_is_outside_it(
        self,
    ) -> None:
        """A shared stretch of zero length is not a meeting."""
        assert step_concerns_window(1530, 15, 1500, 45) is True
        assert step_concerns_window(1545, 15, 1500, 45) is False
        assert overlap_minutes(1545, 15, 1500, 45) == 0

    def test_a_window_shorter_than_the_step_still_concerns_one(self) -> None:
        """A timestep decides how finely a window is resolved, never whether
        the window happened."""
        assert steps_concerning_window(2460, 15, 1501, 2) == (1500,)
        assert window_share_of_step(1500, 15, 1501, 2) == 1

    def test_the_same_short_window_straddling_a_boundary_concerns_two(
        self,
    ) -> None:
        """The statement's own example, and the reason a length is not a count.

        Two minutes, one answer of one step and one answer of two, from the same
        line of arithmetic.
        """
        assert steps_concerning_window(2460, 15, 1499, 2) == (1485, 1500)
        assert window_share_of_step(1485, 15, 1499, 2) == Fraction(1, 2)
        assert window_share_of_step(1500, 15, 1499, 2) == Fraction(1, 2)
        assert Fraction(120) * window_share_of_step(1485, 15, 1499, 2) == 60
        assert Fraction(120) * window_share_of_step(1500, 15, 1499, 2) == 60

    def test_a_window_off_the_grid_at_a_legal_hourly_timestep(self) -> None:
        """`[1500, 1545)` is off a sixty-minute grid and still selects a step."""
        assert steps_concerning_window(2460, 60, 1500, 45) == (1500,)
        assert window_share_of_step(1500, 60, 1500, 45) == 1

    def test_the_shares_sum_to_exactly_one_at_every_alignment(self) -> None:
        """The property that makes a declared quantity move in full.

        Exercised over a range of offsets, lengths and timesteps rather than the
        one alignment the shipped document happens to use, because the rule says
        it holds at every alignment and a single aligned case would not show it.
        """
        checked = 0
        for timestep in (5, 15, 60):
            for offset in (0, 7, 15, 1499, 1500, 2399):
                for length in (1, 2, 45, 90, 240):
                    if offset + length > 2460:
                        continue
                    steps = steps_concerning_window(
                        2460, timestep, offset, length
                    )
                    assert steps, (offset, length, timestep)
                    total = sum(
                        window_share_of_step(step, timestep, offset, length)
                        for step in steps
                    )
                    assert total == 1, (offset, length, timestep, total)
                    checked += 1
        assert checked >= 60, checked

    def test_a_step_the_window_does_not_concern_gets_exactly_zero(self) -> None:
        assert window_share_of_step(0, 15, 1500, 45) == 0

    def test_a_window_of_no_length_is_refused_rather_than_resolved(
        self,
    ) -> None:
        with pytest.raises(ValueError) as raised:
            window_share_of_step(0, 15, 100, 0)
        assert "point-applied-once" in str(raised.value)


class TestWhenAPointApplies:
    def test_a_point_belongs_to_the_step_that_begins_at_its_offset(
        self,
    ) -> None:
        steps = tuple(range(0, 2460, 15))
        assert point_due_at(steps, 15, 2400) == 2400

    def test_a_point_inside_a_step_is_applied_at_that_step_s_start(
        self,
    ) -> None:
        steps = tuple(range(0, 2460, 15))
        assert point_due_at(steps, 15, 2407) == 2400

    def test_a_point_outside_the_interval_is_due_nowhere(self) -> None:
        steps = tuple(range(0, 2460, 15))
        assert point_due_at(steps, 15, 2460) is None


class TestTheCycleThisKernelRuns:
    def test_the_order_is_the_contract_s_declared_sequence(self) -> None:
        expected = tuple(
            phase.phase_id
            for phase in sorted(BOUNDARY_CYCLE, key=lambda item: item.sequence)
        )
        assert declared_phase_order() == expected

    def test_every_declared_phase_has_an_implementation(self) -> None:
        """A phase added to the contract stops this kernel until it is built."""
        assert {phase.phase_id for phase in BOUNDARY_CYCLE} == set(_PHASES)

    def test_a_phase_with_no_implementation_is_refused_not_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The guard above proves the sets agree; this proves it would bite.

        Without this, the agreement could be a coincidence of two lists somebody
        keeps in step by hand, and nothing would say what happens when they stop
        agreeing.
        """
        monkeypatch.delitem(_PHASES, "evolve")
        with pytest.raises(RuntimeError) as raised:
            declared_phase_order()
        assert "evolve" in str(raised.value)
        assert "rather than being skipped" in str(raised.value)


class TestTheInputBoundaryIsTheOnlyApproximation:
    def test_an_authored_decimal_becomes_the_rational_it_was_written_as(
        self,
    ) -> None:
        assert normalize_authored_float(0.311) == Fraction(311, 1000)
        assert normalize_authored_float(430.0) == Fraction(430)

    def test_a_canonical_conversion_stays_exact(self) -> None:
        value, unit, dimension = canonical_fraction(14.0, "L/h")
        assert value == Fraction(14, 60)
        assert unit == "L/min"
        assert dimension == "VOLUME_RATE"
        assert value * 240 == Fraction(56)

    def test_the_policy_is_named_so_a_trajectory_can_say_which(self) -> None:
        assert NUMERIC_POLICY == "EXACT_RATIONAL"

    def test_no_kernel_module_limits_a_denominator(self) -> None:
        """v4 section 8.3's forbidden half, checked rather than intended.

        One-time authored-float normalization is allowed and lives in the
        contract's own input boundary. `limit_denominator` anywhere under
        `kernel/` or `packs/` would be a per-step approximation, and the phrase
        "exact rational runtime" would stop being true.
        """
        from pathlib import Path

        root = Path(__file__).resolve().parents[1] / "assetops_simulator"
        scanned = sorted(root.rglob("*.py"))
        assert len(scanned) >= 5, scanned
        offenders = [
            str(path.relative_to(root))
            for path in scanned
            if "limit_denominator" in path.read_text(encoding="utf-8")
            or "float(" in path.read_text(encoding="utf-8")
        ]
        assert offenders == [], offenders
