# Streaming Agent Implementation Guide

## Overview

The LangGraph agent now provides **real-time streaming updates** to power a responsive "Agent Activity Feed" on the frontend. Instead of showing a generic loading spinner, users can see exactly what the AI agent is doing at each step.

---

## What Changed

### 1. **State Schema (`app/agent/state.py`)**

Added two new fields to `TaxState`:

```python
class AgentLog(TypedDict):
    timestamp: str  # ISO 8601 timestamp
    node: str       # "aggregator", "calculator", "validator"
    message: str    # Human-readable status message
    type: str       # "info", "success", "warning", "error"

class TaxState(TypedDict):
    # ... existing fields ...
    current_step: str        # Current stage: "aggregating", "calculating", "validating"
    logs: List[AgentLog]     # Chronological log of agent's actions
```

### 2. **Node Instrumentation (`app/agent/nodes.py`)**

Each node now appends detailed log entries:

**Example from `aggregator_node`:**
```python
state["logs"].append({
    "timestamp": datetime.now(UTC).isoformat(),
    "node": "aggregator",
    "message": "Found 2 document(s) in session. Extracting financial data...",
    "type": "info"
})
```

**Key Moments Logged:**
- Document discovery and count
- Data extraction progress
- Validation checks (missing fields)
- Aggregation completion
- Tax calculation start/finish
- AI audit results

### 3. **New Streaming Endpoint (`app/api/endpoints.py`)**

**Endpoint:** `POST /api/sessions/{session_id}/process/stream`

**Technology:** Server-Sent Events (SSE)

**Behavior:**
- Streams each node's state update as it completes
- Uses `graph.stream()` instead of `graph.invoke()`
- Returns `Content-Type: text/event-stream`

**Response Format:**
```
data: {"node": "aggregate", "status": "aggregated", "logs": [...], ...}

data: {"node": "calculate", "status": "calculated", "logs": [...], ...}

data: {"node": "validate", "status": "validated", "logs": [...], ...}

data: {"status": "complete", "final_state": {...}}
```

### 4. **Updated Non-Streaming Endpoint**

The original `POST /api/sessions/{session_id}/process` endpoint now includes `logs` and `current_step` in the response.

---

## Frontend Integration

### Option A: Non-Streaming (Simpler)

1. Call `POST /sessions/{session_id}/process`
2. Wait for complete response
3. Display the `logs` array sequentially with a delay to simulate "thinking"

**Example (React):**
```typescript
const response = await fetch(`/api/sessions/${sessionId}/process`, {
  method: 'POST',
  body: JSON.stringify(requestData)
});

const result = await response.json();

// Animate through logs
result.logs.forEach((log, index) => {
  setTimeout(() => {
    addLogToFeed(log);
  }, index * 500);
});
```

### Option B: Streaming (Real-time)

1. Use EventSource API or fetch with SSE
2. Display logs as they arrive in real-time

**Example (React):**
```typescript
const eventSource = new EventSource(`/api/sessions/${sessionId}/process/stream`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.logs) {
    data.logs.forEach(log => addLogToFeed(log));
  }
  
  if (data.status === 'complete') {
    eventSource.close();
    showResults(data.final_state);
  }
};
```

---

## Agent Activity Feed UI Component

### Recommended Structure

```tsx
interface AgentLog {
  timestamp: string;
  node: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

function AgentActivityFeed({ logs }: { logs: AgentLog[] }) {
  const getIcon = (type: string) => {
    switch(type) {
      case 'info': return '📄';
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '•';
    }
  };
  
  const getColor = (type: string) => {
    switch(type) {
      case 'success': return 'text-green-600';
      case 'warning': return 'text-amber-600';
      case 'error': return 'text-red-600';
      default: return 'text-blue-600';
    }
  };
  
  return (
    <div className="space-y-2 font-mono text-sm">
      {logs.map((log, i) => (
        <div key={i} className={`flex items-start gap-2 ${getColor(log.type)}`}>
          <span>{getIcon(log.type)}</span>
          <span className="text-gray-500">[{log.node}]</span>
          <span>{log.message}</span>
        </div>
      ))}
    </div>
  );
}
```

### Visual States

1. **Info (Blue)**: Agent is processing
   - "Starting data aggregation..."
   - "Applying 2024 tax rules..."

2. **Success (Green)**: Step completed successfully
   - "Extracted income: Wages $85,000.00..."
   - "Audit Passed: No anomalies detected."

3. **Warning (Amber)**: Needs attention but not fatal
   - "Missing critical information: filing_status"
   - "Multiple tax years detected in documents"

4. **Error (Red)**: Critical failure
   - "Validation failed: No calculation results found."

---

## Testing

### Manual Test (Backend Running)

```bash
cd backend
uv run python test_streaming.py
```

This script connects to the streaming endpoint and displays logs in the terminal with colored icons.

### Expected Output

```
🚀 Starting streaming workflow for session: test-session-123

============================================================
📄 [aggregator] Starting data aggregation and validation...
📄 [aggregator] Found 0 document(s) in session. Extracting financial data...
⚠️ [aggregator] Missing critical information: income_data. User input required.

============================================================
✅ Workflow Complete!
```

---

## Benefits

### For Users
- **Transparency**: See what the AI is doing, not just a spinner
- **Trust**: Understand the agent's decision-making process
- **Faster Perceived Performance**: Real-time updates feel faster than waiting

### For Developers
- **Debugging**: Logs show exactly where the workflow is failing
- **Analytics**: Track which steps take the longest
- **User Support**: Users can screenshot the feed for bug reports

---

## Production Considerations

### Performance
- SSE keeps the connection open longer
- Consider connection pooling limits
- Add timeout for stuck workflows (e.g., 60s max)

### Security
- Validate session ownership before streaming
- Don't log sensitive data (SSNs, full addresses) in messages
- Rate limit the streaming endpoint

### Monitoring
- Track stream completion rates
- Monitor for abandoned connections
- Log average workflow duration per node

---

## Summary

| Feature | Before | After |
|---------|--------|-------|
| **UI Feedback** | Generic spinner | Real-time activity feed |
| **User Trust** | Black box | Transparent reasoning |
| **Debugging** | Check logs after failure | See failure happen live |
| **API Response** | Single final result | Streaming node updates |
| **Frontend Complexity** | Simple fetch() | EventSource or SSE handling |

The agent is no longer a mysterious "calculating..." box—it's now a collaborative assistant that shows its work.

