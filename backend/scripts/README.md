# Test Scripts Documentation

This directory contains test scripts for the tax processing workflow.

## Test Scripts

### 1. `test_tax_calculations.py` - Unit Tests (No API Required)

Tests the tax calculation logic independently without requiring the API server.

**Usage:**
```bash
cd backend
uv run python scripts/test_tax_calculations.py
```

**What it tests:**
- Test Case A: Simple Single filer with refund ($984)
- Test Case B: Freelancer owing tax ($540)
- W-2 only income scenario
- W-2 + 1099-NEC scenario
- W-2 + small interest (< $10) scenario
- All filing statuses (single, married_filing_jointly, head_of_household)

**Requirements:**
- No API server needed
- No database needed
- Pure unit tests for tax math

---

### 2. `test_workflow_e2e.py` - End-to-End Workflow Tests

Tests the complete workflow: Upload → Extract → Agent → Calculate

**Usage:**
```bash
# Terminal 1: Start the API server
cd backend
uvicorn app.main:app --reload

# Terminal 2: Run the tests
cd backend
uv run python scripts/test_workflow_e2e.py
```

**What it tests:**
- **Scenario 1**: W-2 only income
  - Uploads W-2 PDF
  - Extracts data
  - Tests missing filing status handling
  - Completes calculation with filing status
  
- **Scenario 2**: W-2 + 1099-NEC
  - Uploads both PDFs
  - Extracts both documents
  - Aggregates income from both sources
  - Calculates tax on combined income

- **Scenario 3**: W-2 + Small Interest
  - Uploads W-2 and 1099-INT
  - Verifies small interest amounts are included
  - Tests that no minimum threshold exists

- **Missing Info Handling**:
  - Tests agent asking for missing filing status
  - Tests user providing inputs
  - Tests user input override functionality

**Requirements:**
- API server must be running on `http://localhost:8000`
- Sample PDFs in `sample_docs/` directory:
  - `w2.pdf` - Sample W-2 form
  - `1099-nec.pdf` - Sample 1099-NEC form
  - `1099-int.pdf` - Sample 1099-INT form
- Database must be initialized (tables created)

**Sample Documents:**
Place your test PDFs in the `sample_docs/` directory at the project root:
```
tax-processing/
├── sample_docs/
│   ├── w2.pdf
│   ├── 1099-nec.pdf
│   └── 1099-int.pdf
└── backend/
    └── scripts/
        └── test_workflow_e2e.py
```

---

### 3. `test_extraction_api.py` - Extraction Testing

Tests document extraction only (from Phase 3).

**Usage:**
```bash
cd backend
uv run python scripts/test_extraction_api.py
```

**What it tests:**
- Uploads PDFs
- Extracts data using Azure Document Intelligence
- Saves extraction results to `sample_docs/outputs/`

---

## Running All Tests

### Step 1: Unit Tests (No Setup Required)
```bash
cd backend
uv run python scripts/test_tax_calculations.py
```

### Step 2: Start API Server
```bash
cd backend
uvicorn app.main:app --reload
```

### Step 3: End-to-End Tests
```bash
cd backend
uv run python scripts/test_workflow_e2e.py
```

---

## Expected Test Output

### Unit Tests
```
============================================================
  TAX CALCULATION UNIT TESTS
============================================================

============================================================
  TEST CASE A: Simple Single (Refund)
============================================================
   Standard Deduction: $14,600.00
   Taxable Income: $35,400.00
   Tax Liability: $4,016.00
   Result: REFUND $984.00
   ✅ PASS: Refund matches expected value

...

============================================================
  TEST SUMMARY
============================================================
   ✅ PASS: Case A
   ✅ PASS: Case B
   ...
   Total: 6/6 tests passed
```

### End-to-End Tests
```
============================================================
  TAX PROCESSING WORKFLOW - END-TO-END TESTS
============================================================

📁 Using sample documents from: /path/to/sample_docs
✅ API server is running

------------------------------------------------------------
Starting tests...
------------------------------------------------------------

============================================================
  TEST SCENARIO 1: W-2 Only Income
============================================================

============================================================
  Step 1: Upload Documents
============================================================
✅ Session created: abc-123-def-456
   Documents uploaded: 1
   - w2.pdf (ID: doc-123)

============================================================
  Step 2: Extract Document Data
============================================================
   Extracting document doc-123...
   ✅ Extracted: tax.us.w2

============================================================
  Step 3: Process Session (Agent Workflow)
============================================================
   Status: waiting_for_user
   ⚠️  Missing fields: ['filing_status']
   Message: Please provide the following information to continue

   Second call (with filing status):
   Status: complete
   ✅ Calculation complete!
   ...
```

---

## Troubleshooting

### API Server Not Running
```
❌ API server is not running: ...
   Please start the server with: uvicorn app.main:app --reload
```

**Solution:** Start the FastAPI server in a separate terminal.

### Sample Documents Not Found
```
❌ Sample documents directory not found: sample_docs
```

**Solution:** Create `sample_docs/` directory and add test PDFs.

### Database Errors
```
❌ Workflow failed: ...
```

**Solution:** Ensure database tables are created. The app auto-creates tables on startup, but you may need to check database file permissions.

---

## Test Coverage

- ✅ Tax calculation logic (all scenarios)
- ✅ Document upload and storage
- ✅ Document extraction (Azure Document Intelligence)
- ✅ Data aggregation (W-2, 1099-NEC, 1099-INT)
- ✅ Agent workflow (aggregate → calculate → validate)
- ✅ Missing information handling
- ✅ User input override
- ✅ All filing statuses

