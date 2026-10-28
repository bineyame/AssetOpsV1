"""Register words to an exact value, and back (build spec TEL-01, Q-T14, Q-T15).

Per register the words are combined by `word_order` into an unsigned integer of
the register's width. The sentinel check runs first, on that unsigned value, for
every register: any sentinel register makes the whole row `SENTINEL`. Then
two's complement applies to `int*` types. A multi-register `NUMBER` row is the
exact sum of its signed raw values, scaled once by `10^exponent`. Arithmetic is
`Fraction` throughout.

`encode_value` and `encode_sentinel` exist for the emulator, so encoding and
decoding cannot disagree silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from assetops_field.profile import ProfileRow, RegisterRef


@dataclass(frozen=True)
class Decoded:
    kind: str  # "VALUE" | "SENTINEL" | "STATE"
    value: Fraction | None = None
    state: str | None = None


class DecodeFault(ValueError):
    """A configuration fault: wrong word count, or an unmapped enum code."""


ENCODE_CODES = ("OUT_OF_RANGE", "NOT_A_MULTIPLE", "UNKNOWN_STATE")


class EncodeRefused(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        if code not in ENCODE_CODES:
            raise ValueError(f"unknown encode refusal code {code!r}")
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def _combine(register: RegisterRef, words: Sequence[int]) -> int:
    for word in words:
        if type(word) is not int or not 0 <= word <= 0xFFFF:
            raise DecodeFault(f"{word!r} is not a 16-bit word")
    if register.words == 1:
        return words[0]
    high, low = (words[0], words[1]) if register.word_order == "BIG" else (words[1], words[0])
    return (high << 16) | low


def _signed(register: RegisterRef, unsigned: int) -> int:
    if register.signed and unsigned >= 1 << (register.bits - 1):
        return unsigned - (1 << register.bits)
    return unsigned


def _split(register: RegisterRef, unsigned: int) -> list[int]:
    if register.words == 1:
        return [unsigned]
    high, low = unsigned >> 16, unsigned & 0xFFFF
    return [high, low] if register.word_order == "BIG" else [low, high]


def decode_words(row: ProfileRow, words_per_register: Sequence[Sequence[int]]) -> Decoded:
    if row.decode not in ("NUMBER", "ENUM"):
        raise DecodeFault(f"row {row.row_id} has no register decode")
    if len(words_per_register) != len(row.registers):
        raise DecodeFault(f"row {row.row_id} reads {len(row.registers)} registers, got {len(words_per_register)}")
    unsigned = []
    for register, words in zip(row.registers, words_per_register):
        if len(words) != register.words:
            raise DecodeFault(f"a {register.type} register is {register.words} words, got {len(words)}")
        unsigned.append(_combine(register, words))
    if any(value in row.sentinels for value in unsigned):
        return Decoded("SENTINEL")
    raws = [_signed(register, value) for register, value in zip(row.registers, unsigned)]
    if row.decode == "ENUM":
        state = row.enum_map.get(raws[0]) if row.enum_map is not None else None
        if state is None:
            raise DecodeFault(f"row {row.row_id}: enum code {raws[0]} is not mapped")
        return Decoded("STATE", state=state)
    return Decoded("VALUE", value=Fraction(sum(raws)) * Fraction(10) ** row.exponent)


def encode_value(row: ProfileRow, value: Fraction | str) -> list[list[int]]:
    """The register words a device would present for `value` (emulator only).

    `NUMBER`: the whole raw value goes on the first register and 0 on every
    other register of a multi-register row, by contract. `ENUM`: the state
    text's code. Quantization to the register is the caller's job.
    """
    if row.decode == "ENUM":
        codes = sorted(code for code, state in (row.enum_map or {}).items() if state == value)
        if not codes:
            raise EncodeRefused("UNKNOWN_STATE", f"{value!r} is not a state of row {row.row_id}")
        return [_split(row.registers[0], codes[0])]
    if row.decode != "NUMBER":
        raise ValueError(f"row {row.row_id} has no register decode")
    exact = Fraction(value)
    raw = exact / Fraction(10) ** row.exponent
    if raw.denominator != 1:
        raise EncodeRefused("NOT_A_MULTIPLE", f"{value} is not a whole multiple of 10^{row.exponent}")
    first = row.registers[0]
    low = -(1 << (first.bits - 1)) if first.signed else 0
    high = (1 << (first.bits - 1)) - 1 if first.signed else (1 << first.bits) - 1
    raw_int = raw.numerator
    if not low <= raw_int <= high:
        raise EncodeRefused("OUT_OF_RANGE", f"raw {raw_int} does not fit {first.type}")
    unsigned = raw_int & ((1 << first.bits) - 1)
    if unsigned in row.sentinels:
        raise EncodeRefused("OUT_OF_RANGE", f"raw {raw_int} is a declared sentinel")
    words = [_split(first, unsigned)]
    words += [[0] * register.words for register in row.registers[1:]]
    return words


def encode_sentinel(row: ProfileRow) -> list[list[int]]:
    """The first declared sentinel on every register of the row."""
    if not row.sentinels or not row.registers:
        raise ValueError(f"row {row.row_id} declares no sentinel")
    # `sentinels` is a set, so "first" is read as the smallest (recorded in the T1 packet).
    sentinel = min(row.sentinels)
    return [_split(register, sentinel) for register in row.registers]
