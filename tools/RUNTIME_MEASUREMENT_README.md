# Runtime Measurement

Use `tools/benchmark_runtime.py` for local backend runtime measurements.

For manuscript benchmark runs, temporarily increase the local development rate limit, for example `RATE_LIMIT_REQUESTS_PER_MINUTE=100000`, then restart the backend. Do not interpret HTTP 429 responses as model/runtime latency.

Recommended final command:

```bash
python tools/benchmark_runtime.py --requests 100 --warmup 20
```

Warm-up requests are sent before the measured run and are not written to `runtime_raw_results.csv` or included in `runtime_summary.csv`.

