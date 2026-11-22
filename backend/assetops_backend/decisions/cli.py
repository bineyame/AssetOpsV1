"""6a (spec §4; handshake I8): what the three decision commands share: the refusal line, the time form, the flag
parsers (every value arrives as `str`; a malformed one is the service's code) and the composition and run wrapper."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import UUID

from assetops_backend.decisions.records import DecisionRefused, refusal_sentence


def refuse(code: str, status: int = 2) -> int:
    sys.stderr.write(f"{code} {refusal_sentence(code)}\n")
    return status


def iso_seconds(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def as_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise DecisionRefused("BAD_UUID") from None


def as_decimal(value: str, code: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        raise DecisionRefused(code) from None


def as_int(value: str, code: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise DecisionRefused(code) from None


def run(args: Any, services: Any, clock: Callable[[], datetime] | None, act: Callable[[Any], dict]) -> int:
    """Compose the service when none is given, run `act(service)` and print its one JSON line."""
    import json

    from assetops_backend.accounts.composition import ACCOUNTS_UNAVAILABLE

    composed = None
    if services is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            return refuse("NO_DATABASE")
        from assetops_backend.decisions.decisions_composition import build_decisions

        try:
            composed = services = build_decisions(url) if clock is None else build_decisions(url, clock=clock)
        except Exception:  # noqa: BLE001 - any composition error is the store being unreachable
            return refuse("DECISIONS_UNAVAILABLE", 3)
    try:
        line = act(services.service)
    except DecisionRefused as refused:
        return refuse(refused.code, refused.exit)
    except ACCOUNTS_UNAVAILABLE:
        return refuse("DECISIONS_UNAVAILABLE", 3)
    finally:
        if composed is not None:
            composed.dispose()
    sys.stdout.write(json.dumps(line) + "\n")
    return 0
