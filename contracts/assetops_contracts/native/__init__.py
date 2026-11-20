"""3A3 (spec §2.2, §2.3; D-3A3.2): native export layouts, read and rendered by one engine.

`Layout` and `Column` describe a native CSV file as data; `read_layout` reads one into a canonical batch object and
`render_layout` writes canonical records back out. `LAYOUTS` holds the four illustrative layouts, which are both the
emulators' shape and the owner's reshaping template (D-3A3.10). Standard library and `assetops_contracts.canonical`
only.
"""

from assetops_contracts.native.layouts_v1 import (
    BILLING,
    BUDGET,
    COLLECTIONS,
    EXPENSES,
    LAYOUTS,
    Column,
    Layout,
    NativeRead,
    check_layout,
    read_layout,
    render_layout,
)

__all__ = ["BILLING", "BUDGET", "COLLECTIONS", "EXPENSES", "LAYOUTS", "Column", "Layout", "NativeRead",
           "check_layout", "read_layout", "render_layout"]
