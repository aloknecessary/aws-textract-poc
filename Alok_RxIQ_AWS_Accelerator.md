# RxIQ — Intelligent Prescription Processing Accelerator

> Powered by AWS  ·  Partner Accelerator Submission

---

## THE PROBLEM THAT COSTS LIVES AND BILLIONS

Every day, clinicians write prescriptions that pharmacists must manually
re-read, re-type, and re-verify before a patient receives medication.
This chain of manual handoffs is not a workflow inconvenience — it is a
patient safety crisis hiding in plain sight.

The World Health Organization estimates that medication errors harm
**1 in 30 patients globally**, with a significant proportion traced
directly to transcription failures at the prescription stage. In the
United States alone, preventable medication errors cost the healthcare
system **$21 billion annually**. Globally, the figure exceeds
**$42 billion**.

The root cause is structural: prescriptions arrive as unstructured
images — handwritten notes, scanned documents, photographed slips —
and the systems that need to act on them speak only structured data.
The gap between those two states is filled entirely by human effort,
human memory, and human error.

Healthcare organisations have invested heavily in EHR platforms,
dispensing systems, and clinical decision support tools. None of them
solve the ingestion problem. The data still has to be typed in by hand.

**RxIQ closes that gap — completely, on AWS, in weeks.**

---

## WHAT RxIQ IS

RxIQ is a production-ready AI accelerator that transforms unstructured
prescription images into structured, clinically validated data — and
delivers that data directly into the systems that need it.

It is not a research project. It is not a pilot. It is a deployable,
tested, AWS-native pipeline built on a validated proof of concept run
against real-world prescription images across handwritten and printed
formats.

RxIQ ships as four integrated modules:

---

### MODULE 1 — PrescriptScan

#### Intelligent OCR for medical documents

PrescriptScan uses Amazon Textract to extract text from prescription
images with accuracy that matches or exceeds trained human transcribers
— across printed prescriptions, handwritten notes, and mixed-format
documents.

- Handles JPEG, PNG, and multi-page PDF formats
- Normalises image quality before submission — contrast correction,
  format conversion, resolution validation
- Returns structured LINE-level text blocks with spatial positioning
  preserved — critical for reading order accuracy on complex layouts
- Validated against 27 real-world prescription images across varied
  handwriting styles, paper types, and scan qualities

**AWS services:** Amazon Textract (`detect_document_text`,
`start_document_text_detection` for async batch)

---

### MODULE 2 — ClinicalLens

#### Clinical entity extraction and relationship mapping

ClinicalLens passes PrescriptScan output through Amazon Comprehend
Medical to extract every clinically relevant entity — not just
medication names, but the full clinical context surrounding them.

Entities extracted across all 7 Comprehend Medical categories:

| Category | What Gets Extracted |
| --- | --- |
| Medications | Drug name, dosage, frequency, route, form, duration |
| Medical Conditions | Diagnoses, symptoms, comorbidities |
| Anatomy | Body sites, organ systems, laterality |
| Tests & Procedures | Lab orders, imaging, surgical references |
| Protected Health Info | Patient name, DOB, address, contact details |
| Behavioral / Social | Smoking status, alcohol use, social determinants |
| Time Expressions | Prescription date, start/end dates, review dates |

Each entity is returned with a confidence score, trait flags
(e.g., NEGATION, HYPOTHETICAL), and nested attribute relationships —
so a dosage is always linked to its parent medication, not floating
as an orphaned data point.

**AWS services:** Amazon Comprehend Medical (`detect_entities_v2`)

---

### MODULE 3 — GuardianPHI

#### Automated PHI governance and compliance layer

GuardianPHI intercepts every processed prescription and applies
automated PHI governance before data moves downstream — without
requiring a separate compliance tool or manual review queue.

- Detects and labels all PHI entities in real time using Comprehend
  Medical's native PHI category
- Applies configurable downstream routing: PHI fields can be
  redacted, tokenised, or access-controlled based on the consuming
  system's clearance level
- Generates an immutable audit record per prescription — timestamp,
  PHI entities detected, routing decision, consuming system identity
- Designed for HIPAA-eligible deployment under a signed AWS BAA

**AWS services:** Amazon Comprehend Medical, AWS KMS, Amazon S3
(encrypted), Amazon CloudWatch Logs

---

### MODULE 4 — FlowBridge

#### EHR/EMR integration and downstream delivery

FlowBridge takes the structured output from ClinicalLens and delivers
it to the systems that need it — without custom integration work for
every target system.

- Pre-built connectors for HL7 FHIR R4, Epic, Cerner, and generic
  REST endpoints
- Configurable field mapping — the RxIQ output schema maps to the
  target system's data model via a no-code mapping interface
- Supports both real-time (single prescription) and batch
  (end-of-day bulk) delivery modes
- Dead-letter queue and retry logic for failed deliveries — no
  prescription is silently dropped

**AWS services:** Amazon API Gateway, AWS Lambda, Amazon SQS,
Amazon EventBridge, Amazon DynamoDB

---

## THE ARCHITECTURE

```text
[Prescription Image — JPEG / PNG / PDF]
        │
        ▼
[PrescriptScan — Amazon Textract]
  └─ Image normalisation (format, resolution, colour mode)
  └─ OCR extraction → structured text blocks
        │
        ▼
[ClinicalLens — Amazon Comprehend Medical]
  └─ Text chunking (≤20,000 chars per API call)
  └─ Entity extraction across 7 clinical categories
  └─ Confidence scoring + attribute relationship mapping
        │
        ▼
[GuardianPHI — PHI Detection & Governance]
  └─ PHI labelling and routing decision
  └─ Audit record written to CloudWatch Logs
  └─ Encrypted storage in S3 (SSE-KMS)
        │
        ▼
[FlowBridge — Integration & Delivery]
  └─ FHIR / HL7 / REST connector
  └─ Field mapping to target system schema
  └─ Real-time or batch delivery via SQS + Lambda
        │
        ▼
[EHR / EMR / Dispensing System / Analytics Platform]
```

---

## WHY AWS + US

**We bring:**

- A working, validated proof of concept — not a slide deck. The core
  pipeline has been built, tested against real prescription images, and
  hardened for production concerns (PHI safety, API limit handling,
  input sanitisation, error recovery)
- Deep understanding of the Textract + Comprehend Medical integration
  surface — including the non-obvious constraints (image size limits,
  20,000-character chunking, RGBA format normalisation, entity
  attribute nesting) that only emerge from building, not reading docs
- Healthcare domain expertise — clinical entity taxonomy, PHI
  governance requirements, HIPAA-eligible architecture patterns, and
  EHR integration experience
- A repeatable implementation playbook derived from the POC — service
  selection is proven, architecture decisions are documented, and
  known constraints are already scoped

**AWS brings:**

- Amazon Textract — the only managed OCR service with native support
  for handwritten medical text at production scale
- Amazon Comprehend Medical — purpose-built clinical NLP with a
  7-category entity model that no general-purpose NLP service matches
- HIPAA-eligible service coverage under a signed BAA — Textract and
  Comprehend Medical are both on the AWS HIPAA eligible services list
- Amazon Bedrock — for the next generation of RxIQ: conversational
  prescription querying, anomaly flagging, and clinical summarisation
- AWS HealthLake — for longitudinal patient data storage and FHIR-
  native querying as RxIQ scales beyond single-prescription processing
- AWS Marketplace — for streamlined commercial delivery to health
  system procurement teams already transacting on AWS

---

## TARGET MARKET

**Primary:**

- Hospital systems and integrated delivery networks (IDNs)
- Retail pharmacy chains and pharmacy benefit managers (PBMs)
- Specialty pharmacy and compounding pharmacy operators

**Secondary:**

- Health insurance and prior authorisation teams processing
  prescription documentation
- Clinical research organisations (CROs) processing trial prescriptions
- Government health agencies digitising paper prescription archives

**Geography:** US (HIPAA), UK (NHS / GDPR), Australia (My Health Record),
EU (GDPR + national health frameworks), India (ABDM digital health stack)

---

## WHY NOW

**The regulatory window is open — and closing.**

- The US Drug Enforcement Administration (DEA) has expanded electronic
  prescription rules for controlled substances — creating immediate
  demand for compliant digital prescription processing infrastructure
- The 21st Century Cures Act mandates interoperability and information
  blocking prevention — health systems need structured prescription
  data flowing into FHIR-compliant systems, not locked in image files
- NHS England's digital transformation programme is driving UK trusts
  to eliminate paper-based prescription workflows by 2026
- Post-pandemic, health systems are under sustained pressure to reduce
  administrative burden on clinical staff — prescription transcription
  is the highest-volume, lowest-value manual task in the pharmacy
  workflow
- AWS has no dominant, purpose-built prescription intelligence
  accelerator in Marketplace today — the category is open

---

## WHAT A CUSTOMER GETS

An **8–10 week deployment** that includes:

| Deliverable | Detail |
| --- | --- |
| All 4 RxIQ modules | PrescriptScan, ClinicalLens, GuardianPHI, FlowBridge |
| AWS reference architecture | CDK-deployable infrastructure — VPC, IAM roles, S3, Lambda, SQS, DynamoDB, CloudWatch |
| Integration connectors | Pre-built FHIR R4 and REST connectors; custom connector for primary EHR/EMR |
| PHI governance runbook | HIPAA-aligned operating procedures for PHI handling, audit review, and incident response |
| Confidence threshold tuning | Calibrated confidence thresholds per entity category based on customer's prescription corpus |
| Validation report | Accuracy metrics from customer images — not benchmarks |
| Handover & enablement | Walkthrough, runbook training, 30-day hypercare |

**Not a prototype. Not a pilot. Production-ready on day one of go-live.**

---

## PROOF POINTS FROM THE POC

These are measured outcomes from the validated proof of concept —
not projections:

- **100% of test images processed successfully** — Textract extracted
  text from all 27 prescription images across handwritten and printed
  formats without fine-tuning or custom model training
- **All 7 clinical entity categories returned** — Comprehend Medical
  consistently identified medications with nested dosage, frequency,
  and route attributes across every test prescription
- **Sub-3-second end-to-end latency** — from image submission to
  structured entity output, measured across all test runs
- **Zero API limit failures** — the 20,000-character chunking strategy
  handled all test images completely; no truncation, no silent failures
- **PHI detected on every applicable image** — patient names, dates,
  and addresses were consistently identified and labelled without
  additional configuration
- **No custom ML model required** — the entire pipeline runs on AWS
  managed services; no training data, no labelling effort, no MLOps
  overhead in the customer's environment

---

## COMPETITIVE DIFFERENTIATION

| Dimension | RxIQ | Generic OCR + NLP | Build-Your-Own |
| --- | --- | --- | --- |
| Time to production | 8–10 weeks | 6–12 months | 9–18 months |
| Clinical entity depth | 7 categories, nested attributes | Medication name only | Depends on team |
| PHI governance built-in | Yes — GuardianPHI | No | Manual build |
| HIPAA-eligible architecture | Yes | Varies | Yes, if designed correctly |
| EHR integration | Pre-built connectors | Custom only | Custom only |
| Validated on real prescriptions | Yes — 27-image POC | No | No |
| AWS Marketplace listing | Yes | No | No |

---

## THE ASK

1. **Joint accelerator listing on AWS Marketplace** — RxIQ listed as
   an AWS Partner Network (APN) validated solution under the Health &
   Life Sciences category

2. **Co-sell motion with AWS field teams** — alignment with AWS
   Healthcare & Life Sciences specialist sellers for joint customer
   engagements

3. **AWS Competency consideration** — nomination for the AWS Health AI
   Competency to signal validated domain expertise to health system
   buyers

4. **Access to AWS funding programs** — AWS Partner Funding (APF) and
   AWS credits for qualified health system customers in the pipeline

5. **AWS HealthLake and Bedrock early access** — to accelerate the
   next-generation RxIQ roadmap (conversational prescription querying,
   longitudinal patient context, anomaly detection)

---

## THE BOTTOM LINE

Prescription transcription errors kill people. The technology to
eliminate them exists today, on AWS, and has been validated against
real clinical data. RxIQ is not a vision — it is a working system
looking for the distribution that AWS Marketplace and the APN
co-sell motion provide.

The POC is done. The architecture is proven. The market is ready.

**RxIQ — From Image to Insight. In Seconds. On AWS.**
