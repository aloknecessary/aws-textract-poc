# Knowledge Base — AWS Textract POC

> Last reviewed: post-fix pass

---

## 1. What the POC Does

An end-to-end pipeline that:

1. Accepts a prescription image (JPEG/PNG) via a Streamlit UI or CLI
2. Sends raw image bytes to **Amazon Textract** (`detect_document_text`)
   to extract text lines
3. Passes the extracted text to **Amazon Comprehend Medical**
   (`detect_entities_v2`) to identify medical entities across all 7
   categories
4. Renders results in a unified table per category in the Streamlit UI

---

## 2. File Map

| File | Role |
| --- | --- |
| `app.py` | Streamlit frontend — upload, display, orchestrate |
| `main.py` | CLI pipeline + Comprehend Medical logic |
| `textract_service.py` | Textract client init + OCR extraction |
| `test_textract.py` | Standalone single-image Textract test |
| `requirements.txt` | `boto3`, `python-dotenv`, `streamlit`, `Pillow` |
| `.env` | AWS credentials |
| `dataset/test/` | 27 sample prescription images (filenames 90–145) |

---

## 3. Data Flow

```text
User uploads image (app.py)
        │
        ▼
PIL converts to JPEG bytes (RGB normalisation for RGBA/P modes)
        │
        ▼
textract_service.extract_text_from_bytes()
  └─ Textract.detect_document_text(Document={Bytes: ...})
  └─ Joins LINE blocks → plain text string
        │
        ▼
main.extract_medical_insights()
  └─ _chunk_text() splits into ≤20,000-char chunks
  └─ ComprehendMedical.detect_entities_v2(Text: chunk) per chunk
  └─ Merges results across all chunks into structured_data
        │
        ▼
Structured dict (7 category keys)
  Each entity: { text, type, confidence, traits[], attributes{} }
        │
        ▼
app.render_entity_table() → HTML-escaped table per category
```

---

## 4. AWS Services Used

| Service | API Call | Input Limit |
| --- | --- | --- |
| Amazon Textract | `detect_document_text` | Max 5 MB (synchronous) |
| Amazon Comprehend Medical | `detect_entities_v2` | Max 20,000 UTF-8 chars |

Both called **synchronously** — no S3 involvement.

---

## 5. Comprehend Medical Entity Categories

| Output key | Comprehend `Category` value |
| --- | --- |
| `medications` | `MEDICATION` |
| `medical_conditions` | `MEDICAL_CONDITION` |
| `anatomy` | `ANATOMY` |
| `test_treatment_procedures` | `TEST_TREATMENT_PROCEDURE` |
| `protected_health_information` | `PROTECTED_HEALTH_INFORMATION` |
| `behavioral_environmental_social` | `BEHAVIORAL_ENVIRONMENTAL_SOCIAL` |
| `time_expressions` | `TIME_EXPRESSION` |

Each entity carries: `text`, `type`, `confidence`, `traits[]`, and
`attributes{}` (with per-attribute `value` + `confidence`).

---

## 6. Fixes Applied

### `app.py`

| Issue | Fix |
| --- | --- |
| `render_entity_table` defined inside button block | Moved to module level |
| Raw OCR text injected into HTML (XSS risk) | Wrapped with `html.escape()` |
| PHI leaked to console via `print(json.dumps(...))` | Debug block removed |
| Only 3 of 7 categories rendered | All 7 wired to `render_entity_table()` |
| `import json` inside button block | Removed |

### `main.py`

| Issue | Fix |
| --- | --- |
| No Comprehend 20,000-char limit guard | Added `_chunk_text()`; merged |
| Long `if/elif` category chain | Replaced with `category_map` dict lookup |
| Default fallback image `1.jpeg` does not exist | Changed to `90.jpg` |

---

## 7. Remaining Limitations

### Architecture

- No S3 integration — files >5 MB will fail at Textract
- Synchronous-only — no async Textract jobs; multi-page PDFs unsupported
- No shared AWS session — `boto3.client()` called independently in
  `textract_service.py` and `main.py`; `load_dotenv()` called twice

### Code Quality

- `initialize_textract_client()` and `initialize_comprehend_client()`
  are duplicated — no shared `aws_session.py`
- Comprehend logic still lives in `main.py` — should be
  `comprehend_service.py`
- `app.py` imports directly from `main.py` (couples UI to CLI module)
- No logging framework — all output is raw `print()`
- `test_textract.py` default `DATASET_DIR` still points to a
  non-existent path (`curated-handwritten-printed-dataset/...`)

### Error Handling

- No retry logic for transient AWS throttling (`ThrottlingException`)
- `extract_text_from_bytes()` returns `None` on failure — callers must
  null-check manually
- `initialize_*_client()` catches credential errors but not
  region/endpoint misconfiguration

### Security

- AWS credentials in `.env` — IAM roles are preferred

### Functionality Gaps

- No confidence threshold filtering
- No output persistence — results lost on page refresh
- No PDF / multi-page support

---

## 8. Improvement Roadmap

### High Priority

| Area | Action |
| --- | --- |
| Service separation | Move Comprehend logic to `comprehend_service.py` |
| Shared session | Single `aws_session.py` factory used by all clients |
| Fix `test_textract.py` path | Update `DATASET_DIR` to `dataset/test` |

### Medium Priority

| Area | Action |
| --- | --- |
| Confidence filtering | Configurable threshold (default 80%) |
| Retry logic | `botocore` retry config or `tenacity` |
| Logging | Replace `print()` with Python `logging` module |
| Output export | CSV/JSON download button in Streamlit |

### Low Priority

| Area | Action |
| --- | --- |
| IAM roles | Replace `.env` credentials with instance profile |
| S3 + async Textract | `start_document_text_detection` for PDFs |
| Batch processing | Process all images in `dataset/test/` from UI |
| Unit tests | `pytest` with mocked boto3 responses |

---

## 9. Pricing

> Prices shown are for **us-east-1**. Always verify current rates at
> [aws.amazon.com/textract/pricing](https://aws.amazon.com/textract/pricing/)
> and [aws.amazon.com/comprehend/medical/pricing](https://aws.amazon.com/comprehend/medical/pricing/).

### 9.1 Amazon Textract

Textract pricing depends on which API feature is used. The POC uses
`detect_document_text` (Detect Text tier).

#### Detect Text (plain OCR — what the POC uses)

| Monthly Volume | Price per Page |
| --- | --- |
| First 1,000 pages | Free (Free Tier) |
| Up to 1 million pages | $0.0015 per page |
| Over 1 million pages | $0.0006 per page |

#### Analyze Document — Forms (key-value pairs)

| Monthly Volume | Price per Page |
| --- | --- |
| Up to 1 million pages | $0.05 per page |
| Over 1 million pages | $0.04 per page |

#### Analyze Document — Tables

| Monthly Volume | Price per Page |
| --- | --- |
| Up to 1 million pages | $0.015 per page |
| Over 1 million pages | $0.01 per page |

#### Analyze Document — Signatures

| Monthly Volume | Price per Page |
| --- | --- |
| Up to 1 million pages | $0.015 per page |
| Over 1 million pages | $0.01 per page |

#### Analyze Expense (invoices / receipts)

| Monthly Volume | Price per Page |
| --- | --- |
| Up to 1 million pages | $0.01 per page |
| Over 1 million pages | $0.008 per page |

#### Analyze ID (identity documents)

| Monthly Volume | Price per Page |
| --- | --- |
| Up to 1 million pages | $0.01 per page |
| Over 1 million pages | $0.008 per page |

> **POC relevance:** The POC calls `detect_document_text` only —
> billed at the Detect Text rate ($0.0015/page up to 1M).
> Each prescription image = 1 page.

---

### 9.2 Amazon Comprehend Medical

Comprehend Medical is priced per **unit**, where
**1 unit = 100 UTF-8 characters** (minimum 3 units per request).

#### NERe — Named Entity Recognition (what the POC uses)

`detect_entities_v2` is billed under the NERe tier.

| Monthly Volume | Price per Unit |
| --- | --- |
| First 10 million units | $0.01 per unit |
| 10M – 50M units | $0.005 per unit |
| 50M – 100M units | $0.00375 per unit |
| Over 100M units | Contact AWS |

#### ICD-10-CM Linking

| Monthly Volume | Price per Unit |
| --- | --- |
| First 10 million units | $0.01 per unit |
| 10M – 50M units | $0.005 per unit |
| Over 50M units | $0.00375 per unit |

#### RxNorm Linking

| Monthly Volume | Price per Unit |
| --- | --- |
| First 10 million units | $0.01 per unit |
| 10M – 50M units | $0.005 per unit |
| Over 50M units | $0.00375 per unit |

#### SNOMED CT Linking

| Monthly Volume | Price per Unit |
| --- | --- |
| First 10 million units | $0.01 per unit |
| 10M – 50M units | $0.005 per unit |
| Over 50M units | $0.00375 per unit |

> **POC relevance:** The POC calls `detect_entities_v2` only —
> billed under NERe. A typical prescription OCR output is ~500–1,500
> characters = 5–15 units per prescription.

---

### 9.3 Pricing Scenarios

Both scenarios use us-east-1 rates and assume `detect_document_text`
(Textract) + `detect_entities_v2` (Comprehend Medical NERe only).
Average prescription OCR output assumed at **1,000 characters = 10 units**.

---

#### Scenario A — Small Clinic (500 prescriptions/month)

A single GP practice or small pharmacy processing ~500 prescription
images per month.

**Textract cost:**

| Item | Calculation | Cost |
| --- | --- | --- |
| 500 pages × $0.0015 | Within free tier first 1,000 pages | $0.00 |

**Comprehend Medical cost:**

| Item | Calculation | Cost |
| --- | --- | --- |
| 500 prescriptions × 10 units × $0.01 | 5,000 units at NERe tier 1 | $0.50 |

| | Monthly Total |
| --- | --- |
| Textract | $0.00 (free tier) |
| Comprehend Medical | $0.50 |
| **Total** | **$0.50 / month** |

> At this scale the pipeline is essentially free. The dominant cost
> is infrastructure (Lambda, API Gateway, S3) not the AI services.

---

#### Scenario B — Regional Hospital Network (100,000 prescriptions/month)

A mid-size hospital network or pharmacy chain processing ~100,000
prescription images per month across multiple sites.

**Textract cost:**

| Item | Calculation | Cost |
| --- | --- | --- |
| 100,000 pages × $0.0015 | All within first 1M tier | $150.00 |

**Comprehend Medical cost:**

| Item | Calculation | Cost |
| --- | --- | --- |
| 100,000 × 10 units = 1,000,000 units × $0.01 | All within first 10M tier | $1,000.00 |

| | Monthly Total |
| --- | --- |
| Textract | $150.00 |
| Comprehend Medical | $1,000.00 |
| **Total** | **$1,150.00 / month** |
| **Per prescription** | **$0.0115** |

> At $0.0115 per prescription, the AI processing cost is a fraction
> of the ~15–20 minutes of pharmacist time it replaces. At an average
> pharmacist cost of $0.50/minute, each manual transcription costs
> ~$7.50–$10.00 — making the ROI approximately **650x–870x** at
> this volume.

---

## 10. Recommended Target Architecture

```text
app.py                  ← Streamlit UI (display only)
aws_session.py          ← single boto3.Session factory
textract_service.py     ← OCR (sync bytes + async S3 path)
comprehend_service.py   ← entity extraction (all categories, chunked)
pipeline.py             ← orchestrates textract → comprehend → output
```

---

## 11. Dependencies

Current:

```text
boto3              # AWS SDK
python-dotenv      # .env credential loading
streamlit          # Web UI
Pillow             # Image format conversion
```

Suggested additions:

```text
tenacity           # Retry / back-off for AWS throttling
pytest             # Unit testing
```
