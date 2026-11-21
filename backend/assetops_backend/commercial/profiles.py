"""3A6 (spec §2.5; D-3A6.2, D-3A6.3, D-3A6.8, D-3A6.11): admitting a source profile, and reading uploads through one.

Admission is the contract test as product code. `check` and `admit` run the same steps on three files the analyst
hands in (the profile, a sample of the operator's export, and the records the sample must read to, written by hand):

1. the profile compiles (`compile_profile`), and its personal paths are ones 3A2 may pseudonymise;
2. its status follows the database (`PINNED` only where real data lives, `ILLUSTRATIVE` elsewhere);
3. a new version keeps its lineage (source type and source system), and no other profile reads that source system;
4. the sample reads with no refused row, holds 3 to 200 records, and exercises every written column, every map value
   and the order of its dates and numbers (4a to 4c);
5. every record equals its hand-written record exactly;
6. the six probes of `run_probes` refuse what they must.

`admit` then writes one `commercial_source_profile` row. Nothing of the sample or the expected file is kept but their
SHA-256 and the row count (RC4); no refusal carries a cell of the sample.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from uuid import UUID, uuid4

from assetops_backend.commercial.model import ProfileRow, StoreRefused
from assetops_backend.commercial.pseudonym import ALLOWED_EXTRA, CLASSES, cut_path
from assetops_backend.commercial.readers import LayoutReader, ReadContext
from assetops_backend.commercial.store import CommercialStore
from assetops_backend.commercial.uploads import Actor, UploadRefused, reason_words
from assetops_backend.i18n import Message, message, render
from assetops_contracts.canonical import CanonicalRefused, parse_batch
from assetops_contracts.native import (Layout, ProfileInvalid, TransformFailed, XlsxNumber, compile_profile,
                                       run_probes, split_file, transform)

MAX_PROFILE_BYTES = 64 * 1024
MAX_SAMPLE_BYTES = 2**20
SAMPLE_ROWS = range(3, 201)
_READER_ID = re.compile(r"profile\.([a-z][a-z0-9-]{0,47})\.v([1-9][0-9]{0,3})", re.ASCII)
_DAY_FIRST = ("DD/MM/YYYY", "MM/DD/YYYY", "DD-MM-YYYY", "DD.MM.YYYY")
_DATED = ("date", "datetime", "month_of")
#: The unique keys of `commercial_source_profile` (migration 0067): a refused insert is a concurrent admission.
_UNIQUE_KEYS = frozenset({"commercial_source_profile_version_key", "commercial_source_profile_reader_key",
                          "commercial_source_profile_sha256_key"})


class ProfileRefused(Exception):
    """A refused profile, sample or expected file. `params` are strings; no cell of the sample is ever one."""

    def __init__(self, code: str, params: Mapping[str, Any] | None = None, words: Message | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.params = {k: str(v) for k, v in (params or {}).items()}
        self.words = words if words is not None else message(f"source_profile.{code.lower()}", **self.params)


@dataclass(frozen=True)
class AdmissionReport:
    profile_id: str
    version: int
    reader: str
    source_type: str
    source_system: str
    sample_rows: int
    profile_sha256: str
    sample_sha256: str
    expected_sha256: str
    already: ProfileRow | None


@dataclass(frozen=True)
class _Admitted:
    report: AdmissionReport
    status: str
    file_format: str
    profile_json: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes) -> object:
    """Strict UTF-8 (a BOM is not stripped, so `json.loads` refuses it) then JSON; ValueError otherwise."""
    return json.loads(data.decode("utf-8", errors="strict"))


def _first_difference(a: object, b: object, path: str = "") -> str | None:
    """The first differing dotted path in sorted-key walk order (`record` when the root types differ)."""
    if type(a) is not type(b):
        return path or "record"
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            inner = f"{path}.{key}" if path else key
            if key not in a or key not in b:
                return inner
            found = _first_difference(a[key], b[key], inner)
            if found is not None:
                return found
        return None
    if isinstance(a, list):
        for i in range(max(len(a), len(b))):
            inner = f"{path}.{i}" if path else str(i)
            if i >= len(a) or i >= len(b):
                return inner
            found = _first_difference(a[i], b[i], inner)
            if found is not None:
                return found
        return None
    return None if a == b else (path or "record")


def _reads(type_: str, cell: str, values) -> bool:
    try:
        transform(type_, cell, values)
    except TransformFailed:
        return False
    return True


def _swap_day_month(fmt: str) -> str:
    return fmt.replace("DD", "\0").replace("MM", "DD").replace("\0", "MM")


def _coverage(layout: Layout, rows: list[tuple[int, list[str]]]) -> None:
    """Step 4a to 4c (D-3A6.11), on `split_file`'s rows; the first failure only."""
    columns = list(enumerate(layout.columns))
    for i, column in columns:  # 4a
        if column.paths and not any(cells[i] != "" for _, cells in rows):
            raise ProfileRefused("ADMIT_COLUMN_EMPTY", {"header": column.header})
    for i, column in columns:  # 4b: map keys in the profile file's order (compile keeps it)
        for pairs in column.maps.values():
            for key in pairs:
                if not any(cells[i] == key for _, cells in rows):
                    raise ProfileRefused("ADMIT_MAP_UNCOVERED", {"header": column.header, "value": key})
    values = layout.values
    if values.date_format in _DAY_FIRST:  # 4c: dates
        swapped = replace(values, date_format=_swap_day_month(values.date_format))
        read_through: list[tuple[str, str]] = []
        for i, column in columns:
            for path in column.paths:
                type_ = column.types.get(path, "text")
                if type_ not in _DATED:
                    continue
                for _, cells in rows:
                    cell = cells[i]
                    if cell == "" or isinstance(cell, XlsxNumber) or not _reads(type_, cell, values):
                        continue
                    if _reads("datetime", cell, values) and transform("datetime", cell, values) == cell:
                        continue  # an instant kept as is
                    read_through.append((type_, cell))
        if read_through and not any(not _reads(t, cell, swapped) for t, cell in read_through):
            raise ProfileRefused("ADMIT_DATE_AMBIGUOUS")
    if {values.decimal_mark, values.thousands_mark} == {".", ","}:  # 4c: numbers
        swapped = replace(values, decimal_mark=values.thousands_mark, thousands_mark=values.decimal_mark)
        cells_read = [cells[i] for i, column in columns for path in column.paths
                      if column.types.get(path, "text") == "number"
                      for _, cells in rows if cells[i] != "" and not isinstance(cells[i], XlsxNumber)]
        if cells_read and not any(not _reads("number", cell, swapped) for cell in cells_read):
            raise ProfileRefused("ADMIT_NUMBER_AMBIGUOUS")


class SourceProfiles:
    def __init__(self, store: CommercialStore, *, clock: Callable[[], datetime], real_data: bool) -> None:
        self._store = store
        self._clock = clock
        self._real_data = bool(real_data)

    # --- admission (steps 1 to 7) ---------------------------------------------------------------------------------

    def _steps(self, tenant_id: UUID, profile: bytes, sample: bytes, expected: bytes) -> _Admitted:
        profile, sample, expected = bytes(profile), bytes(sample), bytes(expected)
        # 1. the profile
        if len(profile) > MAX_PROFILE_BYTES:
            raise ProfileRefused("PROFILE_INVALID", {"where": "json"})
        try:
            obj = _json(profile)
        except ValueError:
            raise ProfileRefused("PROFILE_INVALID", {"where": "json"}) from None
        if not isinstance(obj, dict):
            raise ProfileRefused("PROFILE_INVALID", {"where": "json"})
        try:
            compile_profile(obj, 1)
        except ProfileInvalid as invalid:
            raise ProfileRefused("PROFILE_INVALID", {"where": invalid.where}) from None
        for i, (path, cls) in enumerate(obj["personal"]):
            if path not in ALLOWED_EXTRA or cls not in CLASSES:
                raise ProfileRefused("PROFILE_INVALID", {"where": f"personal.{i}"})
        # 2. the status follows the database
        if obj["status"] != ("PINNED" if self._real_data else "ILLUSTRATIVE"):
            raise ProfileRefused("PROFILE_STATUS")
        # 3. lineage and version
        profile_id, source_type, system = obj["profile_id"], obj["source_type"], obj["source_system"]
        profile_sha256 = _sha256(profile)
        rows = self._store.source_profiles_all(tenant_id, profile_id)
        already = next((r for r in rows if r.profile_sha256 == profile_sha256), None)
        if already is not None:
            version = already.version
        else:
            if any(r.source_type != source_type or r.source_system != system for r in rows):
                raise ProfileRefused("PROFILE_LINEAGE")
            version = max((r.version for r in rows), default=0) + 1
        if any(r.profile_id != profile_id and r.source_system == system
               for r in self._store.source_profiles_latest(tenant_id)):
            raise ProfileRefused("PROFILE_SOURCE_SYSTEM_TAKEN", {"system": system})
        # 4. the sample
        layout = compile_profile(obj, version)
        reader = LayoutReader(layout)
        if len(sample) > MAX_SAMPLE_BYTES:
            raise ProfileRefused("ADMIT_SAMPLE_FILE", {"code": "FILE_TOO_LARGE"},
                                 message("source_profile.admit_sample_file",
                                         reason=render(message("commercial_upload.too_large", limit_mb=1))))
        slug = self._store.tenant_slug(tenant_id)
        if slug is None:
            raise ProfileRefused("UPLOAD_TENANT_MISMATCH")
        now = self._clock()
        refused: CanonicalRefused | None = None
        try:
            read = reader.read(sample, context=ReadContext(slug, now, self._real_data))
            records = read.obj["records"]
            if len(records) not in SAMPLE_ROWS:
                raise ProfileRefused("ADMIT_SAMPLE_SIZE", {"rows": len(records)})
            parsed = parse_batch(read.obj)
            header, data_rows = split_file(layout, sample)
        except CanonicalRefused as error:
            refused = error
        if refused is not None:  # outside the handler: no driver or parser text survives
            raise ProfileRefused("ADMIT_SAMPLE_FILE", {"code": refused.code},
                                 message("source_profile.admit_sample_file",
                                         reason=render(reason_words(refused.code))))
        _coverage(layout, data_rows)  # before the row verdicts: an emptied column refuses rows too (A9 b)
        for index, outcome in enumerate(parsed.outcomes):
            if index in read.refused:
                code, path = read.refused[index]
            elif isinstance(outcome, CanonicalRefused):
                code, path = outcome.code, outcome.path
            else:
                continue
            row, cut = read.rows[index], cut_path(code, path)
            reason = render(reason_words(code))
            words = (message("source_profile.admit_sample_row", row=row, field=reader.field_label(cut), reason=reason)
                     if cut.startswith("record.") else
                     message("source_profile.admit_sample_row_whole", row=row, reason=reason))
            raise ProfileRefused("ADMIT_SAMPLE_ROW", {"row": row, "code": code, "path": cut}, words)
        # 5. the expected records
        try:
            wanted = _json(expected)
        except ValueError:
            raise ProfileRefused("ADMIT_EXPECTED_FILE") from None
        if not isinstance(wanted, list) or not all(isinstance(item, dict) for item in wanted):
            raise ProfileRefused("ADMIT_EXPECTED_FILE")
        if len(wanted) != len(records):
            raise ProfileRefused("ADMIT_EXPECTED_COUNT", {"expected": len(wanted), "records": len(records)})
        for i, (record, item) in enumerate(zip(records, wanted)):
            where = _first_difference(record, item)
            if where is not None:
                raise ProfileRefused("ADMIT_EXPECTED", {"row": read.rows[i], "where": where})
        # 6. the probes
        produced_at = now.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        failed = run_probes(layout, header, data_rows, tenant_code=slug, produced_at=produced_at,
                            provenance="observed-financial" if self._real_data else "source-emulated")
        if failed is not None:
            raise ProfileRefused("ADMIT_PROBE", {"probe": failed[0], "where": failed[1]})
        report = AdmissionReport(profile_id, version, layout.id, source_type, system, len(records), profile_sha256,
                                 _sha256(sample), _sha256(expected), already)
        return _Admitted(report, obj["status"], layout.file.format, profile.decode("utf-8"))

    def check(self, tenant_id: UUID, profile: bytes, sample: bytes, expected: bytes) -> AdmissionReport:
        """Steps 1 to 6; nothing is written."""
        return self._steps(tenant_id, profile, sample, expected).report

    def admit(self, tenant_id: UUID, actor: Actor, profile: bytes, sample: bytes, expected: bytes) -> ProfileRow:
        """Steps 1 to 7: the admitted row (the existing one, unwritten, when these profile bytes were admitted)."""
        admitted = self._steps(tenant_id, profile, sample, expected)
        r = admitted.report
        if r.already is not None:
            return r.already
        row = ProfileRow(uuid4(), tenant_id, r.profile_id, r.version, r.reader, admitted.status, r.source_type,
                         r.source_system, admitted.file_format, admitted.profile_json, r.profile_sha256,
                         r.sample_sha256, r.expected_sha256, r.sample_rows, self._clock(), actor.person_id, actor.role)
        refused = False
        try:
            self._store.add_source_profile(row)
        except StoreRefused as error:
            if error.constraint not in _UNIQUE_KEYS:
                raise
            refused = True
        if refused:
            raise ProfileRefused("PROFILE_ALREADY_ADMITTED")
        return row

    # --- reading uploads ------------------------------------------------------------------------------------------

    def reader(self, tenant_id: UUID, reader_id: str, *, superseded_ok: bool = False) -> LayoutReader:
        """The admitted profile's reader; only the latest version reads new uploads (D-3A6.8)."""
        m = _READER_ID.fullmatch(reader_id) if isinstance(reader_id, str) else None
        if m is None:
            raise UploadRefused(422, "UPLOAD_READER_UNKNOWN")
        profile_id, version = m[1], int(m[2])
        latest = self._store.source_profile_latest(tenant_id, profile_id)
        if latest is None:
            raise UploadRefused(422, "UPLOAD_READER_UNKNOWN")
        row = latest
        if version != latest.version:
            if not superseded_ok:
                if version < latest.version:
                    raise UploadRefused(422, "UPLOAD_READER_SUPERSEDED", {"latest": latest.reader})
                raise UploadRefused(422, "UPLOAD_READER_UNKNOWN")
            found = [r for r in self._store.source_profiles_all(tenant_id, profile_id) if r.version == version]
            if not found:
                raise UploadRefused(422, "UPLOAD_READER_UNKNOWN")
            row = found[0]
        if _sha256(row.profile_json.encode("utf-8")) != row.profile_sha256:
            raise UploadRefused(500, "COMMERCIAL_STORE_FAULT")
        try:
            layout = compile_profile(json.loads(row.profile_json), row.version)
        except (ValueError, ProfileInvalid):
            raise UploadRefused(500, "COMMERCIAL_STORE_FAULT") from None
        return LayoutReader(layout)

    def latest(self, tenant_id: UUID) -> tuple[ProfileRow, ...]:
        return self._store.source_profiles_latest(tenant_id)
