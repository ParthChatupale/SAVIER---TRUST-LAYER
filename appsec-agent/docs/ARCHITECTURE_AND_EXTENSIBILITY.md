# Savier Architecture and Extensibility

## Overview
Savier is built as a shared trust backend for AI-assisted development. The system supports both developer-in-the-loop workflows inside VS Code and agent-driven workflows through MCP, while keeping trust scoring, findings, revision history, and file state centralized in one backend.

The architecture is designed around three principles:

- one backend, multiple entry points
- multi-stage trust analysis instead of a single monolithic review
- registry-driven extensibility for adding new agents and tools cleanly

## System Architecture
At the system level, Savier is organized into four layers.

### 1. Interaction layer
This is how code enters the product.

- VS Code Extension for editor-native analysis, diagnostics, and dashboard access
- Agent or MCP client for automated or agent-driven trust workflows

### 2. Interface layer
This layer exposes the shared backend through two public paths.

- HTTP API for the extension and dashboard-facing requests
- MCP Server for agent and tool-based access

### 3. Trust engine layer
This is the core backend where trust evaluation happens.

- request parsing and transport normalization
- analysis orchestration
- registry-driven pipeline execution
- model access for planning, review, and aggregation

### 4. State layer
This layer makes Savier revision-aware rather than stateless.

- SQLite-backed persistence
- latest file state tracking
- analysis event history
- developer history and trust progression

## Agent Architecture
Savier uses a staged multi-agent workflow rather than a single generic reviewer.

### Planning
The planning stage reads the code and builds shared context for downstream analysis. It identifies likely intent, sensitive operations, and the parts of the file that matter most for review.

### Specialist reviews
Three specialist reviewers evaluate the code independently:

- security review
- quality review
- performance review

This structure improves clarity because each agent focuses on one trust dimension instead of trying to make one overloaded judgment.

### Aggregation
The aggregation stage combines the specialist outputs into one final trust result. That result includes:

- unified findings
- dimension-aware trust signals
- primary issue prioritization
- revision-aware comparison against earlier state

## Technology Stack
Savier’s current implementation uses a focused full-stack set of technologies.

### Frontend and developer experience
- VS Code Extension for the product surface inside the editor
- VS Code API for commands, diagnostics, and editor integration
- TypeScript for extension logic and UI behavior
- Webviews for the Trust Cockpit and custom editor panels

### Backend and integration
- Python for backend logic, orchestration, and persistence
- Flask for HTTP endpoints used by the extension
- MCP protocol and MCP server support for agent access

### AI and code understanding
- LangChain for LLM-powered orchestration support
- NVIDIA-hosted LLMs for hosted inference
- Ollama for local-model inference
- Tree-sitter for syntax-aware code structure extraction

### Persistence
- SQLite for lightweight local persistence of trust state and analysis history

## Persistence and Revision Awareness
Persistence is a core part of the product, not an afterthought. Savier stores both current file posture and historical analysis events, which enables:

- trust deltas between revisions
- timeline views and trust progression
- repeat analysis with historical context
- future growth toward project-level and team-level trust reporting

This is what turns Savier from a one-shot analyzer into a continuous trust loop.

## Scalability Approach
Savier is designed to scale in both product surface and codebase structure.

### Shared backend model
The same backend powers:

- VS Code workflows through HTTP
- agent workflows through MCP
- dashboard and timeline views through persistent state

This avoids duplicated logic across interfaces.

### Modular pipeline stages
The trust pipeline is split into planning, specialist review, and aggregation stages. This makes it easier to:

- add or remove stages
- enable stages conditionally
- run compatible review stages in parallel
- evolve the product without rewriting the entire backend

### Configurable models and pipeline behavior
Provider selection, model routing, and pipeline configuration can be controlled through configuration, which makes the system easier to adapt across local and hosted environments.

## Extending Savier with New Agents
Savier already uses a registry-based architecture for analysis stages and MCP tools. The main extensibility point is the shared plugin registry used by the backend bootstrap and analysis service.

Core registry concepts:

- `AgentSpec` describes one analysis stage
- `ToolSpec` describes one MCP-exposed capability
- `AgentRegistry` stores enabled agents and tools

### How a new agent is added
Adding a new analysis stage follows a straightforward pattern:

1. Create a new agent module under the backend agent package.
2. Implement a runner that reads the execution context and produces a structured artifact.
3. Return an `AgentSpec` that defines the new stage’s name, order, model key, artifact key, and optional parallel group.
4. Register the new agent in the default agent registry/bootstrap flow.
5. If needed, wire the new stage into aggregation or downstream reporting.

This approach allows the pipeline to grow without hardcoding every stage directly into the server entrypoints.

### Good candidates for extension
The current architecture can naturally support additional stages such as:

- dependency review
- compliance review
- style or standards review
- project-wide trust summary
- auto-fix recommendation

## MCP and Multi-Surface Integration
MCP matters because it lets Savier expose the same trust engine beyond the editor. Instead of building a separate review path for agents, Savier reuses the same backend truth and returns the same kind of structured trust result across interfaces.

That means:

- developers and agents use the same evaluation logic
- trust scoring stays consistent across surfaces
- new MCP tools can be added without redesigning the server

## Implementation Notes
The current codebase reflects this architecture through a few clear responsibilities:

- bootstrap assembles the registry, providers, persistence, and services
- the analysis service orchestrates registered stages
- the memory layer stores file state and event history
- transport layers normalize HTTP and MCP requests into the same backend workflow

This is the key reason the system is both extensible and presentation-ready: the architecture is already modular in the implementation, not just in the diagrams.
