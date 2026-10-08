"""S2-01b phase 3a: the simulated device's exact half-to-even resolution.

`D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary`: after its
modeled bias, a simulated device rounds the exact rational once to its declared
quantum, ties to the even multiple, and the reading is then canonical finite
decimal text. Without a declared resolution nothing changes.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from assetops_contracts.observation import (
    DeviceSignalSpec,
    device_resolution,
    exact_decimal_text,
    quantize_half_even,
)

MICRO = Fraction(1, 1_000_000)


def published(value: Fraction) -> str:
    return exact_decimal_text(quantize_half_even(value, MICRO))


@pytest.mark.parametrize(
    ("exact", "text"),
    [
        # The phase-2 finding: 1035/19 percent is not a finite decimal.
        (Fraction(1035, 19), "54.473684"),
        (Fraction(1, 3), "0.333333"),
        (Fraction(2, 3), "0.666667"),
        # Ties go to the even multiple, both ways and either sign.
        (Fraction("0.0000005"), "0"),
        (Fraction("0.0000015"), "0.000002"),
        (Fraction("0.0000025"), "0.000002"),
        (Fraction("-0.0000005"), "0"),
        (Fraction("-0.0000015"), "-0.000002"),
        (Fraction("-0.0000025"), "-0.000002"),
        (Fraction("12.3456785"), "12.345678"),
        (Fraction("12.3456775"), "12.345678"),
        # Just off a tie is not a tie.
        (Fraction("0.00000050001"), "0.000001"),
        (Fraction("-0.00000049999"), "0"),
        # Negative non-terminating, and canonical text drops trailing zeros.
        (Fraction(-1, 3), "-0.333333"),
        (Fraction("2.5"), "2.5"),
        (Fraction(7), "7"),
        (Fraction("0.0000001"), "0"),
    ],
)
def test_the_device_rounds_half_to_even_and_publishes_canonical_decimal(exact, text) -> None:
    assert published(exact) == text
    assert "/" not in text and text != "-0" and not text.endswith("0") or text == "0"


def test_an_already_representable_value_is_unchanged() -> None:
    for exact in (Fraction("3.49875"), Fraction("-0.5"), Fraction(0), Fraction("100.000001")):
        assert quantize_half_even(exact, MICRO) == exact


def test_the_quantum_is_exact_and_positive() -> None:
    assert device_resolution("0.000001") == MICRO
    for bad in ("0", "-0.1", "1/3", "", None):
        with pytest.raises(ValueError):
            device_resolution(bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        quantize_half_even(Fraction(1), Fraction(0))


def spec(**overrides) -> DeviceSignalSpec:
    fields = dict(
        device_id="battery-pcs-controller",
        signal_id="state-of-charge",
        address="battery-state-of-charge@battery",
        state_key="battery-state-of-charge",
        reading_class="STATE_SIGNAL",
        canonical_unit="%",
        cadence_minutes=15,
        bias=Fraction(0),
        dropout_per_thousand=0,
        statement="s",
    )
    fields.update(overrides)
    return DeviceSignalSpec(**fields)


def test_a_spec_without_a_resolution_keeps_its_earlier_identity_fields() -> None:
    assert len(spec().as_fields()) == 9
    assert spec(resolution=MICRO).as_fields()[-1] == MICRO


def test_an_enum_spec_refuses_a_resolution() -> None:
    with pytest.raises(ValueError, match="no device resolution applies"):
        spec(canonical_unit="state", resolution=MICRO)
    with pytest.raises(ValueError, match="positive quantum"):
        spec(resolution=Fraction(0))
