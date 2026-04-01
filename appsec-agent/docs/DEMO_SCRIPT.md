# Savier Demo Script

## Demo Objective
Show that Savier can:

- analyze code in real time inside VS Code
- identify trust issues across security, quality, and performance
- show a clear trust score and dimension breakdown
- prove whether the latest revision improved or regressed trust

The demo should make judges feel that Savier is:

- practical
- understandable
- technically credible
- useful in real AI-assisted workflows

## Recommended Demo Setup

### Backend
Run the backend HTTP server:

```bash
cd /home/parth/workspace/Savier/appsec-agent
APPSEC_AGENT_PROVIDER=nvidia .venv/bin/python -m appsec_agent.http_server
```

If using a local provider instead:

```bash
cd /home/parth/workspace/Savier/appsec-agent
.venv/bin/python -m appsec_agent.http_server
```

### Extension
Open the VS Code extension project:

```bash
cd /home/parth/workspace/Savier/appsec-interceptor
npm run compile
```

Then launch the Extension Development Host from VS Code and ensure:

- `appsecInterceptor.serverUrl` points to `http://127.0.0.1:5000`
- `appsecInterceptor.mode` is `full`
- auto analysis is enabled

## Recommended Demo File
Use a file that contains:

- at least one obvious security issue
- at least one quality issue
- at least one performance issue

Best options:

- `/home/parth/buggy_code_test.py`
- or a smaller custom `demo.py` with clear before/after revisions

For a short, clean demo, a smaller intentionally flawed file is easier to explain.
For a more powerful demo, `buggy_code_test.py` shows broader system coverage.

## Main Demo Story

### Story Arc
1. Start with flawed code.
2. Savier analyzes it.
3. Show low trust and visible findings.
4. Improve the code.
5. Savier re-analyzes.
6. Show trust improvement through delta and timeline.

### What the story proves
- Savier works in real time
- Savier evaluates more than just security
- Savier keeps trust evaluation inside the coding loop
- Savier makes improvement measurable

## Demo Flow

### Step 1: Introduce the problem
What to show:
- the code file open in VS Code
- ideally a file with obvious risky patterns

What to say:
“AI can generate or accelerate code instantly, but developers still have to decide whether that code should be trusted. Savier solves that by analyzing the code while it is still in the editor.”

### Step 2: Let Savier analyze
What to show:
- status bar changing to analyzing
- inline diagnostics appearing

What to say:
“Instead of waiting until commit or CI, Savier evaluates the file in real time and surfaces trust feedback immediately.”

### Step 3: Open the Trust Cockpit
Use:
- `Savier: Show Trust Cockpit`

What to show:
- primary trust shift
- trust score
- dimension breakdown
- active findings
- revision delta if available

What to say:
“This is not just a list of issues. Savier turns the file into a trust state. We can see the current posture across security, quality, and performance.”

### Step 4: Explain the current findings
What to show:
- primary finding
- dimension breakdown
- active findings panel

What to say:
“Here the system identifies what matters most, but it also keeps the other dimensions visible. That helps us understand whether the file is only risky, or also hard to maintain or inefficient.”

### Step 5: Improve the code
What to do:
- apply a prepared improved version of the file
- or paste a revised version live

What to say:
“Now we revise the file and let Savier judge whether the latest change actually improved trust.”

### Step 6: Re-run analysis
Use:
- auto-analysis after edit
- or `Savier: Re-run Analysis for Active File`

What to show:
- updated trust score
- changed findings
- score delta
- revision timeline

What to say:
“This is the key product moment. Savier doesn’t just show that something exists. It shows that the latest revision improved trust and exactly what changed.”

### Step 7: Show the timeline
What to show:
- revision timeline
- score delta
- fixed findings
- new findings

What to say:
“The timeline makes trust visible over time. That’s what makes Savier more than a scanner. It becomes a feedback loop for code evolution.”

### Step 8: Close on impact
What to say:
“Developers don’t need another late-stage tool. They need trust inside the workflow itself. Savier brings that trust layer directly into AI-assisted coding.”

## UI Surfaces To Show

### Always show
- editor diagnostics
- Trust Cockpit

### Good to show if time allows
- Active File State
- status bar
- revision timeline

### Optional for deeper technical demos
- analysis profile
- technical trace

## Best Narrative For Judges
Use this language repeatedly:

- real-time trust
- in-context validation
- trust before adoption
- revision-aware developer feedback
- security, quality, and performance in one view

Avoid spending too long on:

- backend internals
- low-level provider details
- implementation bugs or edge cases

## Two-Minute Version

### Goal
Deliver a clean, high-impact pitch with minimal complexity.

### Flow
1. Open flawed file.
2. Show that Savier immediately analyzes it.
3. Open Trust Cockpit.
4. Point out:
   - low trust score
   - dimension breakdown
   - active findings
5. Improve the file.
6. Re-run analysis.
7. Show positive delta and cleaner current state.
8. Close with:
   “Savier helps developers trust AI-generated code in real time.”

## Five-Minute Version

### Goal
Show stronger product depth and revision-aware differentiation.

### Flow
1. Introduce the trust gap in AI coding.
2. Open flawed code.
3. Let analysis run.
4. Show:
   - diagnostics
   - Trust Cockpit
   - primary finding
   - dimension breakdown
   - active findings
5. Explain that the backend is the source of truth.
6. Revise the code.
7. Re-run analysis.
8. Show:
   - score movement
   - revision delta
   - fixed findings
   - timeline
9. Optionally show:
   - Active File State
   - analysis profile
10. Close with platform-level impact:
   - trust infrastructure for AI-assisted software development

## Fallback Demo Plan
If live provider analysis is slow or unavailable:

- keep pre-analyzed files ready
- open the Trust Cockpit for an existing analyzed file
- walk through the timeline and file state as if replaying the flow
- use the dashboard to show before/after trust movement

Fallback message:
“Even when we replay the scenario, the key point remains: Savier preserves trust history and makes improvement visible across revisions.”

## Demo Prep Checklist

Before presenting, verify:

- backend server is running
- extension can reach `http://127.0.0.1:5000`
- analysis mode is `full`
- demo file is ready
- improved version is ready
- Trust Cockpit command works
- Active File State command works
- timeline contains at least two revisions

## Final Closing Line
Use this at the end of the demo:

**“Savier makes code trust visible while the code is still being written. That is the shift from post-hoc validation to real-time trust infrastructure.”**
