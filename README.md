# TurkQuish Backend

**TurkQuish Backend** is the FastAPI-based inference service for **TurkQuish**, an explainable URL-only QR-code phishing detection framework designed for the Turkish web ecosystem.

The backend receives a decoded URL string from a client application, extracts URL-only features, performs machine-learning-based classification, generates risk scores and explanations, and returns structured results through a REST API.

TurkQuish is designed for **URL-only inference**. It does not query DNS, WHOIS, webpage HTML, screenshots, browser reputation services, or third-party security lookup APIs during inference.



## Overview

QR-code phishing, also known as **quishing**, hides malicious URLs behind QR codes and often targets mobile users. TurkQuish addresses this problem by analyzing the decoded URL string and producing an explainable risk assessment.

The backend supports:

* URL normalization and validation
* URL-only feature extraction
* lexical and structural feature analysis
* brand/adversarial signal analysis
* Turkish linguistic feature extraction
* graph-based infrastructure feature projection
* machine-learning inference
* URL Transformer inference path, when invoked
* decision fusion and fallback logic
* bilingual explanation generation
* prototype-level runtime instrumentation
* small-scale backend load testing



## Key Features

### URL-only inference

TurkQuish analyzes only the decoded URL string. The backend does **not** perform:

* DNS lookup
* WHOIS lookup
* webpage HTML retrieval
* screenshot capture
* browser reputation checking
* third-party security-service lookup

This design makes the inference path bounded, privacy-aware, and suitable for lightweight QR-code scanning workflows.

### Explainable detection

The backend returns not only the predicted class but also:

* risk score
* risk level
* class probabilities
* recommended action
* top contributing signals
* bilingual explanation content
* model and feature-schema metadata

### REST API

The main inference endpoint is:

```text
POST /api/predict
```

The endpoint accepts a decoded URL and returns a structured prediction response.

### Prototype runtime support

The backend exposes runtime timing information for manuscript and deployment analysis, including:

* backend request latency
* backend internal total time
* feature extraction time
* brand/adversarial analysis time
* HistGB inference time
* URL Transformer inference time, when invoked
* decision fusion time

### Load-test support

The repository includes benchmarking scripts for:

* repeated runtime measurement
* small-scale concurrent API load testing
* CSV output for manuscript-ready runtime tables



## Project Structure

A typical backend structure is:

```text
Turkquish_Backend/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── schemas/
│   ├── services/
│   ├── models/
│   └── main.py
├── tools/
│   ├── benchmark_runtime.py
│   ├── load_test_predict.py
│   └── RUNTIME_MEASUREMENT_README.md
├── requirements.txt
├── README.md
└── .env.example
```

The exact structure may vary depending on the current implementation.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/fandishemussa/TurkQuish_Backend.git
cd TurkQuish_Backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

On Windows:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```



## Configuration

Create a `.env` file if the backend requires environment configuration.

Example:

```env
APP_NAME=TurkQuish Backend
API_PREFIX=/api
ENVIRONMENT=development
RATE_LIMIT_REQUESTS_PER_MINUTE=100000
```

For local benchmarking, increase the rate limit to avoid measuring rate-limit responses instead of backend runtime.


## Running the Backend

Start the FastAPI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```



## Prediction Endpoint

### Endpoint

```text
POST /api/predict
```

### Example request

```json
{
  "decodedUrl": "https://www.ktun.edu.tr",
  "locale": "tr",
  "appVersion": "prototype-runtime-test",
  "clientTimestamp": "2026-06-13T00:00:00Z"
}
```

Depending on the current schema, the URL field may be named `decodedUrl` or `url`.

### Example response fields

```json
{
  "predictedClass": "benign",
  "riskScore": 0.12,
  "riskLevel": "low",
  "recommendedAction": "Proceed with caution",
  "probabilities": {
    "benign": 0.88,
    "phishing": 0.05,
    "malware": 0.03,
    "scam": 0.02,
    "other-malicious": 0.02
  },
  "explanation": {
    "en": "The URL shows mostly benign structural characteristics.",
    "tr": "URL çoğunlukla güvenli yapısal özellikler göstermektedir."
  },
  "timingMs": {
    "feature_extraction": 14.98,
    "histgb_inference": 36.67,
    "url_transformer_inference": 3.65,
    "decision_fusion": 0.07,
    "total_backend": 139.43
  }
}
```

The exact response may vary depending on the current schema and enabled services.



## Runtime Benchmarking

The backend includes tools for prototype-level runtime measurement.

### Single-request repeated benchmark

```bash
python tools/benchmark_runtime.py --requests 100 --warmup 20
```

Expected output files:

```text
runtime_raw_results.csv
runtime_summary.csv
```

The benchmark reports:

* API request-response latency
* backend request latency
* backend internal timing
* feature extraction timing
* model inference timing
* decision fusion timing

### Small-scale load test

```bash
python tools/load_test_predict.py
```

Expected output files:

```text
backend_load_test_raw.csv
backend_load_test_summary.csv
```

The default concurrency levels are:

```text
10, 50, 100
```

These measurements are intended for prototype-level analysis and should not be interpreted as production-scale deployment results.


## Final Runtime Results Used in Manuscript

A clean runtime benchmark was performed using 100 successful post-warm-up requests to `/api/predict`.

Summary:

| Component                               | Median latency |
| --------------------------------------- | -------------: |
| API request-response                    |      144.45 ms |
| Backend internal total                  |      139.43 ms |
| Feature extraction                      |       14.98 ms |
| Brand/adversarial analysis              |       79.53 ms |
| HistGB inference                        |       36.67 ms |
| URL Transformer inference, when invoked |        3.65 ms |
| Decision fusion                         |        0.07 ms |

These results represent prototype-level runtime behaviour under an experimental environment, not production-scale field deployment.


## Small-Scale Load-Test Summary

| Concurrency | Successful requests | Error rate | Median latency |  Throughput |
| ----------: | ------------------: | ---------: | -------------: | ----------: |
|          10 |           500 / 500 |       0.0% |     1693.50 ms | 5.98 URLs/s |
|          50 |         1000 / 1000 |       0.0% |    10914.91 ms | 4.66 URLs/s |
|         100 |         1968 / 2000 |       1.6% |    21377.13 ms | 4.59 URLs/s |

The load-test results characterize a single backend instance and motivate future work on multi-worker serving, containerized deployment, load balancing, and horizontal scaling.


## Model and Feature Pipeline

The backend may include:

* lexical/structural URL features
* Turkish linguistic features
* brand/adversarial features
* graph-based infrastructure features
* HistGB classifier
* URL Transformer path
* decision fusion logic
* explanation generation

The system is designed so that graph features used at inference time are based on frozen or inductive artifacts rather than network-time queries.


## Privacy and Security Notes

TurkQuish avoids external URL enrichment during inference. The backend does not fetch webpage content or contact third-party security APIs. This reduces external dependency and avoids exposing scanned URLs to external lookup services during prediction.

However, TurkQuish is a research prototype. It should not be treated as a complete replacement for enterprise-grade security gateways, browser protection systems, or human security judgment.



## Reproducibility

This repository is intended to support reproducibility of the backend prototype, runtime benchmarking, and inference pipeline.

If some datasets or raw URLs cannot be redistributed due to security or licensing restrictions, provide derived artifacts, scripts, and documentation where possible.

Recommended archival option:

```text
GitHub repository + Zenodo DOI
```



## Citation

If you use this repository, please cite the associated TurkQuish manuscript.

```bibtex
@article{turkquish2026,
  title   = {TurkQuish: Explainable URL-Only Detection of QR-Code Phishing in the Turkish Web Ecosystem},
  author  = {TODO},
  journal = {TODO},
  year    = {2026}
}
```


## License

* MIT License for code
* Apache-2.0 License for code
* CC BY 4.0 for documentation, if appropriate

Do not publish sensitive datasets or malicious URLs unless redistribution is legally and ethically allowed.


## Disclaimer

TurkQuish is a research prototype for URL-only QR-code phishing detection. It may produce false positives or false negatives. Do not rely on it as the sole security control for high-risk environments.
