# Savier Presentation Content

This document maps directly to the fixed SunHacks slide structure. Each section includes:

- slide title
- final slide text
- extended explanation
- speaker notes
- one emphasis line

## 1. Title

### Final slide text
**Savier**  
**A Real-Time Trust Cockpit for AI-Assisted Code**

AI helps developers write code faster, but not trust code faster.

Savier brings real-time trust analysis for **security, quality, and performance** directly into VS Code.

### Extended explanation
Savier is positioned as a trust layer for modern software development. Instead of focusing only on whether code runs, the product focuses on whether the code should be trusted while it is still being actively written or generated with AI support.

### Speaker notes
- Open with the shift from traditional coding to AI-assisted coding.
- Say that code generation speed has increased, but trust verification speed has not.
- Introduce Savier as the bridge between those two.

### Emphasis line
**Savier is the trust layer between AI-generated code and real developer adoption.**

## 2. Problem Statement

### Final slide text
AI coding tools generate code rapidly, but developers still lack an immediate way to verify whether that code is trustworthy.

Today, most validation is post-hoc:

- after commit
- after pull request
- after CI/CD
- after context is already cold

This creates a trust gap:

- risky code enters the workflow too easily
- maintainability and performance issues are accepted too early
- developers only revisit problems later, at higher cost

**Developers can generate code instantly, but they still cannot verify its trustworthiness instantly.**

### Extended explanation
The real problem is broader than security alone. AI-generated code is often adopted before it is deeply evaluated. Existing tools are valuable, but they usually operate too late in the flow. Savier addresses the missing moment between code generation and code adoption.

### Speaker notes
- Explain that the product does not assume AI code is always bad.
- The issue is speed mismatch: generation is instant, trust verification is delayed.
- Mention that this delay creates downstream cost in security, quality, and performance.

### Emphasis line
**The problem is not just insecure code. The problem is untrusted code being adopted before it is properly evaluated.**

## 3. Technology Stack

### Final slide text
**Frontend / IDE Layer**
- VS Code Extension
- TypeScript
- Webview dashboard panels
- Editor diagnostics and status bar integration

**Backend / Service Layer**
- Python
- Flask HTTP server
- MCP server
- SQLite persistence

**Intelligence / Analysis Layer**
- specialist review pipeline
- aggregation-based trust judgment
- configurable provider support
- revision tracking and scoring

### Extended explanation
The stack is intentionally split between a lightweight, product-facing extension and a backend that acts as the source of truth. The extension handles interaction and visualization, while the backend handles analysis, scoring, persistence, and MCP access.

### Speaker notes
- Say the extension is thin by design.
- Mention that Savier keeps trust logic centralized in the backend.
- Note that MCP gives the same trust engine to AI agents and tools beyond the extension.

### Emphasis line
**The stack was chosen for speed, local usability, and strong live-demo capability.**

## 4. System Architecture

### Final slide text
**Closed-loop trust system**

1. Developer writes or pastes code in VS Code
2. Extension captures the active file
3. Backend analyzes the file
4. Backend stores file state and revision events
5. Dashboard updates with trust score and findings
6. Developer or agent revises the code
7. Savier shows whether trust improved or regressed

Core components:
- VS Code extension
- HTTP API layer
- MCP access path
- persistence layer
- dashboard, timeline, and file-state surfaces

### Extended explanation
Savier is not just a scanner that returns a result. It is a continuous feedback loop. Every analysis becomes part of a broader trust story for that file, which lets the user understand not just the current issues, but whether the latest revision moved the code in the right direction.

### Speaker notes
- Explain that the same backend powers both the extension and dashboard.
- Mention that Savier is revision-aware, not just file-aware.
- Point out that this creates a measurable history of trust movement.

### Emphasis line
**Savier turns every code revision into a trust event, not just a one-off scan.**

## 5. Proposed Solution

### Final slide text
Savier is a real-time trust layer for AI-assisted coding.

It provides:
- real-time analysis in the editor
- multi-dimensional review:
  - security
  - quality
  - performance
- trust scoring
- active findings
- revision delta
- timeline of change
- backend-driven dashboard
- MCP support for agent workflows

Why it matters:
- trust becomes visible
- improvement becomes measurable
- feedback stays in hot context

### Extended explanation
Traditional tools tell developers what is wrong after the fact. Savier shows whether the current code is becoming more trustworthy while the developer is still working on it. This makes the product especially useful in AI-assisted workflows where code arrives quickly and must be judged quickly.

### Speaker notes
- Stress that Savier does not just list issues.
- It also shows whether the latest code revision improved trust.
- This is the strongest product differentiator for the demo.

### Emphasis line
**Existing tools tell you what is wrong after the fact. Savier tells you whether the current code is becoming more trustworthy while you are still writing it.**

## 6. Agent Architecture

### Final slide text
**Practical reasoning pipeline**

**Planning stage**
- understands what the code is trying to do
- identifies entry points and sensitive operations

**Specialist review stages**
- security review
- quality review
- performance review

**Aggregation stage**
- merges findings
- selects the primary issue
- creates the final explanation
- computes trust scores and summaries

**Persistence stage**
- stores revision event
- updates active file state
- powers dashboard and timeline

### Extended explanation
Savier uses specialist analysis rather than one generic pass. That makes the results clearer and more useful to developers. Parallel review improves responsiveness, while aggregation ensures the final output still feels like one coherent trust judgment rather than a set of disconnected warnings.

### Speaker notes
- Keep this slide high-level.
- Focus on the practical reasoning flow, not abstract multi-agent terminology.
- Mention that MCP allows the same intelligence path to be reused by AI agents.

### Emphasis line
**This is not multi-agent for novelty. It is a practical pipeline designed for trustworthy developer feedback.**

## 7. Scalability & Impact

### Final slide text
**Scalability**
- file-level analysis keeps the experience fast
- backend persistence supports repeated revisions
- modular architecture enables project and team expansion
- MCP enables wider automation and agent integration
- backend-driven scoring keeps all surfaces consistent

**Impact**
- reduces uncertainty in AI-assisted coding
- shortens time between writing code and understanding risk
- improves code quality before issues spread downstream
- helps teams reason about revision quality, not just final output
- builds a foundation for safer agentic software development

Future directions:
- CI/CD trust gates
- auto-fix workflows
- project posture dashboards
- team trend views
- agent benchmarking

### Extended explanation
Savier starts as a file-level trust product, but its design supports much broader evolution. Because it already stores revision history, scores, and file state, it can grow naturally into team-facing and workflow-facing infrastructure.

### Speaker notes
- Show that the project is useful today but extensible tomorrow.
- Judges should feel this is both demoable and future-relevant.

### Emphasis line
**Savier scales from a single file review to a trust layer for the full AI-assisted development lifecycle.**

## 8. Conclusion

### Final slide text
Savier helps developers trust AI-generated code in real time.

Key takeaways:
- real-time trust analysis in VS Code
- security, quality, and performance in one view
- revision-aware scoring and history

As AI writes more code, trust infrastructure becomes essential.

**Savier is not just a scanner. It is the trust layer for AI-assisted coding.**

### Extended explanation
The future of software development is not just about generating code faster. It is about deciding which code deserves trust. Savier is built to support that shift by making trust visible, measurable, and actionable within the workflow itself.

### Speaker notes
- End by restating the problem-speed mismatch.
- Close on the idea that trust infrastructure is becoming necessary as AI-assisted development grows.

### Emphasis line
**The future of AI-assisted coding needs trust infrastructure, and Savier is built to be that layer.**
