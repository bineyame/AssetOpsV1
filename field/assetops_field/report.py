"""One aggregation result as one public `DeviceReport` V1 text (ruling D4)."""

from __future__ import annotations

from datetime import datetime, timedelta
from fractions import Fraction

from assetops_contracts.gateway_report import (
    MEASUREMENT_OF_READING_CLASS,
    DeviceReport,
    device_report_text,
    parse_device_report_text,
)
from assetops_contracts.observation import exact_decimal_text

from assetops_field.aggregate import Result
from assetops_field.profile import FieldProfile, ProfileRow, report_key_text


def instant_z(instant: datetime) -> str:
    if instant.tzinfo is None or instant.utcoffset() != timedelta(0) or instant.microsecond:
        raise ValueError(f"{instant!r} is not a whole-second UTC instant")
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ")


def report_key(profile: FieldProfile, row: ProfileRow, source_time: datetime) -> str:
    return report_key_text(profile.profile_id, profile.profile_version, row.device_id, row.signal_id,
                           instant_z(source_time))


def build_report(profile: FieldProfile, row: ProfileRow, result: Result) -> DeviceReport:
    measurement = MEASUREMENT_OF_READING_CLASS[row.reading_class]
    interval_start = None
    if measurement == "INTERVAL_MEAN":
        if result.interval_start is None:
            raise ValueError("every INTERVAL_MEAN carries its span, UNAVAILABLE included")
        interval_start = instant_z(result.interval_start)
    if isinstance(result.value, Fraction):
        value = exact_decimal_text(result.value)
    else:
        value = result.value
    return DeviceReport(
        report_key=report_key(profile, row, result.source_time),
        device_id=row.device_id,
        signal_id=row.signal_id,
        source_time=instant_z(result.source_time),
        measurement=measurement,
        interval_start=interval_start,
        value=value,
        unit=row.source_unit,
        quality=result.quality,
        unavailable_reason=result.reason,
    )


def report_text(report: DeviceReport) -> str:
    text = device_report_text(report)
    if parse_device_report_text(text) != report:
        raise ValueError("the report text does not round-trip through parse_device_report_text")
    return text
