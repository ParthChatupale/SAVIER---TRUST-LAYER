# AppSec Interceptor

`appsec-interceptor` is a thin VS Code client for the local `appsec-agent` service. It watches supported files, calls the HTTP analysis API, and turns normalized findings into editor diagnostics, status bar updates, and lightweight dashboards.

## Features

- Live analysis for Python, JavaScript, and TypeScript files
- Typed integration with the normalized `appsec-agent` HTTP contract
- Per-document debounce and stale-result protection
- Safe history and dashboard webviews
- Commands for viewing history, viewing the dashboard, clearing history, and re-running analysis

## Requirements

The extension expects a local `appsec-agent` HTTP server to be available.

Example:

```bash
cd /home/parth/workspace/Savier/appsec-agent
.venv/bin/python appsec_agent/http_server.py
```

Default backend URL:

```text
http://127.0.0.1:5000
```

## Settings

- `appsecInterceptor.serverUrl`: HTTP base URL for the local AppSec service
- `appsecInterceptor.developerId`: developer identifier sent with each request
- `appsecInterceptor.mode`: `security`, `quality`, `performance`, or `full`
- `appsecInterceptor.debounceMs`: delay before auto-analysis runs
- `appsecInterceptor.enabledLanguages`: language IDs to analyze automatically
- `appsecInterceptor.autoAnalyze`: enable or disable automatic analysis

## Commands

- `AppSec: Show Developer History`
- `AppSec: Show Score Dashboard`
- `AppSec: Clear Developer History`
- `AppSec: Re-run Analysis for Active File`

## Development

```bash
npm run compile
npm run lint
npm test
```

## Troubleshooting

If the status bar shows `Backend unavailable`:

1. Confirm the local `appsec-agent` HTTP server is running.
2. Confirm `appsecInterceptor.serverUrl` matches the backend URL.
3. Check that the backend can reach Ollama and return normalized responses.
