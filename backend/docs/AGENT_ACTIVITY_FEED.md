# 🧠 Agent Activity Feed Documentation

## Overview
The **Agent Activity Feed** is a frontend component designed to visualize the AI agent's "thinking process." Instead of a static loading spinner, it displays a chronological log of the agent's actions, decisions, and findings. This builds user trust and makes the system transparent.

## Data Source
The feed is populated using the `logs` array returned in the `ProcessSessionResponse` from the `POST /api/sessions/{session_id}/process` endpoint.

### API Response Structure
```json
{
  "status": "complete",
  "logs": [
    {
      "timestamp": "2024-05-20T10:30:01.123",
      "node": "aggregator",
      "message": "Starting document analysis...",
      "type": "info"
    },
    {
      "timestamp": "2024-05-20T10:30:02.456",
      "node": "aggregator",
      "message": "Identified Tax Year: 2024",
      "type": "success"
    },
    {
      "timestamp": "2024-05-20T10:30:05.789",
      "node": "validator",
      "message": "AI Auditor reviewing results...",
      "type": "info"
    }
  ],
  "current_step": "validating"
}
```

## Log Types & UI Representation

Map the `type` field to specific visual styles:

| Log Type | Icon | Color | Meaning |
| :--- | :--- | :--- | :--- |
| `info` | ℹ️ / 🔵 | Blue/Gray | General progress update. |
| `success` | ✅ | Green | Successful action or finding (e.g., "Found W-2"). |
| `warning` | ⚠️ | Amber | Potential issue or missing data (e.g., "Missing SSN"). |
| `error` | ❌ | Red | Critical failure that stopped the workflow. |

## Implementation Guide (Frontend)

### 1. State Management
Create a state variable to hold the logs:
```tsx
const [logs, setLogs] = useState<AgentLog[]>([]);
const [isProcessing, setIsProcessing] = useState(false);
```

### 2. Processing Loop
Since the API currently returns the *full* log history at the end of the request, you can render the logs sequentially with a small delay to simulate "streaming" for a better UX, or simply display them all at once.

**Simulated Streaming Effect (Recommended):**
```typescript
const handleProcess = async () => {
  setIsProcessing(true);
  const response = await api.processSession(sessionId);
  
  // "Replay" the logs to the user
  for (const log of response.logs) {
    setLogs(prev => [...prev, log]);
    await new Promise(r => setTimeout(r, 800)); // 800ms delay between logs
  }
  
  setIsProcessing(false);
};
```

### 3. Component Structure
```tsx
<div className="agent-feed-container p-4 bg-gray-50 rounded-lg max-h-96 overflow-y-auto">
  {logs.map((log, index) => (
    <div key={index} className="flex items-start mb-3 animate-fade-in">
      <div className="mr-3 mt-1">
        {log.type === 'info' && <IconInfo className="text-blue-500" />}
        {log.type === 'success' && <IconCheck className="text-green-500" />}
        {log.type === 'warning' && <IconAlert className="text-yellow-500" />}
        {log.type === 'error' && <IconX className="text-red-500" />}
      </div>
      <div>
        <p className="text-sm font-medium text-gray-900">{log.message}</p>
        <span className="text-xs text-gray-500 capitalize">{log.node} Node • {formatTime(log.timestamp)}</span>
      </div>
    </div>
  ))}
  {isProcessing && (
    <div className="flex items-center text-gray-400 text-sm">
      <Spinner className="mr-2" />
      Agent is thinking...
    </div>
  )}
</div>
```

## Key Benefits
1. **Transparency**: Users know exactly what data was found.
2. **Trust**: Users see the "AI Auditor" checking the math.
3. **Clarity**: Errors are contextual (e.g., "Aggregation failed" vs. "Upload failed").

