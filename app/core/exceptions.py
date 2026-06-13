from fastapi import Request
from fastapi.responses import JSONResponse


class TurkQuishError(Exception):
    status_code = 400
    code = "turkquish_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidUrlError(TurkQuishError):
    status_code = 422
    code = "invalid_url"


class ArtifactError(TurkQuishError):
    status_code = 500
    code = "artifact_error"


async def turkquish_exception_handler(request: Request, exc: TurkQuishError):
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_content(request, exc.code, exc.message),
        headers=_request_headers(request),
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=_error_content(request, "internal_error", "Unexpected backend error."),
        headers=_request_headers(request),
    )


def _error_content(request: Request, code: str, message: str) -> dict:
    error = {"code": code, "message": message}
    request_id = _request_id(request)
    if request_id:
        error["requestId"] = request_id
    return {"error": error}


def _request_headers(request: Request) -> dict | None:
    request_id = _request_id(request)
    if not request_id:
        return None
    return {"X-Request-ID": request_id}


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)
