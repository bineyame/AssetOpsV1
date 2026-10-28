"""The illustrative generic interval CSV collector (TEL-06, proof B1, Q-T65).

`assetops-generic-interval-csv/1` is a format defined by AssetOps for the
October proof. It is illustrative and is not any vendor's export format (owner
Q7 = (c)). One file is validated whole before anything crosses the gateway
channel: a refusal raises `CsvRefused(code, field, detail, profile_sha256)`
with one of the eight `CSV_CODES`, and no admission is made.

File grammar (build spec TEL-06):
- UTF-8 without a BOM, comma delimiter, LF or CRLF line ends, read with `csv`.
- Header: `timestamp_utc`, then one `<column> [<unit>]` per profile row, in any
  order. The bracket unit becomes the report unit verbatim; it is not compared
  with the profile, so a wrong unit reaches the gateway and is held there.
- Each data row is one interval `[t - span, t)` ending at `timestamp_utc`
  (`YYYY-MM-DDTHH:MM:SSZ`, a whole multiple of the span from 00:00:00Z),
  strictly increasing. A blank cell is `UNAVAILABLE` / `NO_MEASUREMENT`;
  otherwise a decimal with `.` and no thousands separator that is an exact
  multiple of the row's `output_resolution`.

The collector is not an aggregator: each cell is one report as written.
"""

from __future__ import annotations

import csv
import dataclasses
import io
import re
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from assetops_contracts.gateway_report import DeviceReport

from assetops_field.aggregate import Result
from assetops_field.profile import FieldProfile, ProfileRow
from assetops_field.publish import GatewayPublisher
from assetops_field.report import build_report, report_text

FORMAT = "assetops-generic-interval-csv/1"
CSV_CODES = ("ENCODING", "EMPTY_FILE", "HEADER_MISMATCH", "INVALID_TIMING", "SPAN_MISMATCH",
             "DUPLICATE_ROW", "UNSORTED_ROWS", "INVALID_VALUE")
TIMESTAMP_COLUMN = "timestamp_utc"

_BOM = b"\xef\xbb\xbf"
_HEADER_CELL = re.compile(r"([a-z][a-z0-9_]{0,63}) \[([^\]]+)\]")
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_DECIMAL = re.compile(r"-?[0-9]+(\.[0-9]+)?")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class CsvRefused(ValueError):
    """A whole CSV file refused before any admission; names the profile it was checked against."""

    def __init__(self, code: str, field: str, detail: str, profile_sha256: str) -> None:
        if code not in CSV_CODES:
            raise ValueError(f"unknown CSV refusal code {code!r}")
        self.code, self.field, self.detail, self.profile_sha256 = code, field, detail, profile_sha256
        super().__init__(f"{code} at {field}: {detail} (profile sha256 {profile_sha256})")


class CsvCollector:
    def __init__(self, profile: FieldProfile, publisher: GatewayPublisher) -> None:
        if profile.interface != "EXPORT_CSV":
            raise ValueError(f"profile interface {profile.interface} is not EXPORT_CSV")
        self.profile = profile
        self.publisher = publisher
        self._columns: dict[str, ProfileRow] = {}
        for row in profile.rows:
            assert row.csv is not None and row.span_seconds is not None and row.output_resolution is not None
            self._columns[row.csv.column] = row
        self.span_seconds = profile.rows[0].span_seconds

    def _refuse(self, code: str, field: str, detail: str) -> CsvRefused:
        return CsvRefused(code, field, detail, self.profile.sha256)

    # --- whole-file validation -------------------------------------------------------------------------

    def _text(self, path: Path) -> str:
        data = path.read_bytes()
        if data.startswith(_BOM):
            raise self._refuse("ENCODING", "file", "a UTF-8 byte order mark is not accepted")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise self._refuse("ENCODING", "file", f"not UTF-8 at byte {error.start}") from error

    def _header(self, header: list[str]) -> list[tuple[ProfileRow, str]]:
        if not header or header[0] != TIMESTAMP_COLUMN:
            found = header[0] if header else None
            raise self._refuse("HEADER_MISMATCH", "header[0]", f"{TIMESTAMP_COLUMN!r} is wanted, not {found!r}")
        columns: list[tuple[ProfileRow, str]] = []
        seen: set[str] = set()
        for index, cell in enumerate(header[1:], start=1):
            match = _HEADER_CELL.fullmatch(cell)
            if match is None:
                raise self._refuse("HEADER_MISMATCH", f"header[{index}]", f"{cell!r} is not '<column> [<unit>]'")
            column, unit = match.group(1), match.group(2)
            if column not in self._columns:
                raise self._refuse("HEADER_MISMATCH", f"header[{index}]", f"{column!r} is not a profile column")
            if column in seen:
                raise self._refuse("HEADER_MISMATCH", f"header[{index}]", f"{column!r} appears twice")
            seen.add(column)
            columns.append((self._columns[column], unit))
        missing = sorted(set(self._columns) - seen)
        if missing:
            raise self._refuse("HEADER_MISMATCH", "header", f"missing profile columns {missing}")
        return columns

    def _timestamp(self, cell: str, field: str) -> datetime:
        if _TIMESTAMP.fullmatch(cell) is None:
            raise self._refuse("INVALID_TIMING", field, f"{cell!r} is not YYYY-MM-DDTHH:MM:SSZ")
        try:
            instant = datetime.strptime(cell, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError as error:
            raise self._refuse("INVALID_TIMING", field, f"{cell!r} is not a calendar instant") from error
        if int((instant - _EPOCH).total_seconds()) % self.span_seconds:
            raise self._refuse("SPAN_MISMATCH", field,
                               f"{cell} is not a whole multiple of {self.span_seconds} s from 00:00:00Z")
        return instant

    def _value(self, row: ProfileRow, cell: str, field: str) -> Fraction | None:
        if cell == "":
            return None
        if _DECIMAL.fullmatch(cell) is None:
            raise self._refuse("INVALID_VALUE", field, f"{cell!r} is not a decimal with '.' as separator")
        value = Fraction(cell)
        if (value / row.output_resolution).denominator != 1:
            raise self._refuse("INVALID_VALUE", field,
                               f"{cell} is not a multiple of the output resolution {row.output_resolution}")
        return value

    def reports(self, path: Path) -> list[DeviceReport]:
        """Validate the whole file, then build one report per cell; raises `CsvRefused`; no IPC."""
        lines = list(csv.reader(io.StringIO(self._text(path), newline="")))
        if not lines:
            raise self._refuse("EMPTY_FILE", "file", "the file has no header and no data rows")
        columns = self._header(lines[0])
        if len(lines) == 1:
            raise self._refuse("EMPTY_FILE", "file", "the file has a header and no data rows")
        span = timedelta(seconds=self.span_seconds)
        order = {row.row_id: index for index, row in enumerate(self.profile.rows)}
        built: list[DeviceReport] = []
        previous: datetime | None = None
        for index, cells in enumerate(lines[1:]):
            path_text = f"rows[{index}]"
            if len(cells) != len(columns) + 1:
                # Provisional code, see .agent/TEL-06-questions.md Q6.
                raise self._refuse("INVALID_VALUE", path_text,
                                   f"{len(cells)} cells where the header has {len(columns) + 1}")
            end = self._timestamp(cells[0], f"{path_text}.{TIMESTAMP_COLUMN}")
            if previous is not None and end == previous:
                raise self._refuse("DUPLICATE_ROW", f"{path_text}.{TIMESTAMP_COLUMN}", f"{cells[0]} repeats")
            if previous is not None and end < previous:
                raise self._refuse("UNSORTED_ROWS", f"{path_text}.{TIMESTAMP_COLUMN}",
                                   f"{cells[0]} is earlier than the row before")
            previous = end
            row_reports = []
            for (row, unit), cell in zip(columns, cells[1:]):
                value = self._value(row, cell, f"{path_text}.{row.csv.column}")
                if value is None:
                    result = Result("UNAVAILABLE", "NO_MEASUREMENT", None, end, end - span)
                else:
                    result = Result("GOOD", None, value, end, end - span)
                report = dataclasses.replace(build_report(self.profile, row, result), unit=unit)
                row_reports.append((order[row.row_id], report))
            built.extend(report for _, report in sorted(row_reports, key=lambda item: item[0]))
        return built

    # --- publishing ------------------------------------------------------------------------------------

    def collect(self, path: Path) -> dict[str, Any]:
        """`reports()`, then one admission in file order, then `seal_and_release` (Q-T65)."""
        texts = [report_text(report) for report in self.reports(path)]
        admissions = self.publisher.admit(texts)
        sealed = self.publisher.seal_and_release()
        # Return keys are provisional, see .agent/TEL-06-questions.md Q7.
        return {"profile_sha256": self.profile.sha256, "report_count": len(texts), "admissions": admissions,
                "sealed": sealed}
