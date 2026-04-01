import { ActiveDashboardState } from '../services/state';
import { escapeHtml } from './html';
import {
    findLatestFileEvent,
    renderAgentTrace,
    renderAnalysisProfile,
    renderDiffCard,
    renderDimensionCards,
    renderFindingList,
    renderFindingsByDimension,
    renderFixCard,
    renderPrimaryFindingCard,
    renderTimeline,
    renderTrustNarrative,
} from './components';
import { createAppShell } from './theme';

export function renderDashboardHtml(state: ActiveDashboardState): string {
    const latestEvent = findLatestFileEvent(state.fileState, state.timeline);
    const dashboard = state.dashboard;
    const result = state.lastResult;
    const currentScores = state.fileState?.scores ?? result?.scores;

    const body = `
        <section class="grid">
            <article class="panel strong span-8">
                <div class="panel-header">
                    <div>
                        <h2 class="panel-title">Primary trust shift</h2>
                        <div class="panel-meta">${escapeHtml(state.fileUri || 'No active file selected')} ${state.loading ? '• refreshing…' : ''}</div>
                    </div>
                    <div class="chip-row">
                        <span class="chip">Events ${dashboard?.total_events ?? 0}</span>
                        <span class="chip">Files ${dashboard?.total_files ?? 0}</span>
                        <span class="chip">Open findings ${dashboard?.open_findings ?? 0}</span>
                    </div>
                </div>
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
            <article class="panel soft span-4">
                <div class="panel-header"><h2 class="panel-title">Narrative</h2><div class="panel-meta">Judge-friendly framing</div></div>
                <div class="panel-body">
                    ${renderTrustNarrative(result, state.fileState)}
                    ${renderFixCard(result)}
                </div>
            </article>
        </section>

        <section class="grid">
            <article class="panel span-7">
                <div class="panel-header"><h2 class="panel-title">Current file posture</h2><div class="panel-meta">What this file looks like with Savier watching</div></div>
                <div class="panel-body">
                    ${currentScores ? `<div class="metric-grid">${renderDimensionCards(currentScores)}</div>` : '<div class="empty-state">No active file state available yet.</div>'}
                </div>
            </article>
            <article class="panel soft span-5">
                <div class="panel-header"><h2 class="panel-title">Revision delta</h2><div class="panel-meta">Proof that the latest change improved trust</div></div>
                <div class="panel-body">
                    ${latestEvent ? renderDiffCard(latestEvent.diff) : '<div class="empty-state">Run at least two revisions to show score movement and fixed findings.</div>'}
                </div>
            </article>
        </section>

        <section class="two-col">
            <article class="panel span-7">
                <div class="panel-header"><h2 class="panel-title">Dimension breakdown</h2><div class="panel-meta">Security, quality, and performance now stay separate</div></div>
                <div class="panel-body">${renderFindingsByDimension(result?.dimensions ?? {})}</div>
            </article>
            <article class="panel soft span-5">
                <div class="panel-header"><h2 class="panel-title">Active findings</h2><div class="panel-meta">What still needs attention right now</div></div>
                <div class="panel-body">${renderFindingList(state.fileState?.findings ?? [])}</div>
            </article>
        </section>

        <section class="grid">
            <article class="panel span-8">
                <div class="panel-header"><h2 class="panel-title">Revision timeline</h2><div class="panel-meta">Without Savier vs with Savier becomes visible here</div></div>
                <div class="panel-body">${renderTimeline(state.timeline)}</div>
            </article>
            <article class="panel soft span-4">
                <div class="panel-header"><h2 class="panel-title">Workspace posture</h2><div class="panel-meta">Developer-wide average from backend state</div></div>
                <div class="panel-body">
                    ${dashboard ? `<div class="metric-grid">${renderDimensionCards(dashboard.average_scores)}</div>` : '<div class="empty-state">No dashboard data yet. Analyze a supported file to generate the first trust snapshot.</div>'}
                </div>
            </article>
        </section>

        <section class="two-col">
            <article class="panel span-6">
                <div class="panel-header"><h2 class="panel-title">Analysis profile</h2><div class="panel-meta">Backend proof of how this judgment was made</div></div>
                <div class="panel-body">
                    ${renderAnalysisProfile(result?.analysis_profile ?? null)}
                </div>
            </article>
            <article class="panel soft span-6">
                <div class="panel-header"><h2 class="panel-title">Technical trace</h2><div class="panel-meta">Visible, but intentionally secondary</div></div>
                <div class="panel-body">
                    ${state.error ? `<div class="empty-state">${escapeHtml(state.error)}</div>` : renderAgentTrace(result?.agent_trace ?? [])}
                </div>
            </article>
        </section>`;

    return createAppShell('Savier Trust Cockpit', body);
}
