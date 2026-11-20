"""The canonical format version 1 and the leaf factor IDs (spec `specs/2a-canonical-format/spec.md`).

One definition that the commercial record store (3A1, 3A2), the structure
registry (3B1, 3B3) and the generator's writers (DS1b) all read, so they cannot
drift. Standard library only (D-2A.1). A protected seam (D-2A.2): a change to
what a valid record is, or to a factor ID or unit, is a new format version
beside this one, never an edit of version 1.

- `units`: the six dimensions, `Unit`, `parse_unit`, `QUANTITY_UNITS`, `BAND_UNITS`;
- `factors`: the 73 leaf factors, `leaves_of`, `FACTOR_ID_PATTERN`;
- `records_v1`: the fourteen kinds, batch and record parsing, canonical bytes, digests;
- `sources_v1`: the seventeen source types and the formats that stay as they are.
"""

from assetops_contracts.canonical.factors import (
    FACTOR_ID_PATTERN,
    LEAF_FACTORS,
    STRUCTURE_KEYS,
    Factor,
    leaves_of,
)
from assetops_contracts.canonical.records_v1 import (
    FORMAT_VERSION,
    KIND_SPECS,
    KINDS,
    BatchResult,
    CanonicalBatchV1,
    CanonicalRecordV1,
    CanonicalRefused,
    KindSpec,
    batch_digest,
    loads_canonical,
    parse_batch,
    parse_record,
    record_digest,
    to_canonical_json,
)
from assetops_contracts.canonical.sources_v1 import EXISTING_FORMATS, SOURCE_TYPES, SourceType
from assetops_contracts.canonical.units import (
    BAND_UNITS,
    DAY,
    DIMENSIONS,
    HOUR,
    KW,
    KWH,
    L,
    MINUTE,
    MONEY,
    ONE,
    QUANTITY_UNITS,
    Unit,
    parse_unit,
)

__all__ = [
    "BAND_UNITS", "DAY", "DIMENSIONS", "EXISTING_FORMATS", "FACTOR_ID_PATTERN", "FORMAT_VERSION", "HOUR",
    "KINDS", "KIND_SPECS", "KW", "KWH", "L", "LEAF_FACTORS", "MINUTE", "MONEY", "ONE", "QUANTITY_UNITS",
    "SOURCE_TYPES", "STRUCTURE_KEYS", "BatchResult", "CanonicalBatchV1", "CanonicalRecordV1",
    "CanonicalRefused", "Factor", "KindSpec", "SourceType", "Unit", "batch_digest", "leaves_of",
    "loads_canonical", "parse_batch", "parse_record", "parse_unit", "record_digest", "to_canonical_json",
]
