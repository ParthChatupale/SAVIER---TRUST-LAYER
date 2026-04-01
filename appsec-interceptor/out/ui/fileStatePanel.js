"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.renderFileStateHtml = renderFileStateHtml;
const components_1 = require("./components");
const theme_1 = require("./theme");
const html_1 = require("./html");
function renderFileStateHtml(state) {
    if (!state.fileState) {
        return (0, theme_1.createAppShell)('Active File State', '<section class="grid"><article class="panel"><div class="panel-body"><div class="empty-state">Open a supported file and run analysis to inspect the active file state.</div></div></article></section>');
    }
    const result = state.lastResult;
    const body = `<section class="grid">
        <article class="panel strong span-8">
            <div class="panel-header">
                <div>
                    <h2 class="panel-title">Active file state</h2>
                    <div class="panel-meta">${(0, html_1.escapeHtml)(state.fileState.file_uri)}</div>
                </div>
                <div class="chip-row">
                    <span class="chip">Event ${(0, html_1.escapeHtml)(state.fileState.last_event_id)}</span>
                    <span class="chip">Updated ${(0, html_1.escapeHtml)(state.fileState.updated_at)}</span>
                </div>
            </div>
            <div class="panel-body">
                <div class="metric-grid">${(0, components_1.renderDimensionCards)(state.fileState.scores)}</div>
            </div>
        </article>
        <article class="panel soft span-4">
            <div class="panel-header"><h2 class="panel-title">Primary issue</h2><div class="panel-meta">Most important thing to explain in the demo</div></div>
            <div class="panel-body">
                ${(0, components_1.renderPrimaryFindingCard)(result?.primary_finding ?? {
        dimension: '',
        vuln_type: '',
        severity: 'NONE',
        vulnerable_line: '',
        pattern: '',
        explanation: '',
        suggested_fix: '',
        confidence: 0,
    }, result)}
            </div>
        </article>
        <article class="panel span-7">
            <div class="panel-header"><h2 class="panel-title">Dimension evidence</h2><div class="panel-meta">What the backend believes for this exact file</div></div>
            <div class="panel-body">${(0, components_1.renderFindingsByDimension)(result?.dimensions ?? {})}</div>
        </article>
        <article class="panel soft span-5">
            <div class="panel-header"><h2 class="panel-title">Open findings</h2><div class="panel-meta">Current risk remaining in the file</div></div>
            <div class="panel-body">${(0, components_1.renderFindingList)(state.fileState.findings)}</div>
        </article>
        <article class="panel span-6">
            <div class="panel-header"><h2 class="panel-title">Analysis profile</h2><div class="panel-meta">Model routing and pipeline fingerprint</div></div>
            <div class="panel-body">${(0, components_1.renderAnalysisProfile)(result?.analysis_profile ?? null)}</div>
        </article>
        <article class="panel soft span-6">
            <div class="panel-header"><h2 class="panel-title">Latest analysis trace</h2><div class="panel-meta">What Savier used to judge this file</div></div>
            <div class="panel-body">${(0, components_1.renderAgentTrace)(result?.agent_trace ?? [])}</div>
        </article>
    </section>`;
    return (0, theme_1.createAppShell)('Active File State', body);
}
//# sourceMappingURL=fileStatePanel.js.map