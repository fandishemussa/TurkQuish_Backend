from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import InvalidUrlError, turkquish_exception_handler
from app.core.middleware import RequestContextMiddleware


def _app(limit: int = 100) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware, max_requests_per_minute=limit)
    app.add_exception_handler(InvalidUrlError, turkquish_exception_handler)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/invalid")
    def invalid():
        raise InvalidUrlError("Bad URL")

    return app


def test_request_id_is_returned_on_success_and_errors():
    with TestClient(_app()) as client:
        ok = client.get("/ok", headers={"X-Request-ID": "req-test-1"})
        assert ok.status_code == 200
        assert ok.headers["X-Request-ID"] == "req-test-1"
        assert "X-Response-Time-ms" in ok.headers

        error = client.get("/invalid", headers={"X-Request-ID": "req-test-2"})
        assert error.status_code == 422
        assert error.headers["X-Request-ID"] == "req-test-2"
        assert error.json()["error"]["requestId"] == "req-test-2"


def test_rate_limiter_returns_structured_429_response():
    with TestClient(_app(limit=1)) as client:
        assert client.get("/ok").status_code == 200

        response = client.get("/ok")
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "rate_limited"
        assert "requestId" in response.json()["error"]
        assert "X-Request-ID" in response.headers
