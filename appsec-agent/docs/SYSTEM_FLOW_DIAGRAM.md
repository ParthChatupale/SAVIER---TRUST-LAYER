# Savier System Flow Diagram

This document captures the main architectural flows in Savier using Mermaid diagrams so they can be viewed directly in GitHub, Markdown viewers, or copied into presentation material.

## 1. High-Level System Architecture

```mermaid
flowchart LR
    Dev[Developer / Agent] --> VSCode[VS Code Extension]
    Dev --> MCPClient[MCP Client / Agent Runtime]

    VSCode -->|HTTP analyze/dashboard/timeline/file-state| HTTP[Flask HTTP Server]
    MCPClient -->|MCP tool calls| MCP[appsec-agent MCP Server]

    HTTP --> Bootstrap[Bootstrap Layer]
    MCP --> Bootstrap

    Bootstrap --> AnalysisService[AnalysisService]
    Bootstrap --> Registry[AgentRegistry]
    Bootstrap --> Provider[Model Provider]
    Bootstrap --> Repo[SQLite Repository]

    Registry --> AnalysisService
    Provider --> AnalysisService
    Repo --> AnalysisService

    AnalysisService --> Repo
    AnalysisService --> HTTP
    AnalysisService --> MCP

    Repo --> Dashboard[Trust Cockpit / File State / Timeline]
    HTTP --> Dashboard
```

### What this shows
- The VS Code extension and MCP clients both use the same backend trust engine.
- The backend is assembled through the bootstrap layer.
- The registry, provider, and repository are shared dependencies of the analysis service.
- Persistence is not an afterthought; it directly powers dashboard and revision-aware views.

## 2. Runtime Analysis Flow

```mermaid
flowchart TD
    A[Code enters system] --> B{Entry path}
    B -->|VS Code| C[HTTP /analyze]
    B -->|Agent / MCP| D[MCP analyze_code]

    C --> E[parse_analysis_request]
    D --> E

    E --> F[AnalysisService.analyze]
    F --> G[Load developer history]
    G --> H[Create ExecutionContext]
    H --> I[Run registered pipeline]

    I --> J[Planning result]
    I --> K[Specialist review results]
    K --> L[Aggregation result]
    L --> M[Build findings + dimensions + primary finding]
    M --> N[Compute analysis profile]
    N --> O[Compute scores and revision diff]
    O --> P[Persist analysis event]
    P --> Q[Upsert latest file state]
    Q --> R[Return response]
```

### What this shows
- Both HTTP and MCP enter the same request normalization and analysis path.
- Analysis is context-aware because history is loaded before the pipeline runs.
- The returned result is not just findings; it also includes scores, revision diff, and analysis profile.

## 3. Agent Pipeline Flow

```mermaid
flowchart TD
    Start[ExecutionContext created] --> Plan[Planning Agent]
    Plan --> Parallel{Parallel review group?}

    Parallel --> Sec[Security Review]
    Parallel --> Qual[Quality Review]
    Parallel --> Perf[Performance Review]

    Sec --> Agg[Aggregation Agent]
    Qual --> Agg
    Perf --> Agg

    Agg --> Persist[Persistence + revision enrichment]
    Persist --> End[Final AnalysisResponse]
```

### What this shows
- Planning runs first and provides context.
- Specialist reviewers are independent and can run in parallel.
- Aggregation merges specialist outputs into one coherent trust result.
- Persistence and revision enrichment happen after aggregation.

## 4. Registry-Based Architecture

```mermaid
flowchart TD
    A[bootstrap.get_plugin_registry] --> B[Create AgentRegistry]
    B --> C[register_default_agents]
    B --> D[register_default_tools]

    C --> E[AgentSpec: planning]
    C --> F[AgentSpec: security_review]
    C --> G[AgentSpec: quality_review]
    C --> H[AgentSpec: performance_review]
    C --> I[AgentSpec: aggregation]

    D --> J[ToolSpec: analyze_code]
    D --> K[ToolSpec: get_dashboard]
    D --> L[ToolSpec: get_analysis_timeline]
    D --> M[ToolSpec: get_file_state]
    D --> N[ToolSpec: get_developer_history]
    D --> O[ToolSpec: clear_developer_history]
```

### What this shows
- Savier uses one registry object for both internal analysis stages and MCP-exposed tools.
- New agents and tools are added through registration, not by rewriting the whole server.
- This is the main extensibility mechanism in the current system.

## 5. How a New Agent Fits into the System

```mermaid
flowchart TD
    A[Create new agent module] --> B[Implement runner using ExecutionContext]
    B --> C[Return AgentSpec via get_agent_spec]
    C --> D[Add factory to agents/registry.py]
    D --> E[Enable in AppConfig / APPSEC_AGENT_PIPELINE]
    E --> F[Optional model config + fallbacks]
    F --> G[AnalysisService picks it up from AgentRegistry]
    G --> H[Agent runs in pipeline]
    H --> I[Optional aggregation integration]
    I --> J[User-visible results or internal artifact]
```

### What this shows
- New agents are added by registration and configuration.
- The analysis service does not need to be rewritten to support a new stage.
- A new stage can contribute internal artifacts, user-visible findings, or both.

## 6. Persistence and Revision-Aware Product Loop

```mermaid
flowchart LR
    A[Current code revision] --> B[Analyze]
    B --> C[Current findings]
    C --> D[Merge dimension scores]
    D --> E[Compare with previous file state]
    E --> F[Compute diff]
    F --> G[Store analysis event]
    G --> H[Update file state]
    H --> I[Dashboard / Timeline / Active File State]
    I --> J[Developer revises code]
    J --> A
```

### What this shows
- Savier is a feedback loop, not a one-shot scanner.
- Revision delta is a product feature built on top of persistence.
- The UI can prove improvement over time because state is stored between runs.

## 7. Suggested “Single Slide” Diagram for PPT
If you want only one diagram for a slide, this is the cleanest version:

```mermaid
flowchart LR
    Code[Developer or Agent writes code] --> Intake[VS Code Extension or MCP]
    Intake --> Backend[Shared Savier Backend]
    Backend --> Plan[Planning]
    Backend --> Reviews[Security + Quality + Performance Reviews]
    Reviews --> Agg[Aggregation]
    Agg --> State[Scores + Findings + Revision State]
    State --> UI[Trust Cockpit + File State + Timeline]
    UI --> Revise[Developer / Agent revises code]
    Revise --> Intake
```

### Suggested caption
Savier creates a closed trust loop where code is analyzed in context, judged across multiple dimensions, stored as revision-aware state, and fed back into the developer workflow.

## 8. Key Architectural Takeaways
- Savier uses a shared backend for both human and agent workflows.
- The system is registry-driven, which makes agent and tool addition clean.
- The pipeline is modular and supports parallel specialist reviews.
- Persistence makes the product revision-aware rather than stateless.
- The dashboard and timeline are powered by stored analysis state, not frontend-only logic.

