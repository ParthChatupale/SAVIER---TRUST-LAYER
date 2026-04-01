# Savier Scalability and Agent Integration

## Overview
This document explains two important parts of Savier’s architecture:

1. why the system is scalable as a product and as a codebase
2. how new agents can be added directly into the existing pipeline

The short answer is yes: Savier is already using a registry-based architecture for both analysis agents and MCP tools. That registry layer is one of the main reasons the system is extensible.

At the code level, the core extension points are built around:

- `AgentRegistry`
- `AgentSpec`
- `ToolSpec`
- registry bootstrap functions for default agents and tools

This means the system does not hardcode the full pipeline directly into the MCP server or HTTP entrypoint. Instead, it assembles the pipeline from registered components.

## Why Savier Is Scalable

### 1. Clear separation between product surfaces and trust logic
Savier’s VS Code extension is intentionally thin. It focuses on:

- editor integration
- dashboard rendering
- diagnostics
- status updates

The backend handles:

- analysis
- scoring
- revision diffs
- persistence
- timeline generation
- MCP access

This separation improves scalability because the trust engine can evolve without tightly coupling changes to the UI.

### 2. One backend powers multiple interfaces
The same backend service powers:

- the VS Code extension through HTTP
- MCP consumers through the MCP server
- dashboard and history views through repository-backed state

This is important for scale because Savier does not have one logic path for the editor and another for agents. It has one trust engine that can be reused across surfaces.

### 3. Pipeline stages are modular
The analysis flow is not implemented as one giant function. It is broken into stages:

- planning
- security review
- quality review
- performance review
- aggregation

Each stage is represented by an `AgentSpec`, which means stages can be:

- added
- removed
- reordered
- enabled or disabled
- run conditionally

That makes the system much easier to extend over time.

### 4. Parallel execution already exists
The analysis service supports `parallel_group` execution for registered agents. In practice, this means multiple independent specialist reviewers can be run concurrently when grouped together.

This is a strong scalability feature because it allows Savier to increase analysis breadth without forcing everything into one serial bottleneck.

### 5. Configurable pipeline and model routing
Savier’s config supports:

- selecting the provider
- choosing per-stage models
- enabling fallback models
- changing the enabled pipeline through configuration

This means scaling is not only about adding more code. It is also about evolving deployment strategies without rewriting the system.

### 6. Persistence makes the product scale beyond one-off scans
Savier stores:

- file state
- analysis events
- developer history

That makes it possible to scale from a single-file analyzer into:

- revision-aware feedback
- developer history
- project-level posture
- team-level reporting
- future trust dashboards and CI/CD workflows

### 7. Registry-driven MCP tools support future automation
The MCP server uses the same registry pattern for tools. This means Savier can expose new capabilities to agents without restructuring the server itself.

Examples of scalable future MCP additions:

- project-wide trust summary
- auto-fix recommendation
- trust trend reporting
- agent benchmarking tools

## The Current Registry Architecture

## Core objects
Savier’s extensibility is centered on `appsec_agent/core/plugins.py`.

The key types are:

### `AgentSpec`
Defines one analysis stage. It includes:

- `name`
- `stage`
- `order`
- `description`
- `input_type`
- `output_type`
- `model_config_key`
- `runner`
- `artifact_key`
- `should_run`
- `parallel_group`
- `review_dimension`
- `required`
- `enabled`

This structure is powerful because each stage is described declaratively, not just as an ad hoc function call.

### `ToolSpec`
Defines one MCP-accessible tool. It includes:

- `name`
- `description`
- `input_schema`
- `handler`
- `implementation_ref`
- `enabled`

This gives Savier the same style of registration for external capabilities as it uses for internal agent stages.

### `AgentRegistry`
This is the central registry object. It stores:

- `agents`
- `tools`

It provides:

- `register_agent`
- `register_tool`
- `get_enabled_agents`
- `get_enabled_tools`

This confirms that Savier is indeed using a registry architecture.

## Where registration happens

### Default analysis agents
The default analysis agents are registered in:

- `appsec_agent/agents/registry.py`

The current default pipeline is constructed from agent spec factories for:

- planning
- security review
- quality review
- performance review
- aggregation

### Default MCP tools
The default MCP tools are registered in:

- `appsec_agent/tools/registry.py`

That module currently exposes tools such as:

- `analyze_code`
- `get_dashboard`
- `get_analysis_timeline`
- `get_file_state`
- `get_developer_history`
- `clear_developer_history`

### Bootstrap layer
The registry is assembled in:

- `appsec_agent/bootstrap.py`

The bootstrap function:

- creates an `AgentRegistry`
- registers default agents
- registers default tools
- injects the registry into the `AnalysisService`
- reuses the same registry for MCP

That is what makes Savier cohesive: one bootstrap path, one registry, one backend truth.

## How the Pipeline Uses the Registry
`AnalysisService` takes the registry as a dependency and does not hardcode the pipeline stages inline.

The service:

- asks the registry for enabled agents
- runs them in order
- detects parallel groups
- records trace entries for each stage
- collects artifacts produced by stages
- continues into aggregation and persistence

This is a scalable pattern because the service is orchestrating registered behavior instead of owning every implementation detail.

## How to Add a New Agent Directly
Adding a new agent to Savier is straightforward because of the registry pattern.

## Step 1: Create a new agent module
Create a module under `appsec_agent/agents`, for example:

- `appsec_agent/agents/compliance_review.py`
- or `appsec_agent/agents/style_review.py`
- or `appsec_agent/agents/dependency_review.py`

This module should expose a `get_agent_spec()` function that returns an `AgentSpec`.

## Step 2: Implement the runner
The `runner` function should:

- accept an `ExecutionContext`
- read the request and any earlier stage artifacts
- call the configured provider if needed
- create a structured output
- store its result into `context.artifacts` using `artifact_key`

Good patterns to follow:

- planning-like agents set planning/context artifacts
- review agents produce dimension-specific findings
- post-processing agents can consume earlier artifacts

## Step 3: Define the `AgentSpec`
The new spec should define:

- a unique `name`
- the `stage`
- the `order`
- the model config key it uses
- its `artifact_key`
- whether it is required
- whether it belongs to a `parallel_group`
- its `review_dimension` if applicable

Example design choices:

- a new specialized review agent can share the same `parallel_group` as quality/performance/security if it is independent
- a later-stage agent can run after aggregation if it needs merged outputs
- an optional agent can use `required=False` so the pipeline can degrade gracefully

## Step 4: Register it in the default agent registry
Update `appsec_agent/agents/registry.py` and add the new `get_agent_spec` factory into `DEFAULT_AGENT_SPEC_FACTORIES`.

That is the current codebase’s main registration hook for default analysis stages.

## Step 5: Enable it in config
If the new agent should be part of the runtime pipeline, it must appear in the enabled agent list.

Today, that pipeline is driven by config through:

- `AppConfig.enabled_agents`
- `APPSEC_AGENT_PIPELINE`

That means you can:

- add the new stage as part of the default config
- or enable it selectively via environment configuration

## Step 6: Add model routing if needed
If the agent uses a new `model_config_key`, then the config layer should expose:

- the primary model variable
- optional fallback model variables

This keeps the new stage consistent with the rest of the pipeline.

## Step 7: Update aggregation if the agent contributes findings
If the new agent produces user-facing findings or contributes to trust scoring, then aggregation must understand its output.

Typical integration points include:

- aggregation logic
- dimension summaries
- score merging rules
- response serialization

In other words, adding a stage is easy at the registry level, but full product integration also requires deciding whether the new stage is:

- internal context only
- trace-only
- or part of the user-visible trust result

## Example Agent Categories That Fit Naturally
Because the architecture is registry-driven, Savier can evolve beyond the current three review dimensions.

Examples:

- compliance review
- dependency risk review
- code style review
- API misuse review
- privacy review
- cloud configuration review
- architecture smell review
- auto-fix recommendation stage

Some of these would behave like review agents, while others could behave like post-processing or advisory agents.

## How Agents Can Be Added for MCP Workflows
There are two distinct ways agents can be added into Savier:

### 1. Internal analysis agents
These are the pipeline stages described above. They change how Savier reasons about code.

### 2. External MCP tools
These are capabilities exposed through the MCP server. They do not have to be analysis stages themselves, but they can let other agents use Savier.

Examples of new MCP tools:

- `suggest_fix`
- `get_project_posture`
- `compare_revisions`
- `benchmark_agent_revision`
- `get_dimension_breakdown`

To add a new MCP tool:

1. create a `ToolSpec`
2. implement the handler
3. register it in `appsec_agent/tools/registry.py`

This means Savier is scalable not only in what it analyzes internally, but also in how outside agents can consume and orchestrate it.

## What “Directly Added” Means in Practice
If the question is whether a new agent can be added without rewriting the MCP server or the main analysis entrypoint, the answer is yes.

That is exactly the advantage of the current design:

- the MCP server calls the registry
- the analysis service calls the registry
- bootstrap assembles the registry once

So new capabilities are introduced by registering them, not by rewriting the whole system.

## Current Strengths of This Architecture
The current registry design already gives Savier several strong engineering properties:

- modularity
- easier onboarding for new stages
- safer experimentation
- pipeline configurability
- better separation of concerns
- cleaner MCP extensibility
- support for parallel review groups

This is a solid base for hackathon scale and also for future product growth.

## Current Limits to Be Aware Of
The current architecture is registry-based, but still mostly static by code registration. In its present form, new agents are added by editing the codebase and registering them in the default registry bootstrap path.

So Savier is not yet doing:

- dynamic plugin discovery from external packages
- hot-loaded third-party agents
- marketplace-style runtime plugin installation

That means the architecture is extensible, but within a controlled internal plugin model.

This is still a very good architecture for the current stage of the project because it stays simple, predictable, and demo-friendly.

## Why This Matters for the Project Story
This document supports an important product claim:

Savier is not a fixed one-purpose scanner. It is a trust platform with a registry-based backend that can grow by adding new reasoning stages and new MCP-accessible capabilities.

That gives Savier a strong long-term story:

- today: trust cockpit for active files
- next: richer trust dimensions and stronger agent workflows
- later: broader trust infrastructure for AI-assisted engineering systems

## Final Answer
Yes, Savier is using a registry architecture.

More specifically:

- analysis stages are registered through `AgentRegistry`
- MCP tools are registered through the same registry object
- bootstrap assembles the enabled platform from those registered specs
- `AnalysisService` orchestrates the registered agents
- the MCP server exposes the registered tools

That is exactly why the system is scalable and why new agents can be added directly into it in a clean way.
