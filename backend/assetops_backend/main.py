"""FastAPI application root for AssetOps.

T001 scope is implementation posture only. The app reports service liveness so
the stack can be started and smoke-tested. No Site schema, simulator execution,
ingestion, analytics, configuration editing, or Findings are served, and no
endpoint here implies that operational evidence exists.
"""

from fastapi import FastAPI

app = FastAPI(title="AssetOps", version="0.0.0")


@app.get("/api/health")
def read_health() -> dict[str, str]:
    """Report that the backend process is serving.

    This is a liveness signal about the service only. It is not evidence about
    any Site, device, source, or simulator run.
    """
    return {"status": "ok", "service": "assetops-backend"}
