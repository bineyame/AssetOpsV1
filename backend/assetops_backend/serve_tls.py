"""Serve the product API over TLS for registered gateway upload (S2-02 phase 2).

    python -m assetops_backend.serve_tls --cert var/tls/server.crt --key var/tls/server.key \
        --host 127.0.0.1 --port 8443

Gateway Batch V2 and diagnostics requests are refused with 426 unless they
arrive over HTTPS (`gateway_api.install_gateway_tls_boundary`), so this is the
serving entry for any gateway that uploads. A plaintext server without
certificates is not offered for those routes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.serve_tls")
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8443)
    args = parser.parse_args(argv)
    for name in (args.cert, args.key):
        if not Path(name).is_file():
            print(f"TLS file {name!r} does not exist; refusing to serve gateway routes without TLS.",
                  file=sys.stderr)
            return 2
    import uvicorn

    uvicorn.run("assetops_backend.main:app", host=args.host, port=args.port,
                ssl_certfile=args.cert, ssl_keyfile=args.key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
