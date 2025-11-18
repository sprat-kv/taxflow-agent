# Project Phase Implementation

High-level, phase-wise implementation plan for `marker-tax-agent-1040`.

---

## Phase 1 – Scaffolding & Setup
- Init mono-repo: `backend/`, `frontend/`, shared `README`, `.gitignore`.
- Backend: FastAPI app skeleton, config, db wiring (SQLite + SQLAlchemy), basic models/schemas.
- Frontend: Next.js (App Router) + TypeScript + Tailwind + shadcn/ui.

## Phase 2 – Upload & Storage Pipeline
- Create `UploadSession` and `Document` models.
- Implement `POST /api/sessions` for multi-PDF upload + filing details.
- Save PDFs under `storage/uploads/<session_id>/<doc_id>.pdf` with random IDs.
- Add file type/size validation and minimal logging (no PII).

## Phase 3 – Marker Extraction & Parsing
- Integrate `marker-pdf` and build `run_marker_on_pdf(pdf_path)` helper.
- Design `ParsedDocument`, `W2Data`, `NECData`, `INTData` Pydantic schemas.
- Implement doc type detection (W-2, 1099-NEC, 1099-INT, UNKNOWN).
- Implement extraction functions mapping Marker output → typed tax data.
- Persist `ExtractionResult` (structured_json + warnings) per document.

## Phase 4 – Tax Logic & Aggregation
- Implement 2024 standard deduction + tax bracket constants.
- Build pure functions: `aggregate_income`, `compute_taxable_income`, `compute_tax`, `compute_refund_or_due`.
- Implement `compute_tax_for_session(session_id, filing_status)` using parsed docs.
- Persist `TaxResult` and add basic unit tests for tax math.

## Phase 5 – PDF Reporting
- Design a simple 1040-style summary layout.
- Implement `generate_1040_report(session_id, tax_summary, output_path)` with ReportLab.
- Store report under `storage/reports/<session_id>/<report_id>.pdf` and create `Report` row.
- Add `GET /api/sessions/{session_id}/report` for secured PDF download.

## Phase 6 – Tools & LangGraph Agent
- Define tool input schemas (ParseDocsInput, TaxCalcInput, ReportInput).
- Wrap services as LangChain tools: `parse_documents_tool`, `tax_calc_tool`, `generate_report_tool`.
- Configure LLM + tool-calling prompt for ReAct-style behavior.
- Build LangGraph state + nodes to orchestrate parse → tax → report for a session.
- Expose `POST /api/sessions/{session_id}/process` to run the agent and return summary.

## Phase 7 – Frontend Integration
- Upload page: multi-file upload, filing status, dependents, submit to `/api/sessions`.
- After creation, call `/api/sessions/{session_id}/process` and navigate to result page.
- Result page: fetch session summary, render tax summary, show warnings, expose download button.
- Add loading states and basic error handling using shadcn components.

## Phase 8 – Hardening & Cleanup
- Add structured logging for key events (upload, parse, tax, report) without PII.
- Implement optional cleanup job for old uploads/reports.
- Final pass on security for local dev: env-based secrets, no raw SSNs in DB/logs, safe LLM prompts.
