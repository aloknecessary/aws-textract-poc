# Technical Documentation: AWS Textract POC

## 1. Overview

This proof-of-concept (POC) demonstrates an automated pipeline for extracting structured medical information from prescription images. It combines two AWS AI services:

- **Amazon Textract** for Optical Character Recognition (OCR)
- **Amazon Comprehend Medical** for Natural Language Processing (NLP) of medical text

The system accepts a prescription image, extracts raw text using Textract, then passes that text through Comprehend Medical to identify medications, medical conditions, and clinical procedures with associated attributes and confidence scores.

---

## 2. Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                     (Streamlit - app.py)                             │
│                                                                     │
│   ┌───────────┐    ┌──────────────┐    ┌────────────────────────┐  │
│   │  Upload   │───>│  Image       │───>│  Display Results       │  │
│   │  Image    │    │  Preview     │    │  (Tables + OCR Text)   │  │
│   └───────────┘    └──────────────┘    └────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ JPEG Bytes
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROCESSING PIPELINE                             │
│                                                                     │
│  ┌─────────────────────┐         ┌──────────────────────────────┐  │
│  │  textract_service.py │         │         main.py              │  │
│  │                     │         │                              │  │
│  │  ┌───────────────┐  │  text   │  ┌────────────────────────┐ │  │
│  │  │  Textract API  │──┼────────>│  │  Comprehend Medical    │ │  │
│  │  │  (OCR)        │  │         │  │  (NLP Entity Extract)  │ │  │
│  │  └───────────────┘  │         │  └────────────────────────┘ │  │
│  └─────────────────────┘         └──────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS CLOUD SERVICES                            │
│                                                                     │
│   ┌──────────────────┐          ┌─────────────────────────────┐    │
│   │ Amazon Textract   │          │ Amazon Comprehend Medical    │    │
│   │                  │          │                             │    │
│   │ - DetectDocument │          │ - DetectEntitiesV2          │    │
│   │   Text           │          │ - 7 Entity Categories       │    │
│   │ - LINE blocks    │          │ - Attributes + Traits       │    │
│   └──────────────────┘          └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Diagram

```
┌──────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Prescrip-│     │   Pillow     │     │   Amazon      │     │   Amazon     │
│ tion     │────>│   Image      │────>│   Textract    │────>│   Comprehend │
│ Image    │     │   Convert    │     │   OCR         │     │   Medical    │
│ (Upload) │     │   to JPEG    │     │               │     │              │
└──────────┘     └──────────────┘     └───────────────┘     └──────────────┘
                                            │                       │
                                            ▼                       ▼
                                      ┌───────────┐         ┌─────────────┐
                                      │ Raw Text  │         │ Structured  │
                                      │ (lines)   │         │ JSON with   │
                                      │           │         │ entities    │
                                      └───────────┘         └─────────────┘
                                                                    │
                                                                    ▼
                                                            ┌─────────────┐
                                                            │ Streamlit   │
                                                            │ UI Tables   │
                                                            └─────────────┘
```

### 2.3 Component Interaction Sequence

```
User          Streamlit(app.py)     textract_service.py     main.py        AWS
 │                  │                      │                   │             │
 │─── Upload ──────>│                      │                   │             │
 │                  │── Convert to JPEG ──>│                   │             │
 │                  │                      │── detect_document_text ────────>│
 │                  │                      │<──── Blocks (LINE) ────────────│
 │                  │<── extracted_text ───│                   │             │
 │                  │                      │                   │             │
 │                  │──────────────────────────── raw_text ───>│             │
 │                  │                      │                   │── detect_entities_v2 ─>│
 │                  │                      │                   │<── Entities ───────────│
 │                  │<──────────────────────── structured_data │             │
 │<── Render ──────│                      │                   │             │
 │    Tables        │                      │                   │             │
```

---

## 3. Project Structure

```
aws-textract-poc/
├── app.py                  # Streamlit web frontend
├── main.py                 # Pipeline orchestration + Comprehend Medical logic
├── textract_service.py     # Amazon Textract OCR service module
├── test_textract.py        # Standalone Textract testing script
├── requirements.txt        # Python dependencies
├── .env                    # AWS credentials (not committed)
├── .gitignore              # Git ignore rules
├── README.md               # Project overview
├── docs/
│   └── TECHNICAL_DOCUMENTATION.md  # This file
└── dataset/
    └── test/               # Sample prescription images for testing
```

---

## 4. Module Documentation

### 4.1 textract_service.py

Handles all interactions with Amazon Textract. Isolated for independent testing and reuse.

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `initialize_textract_client()` | None | `boto3.client` or `None` | Creates a Textract client using credentials from `.env` |
| `extract_text_from_bytes(textract_client, image_bytes)` | Textract client, raw image bytes | `str` or `None` | Sends image to Textract, returns stitched text lines |
| `extract_text_from_file(image_path)` | File path string | `str` or `None` | Convenience wrapper that reads a file and extracts text |

**Textract API Used:** `detect_document_text`

**Processing Logic:**
1. Sends raw image bytes to Textract's `detect_document_text` API
2. Iterates through response `Blocks`
3. Filters for `BlockType == 'LINE'`
4. Joins all line texts with newline characters

### 4.2 main.py

Orchestrates the full pipeline and contains the Comprehend Medical integration.

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `initialize_comprehend_client()` | None | `boto3.client` or `None` | Creates a Comprehend Medical client |
| `extract_medical_insights(comprehend_client, raw_text)` | Client, text string | `dict` or `None` | Extracts all medical entities from text |
| `run_prescription_pipeline(local_image_path)` | File path string | `dict` or `None` | End-to-end pipeline: OCR then NLP |

**Comprehend Medical API Used:** `detect_entities_v2`

**Entity Categories Extracted:**

| Category | Description | Example Types |
|----------|-------------|---------------|
| `MEDICATION` | Drug names and dosage info | BRAND_NAME, GENERIC_NAME |
| `MEDICAL_CONDITION` | Diagnoses, symptoms, signs | DX_NAME |
| `ANATOMY` | Body parts and systems | SYSTEM_ORGAN_SITE |
| `TEST_TREATMENT_PROCEDURE` | Clinical procedures and tests | TEST_NAME, PROCEDURE_NAME, TREATMENT_NAME |
| `PROTECTED_HEALTH_INFORMATION` | Patient PII | NAME, ADDRESS, AGE, ID |
| `BEHAVIORAL_ENVIRONMENTAL_SOCIAL` | Lifestyle factors | TOBACCO_USE, ALCOHOL_CONSUMPTION, ALLERGIES |
| `TIME_EXPRESSION` | Temporal references | TIME_TO_MEDICATION_NAME, TIME_TO_DX_NAME |

**Entity Data Structure:**
```json
{
  "text": "ibuprofen",
  "type": "GENERIC_NAME",
  "confidence": 98.75,
  "traits": ["NEGATION", "PAST_HISTORY"],
  "attributes": {
    "dosage": {
      "value": "200mg",
      "confidence": 95.2
    },
    "frequency": {
      "value": "twice daily",
      "confidence": 91.8
    }
  }
}
```

### 4.3 app.py

Streamlit-based web interface providing image upload and results visualization.

**Key Features:**
- Image upload with format validation (JPEG, JPG, PNG)
- Automatic image conversion to JPEG via Pillow (handles RGBA/PNG transparency)
- Real-time progress spinners during API calls
- Dynamic table rendering that adapts columns to detected attributes
- Confidence score badges for each entity
- Console logging of raw Comprehend Medical response for debugging

**UI Sections Displayed:**
1. Extracted Text (monospace OCR output)
2. Medications table
3. Medical Conditions table
4. Tests, Treatments and Procedures table

---

## 5. AWS Services Configuration

### 5.1 Required AWS Services

| Service | API | Purpose | Pricing Model |
|---------|-----|---------|---------------|
| Amazon Textract | `DetectDocumentText` | OCR - extract text from images | Per page processed |
| Amazon Comprehend Medical | `DetectEntitiesV2` | NLP - extract medical entities | Per character analyzed |

### 5.2 IAM Permissions Required

The IAM user or role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "comprehendmedical:DetectEntitiesV2"
      ],
      "Resource": "*"
    }
  ]
}
```

### 5.3 Authentication

Credentials are managed via a `.env` file loaded by `python-dotenv`:

```
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_DEFAULT_REGION=us-east-1
```

Boto3 automatically reads these environment variables when creating clients.

### 5.4 Supported Regions

Amazon Comprehend Medical is available in limited regions. Ensure `AWS_DEFAULT_REGION` is set to one of:
- `us-east-1` (N. Virginia)
- `us-east-2` (Ohio)
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)
- `eu-west-2` (London)
- `ap-southeast-2` (Sydney)
- `ca-central-1` (Canada)

---

## 6. Input Specifications

### 6.1 Supported Image Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| JPEG | `.jpeg`, `.jpg` | Native Textract support |
| PNG | `.png` | Converted to JPEG before sending (handles RGBA) |

### 6.2 Textract Limits

| Constraint | Limit |
|-----------|-------|
| Max file size (synchronous) | 10 MB |
| Max image dimensions | 10,000 x 10,000 pixels |
| Supported formats | JPEG, PNG, PDF, TIFF |
| Max pages (synchronous) | 1 |

### 6.3 Comprehend Medical Limits

| Constraint | Limit |
|-----------|-------|
| Max text length per request | 20,000 characters (UTF-8) |
| Min text length | 1 character |

---

## 7. Output Schema

### 7.1 Full Response Structure

```json
{
  "medications": [
    {
      "text": "Amoxicillin",
      "type": "GENERIC_NAME",
      "confidence": 99.12,
      "traits": [],
      "attributes": {
        "dosage": { "value": "500mg", "confidence": 97.5 },
        "frequency": { "value": "three times daily", "confidence": 94.3 },
        "duration": { "value": "7 days", "confidence": 91.0 },
        "route_or_mode": { "value": "oral", "confidence": 96.8 },
        "form": { "value": "capsule", "confidence": 95.1 }
      }
    }
  ],
  "medical_conditions": [
    {
      "text": "hypertension",
      "type": "DX_NAME",
      "confidence": 97.8,
      "traits": ["DIAGNOSIS"],
      "attributes": {
        "acuity": { "value": "chronic", "confidence": 88.5 }
      }
    }
  ],
  "test_treatment_procedures": [
    {
      "text": "blood pressure",
      "type": "TEST_NAME",
      "confidence": 96.2,
      "traits": [],
      "attributes": {
        "test_value": { "value": "140/90", "confidence": 93.1 }
      }
    }
  ],
  "anatomy": [],
  "protected_health_information": [],
  "behavioral_environmental_social": [],
  "time_expressions": []
}
```

---

## 8. Error Handling

| Error Scenario | Handling |
|---------------|----------|
| Missing AWS credentials | Caught by `NoCredentialsError`/`PartialCredentialsError`, user-friendly message |
| Invalid image format | Pillow converts to JPEG; Textract `ClientError` caught |
| Textract API failure | `ClientError` caught, error message displayed |
| Comprehend Medical API failure | `ClientError` caught, error message displayed |
| Empty text extraction | Pipeline halts with warning before calling Comprehend |
| File not found (CLI mode) | Path check with `os.path.exists()` before processing |

---

## 9. Running the Application

### 9.1 Prerequisites

- Python 3.8+
- AWS account with Textract and Comprehend Medical access
- IAM credentials with appropriate permissions

### 9.2 Installation

```bash
pip install -r requirements.txt
```

### 9.3 Configuration

Create a `.env` file in the project root:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 9.4 Usage

**Web UI:**
```bash
streamlit run app.py
```

**Command Line (full pipeline):**
```bash
python main.py path/to/image.jpeg
```

**Textract only (testing OCR):**
```bash
python test_textract.py path/to/image.jpeg
```

---

## 10. Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `boto3` | Latest | AWS SDK for Python |
| `python-dotenv` | Latest | Load `.env` credentials |
| `streamlit` | Latest | Web UI framework |
| `Pillow` | Latest | Image format conversion |

---

## 11. Limitations and Future Considerations

### Current Limitations

- **Synchronous API only:** Single-page document processing (no batch mode in UI)
- **No result persistence:** Results are not stored; each analysis is ephemeral
- **Image quality dependency:** OCR accuracy depends heavily on image clarity and handwriting legibility
- **No confidence threshold filtering:** All detected entities shown regardless of score
- **Single region:** Configured for one AWS region at a time

### Potential Enhancements

- Add confidence threshold slider in the UI to filter low-confidence entities
- Implement batch processing with `StartEntitiesDetectionV2Job` for multiple documents
- Store results in DynamoDB or S3 for historical analysis
- Add PDF support via Textract async APIs
- Implement `DetectPHI` for dedicated PHI detection workflows
- Add export functionality (CSV, PDF report)
- Integrate with Amazon S3 for document storage
- Add authentication layer to the Streamlit app for production use
