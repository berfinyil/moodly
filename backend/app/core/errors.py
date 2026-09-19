"""Consistent API error format.

Every error response has the same shape:

    {"error": true, "message": "..."}

Unexpected exceptions are logged server-side but never leaked to the client —
stack traces and database details must not reach the browser.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("moodly.errors")


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": True, "message": message}
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Name the offending fields without echoing the submitted values —
        # those may contain private journal content.
        fields = []
        for error in exc.errors():
            location = [str(part) for part in error["loc"] if part != "body"]
            fields.append(".".join(location) or "Eingabe")
        message = "Ungültige Eingabe: " + ", ".join(dict.fromkeys(fields))
        return _error_response(422, message)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Log the path, never the request body (it may contain journal text).
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _error_response(
            500, "Ein interner Fehler ist aufgetreten. Bitte versuche es erneut."
        )
