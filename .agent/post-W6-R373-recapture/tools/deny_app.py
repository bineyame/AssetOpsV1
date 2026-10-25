"""R373 recapture entry: the product create_app with one shared Site-read access callable that denies every Site (403)."""
from assetops_backend.main import create_app

app = create_app(site_read_access=lambda request, code: 403)
