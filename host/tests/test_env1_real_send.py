"""ENV-1 H6s (spec §4; D-ENV1.9): the real `send` of the 2 MiB worst cases through TEL-06a's real gateway, under the
production memory and CPU of `SEND_LIMITS` (wall and slot wait widened to 600 s, D-ENV1.16 I5). Slow tier.

The gateway is a real `python -m assetops_gateway serve` from the TEL-04 `Bench`, one fresh bench per file; the
sender's delivery is a no-op (central delivery is not what is measured).
"""

from __future__ import annotations

import dataclasses
import shutil
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import reading_upload_process as up  # noqa: E402
import test_field_modbus_tcp_proof as tel4  # noqa: E402
from assetops_backend.reading_upload import service as svc  # noqa: E402
from test_up1_reading_upload_process import F1, F2  # noqa: E402

pytestmark = pytest.mark.slow


@pytest.mark.parametrize("data,cells", [(F1, 204_588), (F2, 322_620)], ids=["F1", "F2"])
def test_h6s_the_real_send_of_the_worst_case_passes_under_production_limits(tmp_path, data, cells):
    limits = dataclasses.replace(up.SEND_LIMITS, wall_seconds=600.0, slot_wait_seconds=600.0)
    bench = tel4.Bench(tmp_path)
    try:
        gateway = {"gateway_address": bench.address, "ipc_credential": str(bench.state / "gateway.credential"),
                   "snapshot_sha256": tel4.snapshot_sha256(), "expect_identity": str(bench.expect_path)}
        started = time.monotonic()
        sent = up.ProcessReadingSender(gateway, deliver=lambda g: 0, limits=limits).send(data)
        print(f"ENV-1 H6s send cells={cells} wall={time.monotonic() - started:.1f}s")
    except svc.ParseLimitBreach as breach:  # pragma: no cover - the failure this test exists to catch
        pytest.fail(f"the real send breached its production limits: {breach}")
    finally:
        bench.stop()
        shutil.rmtree(tmp_path / "gateway", ignore_errors=True)  # the ledger of 200k+ admissions; tmp may be tmpfs
    assert isinstance(sent, svc.Sent)
    assert sent.admitted + sent.held == cells
