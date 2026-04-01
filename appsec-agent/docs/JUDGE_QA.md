# Savier Judge Summary and Q&A

## One-Paragraph Project Summary
Savier is a real-time trust layer for AI-assisted software development. It helps developers evaluate whether code should be trusted while it is still being written or generated, instead of waiting for post-hoc scanning after commit or CI. Savier works inside VS Code, analyzes code across security, quality, and performance, computes trust scores and revision deltas, and shows how trust changes across revisions through a backend-driven dashboard. The same backend is also accessible through MCP, making Savier compatible with both human and agent workflows.

## One-Line Core Thesis
**AI helps developers write code faster, but Savier helps them trust code faster.**

## Three Strongest Differentiators

### 1. Pre-hoc trust verification
Savier evaluates code while it is still in the editor, not only after it reaches pull requests or CI/CD.

### 2. Multi-dimensional trust in one product
It combines security, quality, and performance into one coherent trust surface instead of forcing developers to interpret disconnected tools.

### 3. Revision-aware judgment
Savier does not just say what is wrong. It shows whether the latest revision improved or regressed trust.

## Three Strongest Technical Proof Points

### 1. Backend-driven source of truth
The Python backend computes findings, scores, diffs, file state, and timeline history, while the extension renders that data consistently.

### 2. Specialist analysis pipeline
The system uses planning, specialist dimension reviews, and aggregation rather than one generic pass, leading to clearer trust output.

### 3. MCP support
The same trust engine is available both to the VS Code extension and to AI agents through MCP.

## Expected Judge Questions

### Why not just use existing scanners like Snyk or Semgrep?
Those tools are valuable, but they usually operate after code has already entered the workflow. Savier focuses on the earlier moment when code is still being written or accepted. The difference is not simply what gets scanned, but **when trust is evaluated**.

### How is this different from a linter?
A linter applies mostly static rules. Savier creates a broader trust judgment that includes multi-dimension findings, trust scoring, revision comparison, and a developer-facing explanation of whether the file is improving.

### Why does MCP matter here?
MCP allows the same Savier trust engine to be used by agents and automation, not just by a human inside the IDE. That makes Savier more future-ready for agentic software workflows.

### Why include quality and performance instead of only security?
Trust in code is broader than security. Developers also need to know whether code is maintainable and efficient. Savier’s strength is that it combines those concerns into one trust surface instead of treating them as separate tools.

### How does this scale beyond a single file demo?
The backend already tracks file state, revision history, and dashboard summaries. That foundation can naturally extend to project-level posture, team dashboards, CI/CD trust gates, and broader agent workflows.

### Why does this matter beyond a hackathon?
AI-assisted coding is becoming normal. As more code is generated quickly, developers need trust infrastructure, not just generation infrastructure. Savier is designed for that emerging need.

## Concise Answers For Live Use

### Why now?
Because AI coding speed has already increased, but trust verification has not kept up.

### What is the product in one sentence?
Savier is a real-time trust cockpit for AI-assisted coding.

### What is the strongest demo moment?
Showing a flawed file, revising it, and proving improvement through trust delta and revision history.

### What is the strongest product idea?
Trust before adoption.

### What is the strongest technical idea?
One backend-driven trust engine used by both the editor and MCP agent workflows.

## Memorable Lines To Reuse
- “Trust before adoption.”
- “Real-time code trust.”
- “Hot-context validation.”
- “Revision-aware developer feedback.”
- “Savier is not just a scanner. It is the trust layer for AI-assisted coding.”

## Closing Summary
Savier is compelling because it connects a clear modern problem with a practical product solution. AI-generated code is already here. The missing layer is trust. Savier provides that trust layer in a way that is visible, measurable, technically grounded, and demoable.
