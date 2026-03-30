# AppSec Agent

## Manual Validation Pack

The repo now includes intentionally flawed samples under [`examples/`](/home/parth/workspace/Savier/appsec-agent/examples) so you can sanity-check the refactor without inventing test inputs.

### Preflight

Before testing the actual analysis quality:

1. Use the virtualenv interpreter or activate `.venv`.
2. Make sure Ollama is running.
3. Make sure these models exist locally:
   - `llama3.2`
   - `llama3.1:8b`

If Ollama is down, that is still a useful test: the app should now return a structured failed response instead of crashing.

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

- The app should not crash if Ollama is unavailable.
- Invalid modes should return normalized failed responses.
- HTTP and MCP should shape failures the same way.
- Security samples should surface security-oriented findings.
- Quality and performance samples should produce mode-appropriate findings.
- The full sample should return one high-signal issue, not random malformed output.
