# TurkQuish Backend 

FastAPI backend for the TurkQuish QR-code URL threat detection prototype.

It supports:

- Primary 5-class HistGB inference using exported feature artifacts.
- Optional URL-Transformer fallback when HistGB confidence is low.
- URL-only runtime: no DNS, WHOIS, HTML fetching, screenshots, or reputation lookup.
- Privacy-preserving logs: stores salted URL hash and masked URL, not full raw URL by default.
- Flutter-ready REST API.

## 1. Required artifact folder

Copy your exported artifacts into:

```text
app/artifacts/
  model.joblib
  preprocessing_pipeline.joblib
  feature_schema.json
  label_encoder.json
  threshold.json
  frozen_token_graph.pkl
  explanation_templates.json
  model_card.json
```

Optional URL-Transformer fallback:

```text
app/artifacts/url_transformer/
  url_transformer.pt
  char_vocab.json
  transformer_config.json
  label_encoder.json
```

If the URL-Transformer folder is missing, the backend still works using HistGB only.

## 2. Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

## 3. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

## 4. API

### Health

```http
GET /api/v1/health
```

### Model info

```http
GET /api/v1/model-info
```

### Prediction

```http
POST /api/v1/predict
```

Request:

```json
{
  "decodedUrl": "https://example.com/login",
  "clientTimestamp": "2026-06-10T12:00:00Z",
  "locale": "en",
  "appVersion": "1.0.0"
}
```

Response includes:

- predictedClass
- riskScore
- probabilities
- topFeatures
- explanation in English and Turkish
- primary HistGB decision
- optional URL-Transformer fallback decision

## 5. Confidence-gated URL-Transformer logic

The backend uses HistGB first. URL-Transformer is used only when available and:

- HistGB top probability is below `HISTGB_CONFIDENCE_THRESHOLD`, or
- top1-top2 margin is below `HISTGB_MARGIN_THRESHOLD`, or
- risk score is near the decision boundary, or
- URL has high unseen token ratio.

This keeps the backend fast and explainable while adding a raw-character fallback for uncertain QR URLs.

## 6. Important deployment warning

The backend can only be as accurate as its feature reproduction. Your `feature_schema.json` controls the exact feature order. Missing features are zero-filled, but if your exported model expects features not reproducible from the URL and frozen artifacts, predictions may become unreliable.

## 7. Docker

```bash
docker compose up --build
```

## Brand impersonation + Levenshtein checks

The backend includes a URL-only `BrandImpersonationService` that detects:

- exact brand mentions outside the registered domain,
- brand mentions in subdomain/path/query,
- suspicious TLD + brand combinations,
- punycode/homoglyph indicators,
- Levenshtein edit-distance lookalikes such as `garantii` → `garanti`.

The `/api/v1/predict` response includes a `brandSignals` object. If URL-Transformer fallback is enabled, strong brand impersonation signals also trigger the URL-Transformer as a secondary raw-character check.


## Turkish protected brand registry

The backend includes a URL-only protected brand/institution registry at:

```text
app/resources/turkish_protected_brands.json
```

It is used by `BrandImpersonationService` to catch Turkish brand, bank, government, university, cargo, telecom, e-commerce, and crypto/streaming lookalikes. The normal `TR_BRANDS` lexicon is still used for broad brand and Levenshtein matching, while the protected registry adds official-domain checks. For example:

```text
https://www.ktun.edu.tr      -> official KTUN domain, no brand impersonation
https://www.kkktun.edu.tr   -> KTUN lookalike, protected-brand impersonation
https://akbank-login.xyz    -> Akbank impersonation
```

To add more local organizations, add entries to `turkish_protected_brands.json` without changing Python code.
