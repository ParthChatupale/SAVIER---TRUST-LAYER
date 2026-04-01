# AppSec Agent

`appsec-agent` exposes the same analysis backend over HTTP and MCP stdio.
The MCP server name is `appsec-agent`.

## Running The MCP Server

Start the MCP server with the project virtualenv:

```bash
.venv/bin/python -m appsec_agent.server
```

This launches a stdio MCP server that another agent or MCP client can use.
The primary MCP tools are:

- `analyze_code`
- `get_dashboard`
- `get_analysis_timeline`
- `get_file_state`
- `get_developer_history`
- `clear_developer_history`

By default, `analyze_code` now runs in `full` mode unless the caller
explicitly asks for `security`, `quality`, or `performance`.

## Example MCP Client Config

If your MCP client expects a local server entry, point it at the module
entrypoint instead of a separate root script.

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

After this is registered, you can ask another agent to use the
`appsec-agent` MCP server for code analysis, dashboard reads, timeline
inspection, and active-file state checks.

## HTTP Server

For local dashboard and extension development, you can run the HTTP server:

```bash
APPSEC_AGENT_PROVIDER=nvidia .venv/bin/python -m appsec_agent.http_server
```

It serves:

- `POST /analyze`
- `GET /dashboard`
- `GET /timeline`
- `GET /file-state`
- `POST /clear`

## Manual Validation Pack

The repo includes intentionally flawed samples under
[`examples/`](/home/parth/workspace/Savier/appsec-agent/examples) so you can
sanity-check the analysis pipeline without inventing test inputs.

### Preflight

Before testing analysis quality:

1. Use the virtualenv interpreter or activate `.venv`.
2. Make sure your configured provider is available.
3. For NVIDIA-backed runs, set the required environment variables.
4. For Ollama-backed runs, make sure Ollama is running and the configured
   local models are installed.

If the provider is unavailable, that is still a useful test: the app should
return a structured failed response instead of crashing.

### Sample Cases

- `examples/flawed_security.py`
  - Hardcoded secret
  - SQL injection
  - Path handling that should look suspicious
- `examples/flawed_quality.py`
  - God function shape
  - Magic numbers
  - Weak validation / weak error handling
- `examples/flawed_performance.py`
  - N+1 style repeated queries
  - Nested loops
- `examples/flawed_full.py`
  - Mixed security + performance + quality issues

### Quick Run

Use the helper runner:

```bash
.venv/bin/python examples/run_manual_validation.py security
.venv/bin/python examples/run_manual_validation.py quality
.venv/bin/python examples/run_manual_validation.py performance
.venv/bin/python examples/run_manual_validation.py full
```

You can also override the developer id and mode:

```bash
.venv/bin/python examples/run_manual_validation.py full parth full
```

### What To Look For

- The app should not crash if the configured provider is unavailable.
- Invalid modes should return normalized failed responses.
- HTTP and MCP should shape failures the same way.
- Security samples should surface security-oriented findings.
- Quality and performance samples should produce mode-appropriate findings.
- The full sample should return a believable multi-dimension result.
