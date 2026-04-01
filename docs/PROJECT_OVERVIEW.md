# Savier Project Overview

## Executive Summary
Savier is a real-time trust layer for AI-assisted software development. It helps developers evaluate whether code generated or revised with AI tools should be trusted before that code becomes part of the workflow. Instead of waiting for post-hoc scanning in CI/CD or code review, Savier analyzes code while context is still hot and surfaces a unified trust judgment across security, quality, and performance.

Savier is built as a VS Code-first product backed by a Python analysis engine. The backend serves as the source of truth for findings, trust scoring, revision deltas, file state, and timeline history. The frontend presents that truth through a Trust Cockpit dashboard, active file state views, editor diagnostics, and status bar feedback. The same backend is also exposed through MCP, allowing both human developers and AI agents to use the same trust evaluation system.

At its core, Savier exists to solve a growing mismatch: AI can generate code instantly, but developers still cannot verify its trustworthiness instantly. Savier closes that gap.

## Problem Statement
AI coding assistants have dramatically increased the speed of code creation. Developers can now prompt copilots to generate a feature, accept the result in seconds, and continue building. However, trust verification has not kept up with generation speed. Most tools that identify security flaws, maintainability issues, or performance problems run later in the lifecycle, after code has already entered the repository, the pull request, or the deployment pipeline.

This is not just a security problem. It is a broader trust problem:

- insecure code may spread downstream before anyone notices
- maintainability problems compound as more code depends on weak patterns
- performance inefficiencies remain hidden until load or scale reveals them
- developers lose context by the time they come back to fix the issue

Savier addresses this by moving trust verification into the coding loop itself.

## Why Now
AI-assisted coding is moving from novelty to default workflow. As generation tools become faster and more capable, the burden shifts to developers to decide whether generated code should be accepted, revised, or rejected. Existing tools are still optimized for late-stage validation:

- static analyzers run after the code exists in the codebase
- security scanners often run at pull request or CI time
- coding copilots optimize for functionality and speed, not for trustworthiness

This creates a gap between code generation and code adoption. Savier is designed for that exact moment.

## Core Thesis
Savier is based on one central idea:

**AI helps developers write code faster, but not trust code faster.**

The product thesis is that trust verification should happen:

- in context
- before adoption
- inside the editor
- across multiple quality dimensions
- with revision-aware feedback rather than isolated one-off alerts

## Product Vision
Savier aims to become the trust infrastructure for AI-assisted development. In the near term, it works as a trust cockpit for single files and active revisions. In the long term, it can evolve into:

- project-level trust dashboards
- team-wide risk and quality tracking
- CI/CD trust gates
- auto-fix suggestion workflows
- benchmarking for AI agents based on trust improvement

The vision is not to replace coding copilots. It is to make them safer, clearer, and more usable.

## Target Users
Savier is useful for:

- developers using AI coding assistants like Copilot or Cursor
- hackathon teams building quickly and needing faster judgment
- student developers learning secure and maintainable coding habits
- engineering teams experimenting with agent-assisted workflows
- technical leads who want clearer trust signals for evolving code

## Key Workflows

### Workflow 1: Developer-in-the-loop trust checking
1. Developer writes or pastes code in VS Code.
2. Savier analyzes the active file after a short debounce.
3. Editor diagnostics highlight key issues.
4. The Trust Cockpit shows:
   - overall trust score
   - dimension breakdown
   - active findings
   - revision delta
   - timeline
5. The developer revises the code.
6. Savier re-analyzes and shows whether trust improved or regressed.

### Workflow 2: Agent-assisted trust evaluation
1. An agent generates or revises code.
2. The same analysis backend is invoked through MCP.
3. Savier returns the same structured findings, scores, and explanations used by the extension.
4. The result can be consumed by agentic workflows, dashboards, or follow-up automation.

### Workflow 3: Demo / judge-facing trust proof
1. Start with intentionally flawed code.
2. Show low trust score and active findings.
3. Improve the code.
4. Show positive score delta, fixed findings, and a cleaner current state.
5. Use the timeline to prove visible trust progression.

## Technology Stack

### Frontend / IDE Layer
- VS Code Extension
- TypeScript
- Webview-based dashboard panels
- Editor diagnostics
- Status bar integration

### Backend / Service Layer
- Python
- Flask HTTP server
- MCP stdio server
- SQLite persistence

### Intelligence Layer
- multi-stage analysis pipeline
- specialist review stages for security, quality, and performance
- aggregation stage for unified trust judgment
- configurable provider support for local and hosted models

### Data / Product Layer
- file state storage
- revision event history
- dashboard summary generation
- trust scoring and diff calculation

## System Architecture
Savier operates as a closed-loop trust system:

1. The VS Code extension captures active file contents.
2. The backend receives the file via HTTP.
3. The analysis pipeline evaluates the file.
4. Results are normalized into findings, scores, summaries, and a primary issue.
5. The backend stores:
   - the latest file state
   - the revision event
   - developer history
6. The frontend fetches:
   - dashboard summary
   - file state
   - analysis timeline
7. The UI updates with the latest trust posture.
8. On the next revision, Savier computes trust movement from the prior state.

This architecture keeps the backend as the source of truth and prevents the extension from inventing its own scoring or diff logic.

## Agent Architecture
Savier uses a practical multi-stage reasoning pipeline rather than a single generic pass.

### Planning Stage
The planning stage interprets what the code is trying to do and identifies:

- developer intent
- possible entry points
- sensitive operations
- focus areas for later review

### Specialist Review Stages
Specialist stages evaluate distinct dimensions:

- **Security review**: unsafe query construction, shell execution, file misuse, exposed secrets, weak trust boundaries
- **Quality review**: maintainability, shared mutable state, oversized logic blocks, poor structure
- **Performance review**: repeated queries, nested loops, unbounded memory growth, blocking or wasteful behavior

### Aggregation Stage
The aggregation stage:

- merges specialist findings
- deduplicates overlaps
- selects the primary finding
- produces final trust scores
- builds dimension summaries
- generates a coherent explanation and suggested fix path

### Persistence Stage
After aggregation, Savier:

- stores the analysis as a revision event
- updates active file state
- powers dashboard and timeline views

This design makes the system explainable, revision-aware, and reusable through both HTTP and MCP.

## Backend Architecture
The backend is implemented in Python and serves as the product brain.

Its responsibilities include:

- loading configuration and model routing
- receiving and parsing analysis requests
- running the analysis pipeline
- computing trust scores
- computing revision deltas
- persisting file state and analysis history
- exposing HTTP endpoints
- exposing MCP tools

Key backend components:

- `appsec_agent/services/analysis.py`
- `appsec_agent/memory/store.py`
- `appsec_agent/http_server.py`
- `appsec_agent/server.py`

## Frontend / Extension Architecture
The VS Code extension is intentionally thin and product-facing.

Its responsibilities include:

- observing active editor changes
- triggering analysis with debouncing
- sending requests to the backend
- rendering diagnostics
- rendering dashboard webviews
- showing trust posture in the status bar
- fetching dashboard, file-state, and timeline data

Key extension concepts:

- `DocumentAnalyzer` for active-file analysis flow
- `AppSecApiClient` for backend HTTP communication
- state store for panel state and latest results
- Trust Cockpit and Active File State webviews
- status bar trust state updates

## MCP Integration
Savier exposes the same analysis engine through an MCP server named `appsec-agent`.

Primary MCP tools:

- `analyze_code`
- `get_dashboard`
- `get_analysis_timeline`
- `get_file_state`
- `get_developer_history`
- `clear_developer_history`

Why MCP matters:

- allows AI agents to access the same trust logic as the IDE
- makes Savier usable in agent-assisted workflows
- supports future automation beyond the VS Code extension

## Data Flow
The product data flow is:

1. code content enters from the active file or an MCP caller
2. request is parsed into a normalized analysis request
3. planning stage adds intent and code context
4. specialist stages produce dimension-specific findings
5. aggregation stage produces:
   - merged findings
   - primary finding
   - explanation
   - scores
6. persistence layer stores:
   - active file state
   - analysis event
   - developer history entry
7. UI or MCP clients fetch:
   - dashboard summary
   - timeline
   - file state

## Persistence and Revision Model
Savier is revision-aware by design.

It stores:

- developer findings history
- analysis events
- latest file state

Each file analysis can be compared against the previous state for that file to compute:

- fixed findings
- new findings
- unchanged findings
- trust score delta

This enables Savier to tell the user not just what is wrong, but whether the latest revision improved trust.

## Trust Scoring Model
Savier computes four scores:

- security
- quality
- performance
- overall

Findings are normalized into issue types and severities. Those severities influence dimension scores. The overall score provides a single trust signal, while the dimension breakdown preserves detail.

This gives the product two levels of usefulness:

- a quick judge-friendly or developer-friendly headline score
- a more technical explanation beneath it

## Dashboard and UI Surfaces

### Trust Cockpit
Main presentation surface showing:

- primary trust shift
- narrative framing
- current file posture
- revision delta
- dimension breakdown
- active findings
- revision timeline
- workspace posture
- analysis profile
- technical trace

### Active File State
Focused file-level view showing:

- active file scores
- primary issue
- dimension evidence
- open findings
- analysis profile
- latest trace

### Developer History
History-oriented view for recent findings and recurring issue patterns.

### In-Editor Diagnostics
Highlights issues directly in the active code file.

### Status Bar
Shows:

- ready
- analyzing
- clean
- issue found
- partial
- backend unavailable
- trust-up states after revision improvement

## Demo Story
The strongest Savier demo follows a simple arc:

1. Open flawed code.
2. Let Savier analyze it.
3. Show low trust score and active findings.
4. Highlight security, quality, and performance breakdown.
5. Improve the code.
6. Re-run analysis.
7. Show positive delta, fixed findings, and updated trust posture.

This demo is powerful because it makes trust movement visible rather than theoretical.

## Innovation and Differentiation
Savier’s innovation is not just that it finds issues. Its innovation is how and when it does so.

### Key differentiators
- **Pre-hoc trust verification**
  - trust is evaluated before code becomes deeply embedded in the workflow
- **One trust surface across multiple dimensions**
  - security, quality, and performance are judged together
- **Revision-aware analysis**
  - Savier compares revisions, not just files in isolation
- **Backend-driven source of truth**
  - frontend surfaces remain consistent because trust logic stays centralized
- **Human + agent compatibility**
  - extension users and MCP agents use the same backend
- **Real-time editor integration**
  - trust feedback appears where code is being written

### Why this is stronger than a linter or scanner
- a linter applies static rules
- a traditional scanner usually runs later
- Savier is a productized trust layer with memory, scoring, and revision-awareness

## Impact

### Individual Developer Impact
- reduces uncertainty around AI-generated code
- keeps remediation in hot context
- shortens the loop from issue discovery to correction
- provides a measurable sense of progress

### Team and Workflow Impact
- helps teams adopt AI coding tools more safely
- supports consistent trust evaluation across revisions
- provides clearer posture for evolving files
- can grow into broader governance and workflow support

### Ecosystem Impact
- lays groundwork for trust infrastructure in agent-assisted development
- provides a reusable analysis layer for future agentic systems
- makes “trust before adoption” a practical development concept

## Scalability and Future Roadmap
Savier starts with file-level trust evaluation but is designed to expand.

Potential next directions:

- project-wide dashboards
- team and repository trust posture
- CI/CD trust gates
- auto-fix suggestions
- richer file identity and cross-surface continuity
- agent benchmarking based on trust improvements
- stronger project-context reasoning

## Conclusion
Savier is a real-time trust cockpit for AI-assisted development. It helps developers evaluate code as it is being created, not after it has already spread through the workflow. By combining multi-dimensional analysis, revision-aware scoring, a backend-driven dashboard, and MCP support, Savier turns code review into a clearer and more actionable trust loop.

Savier is not just another scanner. It is the trust layer for AI-assisted coding.
