# Savier Project Documentation

## Executive Summary
Savier is a real-time trust layer for AI-assisted software development. It helps developers evaluate whether code should be trusted while that code is still being written, generated, or revised inside the editor. Instead of relying on post-hoc validation after a pull request, after CI/CD, or after deployment, Savier moves trust verification directly into the coding loop.

Savier is built as a VS Code-first product with a Python backend that acts as the source of truth for analysis, trust scoring, revision history, file state, and dashboard summaries. The system evaluates code across three trust dimensions: security, quality, and performance. It then turns those findings into a single trust posture that developers can understand quickly, improve iteratively, and demonstrate clearly.

The same trust engine is accessible through both HTTP and MCP. This makes Savier useful for individual developers working in the editor, for hackathon teams needing fast feedback, and for future agent-based workflows where AI systems need the same trust judgment that humans do.

At its core, Savier exists to solve a simple but growing mismatch: AI can generate code instantly, but developers still cannot verify its trustworthiness instantly.

## Problem Statement
AI coding assistants have dramatically accelerated software development. Developers can now prompt copilots, generate a feature in seconds, and move on almost immediately. However, the speed of trust verification has not kept up with the speed of code generation.

Most existing tools validate code too late in the lifecycle:

- static analyzers often run after code is already in the project
- security scanners commonly operate during review or CI/CD
- many AI coding tools optimize for correctness or speed, not trustworthiness

This creates a broader trust gap. The problem is not just that insecure code may slip through. The deeper issue is that untrusted code is often adopted before it is properly evaluated.

That gap affects several dimensions at once:

- security risks can spread downstream before anyone notices
- maintainability issues become harder to unwind once other code depends on them
- performance inefficiencies remain hidden until scale exposes them
- developers lose context by the time they return to fix earlier AI-generated code

Savier addresses this problem by bringing trust verification into the moment of code adoption, when the developer is still in context and the cost of correction is still low.

## Why Now
AI-assisted coding is moving from novelty to default workflow. Developers are increasingly working with Copilot-style tools, chat-driven code generation, and agentic editing experiences. As generation becomes faster and more capable, the burden shifts to developers to decide whether generated code should be accepted, revised, or rejected.

Current tooling is still optimized for late-stage validation:

- post-hoc scanning after code is written
- fragmented tooling for security, quality, and performance
- limited revision awareness inside the editor

Savier is designed for the moment that existing tools miss: the point between code generation and code adoption. That makes it especially relevant now, when software teams are moving toward human-plus-AI development workflows but still lack strong trust infrastructure.

## Core Thesis
Savier is built around one central idea:

**AI helps developers write code faster, but not trust code faster.**

The product thesis is that trust verification should happen:

- in context
- before adoption
- inside the editor
- across multiple dimensions
- with revision-aware feedback instead of isolated one-off alerts

Savier therefore treats trust as a product surface, not as a background utility.

## Product Vision
Savier aims to become trust infrastructure for AI-assisted development. In the current form, it operates as a trust cockpit for active files and evolving revisions. Over time, the same foundation can expand into broader workflow infrastructure.

Near-term product value:

- real-time trust analysis in VS Code
- unified trust posture across security, quality, and performance
- revision-aware comparisons for active files
- clear evidence for demos, judges, and developer decision-making

Long-term direction:

- project-level trust dashboards
- team-wide posture and trend analysis
- CI/CD trust gates
- auto-fix recommendation workflows
- agent benchmarking based on trust improvement

The vision is not to replace AI coding tools. It is to make those tools safer, more accountable, and more practical to use in real development environments.

## Target Users
Savier is designed for several overlapping user groups.

### Developers using AI coding tools
These users need fast trust feedback while accepting or revising generated code.

### Hackathon teams and rapid-build teams
These users move quickly and need a way to validate code quality without slowing the whole workflow down.

### Student developers and learners
These users benefit from seeing trust feedback early and in context, which reinforces better coding habits.

### Engineering teams exploring agentic workflows
These users need a shared trust layer that can be used by both humans and agents.

### Technical leads and reviewers
These users need clearer signals about whether a change is improving or regressing the trust posture of the code.

## End-to-End Workflows
Savier is designed around practical workflows rather than isolated analysis calls.

### Workflow 1: Developer-in-the-loop trust checking
1. The developer writes or pastes code in VS Code.
2. Savier analyzes the active file after a short debounce.
3. Diagnostics highlight relevant issues in the editor.
4. The Trust Cockpit shows the current trust posture.
5. The developer revises the code.
6. Savier re-analyzes and shows whether trust improved, regressed, or stayed the same.

### Workflow 2: Agent-assisted trust evaluation
1. An agent generates or modifies code.
2. The same backend is invoked through MCP.
3. Savier returns structured findings, scores, explanations, and revision-aware context.
4. The result can be used by agent workflows, orchestration logic, or future automation.

### Workflow 3: Demo and judge-facing proof
1. Start with intentionally flawed code.
2. Show low trust and visible findings.
3. Improve the code.
4. Show positive delta, fewer findings, and a stronger current posture.
5. Use the timeline to prove that trust improvement is measurable.

## Technology Stack
Savier uses a stack chosen for speed, clarity, local usability, and strong demoability.

### Frontend / IDE Layer
- VS Code Extension
- TypeScript
- Webview-based dashboard panels
- Editor diagnostics
- Status bar trust indicators

This layer provides the user-facing product experience. It stays intentionally lightweight and delegates trust logic to the backend.

### Backend / Service Layer
- Python
- Flask HTTP server
- MCP stdio server
- SQLite persistence

This layer serves as the system of record. It receives requests, runs analysis, stores state, and serves dashboard and timeline data.

### Intelligence / Analysis Layer
- multi-stage analysis pipeline
- planning stage
- specialist review stages
- aggregation stage
- configurable provider support

This layer turns raw code into structured trust judgments.

### Data / Product Layer
- file state persistence
- revision event history
- dashboard summaries
- trust scoring
- revision diff calculation

This layer makes Savier revision-aware rather than stateless.

## System Architecture
Savier operates as a closed-loop trust system.

1. The VS Code extension captures the active file contents.
2. The backend receives the file through HTTP.
3. The analysis pipeline evaluates the code.
4. Findings, summaries, scores, and a primary issue are produced.
5. The backend stores the latest file state and revision event.
6. The UI fetches dashboard, file-state, and timeline data.
7. The developer or agent revises the code.
8. Savier evaluates the next revision relative to the prior one.

This architecture creates a continuous feedback loop instead of a one-off scan. It also keeps trust logic centralized in the backend, so the extension remains consistent with the dashboard and MCP surfaces.

## Agent Architecture
Savier uses a practical multi-stage reasoning pipeline.

### Planning Stage
The planning stage interprets what the code is trying to do and identifies:

- likely developer intent
- entry points
- sensitive operations
- focus areas for later review

### Specialist Review Stages
Specialist review stages evaluate distinct trust dimensions.

- **Security review** looks for risky data flow, unsafe execution, exposed secrets, weak trust boundaries, and other vulnerable patterns.
- **Quality review** focuses on maintainability, shared mutable state, poor structure, and code-health issues.
- **Performance review** focuses on repeated work, inefficient logic, unbounded growth, and avoidable runtime overhead.

### Aggregation Stage
The aggregation stage:

- merges specialist findings
- deduplicates overlaps
- selects the primary issue
- computes trust scores
- builds dimension summaries
- generates the final explanation and fix guidance

### Persistence Stage
After aggregation, Savier:

- stores the revision as an analysis event
- updates the latest file state
- powers dashboard, timeline, and history surfaces

This design gives Savier clearer reasoning than a single generic pass while still producing one coherent result for the user.

## Backend Architecture
The backend is implemented in Python and serves as the product brain.

Its responsibilities include:

- loading configuration and provider routing
- receiving and parsing analysis requests
- running the staged analysis pipeline
- computing trust scores and revision deltas
- persisting state and history
- exposing HTTP endpoints
- exposing MCP tools

Key backend areas include:

- `appsec_agent/services` for orchestration
- `appsec_agent/agents` for planning, specialist reviews, and aggregation
- `appsec_agent/memory` for SQLite persistence
- `appsec_agent/providers` for provider-specific model integrations
- `appsec_agent/transports` for request parsing and response handling
- `appsec_agent/http_server.py` for HTTP entrypoints
- `appsec_agent/server.py` for MCP server entrypoints

The backend is the source of truth for findings, scoring, revision history, and dashboard posture.

## Frontend / VS Code Extension Architecture
The VS Code extension is intentionally thin and product-facing.

Its responsibilities include:

- watching active editor changes
- debouncing analysis requests
- sending code to the backend
- rendering diagnostics inside the editor
- rendering dashboard webviews
- showing trust posture in the status bar
- refreshing file-state and timeline views

Key frontend areas include:

- `src/extension.ts` for activation and command wiring
- `src/services` for request flow and API communication
- `src/editor` for diagnostics
- `src/ui` for the Trust Cockpit and related panels
- `src/core` for contracts and configuration
- `src/test` for extension verification

The extension does not invent trust logic locally. It renders the backend’s view of the file.

## MCP Integration
Savier exposes the same trust engine through an MCP server named `appsec-agent`.

Primary MCP tools include:

- `analyze_code`
- `get_dashboard`
- `get_analysis_timeline`
- `get_file_state`
- `get_developer_history`
- `clear_developer_history`

MCP matters because it allows the same trust logic to be used by:

- the VS Code extension
- human developers
- AI agents
- future automation workflows

This makes Savier future-ready for agent-assisted development rather than limited to a single UI surface.

## Data Flow and Persistence
Savier’s core data flow is:

1. Code enters from an active editor file or an MCP caller.
2. The request is normalized into a common analysis shape.
3. The planning stage builds contextual understanding.
4. Specialist stages produce dimension-specific findings.
5. Aggregation produces merged findings, scores, summaries, and a primary issue.
6. Persistence stores:
   - the active file state
   - the revision event
   - developer history
7. UI surfaces or MCP callers request dashboard, timeline, and file-state views.

This persistence model is central to the product. It makes revision-aware trust movement possible instead of treating every analysis as a stateless standalone event.

## Trust Scoring and Revision Awareness
Savier evaluates trust across three dimensions:

- security
- quality
- performance

For each analysis, the backend computes:

- dimension-level findings
- dimension-level summaries
- per-dimension scores
- overall trust score

The backend also compares the current revision against the prior stored file state and computes:

- fixed findings
- new findings
- unchanged findings
- score delta

This creates one of Savier’s strongest product differentiators: the ability to show whether the latest code revision actually improved trust.

## Dashboard and UI Surfaces
Savier presents trust through multiple coordinated UI surfaces.

### Trust Cockpit
The main dashboard surface shows:

- overall trust score
- dimension breakdown
- primary finding
- current posture
- revision delta
- active findings
- revision timeline
- workspace posture
- analysis profile

### Active File State
This surface focuses on the current file:

- latest file posture
- dimension summaries
- active findings
- current trust scores

### Developer History and Timeline
These surfaces show how trust evolves across revisions and help prove improvement over time.

### Editor Diagnostics
Findings are rendered directly in the editor so the user can see trust issues where they occur.

### Status Bar
The status bar provides quick posture feedback, such as:

- analyzing
- improved
- issue found
- partial
- unavailable

Together, these surfaces make Savier feel like a trust cockpit rather than a background scanner.

## Demo Narrative
Savier’s strongest live-demo story is a before-and-after trust loop.

### Demo arc
1. Open flawed code.
2. Let Savier analyze it immediately.
3. Show the Trust Cockpit, low trust score, and active findings.
4. Revise the file.
5. Re-run analysis.
6. Show improved trust score, reduced findings, and positive revision delta.
7. Use the timeline to prove visible trust progression.

### Why this works
This narrative shows:

- real-time analysis
- multi-dimensional trust
- revision-aware feedback
- practical value in AI-assisted workflows

It gives judges and teammates a concrete way to understand the product without needing deep backend detail.

## Setup and Usage Summary
Savier currently spans two local projects:

- backend and MCP server: `/home/parth/workspace/Savier/appsec-agent`
- VS Code extension frontend: `/home/parth/workspace/Savier/appsec-interceptor`

### Backend setup
Typical backend requirements:

- Python 3.11+
- local `.venv`
- provider credentials if using NVIDIA-backed models

Useful environment variables include:

- `APPSEC_AGENT_PROVIDER`
- `NVIDIA_API_KEY`
- `NVIDIA_BASE_URL`
- `APPSEC_AGENT_DB_PATH`
- `APPSEC_AGENT_PIPELINE`

Backend server command:

```bash
cd /home/parth/workspace/Savier/appsec-agent
APPSEC_AGENT_PROVIDER=nvidia .venv/bin/python -m appsec_agent.http_server
```

MCP server command:

```bash
cd /home/parth/workspace/Savier/appsec-agent
.venv/bin/python -m appsec_agent.server
```

### Extension setup
Compile the extension:

```bash
cd /home/parth/workspace/Savier/appsec-interceptor
npm run compile
```

Then launch the Extension Development Host from VS Code.

Important extension settings:

- `appsecInterceptor.serverUrl`
- `appsecInterceptor.developerId`
- `appsecInterceptor.mode`
- `appsecInterceptor.autoAnalyze`
- `appsecInterceptor.debounceMs`
- `appsecInterceptor.requestTimeoutMs`

### Testing
Backend tests:

```bash
cd /home/parth/workspace/Savier/appsec-agent
.venv/bin/python -m unittest discover -s tests -v
```

Extension tests:

```bash
cd /home/parth/workspace/Savier/appsec-interceptor
npm run compile
node ./out/test/runUnitTests.js
```

This setup model keeps the project easy to demo, extend, and hand off.

## Innovation and Differentiation
Savier’s innovation is practical rather than novelty-driven.

### Pre-hoc trust verification
Most tools validate code after it has already entered the workflow. Savier evaluates code before it is deeply adopted.

### One trust surface across multiple dimensions
Instead of forcing developers to combine separate security, quality, and performance tools mentally, Savier presents one coherent trust posture.

### Revision-aware evaluation
Savier does not just report what is wrong. It shows whether the latest revision improved or regressed trust.

### Backend-driven source of truth
The backend computes findings, scores, diffs, and timelines, while the frontend presents them consistently.

### Human and agent compatibility
Through MCP, the same trust engine is reusable by AI agents and future automation workflows.

### Real-time editor integration
Trust feedback appears where code is being actively written, not only in distant review pipelines.

This combination is what makes Savier feel like trust infrastructure rather than a narrow code scanner.

## Impact
Savier creates value at three levels.

### Individual developer impact
- reduces uncertainty in AI-assisted coding
- keeps remediation in hot context
- shortens time from code creation to trustworthy judgment
- helps developers understand whether the latest revision is actually better

### Team and workflow impact
- improves confidence in rapid iteration
- helps teams discuss revision quality more clearly
- supports demos, reviews, and internal decision-making
- creates a bridge between developer tooling and agent-assisted workflows

### Broader ecosystem impact
- supports safer adoption of AI-generated code
- lays groundwork for trust-aware automation
- points toward future CI/CD trust gates and team dashboards
- helps define what trust infrastructure could look like in AI-native software development

## Scalability and Future Roadmap
Savier starts with active-file trust evaluation, but the design supports broader expansion.

Scalable characteristics already present:

- file-level analysis keeps the experience fast and focused
- SQLite persistence supports repeated revisions over time
- one backend powers multiple UI surfaces consistently
- MCP opens the door for wider automation and agent integration

Natural future directions:

- project-level posture dashboards
- team trend views
- CI/CD trust gates
- auto-fix and remediation workflows
- benchmarking of human and agent-generated revisions

Savier is therefore well positioned to grow from a hackathon-ready demo into a broader trust platform.

## Judge Summary and Q&A
### One-paragraph summary
Savier is a real-time trust layer for AI-assisted software development. It helps developers evaluate whether code should be trusted while it is still being written or generated, instead of waiting for post-hoc scanning after commit or CI. Savier works inside VS Code, analyzes code across security, quality, and performance, computes trust scores and revision deltas, and shows how trust changes across revisions through a backend-driven dashboard. The same backend is also accessible through MCP, making Savier compatible with both human and agent workflows.

### One-line thesis
**AI helps developers write code faster, but Savier helps them trust code faster.**

### Three strongest differentiators
- pre-hoc trust verification inside the workflow
- multi-dimensional trust in one product
- revision-aware judgment instead of isolated alerts

### Three strongest technical proof points
- backend-driven source of truth
- specialist analysis pipeline
- MCP support for human and agent workflows

### Common judge questions
**Why not just use existing scanners?**  
Existing scanners are valuable, but they usually operate after code has already entered the workflow. Savier focuses on the earlier moment when the developer is deciding whether to trust the current code.

**How is this different from a linter?**  
A linter applies mostly static rules. Savier produces a broader trust judgment that includes multi-dimension findings, scoring, revision comparison, and dashboard-level explanation.

**Why does MCP matter?**  
MCP lets the same trust engine be used by AI agents and automation, not just by a human in the IDE.

**Why include quality and performance instead of only security?**  
Trust in code is broader than security. Developers also need to know whether code is maintainable and efficient.

**How does this scale beyond a single demo?**  
The backend already stores file state, revision history, and dashboard summaries, which naturally support broader project and team-level trust products.

## Conclusion
Savier is designed for a world where AI can generate code instantly but developers still need help deciding whether that code should be trusted. By bringing trust verification into the editor, evaluating code across security, quality, and performance, and showing how trust changes across revisions, Savier turns code review into a visible, measurable feedback loop.

It is not just a scanner. It is a trust cockpit for AI-assisted coding.
