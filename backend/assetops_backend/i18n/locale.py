"""UQ-6a (D-I18N.1, D-I18N.2, D-I18N.3): the request locale.

`LocaleMiddleware` resolves the locale from `Accept-Language` once per HTTP request, holds it in a context variable
for the request (`current_locale`), and sends it back as `Content-Language`. A locale is offered only when its
catalogue is complete and reviewed (D-I18N.3): today that is English alone, so every request resolves to `en`.
Outside a request (the pre-build, the tick) the locale is English, so the pre-load list builds English rows.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

DEFAULT_LOCALE = "en"
#: Locales offered (D-I18N.3). A language is added here only when its catalogue is complete and reviewed.
SUPPORTED: tuple[str, ...] = ("en",)

_LOCALE: ContextVar[str] = ContextVar("assetops_locale", default=DEFAULT_LOCALE)


def current_locale() -> str:
    return _LOCALE.get()


@contextmanager
def using(locale: str) -> Iterator[None]:
    token = _LOCALE.set(locale)
    try:
        yield
    finally:
        _LOCALE.reset(token)


def resolve(header: str | None) -> str:
    """The first offered locale in `Accept-Language` by quality (ties keep header order), matched on the primary
    language subtag; `en` when none is offered or the header is absent or malformed."""
    ranked: list[tuple[float, int, str]] = []
    for i, part in enumerate((header or "").split(",")):
        tag, *opts = [p.strip() for p in part.split(";")]
        q = 1.0
        for opt in opts:
            if opt.lower().startswith("q="):
                try:
                    q = float(opt[2:])
                except ValueError:
                    q = 0.0
        if tag and q > 0:
            ranked.append((-q, i, tag.split("-")[0].lower()))
    for _, _, lang in sorted(ranked):
        if lang in SUPPORTED:
            return lang
    return DEFAULT_LOCALE


class LocaleMiddleware:
    """Pure ASGI: sets the request locale for the app call and adds `Content-Language` to the response."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        header = None
        for name, value in scope.get("headers") or ():
            if name == b"accept-language":
                header = value.decode("latin-1")
                break
        locale = resolve(header)

        started = False

        async def send_with_language(event: Any) -> None:
            nonlocal started
            if event["type"] == "http.response.start":
                started = True
                headers = list(event.get("headers") or [])
                if not any(n.lower() == b"content-language" for n, _ in headers):
                    headers.append((b"content-language", locale.encode("latin-1")))
                event = {**event, "headers": headers}
            await send(event)

        with using(locale):
            try:
                await self.app(scope, receive, send_with_language)
            except Exception:
                # An unhandled exception leaves this middleware before Starlette's outer error handler answers, so
                # that 500 would carry no `Content-Language`. Answer it here (Starlette's own body), then re-raise so
                # the error is still logged and visible to the server.
                if not started:
                    await send_with_language({"type": "http.response.start", "status": 500, "headers": [
                        (b"content-type", b"text/plain; charset=utf-8"), (b"content-length", b"21")]})
                    await send_with_language({"type": "http.response.body", "body": b"Internal Server Error"})
                raise
