# Research Assistant - API and CLI Usage Guide

## CLI Usage

The research assistant can be run from the command line using the `research` command.

### Basic Usage

```bash
uv run research --topic "Your research topic"
```

### Options

- `--topic` (required): The research topic
- `--depth` (optional): Research depth - `fast`, `normal`, or `deep` (default: `normal`)
- `--output` (optional): Output directory (default: `Research`)

### Examples

**Basic research (normal depth)**:
```bash
uv run research --topic "AI trends 2025"
```

**Fast research**:
```bash
uv run research --topic "Quantum computing advances" --depth fast
```

**Deep research with custom output**:
```bash
uv run research --topic "Climate change solutions" --depth deep --output ./my_research
```

### Output

The research will be saved as a Markdown file in the specified output directory with a timestamped filename:
```
Research/research_ai_trends_2025_20251222_165000.md
```

---

## API Usage

The research assistant provides a REST API for programmatic access.

### Start Research

**Endpoint**: `POST /api/start-research`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "topic": "AI trends 2025",
  "depth": "normal",
  "outputPath": "./results"
}
```

**Response**:
```json
{
  "status": "started",
  "message": "Research initiated"
}
```

### Examples

**Using curl**:
```bash
curl -X POST http://localhost:5000/api/start-research \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI trends 2025", "depth": "deep", "outputPath": "./results"}'
```

**Using Python**:
```python
import requests

response = requests.post(
    'http://localhost:5000/api/start-research',
    json={
        'topic': 'AI trends 2025',
        'depth': 'deep',
        'outputPath': './results'
    }
)

print(response.json())
```

**Using JavaScript**:
```javascript
fetch('http://localhost:5000/api/start-research', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    topic: 'AI trends 2025',
    depth: 'deep',
    outputPath: './results'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Depth Modes

### Fast Mode
- **Max Topics**: 5
- **Max Iterations**: 1
- **Concurrent Researchers**: 2
- **Use Case**: Quick overview, time-sensitive research

### Normal Mode (Default)
- **Max Topics**: 10
- **Max Iterations**: 3
- **Concurrent Researchers**: 3
- **Use Case**: Balanced depth and speed

### Deep Mode
- **Max Topics**: 20
- **Max Iterations**: 5
- **Concurrent Researchers**: 5
- **Use Case**: Comprehensive research, complex topics

---

## Integration Examples

### Automated Research Pipeline

```bash
#!/bin/bash
# research_pipeline.sh

topics=(
  "AI developments 2025"
  "Quantum computing advances"
  "Climate tech innovations"
)

for topic in "${topics[@]}"; do
  echo "Researching: $topic"
  uv run research --topic "$topic" --depth normal --output ./batch_research
  echo "Completed: $topic"
done
```

### Scheduled Research (Cron)

```cron
# Run daily research at 2 AM
0 2 * * * cd /path/to/research_assistant && uv run research --topic "Daily AI news" --depth fast --output ./daily_reports
```

### API Integration

```python
# research_service.py
import requests
import time

def start_research(topic, depth='normal'):
    """Start research via API."""
    response = requests.post(
        'http://localhost:5000/api/start-research',
        json={'topic': topic, 'depth': depth}
    )
    return response.json()

def monitor_status():
    """Monitor research status via SSE."""
    # Connect to /api/events endpoint
    # Parse status updates
    pass

# Usage
result = start_research("AI trends 2025", depth="deep")
print(f"Research started: {result}")
```

---

## Notes

- The API endpoint `/api/start-research` already existed for UI integration and now fully supports programmatic JSON requests
- Only one research job can run at a time (returns 409 if another job is active)
- Research results are saved to the specified output directory
- The validation loop runs automatically for all research tasks
- Parallel execution is enabled by default based on depth mode
