from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_ENDPOINT = "/api/v1/predict"
PROBLEMATIC_EXAMPLE_URL = "https://ziraat-bankasi-guvenli-giris.example/login"
STABLE_SYNTHETIC_SUSPICIOUS_URL = "https://login-ziraat-bankasi-guvenli.com/login"
RATE_LIMIT_WARNING = (
    "Rate limiting detected. Increase RATE_LIMIT_REQUESTS_PER_MINUTE before using benchmark values in the manuscript."
)
INTERNAL_ERROR_WARNING = (
    "Internal backend errors detected. Fix failing URLs or backend exception handling before using benchmark values in the manuscript."
)

DEFAULT_URLS = [
    "https://ktun.edu.tr",
    "https://obs.ktun.edu.tr",
    "https://turkiye.gov.tr",
    "https://enabiz.gov.tr",
    "https://mhrs.gov.tr",
    "https://ziraatbank.com.tr",
    "https://garanti.com.tr",
    "https://trendyol.com",
    "https://kkktun.edu.tr",
    "https://ktun-login.com",
    STABLE_SYNTHETIC_SUSPICIOUS_URL,
    "https://garanti-guvenli.com/login",
    "https://turkiye-gov-tr.com/basvuru",
    "https://edevlet-basvuru.net/login",
    "https://enabiz-sonuc.com",
    "https://mhrs-randevu.org",
    "https://ptt-kargo-takip.net",
    "https://trendyol-iade-formu.com",
    "https://vakifbank-dogrulama.com",
    "https://webtapu-randevu.com",
]

TIMING_KEYS = [
    "total_backend",
    "feature_extraction",
    "brand_analysis",
    "histgb_inference",
    "url_transformer_inference",
    "decision_fusion",
]


@dataclass(frozen=True)
class BenchmarkResult:
    index: int
    url: str
    status_code: int
    success: bool
    error_message: str
    api_request_response_ms: float
    backend_latency_ms: float | None
    timing_ms: dict[str, float]


def main() -> int:
    args = parse_args()
    base_url = args.base_url or os.getenv("API_BASE_URL") or DEFAULT_BASE_URL
    endpoint_url = urljoin(base_url.rstrip("/") + "/", args.endpoint.lstrip("/"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    urls = DEFAULT_URLS if args.safe_test_urls else load_urls(args.urls_file)
    if args.skip_suspicious_example_url:
        urls = [
            url
            for url in urls
            if "ziraat-bankasi-guvenli-giris.example" not in url.lower()
        ]
    if not urls:
        print("No benchmark URLs are available after filtering.", file=sys.stderr)
        return 2

    if args.warmup > 0:
        print(f"Sending {args.warmup} warm-up requests; these will not be written to CSV.")
        warmup_results = run_requests(
            endpoint_url=endpoint_url,
            urls=urls,
            count=args.warmup,
            timeout=args.timeout,
            locale=args.locale,
            app_version=args.app_version,
            delay_ms=args.delay_ms,
        )
        print_status_counts(warmup_results, title="Warm-up status-code counts")

    print(f"Sending {args.requests} measured requests to {endpoint_url}")
    measured_results = run_requests(
        endpoint_url=endpoint_url,
        urls=urls,
        count=args.requests,
        timeout=args.timeout,
        locale=args.locale,
        app_version=args.app_version,
        delay_ms=args.delay_ms,
    )

    write_runtime_results(output_dir / "runtime_raw_results.csv", measured_results)
    write_runtime_summary(output_dir / "runtime_summary.csv", measured_results)
    print_status_counts(measured_results, title="Measured status-code counts")
    print_summary(measured_results)

    status_counts = Counter(result.status_code for result in measured_results)
    if status_counts.get(429, 0):
        print(RATE_LIMIT_WARNING)
    if status_counts.get(500, 0):
        print(INTERNAL_ERROR_WARNING)
        print_500_failures(measured_results)

    successful = sum(1 for result in measured_results if result.success)
    return 0 if successful == len(measured_results) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark TurkQuish backend prediction runtime.")
    parser.add_argument("--base-url", default=None, help=f"Backend base URL. Defaults to API_BASE_URL or {DEFAULT_BASE_URL}.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"Prediction endpoint path. Default: {DEFAULT_ENDPOINT}.")
    parser.add_argument("--requests", type=int, default=100, help="Measured request count. Default: 100.")
    parser.add_argument("--warmup", type=int, default=20, help="Warm-up request count. Default: 20.")
    parser.add_argument("--delay-ms", type=float, default=0.0, help="Optional sleep between requests in milliseconds. Default: 0.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout in seconds. Default: 30.")
    parser.add_argument("--locale", default="en", help="Request locale. Default: en.")
    parser.add_argument("--app-version", default="benchmark-runtime", help="Request appVersion value.")
    parser.add_argument("--urls-file", default=None, help="Optional newline-delimited URL file.")
    parser.add_argument("--output-dir", default=".", help="Directory for runtime_raw_results.csv and runtime_summary.csv.")
    parser.add_argument(
        "--safe-test-urls",
        action="store_true",
        help="Use the built-in safe synthetic benchmark URL list, ignoring --urls-file.",
    )
    parser.add_argument(
        "--skip-suspicious-example-url",
        action="store_true",
        help="Skip the known problematic ziraat-bankasi-guvenli-giris.example benchmark URL if supplied in a URL file.",
    )
    return parser.parse_args()


def load_urls(urls_file: str | None) -> list[str]:
    if not urls_file:
        return list(DEFAULT_URLS)
    path = Path(urls_file)
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        urls.append(value)
    return urls


def run_requests(
    *,
    endpoint_url: str,
    urls: list[str],
    count: int,
    timeout: float,
    locale: str,
    app_version: str,
    delay_ms: float,
) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []
    for index in range(count):
        url = urls[index % len(urls)]
        results.append(
            send_prediction_request(
                endpoint_url=endpoint_url,
                url=url,
                index=index + 1,
                timeout=timeout,
                locale=locale,
                app_version=app_version,
            )
        )
        if delay_ms > 0 and index < count - 1:
            time.sleep(delay_ms / 1000.0)
    return results


def send_prediction_request(
    *,
    endpoint_url: str,
    url: str,
    index: int,
    timeout: float,
    locale: str,
    app_version: str,
) -> BenchmarkResult:
    body = {
        "decodedUrl": url,
        "clientTimestamp": _utc_timestamp(),
        "locale": locale,
        "appVersion": app_version,
    }
    request = Request(
        endpoint_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    status_code = 0
    response_body = ""
    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        status_code = error.code
        response_body = error.read().decode("utf-8", errors="replace")
    except URLError as error:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return BenchmarkResult(
            index=index,
            url=url,
            status_code=0,
            success=False,
            error_message=str(error.reason),
            api_request_response_ms=elapsed_ms,
            backend_latency_ms=None,
            timing_ms={},
        )
    except OSError as error:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return BenchmarkResult(
            index=index,
            url=url,
            status_code=0,
            success=False,
            error_message=str(error),
            api_request_response_ms=elapsed_ms,
            backend_latency_ms=None,
            timing_ms={},
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    payload, json_error = _parse_json_object(response_body)
    error_message = extract_error_message(payload, response_body)
    if json_error and 200 <= status_code < 300:
        error_message = json_error

    success = 200 <= status_code < 300 and not error_message
    backend_latency_ms = extract_backend_latency_ms(payload) if success else None
    timing_ms = extract_timing_ms(payload) if success else {}
    return BenchmarkResult(
        index=index,
        url=url,
        status_code=status_code,
        success=success,
        error_message=error_message,
        api_request_response_ms=elapsed_ms,
        backend_latency_ms=backend_latency_ms,
        timing_ms=timing_ms,
    )


def write_runtime_results(path: Path, results: list[BenchmarkResult]) -> None:
    fieldnames = [
        "request_index",
        "url",
        "status_code",
        "success",
        "error_message",
        "api_request_response_ms",
        "backend_latency_ms",
        *[f"timingMs.{key}" for key in TIMING_KEYS],
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row: dict[str, Any] = {
                "request_index": result.index,
                "url": result.url,
                "status_code": result.status_code,
                "success": result.success,
                "error_message": result.error_message,
                "api_request_response_ms": round(result.api_request_response_ms, 4),
                "backend_latency_ms": _round_or_blank(result.backend_latency_ms),
            }
            for key in TIMING_KEYS:
                row[f"timingMs.{key}"] = _round_or_blank(result.timing_ms.get(key))
            writer.writerow(row)


def write_runtime_summary(path: Path, results: list[BenchmarkResult]) -> None:
    total_count = len(results)
    success_count = sum(1 for result in results if result.success)
    failure_count = total_count - success_count
    status_counts = Counter(result.status_code for result in results)
    fieldnames = [
        "summary_scope",
        "metric",
        "status_code",
        "count",
        "mean_ms",
        "median_ms",
        "p95_ms",
        "min_ms",
        "max_ms",
        "total_requests",
        "success_count",
        "failure_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            _summary_count_row(
                metric="requests",
                count=total_count,
                total_count=total_count,
                success_count=success_count,
                failure_count=failure_count,
            )
        )
        writer.writerow(
            _summary_count_row(
                metric="successful_requests",
                count=success_count,
                total_count=total_count,
                success_count=success_count,
                failure_count=failure_count,
            )
        )
        writer.writerow(
            _summary_count_row(
                metric="failed_requests",
                count=failure_count,
                total_count=total_count,
                success_count=success_count,
                failure_count=failure_count,
            )
        )
        for status_code, count in sorted(status_counts.items()):
            writer.writerow(
                _summary_count_row(
                    metric="status_code",
                    status_code=status_code,
                    count=count,
                    total_count=total_count,
                    success_count=success_count,
                    failure_count=failure_count,
                )
            )

        successful_results = [result for result in results if result.success]
        timing_sources: dict[str, list[float]] = {
            "api_request_response_ms": [result.api_request_response_ms for result in successful_results],
            "backend_latency_ms": [
                result.backend_latency_ms
                for result in successful_results
                if result.backend_latency_ms is not None
            ],
        }
        for key in TIMING_KEYS:
            timing_sources[f"timingMs.{key}"] = [
                result.timing_ms[key]
                for result in successful_results
                if key in result.timing_ms
            ]
        for metric, values in timing_sources.items():
            writer.writerow(
                _timing_summary_row(
                    metric=metric,
                    values=values,
                    total_count=total_count,
                    success_count=success_count,
                    failure_count=failure_count,
                )
            )


def print_status_counts(results: list[BenchmarkResult], *, title: str) -> None:
    print(f"{title}:")
    counts = Counter(result.status_code for result in results)
    for status_code, count in sorted(counts.items()):
        label = str(status_code) if status_code else "transport_error"
        print(f"  {label}: {count}")


def print_summary(results: list[BenchmarkResult]) -> None:
    total_count = len(results)
    success_count = sum(1 for result in results if result.success)
    failure_count = total_count - success_count
    print(f"Measured requests: total={total_count} success={success_count} failure={failure_count}")


def print_500_failures(results: list[BenchmarkResult]) -> None:
    print("HTTP 500 failures:")
    for result in results:
        if result.status_code == 500:
            message = result.error_message or "(no error message returned)"
            print(f"  {result.url} -> {message}")


def extract_timing_ms(payload: dict[str, Any]) -> dict[str, float]:
    timing = payload.get("timingMs")
    if not isinstance(timing, dict):
        timing = payload.get("timing_ms")
    if not isinstance(timing, dict):
        return {}
    values: dict[str, float] = {}
    for key, value in timing.items():
        number = _float_or_none(value)
        if number is not None:
            values[str(key)] = number
    return values


def extract_backend_latency_ms(payload: dict[str, Any]) -> float | None:
    for key in ("latencyMs", "latency_ms", "backend_latency_ms"):
        value = payload.get(key)
        number = _float_or_none(value)
        if number is not None:
            return number
    return None


def extract_error_message(payload: dict[str, Any], raw_body: str) -> str:
    for key in ("detail", "error", "message"):
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
    return raw_body.strip()[:500] if raw_body.strip() and not payload else ""


def _parse_json_object(raw_body: str) -> tuple[dict[str, Any], str]:
    if not raw_body.strip():
        return {}, ""
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as error:
        return {}, f"Response was not valid JSON: {error.msg}"
    if not isinstance(payload, dict):
        return {}, "Response JSON was not an object."
    return payload, ""


def _summary_count_row(
    *,
    metric: str,
    count: int,
    total_count: int,
    success_count: int,
    failure_count: int,
    status_code: int | str = "",
) -> dict[str, Any]:
    return {
        "summary_scope": "measured",
        "metric": metric,
        "status_code": status_code,
        "count": count,
        "mean_ms": "",
        "median_ms": "",
        "p95_ms": "",
        "min_ms": "",
        "max_ms": "",
        "total_requests": total_count,
        "success_count": success_count,
        "failure_count": failure_count,
    }


def _timing_summary_row(
    *,
    metric: str,
    values: list[float],
    total_count: int,
    success_count: int,
    failure_count: int,
) -> dict[str, Any]:
    summary = summarize_values(values)
    return {
        "summary_scope": "measured_successes_only",
        "metric": metric,
        "status_code": "",
        "count": len(values),
        "mean_ms": _round_or_blank(summary.get("mean")),
        "median_ms": _round_or_blank(summary.get("median")),
        "p95_ms": _round_or_blank(summary.get("p95")),
        "min_ms": _round_or_blank(summary.get("min")),
        "max_ms": _round_or_blank(summary.get("max")),
        "total_requests": total_count,
        "success_count": success_count,
        "failure_count": failure_count,
    }


def summarize_values(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    return {
        "mean": statistics.fmean(ordered),
        "median": statistics.median(ordered),
        "p95": percentile(ordered, 95),
        "min": ordered[0],
        "max": ordered[-1],
    }


def percentile(ordered_values: list[float], percentile_value: float) -> float:
    if not ordered_values:
        raise ValueError("percentile requires at least one value")
    if len(ordered_values) == 1:
        return ordered_values[0]
    position = (len(ordered_values) - 1) * (percentile_value / 100.0)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered_values) - 1)
    fraction = position - lower_index
    return ordered_values[lower_index] + ((ordered_values[upper_index] - ordered_values[lower_index]) * fraction)


def _round_or_blank(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


if __name__ == "__main__":
    raise SystemExit(main())
