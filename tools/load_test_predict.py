from __future__ import annotations

import argparse
import asyncio
import csv
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError as exc:  # pragma: no cover
    raise SystemExit("httpx is required. Install it with: pip install httpx") from exc

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

REPRESENTATIVE_URLS = [
    "https://www.ktun.edu.tr",
    "https://www.google.com",
    "https://hastaneler.erciyes.edu.tr/tr/alt-birimler/dahili-tip/1",
    "https://login-ziraat-bankasi-guvenli.com/login",
    "https://e-devlet-dogrulama-guvenli.com/odeme",
    "https://ptt-kargo-teslimat-takip.com/sorgula",
]


def _payload(decoded_url: str) -> dict[str, Any]:
    return {
        "decodedUrl": decoded_url,
        "locale": "tr",
        "appVersion": "prototype-load-test",
        "clientTimestamp": datetime.now(timezone.utc).isoformat(),
    }


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = math.ceil((pct / 100.0) * len(ordered)) - 1
    return ordered[max(0, min(rank, len(ordered) - 1))]


def _flatten_timing(row: dict[str, Any], data: dict[str, Any]) -> None:
    row["backend_latency_ms"] = _as_float(data.get("latencyMs"))
    timing = data.get("timingMs") if isinstance(data, dict) else None
    if isinstance(timing, dict):
        for key, value in timing.items():
            row[f"timingMs.{key}"] = _as_float(value)


async def _send_one(client: httpx.AsyncClient, url: str, request_id: int, concurrency: int) -> dict[str, Any]:
    decoded_url = REPRESENTATIVE_URLS[request_id % len(REPRESENTATIVE_URLS)]
    started = time.perf_counter()
    try:
        response = await client.post(url, json=_payload(decoded_url))
        latency_ms = round((time.perf_counter() - started) * 1000, 4)
        try:
            data = response.json()
        except ValueError:
            data = {}
        row: dict[str, Any] = {
            "concurrency": concurrency,
            "request_id": request_id + 1,
            "url": decoded_url,
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "client_http_latency_ms": latency_ms,
            "x_response_time_ms": _as_float(response.headers.get("X-Response-Time-ms")),
            "error": "" if 200 <= response.status_code < 300 else response.text[:300],
        }
        _flatten_timing(row, data)
        return row
    except Exception as exc:
        return {
            "concurrency": concurrency,
            "request_id": request_id + 1,
            "url": decoded_url,
            "status_code": 0,
            "success": False,
            "client_http_latency_ms": round((time.perf_counter() - started) * 1000, 4),
            "error": str(exc),
        }


async def _run_level(url: str, concurrency: int, total_requests: int) -> tuple[list[dict[str, Any]], float]:
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=30.0) as client:
        async def guarded(index: int) -> dict[str, Any]:
            async with semaphore:
                return await _send_one(client, url, index, concurrency)

        started = time.perf_counter()
        rows = await asyncio.gather(*(guarded(index) for index in range(total_requests)))
        elapsed = time.perf_counter() - started
        return list(rows), elapsed


def _find_backend_process():
    if psutil is None:
        print("pip install psutil")
        return None
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        lower = cmdline.lower()
        if "uvicorn" in lower and "app.main:app" in lower:
            return proc
    return None


async def _sample_process(proc, stop_event: asyncio.Event, samples: list[tuple[float, float]]) -> None:
    if proc is None:
        return
    try:
        proc.cpu_percent(None)
    except Exception:
        return
    while not stop_event.is_set():
        try:
            cpu = float(proc.cpu_percent(None))
            ram_mb = float(proc.memory_info().rss) / (1024 * 1024)
            samples.append((cpu, ram_mb))
        except Exception:
            return
        await asyncio.sleep(0.5)


def _numeric(rows: list[dict[str, Any]], key: str) -> list[float]:
    values = [_as_float(row.get(key)) for row in rows]
    return [value for value in values if value is not None]


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 4) if values else None


def _median(values: list[float]) -> float | None:
    return round(statistics.median(values), 4) if values else None


def _summary(concurrency: int, total_requests: int, elapsed: float, rows: list[dict[str, Any]], cpu_samples: list[tuple[float, float]], ram_before: float | None, ram_after: float | None) -> dict[str, Any]:
    successes = sum(1 for row in rows if row.get("success") is True)
    failures = len(rows) - successes
    latencies = _numeric(rows, "client_http_latency_ms")
    backend = _numeric(rows, "backend_latency_ms")
    response_header = _numeric(rows, "x_response_time_ms")
    out: dict[str, Any] = {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "successful_requests": successes,
        "failed_requests": failures,
        "mean_latency_ms": _mean(latencies),
        "median_latency_ms": _median(latencies),
        "p95_latency_ms": round(_percentile(latencies, 95), 4) if latencies else None,
        "throughput_urls_per_sec": round(len(rows) / elapsed, 4) if elapsed > 0 else None,
        "error_rate_percent": round((failures / len(rows)) * 100, 4) if rows else None,
        "mean_backend_latency_ms": _mean(backend),
        "median_backend_latency_ms": _median(backend),
        "mean_x_response_time_ms": _mean(response_header),
        "median_x_response_time_ms": _median(response_header),
        "backend_ram_before_mb": ram_before,
        "backend_ram_after_mb": ram_after,
        "backend_cpu_avg_percent": round(statistics.fmean(x[0] for x in cpu_samples), 4) if cpu_samples else None,
        "backend_ram_avg_mb": round(statistics.fmean(x[1] for x in cpu_samples), 4) if cpu_samples else None,
    }
    timing_keys = sorted({key for row in rows for key in row if key.startswith("timingMs.")})
    for key in timing_keys:
        values = _numeric(rows, key)
        safe_key = key.replace(".", "_")
        out[f"mean_{safe_key}"] = _mean(values)
        out[f"median_{safe_key}"] = _median(values)
    return out


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


async def _main_async(args) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    concurrency_levels = _parse_int_list(args.concurrency)
    request_counts = _parse_int_list(args.requests)
    if len(concurrency_levels) != len(request_counts):
        raise SystemExit("--concurrency and --requests must contain the same number of values")

    backend_proc = _find_backend_process()
    if psutil is None:
        print("psutil is missing; CPU/RAM columns will be empty. Install with: pip install psutil")
    elif backend_proc is None:
        print("Could not find a running uvicorn app.main:app process; CPU/RAM columns will be empty.")

    raw_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for concurrency, total_requests in zip(concurrency_levels, request_counts):
        cpu_samples: list[tuple[float, float]] = []
        stop_event = asyncio.Event()
        ram_before = None
        ram_after = None
        sampler = None
        if backend_proc is not None:
            try:
                ram_before = round(float(backend_proc.memory_info().rss) / (1024 * 1024), 4)
            except Exception:
                ram_before = None
            sampler = asyncio.create_task(_sample_process(backend_proc, stop_event, cpu_samples))

        rows, elapsed = await _run_level(args.url, concurrency, total_requests)
        if sampler is not None:
            stop_event.set()
            await sampler
            try:
                ram_after = round(float(backend_proc.memory_info().rss) / (1024 * 1024), 4)
            except Exception:
                ram_after = None

        status_429 = sum(1 for row in rows if row.get("status_code") == 429)
        if status_429:
            print("Many 429 responses detected. Increase or disable rate limiting before interpreting load-test results.")

        raw_rows.extend(rows)
        summary_rows.append(_summary(concurrency, total_requests, elapsed, rows, cpu_samples, ram_before, ram_after))

    _write_csv(output_dir / "backend_load_test_raw.csv", raw_rows)
    _write_csv(output_dir / "backend_load_test_summary.csv", summary_rows)
    print(f"Wrote {output_dir / 'backend_load_test_raw.csv'}")
    print(f"Wrote {output_dir / 'backend_load_test_summary.csv'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Small-scale load test for TurkQuish /predict.")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/predict")
    parser.add_argument("--concurrency", default="10,50,100")
    parser.add_argument("--requests", default="500,1000,2000")
    parser.add_argument("--output-dir", default="tools/runtime_results")
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()

