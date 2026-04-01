import { ActiveDashboardState } from '../services/state';
import {
    renderAgentTrace,
    renderAnalysisProfile,
    renderDimensionCards,
    renderFindingList,
    renderFindingsByDimension,
    renderPrimaryFindingCard,
} from './components';
import { createAppShell } from './theme';
import { escapeHtml } from './html';

export function renderFileStateHtml(state: ActiveDashboardState): string {
    if (!state.fileState) {
        return createAppShell(
            'Active File State',
            '<section class="grid"><article class="panel"><div class="panel-body"><div class="empty-state">Open a supported file and run analysis to inspect the active file state.</div></div></article></section>',
        );
    }

    const result = state.lastResult;
    const body = `<section class="grid">
        <article class="panel strong span-8">
            <div class="panel-header">
                <div>
                    <h2 class="panel-title">Active file state</h2>
                    <div class="panel-meta">${escapeHtml(state.fileState.file_uri)}</div>
                </div>
                <div class="chip-row">
                    <span class="chip">Event ${escapeHtml(state.fileState.last_event_id)}</span>
                    <span class="chip">Updated ${escapeHtml(state.fileState.updated_at)}</span>
                </div>
            </div>
            <div class="panel-body">
                <div class="metric-grid">${renderDimensionCards(state.fileState.scores)}</div>
            </div>
        </article>
        <article class="panel soft span-4">
            <div class="panel-header"><h2 class="panel-title">Primary issue</h2><div class="panel-meta">Most important thing to explain in the demo</div></div>
            <div class="panel-body">
                ${renderPrimaryFindingCard(result?.primary_finding ?? {
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
            <div class="panel-body">${renderFindingsByDimension(result?.dimensions ?? {})}</div>
        </article>
        <article class="panel soft span-5">
            <div class="panel-header"><h2 class="panel-title">Open findings</h2><div class="panel-meta">Current risk remaining in the file</div></div>
            <div class="panel-body">${renderFindingList(state.fileState.findings)}</div>
        </article>
        <article class="panel span-6">
            <div class="panel-header"><h2 class="panel-title">Analysis profile</h2><div class="panel-meta">Model routing and pipeline fingerprint</div></div>
            <div class="panel-body">${renderAnalysisProfile(result?.analysis_profile ?? null)}</div>
        </article>
        <article class="panel soft span-6">
            <div class="panel-header"><h2 class="panel-title">Latest analysis trace</h2><div class="panel-meta">What Savier used to judge this file</div></div>
            <div class="panel-body">${renderAgentTrace(result?.agent_trace ?? [])}</div>
        </article>
    </section>`;

    return createAppShell('Active File State', body);
}
