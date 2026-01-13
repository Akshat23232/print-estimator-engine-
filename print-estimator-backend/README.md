# AI-Driven Print Estimator & Order Intake Engine

A modular FastAPI backend demonstrating AI-assisted specification extraction with deterministic, rule-based pricing. Built for technical assessment with emphasis on architecture clarity, honest documentation, and production-readiness awareness.

---

## 🎯 Executive Summary

This system accepts print job requests (text, PDF metadata, image metadata), uses an LLM to extract structured specifications, calculates pricing via deterministic rules, validates business constraints, and integrates with n8n for human-in-the-loop order processing.

**Key Design Principle**: AI handles *ambiguity* (natural language → structure), rules handle *consistency* (pricing, validation).

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (React)                                  │
│                    Intake Form → Results Display → Demo Mode                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ POST /intake
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (FastAPI)                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  POST /intake              GET /health              GET /docs         │  │
│  │  - Accept text/PDF/image   - Container health       - OpenAPI/Swagger │  │
│  │  - Orchestrate pipeline    - Dependency check                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                          ┌───────────┴───────────┐                          │
│                          ▼                       ▼                          │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │    🤖 LLM EXTRACTOR        │  │       📊 SERVICE LAYER               │  │
│  │                             │  │  ┌─────────────────────────────────┐│  │
│  │  • OpenAI-compatible API    │  │  │  PRICING ENGINE (Deterministic) ││  │
│  │  • Structured JSON prompt   │  │  │  • Material + Print + Setup     ││  │
│  │  • Temperature = 0          │  │  │  • Digital vs Offset decision   ││  │
│  │  • Handles ambiguity        │  │  │  • Quantity discounts           ││  │
│  │                             │  │  │  • Rush pricing                 ││  │
│  │  INPUT:                     │  │  │  • NO AI - pure calculation     ││  │
│  │  "500 business cards,       │  │  └─────────────────────────────────┘│  │
│  │   matte, double-sided"      │  │  ┌─────────────────────────────────┐│  │
│  │                             │  │  │  VALIDATOR                      ││  │
│  │  OUTPUT:                    │  │  │  • Errors (blockers)            ││  │
│  │  {                          │  │  │  • Warnings (acknowledgment)    ││  │
│  │    product_type: "cards",   │  │  │  • Missing fields (defaults)    ││  │
│  │    quantity: 500,           │  │  │  • Artwork DPI check            ││  │
│  │    finish: "matte",         │  │  │  • Turnaround conflicts         ││  │
│  │    sides: "double"          │  │  └─────────────────────────────────┘│  │
│  │  }                          │  └─────────────────────────────────────┘  │
│  └─────────────────────────────┘                                            │
│                                      │                                       │
└──────────────────────────────────────┼───────────────────────────────────────┘
                                       │
                                       ▼ Async Webhook
┌─────────────────────────────────────────────────────────────────────────────┐
│                          n8n WORKFLOW ENGINE                                 │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────────────┐  │
│  │  Webhook  │───▶│ Validate  │───▶│  Route    │───▶│  Human Decision   │  │
│  │  Trigger  │    │  Check    │    │  Logic    │    │  (CSR/Customer)   │  │
│  └───────────┘    └───────────┘    └───────────┘    └───────────────────┘  │
│                                           │                    │            │
│                         ┌─────────────────┼────────────────────┤            │
│                         ▼                 ▼                    ▼            │
│                 ┌──────────────┐  ┌──────────────┐    ┌──────────────┐     │
│                 │ Auto-Approve │  │  CSR Review  │    │   Reject     │     │
│                 │   (Clean)    │  │  (Blockers)  │    │  (Critical)  │     │
│                 └──────┬───────┘  └──────┬───────┘    └──────────────┘     │
│                        │                 │                                   │
│                        └────────┬────────┘                                  │
│                                 ▼                                            │
│                        ┌──────────────┐                                     │
│                        │  MIS / ERP   │                                     │
│                        │  Integration │                                     │
│                        └──────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Design Philosophy

### Why LLM for Extraction Only?

This is the **most critical design decision** in the system. Here's the reasoning:

| Concern | AI Approach | Rule Approach | Our Choice |
|---------|-------------|---------------|------------|
| **Spec Extraction** | ✅ Handles ambiguity, synonyms, typos | ❌ Brittle regex, misses variations | **AI** |
| **Pricing** | ❌ Non-deterministic, unexplainable | ✅ Auditable, consistent, predictable | **Rules** |
| **Validation** | ❌ May miss edge cases, inconsistent | ✅ Explicit business rules | **Rules** |

**The Problem AI Solves:**
Customers express print needs in countless ways:
- "five hundred cards" vs "500 business cards" vs "BC x500"
- "glossy" vs "gloss finish" vs "shiny coating"
- "both sides" vs "duplex" vs "2-sided"

A regex-based parser would need hundreds of patterns and still miss variations. An LLM handles this gracefully.

**Why NOT AI for Pricing:**
1. **Non-Reproducibility**: Same prompt → different outputs (even with temperature=0)
2. **Unexplainability**: "Why does this cost $247?" - "The AI decided"
3. **Liability**: Legal disputes require calculation audit trail
4. **Trust**: Customers need predictable, verifiable pricing

### Why Deterministic Pricing?

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PRICING ENGINE GUARANTEE                                                │
│                                                                          │
│  Given identical inputs:                                                 │
│    • Same product type, quantity, options, turnaround                   │
│                                                                          │
│  The engine will ALWAYS produce:                                        │
│    • Same material cost, print cost, setup cost                         │
│    • Same discounts, rush fees, margin                                  │
│    • Same total price                                                    │
│                                                                          │
│  This is NOT true for LLM-based pricing.                                │
└─────────────────────────────────────────────────────────────────────────┘
```

**Business Justifications:**
1. **Auditability**: Finance can trace every line item
2. **Consistency**: Customer A and Customer B pay the same for identical orders
3. **Legal Compliance**: Pricing disputes require clear calculation trail
4. **Maintainability**: pricing.json is version-controlled, changes are tracked

### Validation Philosophy: Three-Tier Feedback

We categorize validation issues to enable **smart workflow routing**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ERRORS (Blockers)                                                       │
│  ├── Order CANNOT proceed automatically                                  │
│  ├── Requires human intervention (CSR review)                           │
│  └── Examples:                                                           │
│      • Unknown product type                                              │
│      • Quantity below minimum                                            │
│      • Artwork DPI < 200 (unprintable)                                  │
│      • Rush turnaround + slow finishing options                         │
├─────────────────────────────────────────────────────────────────────────┤
│  WARNINGS                                                                │
│  ├── Order CAN proceed with acknowledgment                              │
│  ├── Customer sees and confirms                                          │
│  └── Examples:                                                           │
│      • Non-standard size (may affect price)                             │
│      • Rush fees will apply                                              │
│      • Large order qualifies for sales quote                            │
│      • Artwork DPI 200-300 (quality may suffer)                         │
├─────────────────────────────────────────────────────────────────────────┤
│  MISSING FIELDS                                                          │
│  ├── Defaults applied automatically                                      │
│  ├── Informational only                                                  │
│  └── Examples:                                                           │
│      • Paper stock not specified → use product default                  │
│      • Finish not specified → default to matte                          │
│      • Color mode not specified → assume full color                     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Workflow Routing:**
- **All Errors** → CSR Review Queue (human must intervene)
- **Warnings Only** → Customer Confirmation (automated email/SMS)
- **Clean** → Auto-Approve Path (fastest fulfillment)

---

## 📁 Project Structure

```
print-estimator-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, exception handling
│   ├── config.py               # Pydantic settings, environment config
│   ├── routers/
│   │   └── intake.py           # POST /intake endpoint orchestration
│   ├── services/
│   │   ├── llm_extractor.py    # OpenAI-compatible extraction (AI HERE)
│   │   ├── pricing.py          # Deterministic pricing engine (NO AI)
│   │   └── validator.py        # Business rule validation (NO AI)
│   ├── schemas/
│   │   ├── intake.py           # Request/response models
│   │   └── print_specs.py      # Domain models
│   └── data/
│       └── pricing.json        # Pricing configuration (version controlled)
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_intake.py          # Endpoint tests
│   └── test_pricing.py         # Pricing engine tests
├── n8n_examples/
│   ├── webhook_payloads.json   # Example payloads for testing
│   └── print_order_workflow.json  # Complete importable n8n workflow
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (or compatible endpoint)

### One-Command Startup

```bash
# 1. Clone and configure
cd print-estimator-backend
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 2. Launch
docker-compose up --build

# 3. Test
curl -X POST http://localhost:8000/intake \
  -H "Content-Type: application/json" \
  -d '{"input_type": "text", "content": "500 business cards, double-sided, matte finish with rounded corners"}'
```

### Access Points
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📡 API Reference

### POST /intake

Submit print job specifications for extraction, validation, and pricing.

**Request:**
```json
{
  "input_type": "text",
  "content": "I need 500 business cards, double-sided printing on 14pt cardstock, matte finish with rounded corners. Rush order - need in 2 days.",
  "metadata": null
}
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "extracted_specs": {
    "product_type": "business_cards",
    "quantity": 500,
    "size": "3.5x2",
    "paper_stock": "14pt",
    "sides": "double",
    "finish": "matte",
    "color_mode": "full_color",
    "options": ["rounded_corners"],
    "turnaround_days": 2,
    "is_rush": true
  },
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": [
      "2-day rush turnaround. Rush fees will apply.",
      "Large order: may qualify for additional volume discounts."
    ],
    "missing_fields": []
  },
  "estimate": {
    "print_method": "offset",
    "print_method_reason": "Offset printing selected: quantity (500) at or above 500 threshold.",
    "breakdown": {
      "material_cost": 10.00,
      "print_cost": 28.80,
      "setup_cost": 150.00,
      "finishing_cost": 14.40,
      "option_costs": {"rounded_corners": 15.00},
      "rush_fee": 54.55,
      "quantity_discount": -21.82,
      "margin_amount": 75.28,
      "margin_percent": 30
    },
    "subtotal": 326.21,
    "tax": 0.00,
    "total": 326.21,
    "currency": "USD",
    "estimate_notes": [
      "Double-sided printing applied",
      "10% volume discount applied",
      "2-day rush fee applied (25% surcharge)"
    ]
  }
}
```

---

## 💰 Pricing Engine Details

### Print Method Decision (Digital vs Offset)

The system automatically selects the optimal print method based on quantity:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DIGITAL PRINTING (Quantity < 500)                                       │
│  ├── Setup Cost: $15 (no plates required)                               │
│  ├── Per-Unit Cost: Higher                                               │
│  ├── Turnaround: Faster (no plate production)                           │
│  └── Best For: Short runs, prototypes, variable data                    │
├─────────────────────────────────────────────────────────────────────────┤
│  OFFSET PRINTING (Quantity ≥ 500)                                        │
│  ├── Setup Cost: $150 (plate production)                                │
│  ├── Per-Unit Cost: 40% lower than digital                              │
│  ├── Turnaround: Longer (plate setup time)                              │
│  └── Best For: High volume, consistent quality, Pantone matching        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Why 500 as threshold?**
Industry standard break-even point where offset setup cost is recouped by lower per-unit cost. This is configurable in `pricing.json`.

### Cost Components

```
TOTAL = Material + Print + Setup + Finishing + Options + Rush - Discount + Margin + Tax

Where:
┌───────────────┬────────────────────────────────────────────────────────┐
│ Material      │ Paper/substrate cost × quantity                        │
│ Print         │ Ink/press cost × quantity × method_multiplier          │
│ Setup         │ Fixed cost (Digital: $15, Offset: $150)                │
│ Finishing     │ Post-press costs × quantity                            │
│ Options       │ Flat fee OR per-unit (rounded corners, foil, etc.)     │
│ Rush          │ 25-100% surcharge based on turnaround                  │
│ Discount      │ 5-25% based on quantity tiers                          │
│ Margin        │ 30% business margin                                    │
│ Tax           │ Configurable per jurisdiction                          │
└───────────────┴────────────────────────────────────────────────────────┘
```

### Quantity Discounts

| Quantity | Discount | Rationale |
|----------|----------|-----------|
| 250+ | 5% | Encourages slightly larger orders |
| 500+ | 10% | Offset threshold, economies of scale |
| 1,000+ | 15% | Standard volume discount |
| 5,000+ | 20% | Bulk order |
| 10,000+ | 25% | Maximum standard discount |

---

## ⚡ n8n Integration

### Webhook Payload Structure

The backend sends a fire-and-forget POST to the configured n8n webhook:

```json
{
  "request_id": "uuid",
  "specs": { /* extracted specifications */ },
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": ["..."],
    "missing_fields": []
  },
  "estimate": { /* pricing breakdown */ },
  "source": "text"
}
```

### Workflow Routing Logic

See `n8n_examples/print_order_workflow.json` for complete importable workflow.

```
┌─────────────────────────────────────────────────────────────────┐
│                     INCOMING ORDER                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   Has Blocking Errors?  │
              └─────────────────────────┘
                    │           │
                   YES          NO
                    │           │
                    ▼           ▼
           ┌──────────────┐  ┌─────────────────┐
           │  CSR REVIEW  │  │  Has Warnings?  │
           │    QUEUE     │  └─────────────────┘
           └──────────────┘       │         │
                  │              YES        NO
                  │               │         │
                  ▼               ▼         ▼
           ┌──────────────┐ ┌──────────┐ ┌──────────────┐
           │ CSR Decision │ │ Customer │ │ AUTO-APPROVE │
           │  (Approve/   │ │ Confirm  │ └──────────────┘
           │   Reject)    │ └──────────┘        │
           └──────────────┘      │              │
                  │              │              │
                  └──────────────┴──────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  CREATE PRODUCTION     │
                    │  ORDER IN MIS/ERP      │
                    └────────────────────────┘
```

---

## 🎭 Demo Mode vs Production Mode

### Frontend Demo Mode

The React frontend includes a Demo Mode for assessment/preview purposes:

| Aspect | Demo Mode | Production Mode |
|--------|-----------|-----------------|
| Backend Required | No | Yes |
| Data Source | Mock service | Real API |
| Pricing | Simulated (realistic) | Actual calculation |
| LLM Calls | None | Real extraction |
| Visual Indicator | Amber badge | Connection status |

**Auto-activation**: Demo Mode enables automatically if `/health` endpoint is unreachable.

### Code Separation

```typescript
// In PrintEstimator/index.tsx
if (demoMode) {
  // ============================================
  // DEMO MODE: Use mock service
  // This provides realistic responses without backend
  // ============================================
  data = generateMockResponse(request);
} else {
  // ============================================
  // PRODUCTION MODE: Call real FastAPI backend
  // Requires Docker backend to be running
  // ============================================
  const response = await fetch(`${apiUrl}/intake`, ...);
}
```

**Why This Matters:**
- Assessors can evaluate the frontend without running Docker
- Demo responses match production schema exactly
- Clear visual indicator prevents confusion
- Production code path is unmodified and tested separately

---

## 🔬 Edge Cases & How They're Handled

### Extraction Edge Cases

| Input | Handling | Result |
|-------|----------|--------|
| "five hundred cards" | LLM normalizes to 500 | `quantity: 500` |
| "BC x 1000 matte 2-sided" | LLM expands abbreviations | Full specs extracted |
| "i need some flyers" | Quantity missing | Validation error flagged |
| "business cards, rush!!!" | LLM extracts urgency | `is_rush: true` |
| Empty input | Extraction fails | `status: "extraction_failed"` |
| Mixed languages | LLM attempts extraction | May produce partial results |

### Validation Edge Cases

| Scenario | Classification | Workflow Route |
|----------|----------------|----------------|
| Quantity: 10 (business cards) | ERROR: Below minimum (100) | CSR Review |
| Size: "10x10" (business cards) | WARNING: Non-standard | Customer Confirm |
| Turnaround: 1 day + foil stamp | ERROR: Incompatible combo | CSR Review |
| DPI: 150 | ERROR: Too low for print | CSR Review |
| DPI: 250 | WARNING: Below recommended | Customer Confirm |
| No paper stock specified | MISSING: Default applied | Auto-Approve |

### Pricing Edge Cases

| Scenario | Handling |
|----------|----------|
| Quantity: 499 | Digital printing (below 500 threshold) |
| Quantity: 500 | Offset printing (at threshold) |
| Quantity: 1 (poster) | Minimum price enforced ($15) |
| Unknown option | Logged, not priced, noted in response |
| Same-day rush | 100% surcharge applied |
| 10,000+ quantity | 25% discount (max tier) |

---

## ⚠️ Known Limitations & TODOs

### Current State (Demo/Assessment)

| Feature | Status | Notes |
|---------|--------|-------|
| Text extraction | ✅ Implemented | Works with OpenAI-compatible APIs |
| PDF processing | 📋 Metadata only | Actual parsing needs OCR integration |
| Image processing | 📋 Metadata only | Needs Tesseract/AWS Textract |
| Pricing engine | ✅ Complete | All components implemented |
| Validation | ✅ Complete | 3-tier feedback system |
| n8n integration | ✅ Webhook | Fire-and-forget |
| Authentication | ❌ None | Needs JWT/API key |
| Rate limiting | ❌ None | Needs Redis |
| Database | ❌ None | Orders not persisted |
| Caching | ❌ None | LLM responses not cached |

### Production Requirements

```python
# TODO markers throughout codebase indicate:
# - Where authentication should be added (routers/intake.py)
# - Database integration points (services/pricing.py)
# - Caching opportunities (services/llm_extractor.py)
# - Monitoring hooks (main.py)
# - PDF/Image parsing integration (services/llm_extractor.py)
```

### What Would Change for Production

1. **Authentication**: JWT tokens or API keys for rate limiting and attribution
2. **Database**: PostgreSQL for order persistence, pricing history, customer records
3. **Caching**: Redis for LLM response caching (same input → same extraction)
4. **OCR Integration**: AWS Textract or Google Vision for PDF/image parsing
5. **Monitoring**: Prometheus metrics, structured logging, error tracking
6. **Queue**: Celery/RabbitMQ for async processing at scale
7. **Testing**: Integration tests, load tests, LLM response mocking

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_pricing.py -v
```

### Test Coverage

- `test_pricing.py`: Pricing engine calculations, discounts, methods, edge cases
- `test_intake.py`: Endpoint validation, response formats, error handling

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI or compatible API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | Custom LLM endpoint |
| `OPENAI_MODEL` | No | `gpt-3.5-turbo` | Model for extraction |
| `N8N_WEBHOOK_URL` | No | - | n8n workflow webhook |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `PRICING_CONFIG_PATH` | No | `data/pricing.json` | Pricing config location |

### Pricing Configuration

Edit `app/data/pricing.json` to customize:
- Product base rates (material, print, finishing per unit)
- Digital/offset threshold (default: 500)
- Option pricing (flat vs per-unit)
- Quantity discount tiers
- Rush surcharges (same-day, next-day, 2-day)
- Margin percentage (default: 30%)
- Tax rate (default: 0%, configure per jurisdiction)

---

## 📄 License

MIT

---

## 👤 Author Notes

This project was built for technical assessment with these priorities:

1. **Clarity over cleverness**: Every design decision is documented
2. **Honest limitations**: What's stubbed vs. implemented is explicit
3. **Assessment-ready**: Can be explained in 5-10 minute walkthrough
4. **Production-aware**: TODOs indicate real-world requirements
5. **Separation of concerns**: AI for ambiguity, rules for consistency

### Video Walkthrough Outline (5-10 min)

1. **Architecture Overview** (1 min): Show the diagram, explain the flow
2. **LLM Extraction Demo** (2 min): Submit text, show extracted specs
3. **Pricing Engine** (2 min): Walk through `pricing.py`, show determinism
4. **Validation** (1 min): Explain three-tier system, show workflow routing
5. **Demo Mode** (1 min): Toggle demo mode, show mock responses
6. **n8n Integration** (1 min): Show workflow JSON, explain routing
7. **Limitations & Next Steps** (1 min): Be honest about TODOs

Questions? The code comments explain the reasoning.
