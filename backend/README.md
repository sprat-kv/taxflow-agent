# Tax Processing Backend

AI-powered tax return preparation backend built with FastAPI, LangGraph, and Azure Document Intelligence. Automates document extraction, data aggregation, tax calculation, and Form 1040 generation.

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Environment Setup](#environment-setup)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Agent Workflow](#agent-workflow)
- [Testing](#testing)
- [Features](#features)
- [Development Notes](#development-notes)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Frontend)                        │
└────────────────────────────┬────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Layer (app/api/)                         │   │
│  │  • Upload Sessions  • Document Extraction                │   │
│  │  • Tax Calculation  • Workflow Processing                │   │
│  │  • Form 1040 Generation                                   │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                 │
│  ┌──────────────▼───────────────────────────────────────────┐   │
│  │          Service Layer (app/services/)                   │   │
│  │  • DocumentService      • TaxService                      │   │
│  │  • TaxAggregator        • Form1040Service                 │   │
│  │  • SessionService       • WorkflowStateService            │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                 │
│  ┌──────────────▼───────────────────────────────────────────┐   │
│  │         Agent Layer (app/agent/)                          │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │         LangGraph State Machine                     │  │   │
│  │  │  Aggregate → Calculate → Validate                   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  • graph.py    • nodes.py    • state.py    • llm.py      │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                 │
└─────────────────┼─────────────────────────────────────────────────┘
                  │
      ┌───────────┼───────────┬──────────────┬──────────────┐
      │           │           │              │              │
      ▼           ▼           ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ SQLite   │ │  Azure   │ │  OpenAI  │ │  File    │ │  PDF     │
│ Database │ │ Document │ │   LLM    │ │ Storage  │ │ Generator│
│          │ │Intelligence│ │          │ │          │ │          │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Data Flow

1. **Upload**: Client uploads tax documents (W-2, 1099-NEC, 1099-INT) → stored in `storage/uploads/`.
2. **Extract**: Azure Document Intelligence extracts structured data → saved to `ExtractionResult`.
3. **Aggregate**: Service layer aggregates financial data from all documents.
4. **Process**: LangGraph agent orchestrates workflow (check missing info → calculate → validate).
5. **Calculate**: Tax rules engine computes tax liability using 2024 IRS brackets.
6. **Generate**: Form 1040 PDF filled with calculated values → saved to `storage/reports/`.

### End-to-End Flow: Upload → Parse → Calculate → Generate

1. **Upload**
   - Client calls `POST /api/sessions` with one or more PDFs (W-2, 1099-INT, 1099-NEC).
   - `SessionService` creates an `UploadSession`, saves files under `storage/uploads/{session_id}/`, and creates `Document` rows.

2. **Parse (Extract + Normalize)**
   - Client (or backend) calls `POST /api/documents/{document_id}/extract` for each uploaded document.
   - `DocumentService` loads the PDF file and passes bytes to `DocumentIntelligenceService`, which calls Azure Document Intelligence `prebuilt-tax.us`.
   - The raw Azure result is normalized in `extraction.py`:
     - Document type is normalized (e.g., `tax.us.1099INT.2022` → `tax.us.1099INT`).
     - If Azure returns `other`, the type is inferred from the presence of key fields (W-2 vs 1099-INT vs 1099-NEC).
     - Fields are mapped into typed models: `W2Data`, `NEC1099Data`, `INT1099Data`.
   - A corresponding `ExtractionResult` row is persisted with `document_type` and `structured_data` (JSON).

3. **Calculate (Aggregate → Rules Engine)**
   - Client calls either:
     - `POST /api/tax/calculate/{session_id}` for a direct calculation, or
     - `POST /api/sessions/{session_id}/process` to run the full LangGraph agent (recommended).
   - `TaxAggregator` (`tax_aggregator.py`) reads all `ExtractionResult` rows for the session and:
     - Sums wages and withholding from W‑2s.
     - Sums nonemployee compensation and withholding from 1099‑NECs.
     - Sums interest income and withholding from 1099‑INTs.
   - `TaxService` (`tax_service.py`) converts the aggregated numbers into a `TaxInput` and calls `tax_rules.py`:
     - `get_standard_deduction` selects the 2024 standard deduction based on filing status.
     - `calculate_taxable_income` computes taxable income from gross income minus deduction (minimum 0).
     - `calculate_tax_liability` applies the 2024 progressive tax brackets.
     - `calculate_refund_or_owed` compares liability vs. total withholding and returns both an amount and a `"refund" | "owed" | "even"` status.

4. **Generate Form (1040 PDF)**
   - After a successful calculation, client calls `POST /api/reports/{session_id}/1040`.
   - `Form1040Service` (`form_1040_service.py`):
     - Loads the persisted LangGraph `WorkflowState` for the session, which contains:
       - `personal_info` (name, SSN, address, occupation, digital_assets answer).
       - `aggregated_data` (wages, interest, NEC income, withholding).
       - `calculation_result` (gross income, deductions, tax, refund/owed).
     - Maps these into the official 2024 Form 1040 fields using `1040_field_mapping_template.json`.
     - Fills only text fields (checkboxes are intentionally skipped for now).
     - Writes a filled PDF to `storage/reports/{session_id}/Form_1040.pdf` and returns it as a download.

5. **Validation Against Filing Instructions**
   - The 1040 flow is aligned with `1040_FILING_INSTRUCTIONS.md`:
     - **Universally mandatory** values (filer name, SSN, home address, filing status, digital assets answer, occupation) are enforced by the LangGraph `aggregator_node`. If any are missing, the workflow returns `waiting_for_user` with `missing_fields`.
     - **Conditionally mandatory** lines (e.g., Line 1a, 2b, 8, 9, 25a, 34, 37) are populated based on the extracted and aggregated data. The tax math ensures that derived values such as Line 9 (Total Income), Line 11 (AGI), Line 15 (Taxable Income), Line 24 (Total Tax), and refund/owed lines are internally consistent.
     - Only the 2024 tax year is supported. If documents or user input reference a different year, the agent returns a warning and does not proceed with calculation.

## Tech Stack

### Core Framework
- **FastAPI** (0.121.2+) - Modern Python web framework with automatic API documentation
- **Uvicorn** - ASGI server for production deployment
- **Pydantic** (2.12.4+) - Data validation and settings management

### AI & Orchestration
- **LangChain** (1.0.8+) - LLM integration framework
- **LangGraph** (1.0.3+) - State machine for multi-step agent workflows
- **LangChain OpenAI** (1.0.3+) - OpenAI GPT model integration

### Document Processing
- **Azure Document Intelligence** - Prebuilt tax document model (`prebuilt-tax.us`)
  - Supports W-2, 1099-NEC, 1099-INT extraction
- **PyPDF** (6.3.0+) - PDF manipulation for Form 1040 generation
- **pdfplumber** (0.11.8+) - PDF text extraction utilities

### Database
- **SQLAlchemy** (2.0.44+) - ORM for database operations
- **SQLite** - Development database (configurable for production)

### Development Tools
- **uv** - Fast Python package manager and project manager
- **python-dotenv** - Environment variable management

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   │
│   ├── api/                       # API Layer
│   │   ├── __init__.py
│   │   └── endpoints.py          # REST API route handlers
│   │
│   ├── agent/                     # AI Orchestration
│   │   ├── __init__.py
│   │   ├── graph.py              # LangGraph state machine definition
│   │   ├── nodes.py              # Workflow nodes (aggregate, calculate, validate)
│   │   ├── state.py              # TypedDict state definition
│   │   └── llm.py                # LLM client and prompts
│   │
│   ├── core/                      # Configuration
│   │   ├── __init__.py
│   │   └── config.py              # Settings and environment variables
│   │
│   ├── db/                        # Database
│   │   ├── __init__.py
│   │   ├── base.py               # SQLAlchemy Base
│   │   └── session.py             # Database session management
│   │
│   ├── models/                    # Data Layer
│   │   ├── __init__.py
│   │   └── models.py              # SQLAlchemy ORM models
│   │
│   ├── schemas/                   # Validation Layer
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic request/response models
│   │
│   └── services/                  # Business Logic Layer
│       ├── __init__.py
│       ├── document_intelligence.py  # Azure Document Intelligence wrapper
│       ├── document_service.py       # Document extraction orchestration
│       ├── extraction.py             # Document parsing utilities
│       ├── form_1040_service.py      # Form 1040 PDF generation
│       ├── session_service.py         # Upload session management
│       ├── tax_aggregator.py          # Financial data aggregation
│       ├── tax_rules.py              # 2024 IRS tax calculation rules
│       ├── tax_service.py            # Tax calculation orchestration
│       └── workflow_state_service.py  # Workflow state persistence
│
├── scripts/                       # Utility scripts
│   ├── test_tax_calculations.py   # Unit tests for tax math
│   ├── test_workflow_e2e.py       # End-to-end workflow tests
│   ├── test_extraction_api.py     # Extraction testing
│   └── ...                        # Other utility scripts
│
├── storage/                       # File storage
│   ├── forms/                     # PDF templates (f1040.pdf)
│   ├── uploads/                   # Uploaded tax documents
│   └── reports/                   # Generated Form 1040 PDFs
│
├── tests/                         # Unit tests
│   └── test_tax_rules.py
│
├── pyproject.toml                 # Project dependencies (uv)
├── uv.lock                        # Dependency lock file
├── tax_app.db                     # SQLite database (generated)
└── README.md                      # This file
```

## Core Components

### API Endpoints (`app/api/endpoints.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | POST | Create upload session and upload PDF files |
| `/api/sessions/{session_id}` | GET | Get upload session details |
| `/api/documents/{document_id}/extract` | POST | Extract structured data from document |
| `/api/tax/calculate/{session_id}` | POST | Direct tax calculation (bypasses agent) |
| `/api/sessions/{session_id}/process` | POST | Process session through LangGraph workflow |
| `/api/reports/{session_id}/1040` | POST | Generate filled Form 1040 PDF |
| `/api/sessions/{session_id}` | DELETE | Delete session and all associated data |

### Agent Workflow (`app/agent/`)

**LangGraph State Machine** with three nodes:

1. **Aggregator Node** (`aggregator_node`)
   - Aggregates financial data from all extraction results
   - Validates mandatory fields (name, SSN, address, filing status, tax year)
   - Checks for missing information
   - Returns `waiting_for_user` status if data incomplete

2. **Calculator Node** (`calculator_node`)
   - Computes tax liability using 2024 IRS tax brackets
   - Calculates standard deduction based on filing status
   - Determines refund or amount owed

3. **Validator Node** (`validator_node`)
   - LLM-powered validation of calculation results
   - Identifies anomalies or missing data
   - Generates warnings for review

## 🤖 Why an AI Agent? (vs. Simple Script)

While a simple script works for perfect data, real-world tax processing is messy. The AI Agent (built with LangGraph) provides **reasoning, adaptability, and semantic validation** that a linear script cannot.

### Comparison: Linear Script vs. AI Agent

| Feature | 📜 Linear Script (Happy Path) | 🧠 AI Agent (Real World) |
| :--- | :--- | :--- |
| **Missing Data** | **Crashes.** "Error: 'filing_status' is None." | **Pauses & Asks.** "I see W-2 income, but I need your Filing Status. Are you Single or Married?" |
| **Conflicting Info** | **Blindly Processes.** Uses whatever it finds first. | **Reasons.** "The W-2 says 'John Doe' but the 1099 says 'Jon Doe'. Is this the same person?" |
| **Validation** | **Syntax Only.** Checks if `tax > 0`. | **Semantic Audit.** "Wait, $100k income with $0 tax is suspicious. Flagging for review." |

### Agent Workflow Scenarios

#### Scenario A: The "Happy Path" (Automated)
1. **User** uploads W-2.
2. **Agent** extracts data → Validates mandatory fields (All present).
3. **Agent** calculates tax → Checks logic (Pass).
4. **Agent** generates 1040 PDF.
5. **Result:** Success (No user interaction needed).

#### Scenario B: The "Human-in-the-Loop" (Intervention)
1. **User** uploads 1099-NEC (Freelance).
2. **Agent** extracts data → **Detects Missing Info**: "I need your Filing Status and Home Address."
3. **Agent** pauses (`status: waiting_for_user`) and requests specific fields.
4. **User** provides "Single" and "123 Main St".
5. **Agent** resumes → Aggregates data → Calculates Tax.
6. **Result:** Success (Collaborative completion).

**State Definition** (`TaxState`):
```python
{
    "session_id": str,
    "filing_status": Optional[str],
    "tax_year": Optional[str],
    "personal_info": Dict[str, Any],
    "user_inputs": Dict[str, Any],
    "aggregated_data": Optional[Dict[str, float]],
    "calculation_result": Optional[Dict[str, Any]],
    "validation_result": Optional[str],
    "missing_fields": List[str],
    "warnings": List[str],
    "status": str
}
```

### Document Processing & Parsing (`app/services/`)

- **`document_intelligence.py`**
  - `DocumentIntelligenceService` is a thin wrapper around Azure's `DocumentIntelligenceClient`.
  - Uses the `prebuilt-tax.us` model, which:
    - Classifies the document type (W‑2, 1099‑NEC, 1099‑INT, or `other`).
    - Returns a structured graph of fields and values for each recognized form.
- **`extraction.py`**
  - Centralizes the mapping logic from Azure's generic field dictionary into our strongly-typed Pydantic models:
    - `map_w2_fields` → `W2Data`
    - `map_1099nec_fields` → `NEC1099Data`
    - `map_1099int_fields` → `INT1099Data`
  - Normalizes document types and handles edge cases (like `"other"` classifications) by inspecting the presence of key fields (e.g., W‑2 wage boxes vs. 1099 boxes).
  - Returns a normalized `document_type` string and a typed `W2Data`/`NEC1099Data`/`INT1099Data` instance for storage.
- **`document_service.py`**
  - Fetches the `Document` row, validates that the PDF exists on disk, calls `process_document`, and then persists the resulting `ExtractionResult` with `structured_data` as JSON.

### Tax Logic Modules (`app/services/tax_*.py`)

- **`tax_aggregator.py`**
  - Implements *pure aggregation* over `ExtractionResult` rows:
    - `aggregate_w2_data` → total W‑2 wages and withholding.
    - `aggregate_1099nec_data` → total 1099‑NEC income and withholding.
    - `aggregate_1099int_data` → total 1099‑INT interest and withholding.
  - `aggregate_tax_data` combines these into a single `TaxInput` model, which becomes the source of truth for the rules engine.
- **`tax_rules.py`**
  - Encodes all **deterministic** 2024 US federal tax rules:
    - `STANDARD_DEDUCTIONS` per filing status, matching 1040 instructions.
    - `TAX_BRACKETS` per filing status, expressed as `(rate, upper_limit)` tuples and applied with `Decimal` precision.
    - `get_standard_deduction`, `calculate_taxable_income`, `calculate_tax_liability`, `calculate_refund_or_owed`.
  - Designed to be:
    - Pure and side-effect free.
    - Easy to unit-test independently from the rest of the system.
- **`tax_service.py`**
  - Orchestrates aggregation and rules:
    - Calls `aggregate_tax_data` to produce a `TaxInput`.
    - Calls the functions in `tax_rules.py` and returns a `TaxCalculationResult` Pydantic model ready for serialization and persistence.

### Form 1040 Generation (`app/services/form_1040_service.py`)

- Consumes:
  - The persisted `WorkflowState` (which contains personal info, aggregated data, and calculation result).
  - The official `f1040.pdf` template under `storage/forms/`.
  - The mapping defined in `1040_field_mapping_template.json`.
- Uses `pypdf` to:
  - Clone the AcroForm structure from the template.
  - Fill text fields for:
    - Personal identification (name, SSN, address).
    - Income (Lines 1a, 1z, 2b, 8, 9).
    - Deductions and taxable income (Lines 11–15).
    - Tax, payments, and refund/owed (Lines 16, 24, 25a, 33, 34, 37).
    - Occupation and contact details on Page 2.
- Currently, checkbox fields (filing status, digital assets, etc.) are intentionally **not** filled to keep PDF logic simple and robust.

### Models (`app/models/models.py`)

- **UploadSession**: Session tracking for document uploads
- **Document**: Individual uploaded PDF files
- **ExtractionResult**: Structured data extracted from documents
- **TaxResult**: Calculated tax results for a session
- **WorkflowState**: Persistent state for LangGraph workflow
- **Report**: Generated PDF reports (Form 1040)

## Environment Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Azure Document Intelligence account
- OpenAI API key

### Installation

1. **Clone repository and navigate to backend**:
```bash
cd backend
```

2. **Install dependencies with uv**:
```bash
uv sync
```

3. **Create `.env` file**:
```bash
# Database
DATABASE_URL=sqlite:///./tax_app.db

# Azure Document Intelligence
DOCUMENTINTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
DOCUMENTINTELLIGENCE_API_KEY=your-api-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Environment
ENV=dev
PROJECT_NAME=Tax Processing Agent
```

4. **Initialize database** (tables auto-created on first run):
```bash
uv run python -c "from app.main import app; from app.db.session import Base, engine; Base.metadata.create_all(bind=engine)"
```

5. **Run development server**:

**Local access only (default):**
```bash
uv run uvicorn app.main:app --reload
```

**Access from local network:**
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Find your local IP address:**
- **Windows**: Run `ipconfig` and look for "IPv4 Address" under your active network adapter
- **Mac/Linux**: Run `ifconfig` or `ip addr` and look for your network interface IP

**Access from other devices:**
- Replace `localhost` with your machine's IP address (e.g., `http://192.168.1.100:8000`)
- Make sure your firewall allows incoming connections on port 8000

Server runs on:
- Local: `http://localhost:8000`
- Network: `http://<your-ip-address>:8000`

### API Documentation

**📖 Complete API Reference:** See [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for:
- Detailed request/response schemas for all endpoints
- Complete workflow examples
- Frontend integration guidelines
- Advisor feedback usage instructions

**Interactive Documentation:**
- Swagger UI: `http://localhost:8000/docs` or `http://<your-ip>:8000/docs`
- ReDoc: `http://localhost:8000/redoc` or `http://<your-ip>:8000/redoc`

**Key API Features:**
- **Agent Activity Logs:** The `/sessions/{id}/process` endpoint returns a `logs` array with execution timeline
- **Advisor Feedback:** ⭐ NEW - Personalized financial advice in `advisor_feedback` field
- **Current Step Tracking:** Real-time workflow progress via `current_step` field

## Database Schema

### Tables

**upload_sessions**
- `id` (String, PK) - UUID session identifier
- `created_at` (DateTime) - Session creation timestamp
- `status` (String) - Session status (pending, processing, complete)

**documents**
- `id` (String, PK) - UUID document identifier
- `session_id` (String, FK) - Reference to upload_sessions
- `filename` (String) - Original filename
- `file_path` (String) - Storage path on disk
- `file_size` (Integer) - File size in bytes
- `upload_timestamp` (DateTime) - Upload timestamp
- `status` (String) - Document status

**extraction_results**
- `id` (String, PK) - UUID extraction identifier
- `document_id` (String, FK, Unique) - Reference to documents
- `document_type` (String) - Type (tax.us.w2, tax.us.1099NEC, tax.us.1099INT)
- `structured_data` (JSON) - Extracted data as JSON
- `warnings` (Text) - Extraction warnings
- `created_at` (DateTime) - Extraction timestamp

**tax_results**
- `id` (String, PK) - UUID result identifier
- `session_id` (String, FK, Unique) - Reference to upload_sessions
- `filing_status` (String) - Filing status used
- `gross_income` (JSON) - Gross income breakdown
- `standard_deduction` (JSON) - Deduction details
- `taxable_income` (JSON) - Taxable income details
- `tax_liability` (JSON) - Tax liability breakdown
- `total_withholding` (JSON) - Withholding totals
- `refund_or_owed` (JSON) - Final refund/owed amount
- `status` (String) - Calculation status
- `created_at` (DateTime) - Calculation timestamp

**workflow_states**
- `id` (String, PK) - UUID state identifier
- `session_id` (String, FK, Unique) - Reference to upload_sessions
- `state_data` (JSON) - Complete LangGraph state
- `status` (String) - Workflow status
- `updated_at` (DateTime) - Last update timestamp

**reports**
- `id` (String, PK) - UUID report identifier
- `session_id` (String, FK) - Reference to upload_sessions
- `report_type` (String) - Report type (e.g., "form_1040")
- `file_path` (String) - PDF file path
- `created_at` (DateTime) - Generation timestamp

### Relationships

```
UploadSession (1) ──< (N) Document
Document (1) ──< (1) ExtractionResult
UploadSession (1) ──< (1) TaxResult
UploadSession (1) ──< (1) WorkflowState
UploadSession (1) ──< (N) Report
```

## Testing

### Unit Tests

Test tax calculation logic independently:
```bash
cd backend
uv run python scripts/test_tax_calculations.py
```

Tests cover:
- All filing statuses (single, married_filing_jointly, head_of_household)
- W-2 only scenarios
- W-2 + 1099-NEC scenarios
- W-2 + 1099-INT scenarios
- Refund and tax owed cases

### End-to-End Tests

Test complete workflow (requires running API server):
```bash
# Terminal 1: Start server
uv run uvicorn app.main:app --reload

# Terminal 2: Run E2E tests
cd backend
uv run python scripts/test_workflow_e2e.py
```

Tests cover:
- Document upload and extraction
- Agent workflow with missing data handling
- Tax calculation and validation
- User input override functionality

### Test Scripts

See `scripts/README.md` for detailed testing documentation.

## Features

### ✅ Implemented

- **Multi-Document Upload**: Upload multiple tax documents (W-2, 1099-NEC, 1099-INT) in a single session
- **Azure Document Intelligence**: Automatic extraction of structured data from tax forms
- **Data Aggregation**: Combines income and withholding from all documents
- **Tax Calculation**: 2024 US Federal tax calculation with progressive brackets
- **LangGraph Agent Workflow**: Multi-step processing with state management
- **Missing Data Detection**: Agent identifies and requests missing mandatory fields
- **Form 1040 Generation**: Fills official IRS Form 1040 PDF with calculated values
- **Workflow State Persistence**: Resume processing across API calls
- **LLM Validation**: AI-powered validation of calculation results

### 📋 Supported Document Types

- **W-2**: Wage and tax statements
- **1099-NEC**: Nonemployee compensation
- **1099-INT**: Interest income

### 📋 Supported Filing Statuses

- Single
- Married Filing Jointly
- Head of Household

### 📋 Tax Year Support

- **2024** (current implementation)

## Development Notes

### Architecture Principles

- **Layered Architecture**: API → Service → Data layers with clear separation
- **Service Layer Pattern**: Business logic isolated in services, reusable across endpoints
- **State Machine**: LangGraph provides structured workflow with conditional routing
- **Type Safety**: Pydantic schemas for request/response validation
- **Database Abstraction**: SQLAlchemy ORM for database operations

### Key Design Decisions

1. **LangGraph for Workflow**: Enables complex multi-step processing with state persistence
2. **Azure Document Intelligence**: Prebuilt tax model reduces custom extraction logic
3. **SQLite for Development**: Easy setup, can be swapped for PostgreSQL in production
4. **Form 1040 Field Mapping**: Direct PDF field manipulation using PyPDF for accuracy

### Environment Variables

Required environment variables (see `.env` example above):
- `DOCUMENTINTELLIGENCE_ENDPOINT`: Azure resource endpoint
- `DOCUMENTINTELLIGENCE_API_KEY`: Azure API key
- `OPENAI_API_KEY`: OpenAI API key for LLM validation
- `OPENAI_MODEL`: Model name (default: `gpt-4o-mini`)
- `DATABASE_URL`: Database connection string

### File Storage

- **Uploads**: `storage/uploads/{session_id}/` - Original uploaded PDFs
- **Forms**: `storage/forms/` - PDF templates (f1040.pdf)
- **Reports**: `storage/reports/{session_id}/` - Generated Form 1040 PDFs

### Production Considerations

1. **Database**: Replace SQLite with PostgreSQL for production
2. **File Storage**: Consider cloud storage (Azure Blob, S3) for scalability
3. **Authentication**: Add API key or OAuth authentication
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Error Handling**: Enhanced error logging and monitoring
6. **Migrations**: Use Alembic for database migrations
7. **Caching**: Consider Redis for workflow state caching
8. **Background Jobs**: Use Celery or similar for long-running tasks

### Security Features

**Current Implementation:**

1. **File Validation:**
   - Magic byte verification (`%PDF` header check) to ensure uploaded files are genuine PDFs
   - Content-type validation to reject non-PDF files
   - File size limit of 10MB per upload to prevent DoS attacks

2. **Data Cleanup:**
   - `DELETE /api/sessions/{session_id}` endpoint to wipe all session data
   - Removes uploaded files, generated reports, and database records
   - Enables "temporary processing" workflow where users can delete sensitive data after downloading Form 1040

3. **Input Validation:**
   - Pydantic schema validation for all API inputs
   - Filename sanitization (UUID-based naming) to prevent directory traversal attacks

**Future Improvements (Production Roadmap):**

- **Encryption at Rest:** Column-level encryption for SSN, names, and addresses in the database
- **Encryption in Transit:** HTTPS/TLS enforcement for all API communication
- **Authentication & Authorization:** OAuth2/JWT to restrict session access to authenticated users only
- **Audit Logging:** Immutable logs tracking all access to sensitive tax data
- **Ephemeral Storage:** Memory-only processing with automatic file deletion after 24 hours
- **E-Filing Integration:** IRS MeF (Modernized e-File) compliance for secure electronic filing

### Known Limitations

- Only supports 2024 tax year
- Standard deduction only (no itemized deductions)
- Limited to W-2, 1099-NEC, and 1099-INT income sources
- No support for tax credits beyond basic calculations
- Form 1040 generation uses field mapping that may need updates for form changes
- Sensitive data stored in plain text (encryption planned for production)

### Contributing

1. Follow the layered architecture pattern
2. Add Pydantic schemas for new endpoints
3. Keep business logic in services, not API endpoints
4. Write tests for new tax calculation logic
5. Update this README for significant changes

---

**Version**: 0.1.0  
**License**: See project root LICENSE file

