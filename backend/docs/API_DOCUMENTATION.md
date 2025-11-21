# 📡 Tax Processing API Documentation

## Overview

This API provides an end-to-end tax processing workflow that:
1. Accepts tax document uploads (W-2, 1099-NEC, 1099-INT)
2. Extracts structured data using Azure Document Intelligence
3. Orchestrates tax calculation via a LangGraph AI agent
4. Provides personalized financial advice
5. Generates filled IRS Form 1040 PDFs

**Base URL:** `http://localhost:8000/api` (or your deployed server URL)

---

## 🔄 Complete API Flow

```
1. POST /sessions                    → Create session & upload documents
2. POST /documents/{id}/extract      → Extract data from each document
3. POST /sessions/{id}/process       → Run AI agent workflow (with advisor)
4. POST /reports/{id}/1040           → Generate Form 1040 PDF
5. DELETE /sessions/{id}              → Clean up session data (optional)
```

---

## 📋 API Endpoints

### 1. Create Upload Session

**Endpoint:** `POST /api/sessions`

**Description:** Creates a new tax processing session and uploads one or more PDF tax documents.

**Request:**
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Body:** Form data with `files` field (array of PDF files)
- **Constraints:**
  - Maximum file size: **10MB per file**
  - Only PDF files accepted (validated by magic bytes `%PDF`)
  - Multiple files can be uploaded in a single request

**Request Example:**
```javascript
const formData = new FormData();
formData.append('files', w2File);
formData.append('files', nec1099File);
formData.append('files', int1099File);

const response = await fetch('http://localhost:8000/api/sessions', {
  method: 'POST',
  body: formData
});
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "documents": [
    {
      "id": "doc-uuid-1",
      "filename": "w2.pdf",
      "file_size": 245678,
      "status": "uploaded",
      "upload_timestamp": "2024-05-20T10:30:00Z"
    },
    {
      "id": "doc-uuid-2",
      "filename": "1099_nec.pdf",
      "file_size": 189234,
      "status": "uploaded",
      "upload_timestamp": "2024-05-20T10:30:01Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Session created successfully
- `413 Payload Too Large` - File exceeds 10MB limit
- `500 Internal Server Error` - Server error

---

### 2. Extract Document Data

**Endpoint:** `POST /api/documents/{document_id}/extract`

**Description:** Extracts structured tax data from an uploaded PDF using Azure Document Intelligence.

**Request:**
- **Method:** `POST`
- **Path Parameter:** `document_id` (UUID from upload response)

**Request Example:**
```javascript
const response = await fetch(
  `http://localhost:8000/api/documents/${documentId}/extract`,
  { method: 'POST' }
);
```

**Response:**
```json
{
  "id": "extraction-uuid",
  "document_id": "doc-uuid-1",
  "document_type": "tax.us.w2",
  "structured_data": {
    "tax_year": "2024",
    "employee_ssn": "123-45-6789",
    "employee_name": "John Doe",
    "wages_tips_other_compensation": 75000.00,
    "federal_income_tax_withheld": 8500.00
  },
  "warnings": null,
  "created_at": "2024-05-20T10:30:15Z"
}
```

**Status Codes:**
- `200 OK` - Extraction successful
- `400 Bad Request` - Invalid document or extraction failed
- `500 Internal Server Error` - Server error

**Note:** You must extract **all documents** before proceeding to the workflow step.

---

### 3. Process Session (AI Agent Workflow) ⭐ **NEW: Includes Advisor**

**Endpoint:** `POST /api/sessions/{session_id}/process`

**Description:** Runs the complete LangGraph agent workflow:
1. **Aggregator Node:** Consolidates data from all documents
2. **Calculator Node:** Computes 2024 tax liability
3. **Validator Node:** AI audit of calculation results
4. **Advisor Node:** ⭐ Generates personalized financial advice

**Request:**
- **Method:** `POST`
- **Path Parameter:** `session_id` (UUID from upload response)
- **Content-Type:** `application/json`
- **Body:** `ProcessSessionRequest` object

**Request Schema:**
```typescript
interface ProcessSessionRequest {
  filing_status?: "single" | "married_filing_jointly" | "head_of_household";
  tax_year?: string;  // Currently only "2024" supported
  personal_info?: {
    filer_name?: string;
    filer_ssn?: string;  // Format: "XXX-XX-XXXX"
    home_address?: string;
    occupation?: string;
    digital_assets?: "yes" | "no" | string;
    phone?: string;
  };
  user_inputs?: {
    total_wages?: number;
    total_interest?: number;
    total_nec_income?: number;
    total_withholding?: number;
  };
}
```

**Request Example (Initial - All Mandatory Fields):**
```json
{
  "filing_status": "single",
  "tax_year": "2024",
  "personal_info": {
    "filer_name": "John Doe",
    "filer_ssn": "123-45-6789",
    "home_address": "123 Main St, New York, NY 10001",
    "occupation": "Software Engineer",
    "digital_assets": "no"
  }
}
```

**Request Example (Incremental Update - Missing Fields Only):**
```json
{
  "personal_info": {
    "filer_ssn": "123-45-6789",
    "home_address": "123 Main St, New York, NY 10001"
  }
}
```

**Response Schema:**
```typescript
interface ProcessSessionResponse {
  status: "waiting_for_user" | "complete" | "error";
  message?: string;
  missing_fields?: string[];  // Present if status === "waiting_for_user"
  aggregated_data?: {
    total_wages: number;
    total_interest: number;
    total_nec_income: number;
    total_withholding: number;
  };
  calculation_result?: {
    gross_income: number;
    standard_deduction: number;
    taxable_income: number;
    tax_liability: number;
    total_withholding: number;
    refund_or_owed: number;
    status: "refund" | "owed";
  };
  validation_result?: string;  // AI audit summary
  advisor_feedback?: string;    // ⭐ NEW: Personalized financial advice
  warnings?: string[];
  logs?: AgentLog[];            // ⭐ NEW: Execution timeline
  current_step?: string;        // ⭐ NEW: Current workflow step
}

interface AgentLog {
  timestamp: string;  // ISO 8601 format
  node: "aggregator" | "calculator" | "validator" | "advisor";
  message: string;
  type: "info" | "success" | "warning" | "error";
}
```

**Response Example (Complete - Refund Scenario):**
```json
{
  "status": "complete",
  "message": "Tax calculation completed successfully",
  "aggregated_data": {
    "total_wages": 75000.00,
    "total_interest": 125.50,
    "total_nec_income": 0.00,
    "total_withholding": 8500.00
  },
  "calculation_result": {
    "gross_income": 75125.50,
    "standard_deduction": 14600.00,
    "taxable_income": 60525.50,
    "tax_liability": 8500.00,
    "total_withholding": 8500.00,
    "refund_or_owed": 1250.00,
    "status": "refund"
  },
  "validation_result": "VALID - Calculation appears consistent with 2024 tax brackets.",
  "advisor_feedback": "Great news, John! 🎉 You're estimated to get a refund of $1,250. Since you had freelance income this year, consider setting up a SEP-IRA to lower your taxable income next year while saving for retirement!\n\nPro Tip: Adjust your W-4 withholding to avoid overpaying throughout the year.",
  "warnings": [],
  "logs": [
    {
      "timestamp": "2024-05-20T10:30:27.391676",
      "node": "aggregator",
      "message": "Starting document analysis and data aggregation...",
      "type": "info"
    },
    {
      "timestamp": "2024-05-20T10:30:27.397160",
      "node": "aggregator",
      "message": "Data aggregation complete. Proceeding to calculation.",
      "type": "success"
    },
    {
      "timestamp": "2024-05-20T10:30:27.401160",
      "node": "calculator",
      "message": "Estimated Refund: $1,250.00",
      "type": "success"
    },
    {
      "timestamp": "2024-05-20T10:30:37.291533",
      "node": "validator",
      "message": "AI Audit Passed. Results look consistent.",
      "type": "success"
    },
    {
      "timestamp": "2024-05-20T10:30:52.061182",
      "node": "advisor",
      "message": "Advice generated successfully.",
      "type": "success"
    }
  ],
  "current_step": "advising"
}
```

**Response Example (Waiting for User Input):**
```json
{
  "status": "waiting_for_user",
  "message": "Please provide the following information to continue",
  "missing_fields": ["filing_status", "filer_ssn", "home_address"],
  "warnings": ["Tax year 2023 document detected - using 2024 rules as fallback"],
  "logs": [
    {
      "timestamp": "2024-05-20T10:30:27.391676",
      "node": "aggregator",
      "message": "Missing personal details: filer_ssn, home_address",
      "type": "warning"
    },
    {
      "timestamp": "2024-05-20T10:30:27.397160",
      "node": "aggregator",
      "message": "Pausing workflow. Waiting for 3 mandatory fields.",
      "type": "warning"
    }
  ],
  "current_step": "aggregating"
}
```

**Response Example (Error):**
```json
{
  "status": "error",
  "message": "An error occurred during processing",
  "warnings": ["Tax year 2023 is not supported. This system only supports 2024 tax calculations."],
  "logs": [
    {
      "timestamp": "2024-05-20T10:30:27.391676",
      "node": "aggregator",
      "message": "Tax year 2023 is not supported...",
      "type": "error"
    }
  ],
  "current_step": "aggregating"
}
```

**Status Codes:**
- `200 OK` - Workflow completed (status may be "complete", "waiting_for_user", or "error")
- `400 Bad Request` - Invalid request data
- `500 Internal Server Error` - Server error

---

### 4. Generate Form 1040 PDF

**Endpoint:** `POST /api/reports/{session_id}/1040`

**Description:** Generates a filled IRS Form 1040 PDF based on the completed tax calculation.

**Prerequisites:**
- Session must have `status: "complete"` from the workflow
- All calculations must be finalized

**Request:**
- **Method:** `POST`
- **Path Parameter:** `session_id` (UUID)

**Request Example:**
```javascript
const response = await fetch(
  `http://localhost:8000/api/reports/${sessionId}/1040`,
  { method: 'POST' }
);

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'Form_1040.pdf';
a.click();
```

**Response:**
- **Content-Type:** `application/pdf`
- **Body:** Binary PDF file
- **Headers:**
  - `Content-Disposition: attachment; filename="Form_1040.pdf"`

**Status Codes:**
- `200 OK` - PDF generated successfully
- `400 Bad Request` - Session not ready (workflow incomplete)
- `500 Internal Server Error` - PDF generation failed

---

### 5. Delete Session

**Endpoint:** `DELETE /api/sessions/{session_id}`

**Description:** Permanently deletes a session and all associated data (uploaded files, extraction results, generated PDFs, database records).

**Request:**
- **Method:** `DELETE`
- **Path Parameter:** `session_id` (UUID)

**Response:**
```json
{
  "message": "Session data deleted successfully"
}
```

**Status Codes:**
- `200 OK` - Session deleted successfully
- `500 Internal Server Error` - Deletion failed

---

## 🎯 Using the Advisor Feedback

### Overview

The `advisor_feedback` field contains **personalized, natural language financial advice** generated by the AI Advisor node. It provides:
1. **Result Summary:** Clear statement of refund/amount owed
2. **Actionable Next Steps:** Specific instructions (e.g., "Pay via IRS Direct Pay")
3. **Pro Tips:** Tax optimization advice tailored to the user's income sources

### Frontend Display Guidelines

#### 1. **When to Display**
- Only show `advisor_feedback` when `status === "complete"`
- Hide it for `waiting_for_user` or `error` states

#### 2. **UI Component Structure**

```tsx
// React/Next.js Example
function AdvisorFeedback({ feedback }: { feedback: string | null }) {
  if (!feedback) return null;

  return (
    <div className="advisor-card bg-blue-50 border-l-4 border-blue-500 p-6 rounded-lg my-6">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div className="ml-4 flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            💡 Your Personalized Tax Advice
          </h3>
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-line">
            {feedback}
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### 3. **Formatting Tips**

- **Use `whitespace-pre-line`** CSS class to preserve line breaks in the feedback text
- **Highlight Key Sections:**
  - Use bold/strong tags for "Pro Tip:" sections
  - Use different colors for refund (green) vs. owed (amber) scenarios
- **Make Links Clickable:**
  - The advisor may mention "IRS.gov" or "Direct Pay" - convert these to clickable links

#### 4. **Example Integration**

```typescript
// After receiving ProcessSessionResponse
const response = await processSession(sessionId, requestData);

if (response.status === "complete" && response.advisor_feedback) {
  // Display the advisor feedback prominently
  setAdvisorFeedback(response.advisor_feedback);
  
  // Also show calculation results
  setCalculationResult(response.calculation_result);
  
  // Show the activity feed
  setActivityLogs(response.logs || []);
}
```

#### 5. **Styling Recommendations**

**For Refund Scenarios:**
- Background: Light green (`bg-green-50`)
- Border: Green (`border-green-500`)
- Icon: Checkmark or celebration emoji

**For Owed Scenarios:**
- Background: Light amber (`bg-amber-50`)
- Border: Amber (`border-amber-500`)
- Icon: Alert or payment icon

**For General Advice:**
- Background: Light blue (`bg-blue-50`)
- Border: Blue (`border-blue-500`)
- Icon: Lightbulb or info icon

---

## 📊 Using the Activity Logs

### Overview

The `logs` array provides a **chronological timeline** of the agent's execution. Use this to build an "Agent Activity Feed" component.

### Frontend Implementation

```tsx
function ActivityFeed({ logs }: { logs: AgentLog[] }) {
  const getIcon = (type: string) => {
    switch (type) {
      case "success": return "✅";
      case "warning": return "⚠️";
      case "error": return "❌";
      default: return "ℹ️";
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case "success": return "text-green-600";
      case "warning": return "text-yellow-600";
      case "error": return "text-red-600";
      default: return "text-blue-600";
    }
  };

  return (
    <div className="activity-feed space-y-3 max-h-96 overflow-y-auto">
      {logs.map((log, index) => (
        <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
          <span className="text-xl">{getIcon(log.type)}</span>
          <div className="flex-1">
            <p className={`text-sm font-medium ${getColor(log.type)}`}>
              {log.message}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {log.node} • {new Date(log.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 🔐 Security Considerations

1. **File Upload Limits:** 10MB max per file, PDF magic byte validation
2. **Session Cleanup:** Use `DELETE /sessions/{id}` after user downloads Form 1040
3. **Data Privacy:** All sensitive data (SSN, income) is stored in plain text (encryption planned for production)

---

## 🚨 Error Handling

### Common Error Scenarios

1. **Missing Mandatory Fields:**
   - **Status:** `waiting_for_user`
   - **Action:** Display `missing_fields` array and request user input
   - **Retry:** Send another `POST /sessions/{id}/process` with the missing fields

2. **Unsupported Tax Year:**
   - **Status:** `error`
   - **Message:** "Tax year X is not supported. This system only supports 2024 tax calculations."
   - **Action:** Inform user and request 2024 documents

3. **No Income Data:**
   - **Status:** `waiting_for_user`
   - **Missing Field:** `income_data`
   - **Action:** Request user to verify document uploads or provide manual income values

---

## 📝 Complete Workflow Example

```javascript
// Step 1: Upload Documents
const uploadResponse = await fetch('http://localhost:8000/api/sessions', {
  method: 'POST',
  body: formData
});
const { session_id, documents } = await uploadResponse.json();

// Step 2: Extract All Documents
for (const doc of documents) {
  await fetch(`http://localhost:8000/api/documents/${doc.id}/extract`, {
    method: 'POST'
  });
}

// Step 3: Process Workflow (with personal info)
const processResponse = await fetch(
  `http://localhost:8000/api/sessions/${session_id}/process`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filing_status: "single",
      tax_year: "2024",
      personal_info: {
        filer_name: "John Doe",
        filer_ssn: "123-45-6789",
        home_address: "123 Main St, New York, NY 10001",
        occupation: "Software Engineer",
        digital_assets: "no"
      }
    })
  }
);
const result = await processResponse.json();

// Step 4: Handle Response
if (result.status === "waiting_for_user") {
  // Show form to collect missing_fields
  console.log("Missing:", result.missing_fields);
} else if (result.status === "complete") {
  // Display results
  console.log("Refund/Owed:", result.calculation_result.refund_or_owed);
  console.log("Advice:", result.advisor_feedback);
  
  // Step 5: Generate PDF
  const pdfResponse = await fetch(
    `http://localhost:8000/api/reports/${session_id}/1040`,
    { method: 'POST' }
  );
  const blob = await pdfResponse.blob();
  // Download PDF...
  
  // Step 6: Cleanup (optional)
  await fetch(`http://localhost:8000/api/sessions/${session_id}`, {
    method: 'DELETE'
  });
}
```

---

## 📚 Additional Resources

- **Agent Activity Feed Documentation:** See `docs/AGENT_ACTIVITY_FEED.md`
- **Form 1040 Field Mapping:** See `docs/1040_field_mapping_template.json`
- **Tax Filing Instructions:** See `1040_FILING_INSTRUCTIONS.md`

---

**Last Updated:** 2024-05-20  
**API Version:** 0.1.0

