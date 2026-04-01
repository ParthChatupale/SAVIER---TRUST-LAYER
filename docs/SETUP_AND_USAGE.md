# Savier Setup and Usage Guide

## Overview
This guide is for teammates who want to run, demo, or extend Savier. Savier currently spans two local projects:

- backend and MCP server: `/home/parth/workspace/Savier/appsec-agent`
- VS Code extension frontend: `/home/parth/workspace/Savier/appsec-interceptor`

The backend is the trust engine and persistence layer. The extension is the user-facing product surface.

## Repository Structure Overview

### Backend repo: `appsec-agent`
Important areas:

- `appsec_agent/services`
  - analysis pipeline orchestration
- `appsec_agent/agents`
  - planning, specialist review, aggregation
- `appsec_agent/memory`
  - SQLite persistence
- `appsec_agent/providers`
  - model provider integrations
- `appsec_agent/transports`
  - request parsing and response serialization
- `appsec_agent/tools`
  - MCP tool registration
- `appsec_agent/http_server.py`
  - Flask API entrypoint
- `appsec_agent/server.py`
  - MCP stdio server entrypoint
- `examples`
  - manual validation samples
- `tests`
  - backend tests

### Extension repo: `appsec-interceptor`
Important areas:

- `src/extension.ts`
  - extension activation and wiring
- `src/services`
  - analysis requests, API client, state management
- `src/editor`
  - diagnostics
- `src/ui`
  - Trust Cockpit, Active File State, History panels
- `src/core`
  - contracts and extension config
- `src/test`
  - extension tests

## Backend Setup

### Requirements
- Python 3.11+
- local virtualenv in `.venv`
- provider credentials if using NVIDIA-backed models

### Install / environment
If the environment is already present, activate it:

```bash
cd /home/parth/workspace/Savier/appsec-agent
source .venv/bin/activate
```

If needed, dependencies are managed through `pyproject.toml`.

### Environment variables
Key variables:

- `APPSEC_AGENT_PROVIDER`
  - `nvidia` or `ollama`
- `NVIDIA_API_KEY`
  - required for NVIDIA-backed runs
- `NVIDIA_BASE_URL`
  - optional override for NVIDIA endpoint
- `APPSEC_AGENT_DB_PATH`
  - optional custom SQLite path
- `APPSEC_AGENT_PIPELINE`
  - optional pipeline override

Model routing variables also exist for advanced control:

- `APPSEC_AGENT_MODEL_PLANNING`
- `APPSEC_AGENT_MODEL_SECURITY_REVIEW`
- `APPSEC_AGENT_MODEL_QUALITY_REVIEW`
- `APPSEC_AGENT_MODEL_PERFORMANCE_REVIEW`
- `APPSEC_AGENT_MODEL_AGGREGATION`

The backend also supports fallback model variables.

## Provider Configuration

### NVIDIA-backed configuration
Use when you want the current hosted demo path.

```bash
export APPSEC_AGENT_PROVIDER=nvidia
export NVIDIA_API_KEY=your_key_here
```

Default NVIDIA model routing is:

- planning: `google/gemma-2-9b-it`
- security_review: `google/gemma-2-9b-it`
- quality_review: `google/gemma-2-9b-it`
- performance_review: `google/gemma-2-9b-it`
- aggregation: `openai/gpt-oss-120b`

### Ollama-backed configuration
Use when testing with local models.

```bash
export APPSEC_AGENT_PROVIDER=ollama
```

Optional:

- `OLLAMA_HOST`
- `APPSEC_AGENT_OLLAMA_TIMEOUT`
- `APPSEC_AGENT_OLLAMA_MAX_RETRIES`

## Running the HTTP Server
Start the backend API server:

```bash
cd /home/parth/workspace/Savier/appsec-agent
APPSEC_AGENT_PROVIDER=nvidia .venv/bin/python -m appsec_agent.http_server
```

The default HTTP base URL is:

- `http://127.0.0.1:5000`

Main endpoints:

- `POST /analyze`
- `GET /history`
- `POST /clear`
- `GET /dashboard`
- `GET /timeline`
- `GET /file-state`
- `GET /health`

## Running the MCP Server
Start the MCP stdio server:

```bash
cd /home/parth/workspace/Savier/appsec-agent
.venv/bin/python -m appsec_agent.server
```

The MCP server name is:

- `appsec-agent`

Primary MCP tools:

- `analyze_code`
- `get_dashboard`
- `get_analysis_timeline`
- `get_file_state`
- `get_developer_history`
- `clear_developer_history`

By default, `analyze_code` now defaults to `full` mode unless a caller explicitly requests another mode.

## Example MCP Client Config

```json
{
  "mcpServers": {
    "appsec-agent": {
      "command": "/home/parth/workspace/Savier/appsec-agent/.venv/bin/python",
      "args": ["-m", "appsec_agent.server"],
      "cwd": "/home/parth/workspace/Savier/appsec-agent"
    }
  }
}
```

If using NVIDIA-backed runs through MCP, make sure the MCP host also passes the relevant environment variables.

## Running the VS Code Extension

### Compile the extension

```bash
cd /home/parth/workspace/Savier/appsec-interceptor
npm run compile
```

### Launch the extension
- Open the `appsec-interceptor` repo in VS Code
- Press `F5` to launch the Extension Development Host

### Important extension settings
- `appsecInterceptor.serverUrl`
  - default: `http://127.0.0.1:5000`
- `appsecInterceptor.developerId`
  - defaults to local username if not set
- `appsecInterceptor.mode`
  - should be `full` for the Savier demo
- `appsecInterceptor.autoAnalyze`
  - enabled by default
- `appsecInterceptor.debounceMs`
  - default: `1200`
- `appsecInterceptor.requestTimeoutMs`
  - default: `60000`

### Main extension commands
- `Savier: Show Trust Cockpit`
- `Savier: Show Developer History`
- `Savier: Show Active File State`
- `Savier: Re-run Analysis for Active File`
- `Savier: Clear Developer History`

## Running Tests

### Backend tests

```bash
cd /home/parth/workspace/Savier/appsec-agent
.venv/bin/python -m unittest discover -s tests -v
```

### Extension tests

```bash
cd /home/parth/workspace/Savier/appsec-interceptor
npm run compile
node ./out/test/runUnitTests.js
```

## Manual Validation
The backend repo includes intentionally flawed samples:

- `examples/flawed_security.py`
- `examples/flawed_quality.py`
- `examples/flawed_performance.py`
- `examples/flawed_full.py`

Run the manual validation helper:

```bash
cd /home/parth/workspace/Savier/appsec-agent
.venv/bin/python examples/run_manual_validation.py full
```

Override developer id and mode if needed:

```bash
.venv/bin/python examples/run_manual_validation.py full parth full
```

## Performing a Direct HTTP Analysis
Example request:

```bash
curl -sS -X POST http://127.0.0.1:5000/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "code": "query = \"SELECT * FROM users WHERE id = \" + user_id",
    "developer_id": "parth",
    "mode": "full",
    "file_uri": "file:///demo.py",
    "source": "http_client"
  }'
```

Expected response shape includes:

- `findings`
- `dimensions`
- `primary_finding`
- `scores`
- `diff`
- `analysis_profile`

## Verifying Dashboard, File State, and Timeline

### Dashboard
Use:

```bash
curl -sS "http://127.0.0.1:5000/dashboard?developer_id=parth"
```

Confirms:
- total tracked files
- total events
- open findings
- average scores
- score trend

### Timeline
Use:

```bash
curl -sS "http://127.0.0.1:5000/timeline?developer_id=parth&file_uri=file:///demo.py"
```

Confirms:
- revision history
- score deltas
- fixed/new/unchanged findings

### File State
Use:

```bash
curl -sS "http://127.0.0.1:5000/file-state?developer_id=parth&file_uri=file:///demo.py"
```

Confirms:
- latest state for a file
- latest scores
- currently open findings
- last event id

## Where Major Code Paths Live

### Backend
- analysis orchestration: `appsec_agent/services/analysis.py`
- persistence: `appsec_agent/memory/store.py`
- planning stage: `appsec_agent/agents/planning.py`
- specialist review helpers: `appsec_agent/agents/review_common.py`
- aggregation stage: `appsec_agent/agents/aggregation.py`
- config and model routing: `appsec_agent/core/config.py`
- MCP server: `appsec_agent/server.py`
- HTTP server: `appsec_agent/http_server.py`

### Extension
- activation and panel wiring: `src/extension.ts`
- analysis request flow: `src/services/analyzer.ts`
- HTTP client: `src/services/apiClient.ts`
- Trust Cockpit view: `src/ui/dashboardPanel.ts`
- Active File State view: `src/ui/fileStatePanel.ts`
- status bar: `src/ui/statusBar.ts`

## Recommended Demo Runbook
1. Start backend HTTP server
2. Confirm `/health` is reachable
3. Start or reload the extension host
4. Open the demo file
5. Let Savier analyze automatically
6. Open Trust Cockpit
7. Apply the improved revision
8. Re-run analysis
9. Show score delta and timeline

## Final Notes
- Keep analysis mode on `full` for the main Savier story.
- Use the backend as the source of truth for scores and findings.
- Prefer a clean, intentionally flawed demo file for live judging.
- Use MCP when you want to demonstrate agent compatibility beyond the extension.
