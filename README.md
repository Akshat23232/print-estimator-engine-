AI Print Estimator & Order Intake Engine
Overview

The AI Print Estimator & Order Intake Engine is a backend-first system designed to convert unstructured print job requests into validated, auditable, and workflow-ready print estimates.

The system accepts print orders in natural language (text/email-like input) and metadata from PDFs or images, extracts structured specifications using an LLM, applies deterministic pricing rules, validates feasibility, and orchestrates human-in-the-loop workflows using n8n.

This project prioritizes clarity, correctness, and explainability over feature bloat, in line with real-world production systems.

Key Design Principles
1. LLM for Understanding, Not Pricing

AI is used only for extracting structured specifications from unstructured input.
All pricing decisions are rule-based and deterministic to ensure:

Auditability

Predictability

Business control

This avoids hallucinated pricing and keeps cost logic transparent.

2. Separation of Concerns

The system is intentionally modular:

Intake → Accept unstructured input

Extraction → Convert to structured schema (LLM)

Validation → Detect feasibility issues

Pricing → Deterministic cost calculation

Workflow → Human-in-loop orchestration (n8n)

Each layer can evolve independently without affecting others.

3. Validation-First Architecture

Instead of failing silently, the system explicitly flags issues such as:

Missing specifications

Invalid sizes

Low-resolution artwork (DPI thresholds)

Turnaround conflicts (rush vs standard)

Validation results are categorized into warnings vs blocking errors, enabling informed human review.

Architecture Overview
Frontend (React)
   │
   ▼
FastAPI Backend
   ├── Intake API (/intake)
   ├── LLM Spec Extraction
   ├── Validation Layer
   ├── Pricing Engine (rule-based)
   └── Webhook Trigger
           │
           ▼
        n8n Workflow

Technology Stack
Backend

FastAPI (Python) – API layer & business logic

Pydantic – Schema enforcement

Docker & Docker Compose – Local deployment

Swagger / OpenAPI – API documentation

Frontend

React + TypeScript

Intake UI for text / PDF / image metadata

Results view for pricing & validation feedback

AI Layer

LLM used with a strict structured prompt

Enforces JSON output schema

Handles ambiguity gracefully

Workflow

n8n – Human-in-the-loop orchestration

CSR review, approval, rejection, escalation

Order Intake

The system accepts:

Plain text requests (also covers email body input)

PDF RFQs (metadata-based, OCR marked as future enhancement)

Image uploads (metadata + DPI validation)

Partial implementations for PDF/image content extraction are explicitly documented, prioritizing correctness over pretending full OCR support.

Pricing Engine

Pricing is calculated using a rule-based engine driven by configuration:

Cost Components

Material cost

Print method decision (digital vs offset)

Setup cost

Finishing cost

Quantity-based discounts

Margin

Rush fees

Tax

Final total

Print Method Logic

Digital for low-volume jobs (setup cost dominates)

Offset for high-volume jobs (economies of scale)

All thresholds are documented and configurable.

Validation Layer

Validation checks include:

Missing required fields

Invalid dimensions

Low-resolution artwork (DPI thresholds: 200/300)

Turnaround conflicts (rush vs slow options)

Results are returned as:

Warnings → Can proceed with review

Blockers → Require correction or rejection

Workflow Orchestration (n8n)

After estimation, a webhook triggers an n8n workflow that supports:

CSR review

Customer approval

Auto-rejection for blocking issues

Escalation when required

Final handoff to MIS / ERP (mocked)

The workflow JSON is included for inspection and extension.

Demo Mode vs Production Mode
Demo Mode (Preview)

Automatically enabled when backend is not reachable

Uses realistic mock responses

Mirrors backend schemas exactly

Clearly indicated in the UI

Production Mode

Backend runs locally via Docker Compose

Real FastAPI endpoints

Deterministic pricing & validation

No mock logic in production paths

This separation ensures honest previews without misleading behavior.

API Documentation

Once the backend is running, Swagger docs are available at:

http://localhost:8000/docs

Running Locally
Prerequisites

Docker

Docker Compose

Start the Backend
docker-compose up --build

Access API
http://localhost:8000

Access API Docs
http://localhost:8000/docs

Testing

Basic unit tests are included for:

Pricing calculations

Validation logic

The focus is on correctness of business rules rather than exhaustive coverage.

Known Limitations & Future Improvements

Full OCR for PDFs and images

Persistent storage for orders and estimates

Advanced artwork analysis

ERP/MIS real integrations

Authentication & authorization

Pricing versioning UI

These are intentionally scoped out and documented.

Why This Approach

This project was built to demonstrate:

Correct use of AI (assistive, not authoritative)

Deterministic business logic

Clear validation feedback

Production-ready architecture thinking

Honest documentation of tradeoffs

Partial implementations are intentional and documented, in line with real-world system design.
