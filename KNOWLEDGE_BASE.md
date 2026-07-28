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

## 9. Recommended Target Architecture

```text
app.py                  ← Streamlit UI (display only)
aws_session.py          ← single boto3.Session factory
textract_service.py     ← OCR (sync bytes + async S3 path)
comprehend_service.py   ← entity extraction (all categories, chunked)
pipeline.py             ← orchestrates textract → comprehend → output
```

---

## 10. Dependencies

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
