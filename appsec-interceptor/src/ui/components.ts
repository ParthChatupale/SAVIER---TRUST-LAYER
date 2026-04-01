import {
    AnalysisDiff,
    AnalysisEvent,
    AnalysisProfile,
    AnalysisResponse,
    AnalysisScores,
    DimensionAnalysisResult,
    FileState,
    FindingRecord,
    FindingSeverity,
    PrimaryFinding,
} from '../core/contracts';
import { escapeHtml } from './html';

const DIMENSION_ORDER = ['security', 'quality', 'performance'] as const;

export function severityClass(severity: FindingSeverity): string {
    return `severity-${severity}`;
}

export function dimensionClass(dimension: string): string {
    return `dimension-${dimension}`;
}

export function scoreTone(score: number): string {
    if (score >= 85) {
        return 'Trust recovered';
    }
    if (score >= 65) {
        return 'Improving but still exposed';
    }
    if (score >= 40) {
        return 'At risk';
    }
    return 'Critical trust debt';
}

export function renderMetricCard(label: string, value: string, subtle: string, progress?: number, tone = ''): string {
    return `<article class="metric-card ${escapeHtml(tone)}">
        <div class="metric-label">${escapeHtml(label)}</div>
        <div class="metric-value">${escapeHtml(value)}</div>
        <div class="metric-subtle">${escapeHtml(subtle)}</div>
        ${typeof progress === 'number' ? `<div class="score-bar"><span style="width:${Math.max(0, Math.min(progress, 100))}%"></span></div>` : ''}
    </article>`;
}

export function renderDimensionCards(scores: AnalysisScores): string {
    return `
        ${renderMetricCard('Trust Score', `${scores.overall}`, scoreTone(scores.overall), scores.overall, scoreToneClass(scores.overall))}
        ${renderMetricCard('Security', `${scores.security}`, scores.security >= 80 ? 'Safer posture' : 'Needs hardening', scores.security, scoreToneClass(scores.security))}
        ${renderMetricCard('Quality', `${scores.quality}`, scores.quality >= 80 ? 'Readable and stable' : 'Maintainability risk', scores.quality, scoreToneClass(scores.quality))}
        ${renderMetricCard('Performance', `${scores.performance}`, scores.performance >= 80 ? 'Healthy runtime profile' : 'Efficiency concerns', scores.performance, scoreToneClass(scores.performance))}
    `;
}

export function renderDiffCard(diff: AnalysisDiff): string {
    const deltaClass = diff.score_delta >= 0 ? 'delta-positive' : 'delta-negative';
    const deltaPrefix = diff.score_delta > 0 ? '+' : '';
    const narrative = diff.score_delta >= 0
        ? 'Trust moved upward after this revision.'
        : 'This revision regressed trust and needs another pass.';
    return `<div class="metric-grid">
        ${renderMetricCard('Score Delta', `${deltaPrefix}${diff.score_delta}`, 'Change from previous revision')}
        ${renderMetricCard('Fixed Findings', `${diff.fixed_count}`, 'Resolved in the latest revision')}
        ${renderMetricCard('New Findings', `${diff.new_issue_count}`, 'Introduced in the latest revision')}
        ${renderMetricCard('Unchanged', `${diff.unchanged_count}`, 'Still open after the latest revision')}
    </div>
    <p class="metric-subtle ${deltaClass}">${escapeHtml(narrative)}</p>`;
}

export function renderPrimaryFindingCard(primary: PrimaryFinding, result: AnalysisResponse | null): string {
    if (!primary.vuln_type) {
        return '<div class="empty-state">No primary finding yet. Run analysis on a supported file to spotlight the highest-risk issue.</div>';
    }

    const supportingText = result?.developer_note || primary.explanation || 'No explanation provided.';
    return `<article class="hero-card ${dimensionClass(primary.dimension || 'security')}">
        <div class="event-row">
            <div>
                <div class="metric-label">Primary finding</div>
                <div class="event-title">${escapeHtml(primary.vuln_type)}</div>
            </div>
            <div class="chip-row">
                <span class="severity-pill ${severityClass(primary.severity)}">${escapeHtml(primary.severity)}</span>
                ${primary.dimension ? `<span class="chip dimension-chip ${dimensionClass(primary.dimension)}">${escapeHtml(primary.dimension)}</span>` : ''}
            </div>
        </div>
        <div class="hero-copy">${renderNarrative(primary.explanation || supportingText)}</div>
        ${primary.vulnerable_line ? `<div class="code-block"><code>${escapeHtml(primary.vulnerable_line)}</code></div>` : ''}
        <div class="hero-footer">
            <div class="metric-subtle">Confidence ${escapeHtml(Math.round(primary.confidence * 100).toString())}%</div>
            <div class="metric-subtle">${escapeHtml(result?.owasp_category || '')}</div>
        </div>
    </article>`;
}

export function renderFixCard(result: AnalysisResponse | null): string {
    if (!result?.suggested_fix) {
        return '<div class="empty-state">Suggested fixes will appear here after Savier identifies a dominant issue.</div>';
    }

    return `<article class="fix-card">
        <div class="metric-label">Recommended fix path</div>
        <div class="fix-copy">${renderRichText(result.suggested_fix)}</div>
    </article>`;
}

export function renderFindingsByDimension(dimensions: Partial<Record<'security' | 'quality' | 'performance', DimensionAnalysisResult>>): string {
    const cards = DIMENSION_ORDER.map((dimension) => dimensions[dimension]).filter(Boolean) as DimensionAnalysisResult[];
    if (cards.length === 0) {
        return '<div class="empty-state">No dimension breakdown is available for this analysis yet.</div>';
    }

    return `<div class="dimension-grid">${cards.map((result) => `
        <article class="dimension-card ${dimensionClass(result.dimension)}">
            <div class="event-row">
                <div>
                    <div class="metric-label">${escapeHtml(result.dimension)}</div>
                    <div class="event-title">${escapeHtml(result.summary || `${result.finding_count} finding(s)` )}</div>
                </div>
                <span class="severity-pill ${severityClass(result.top_severity)}">${escapeHtml(result.top_severity)}</span>
            </div>
            <div class="finding-mini-list">
                <div class="finding-mini-item">
                    <div class="metric-value">${escapeHtml(String(result.finding_count))}</div>
                    <div class="metric-subtle">${escapeHtml(result.finding_count === 1 ? 'Finding in this dimension' : 'Findings in this dimension')}</div>
                </div>
                ${result.findings[0]
                    ? `<div class="finding-mini-item"><div class="metric-label">Top issue</div><div class="event-title">${escapeHtml(result.findings[0].vuln_type)}</div>${result.findings[0].vulnerable_line ? `<div class="metric-subtle"><code>${escapeHtml(result.findings[0].vulnerable_line)}</code></div>` : ''}</div>`
                    : '<div class="metric-subtle">No findings in this dimension.</div>'}
            </div>
        </article>
    `).join('')}</div>`;
}

export function renderFindingList(findings: FindingRecord[]): string {
    if (findings.length === 0) {
        return '<div class="empty-state">No active findings remain for the current file.</div>';
    }

    return `<div class="finding-list">${findings.map((finding) => `
        <article class="finding-item ${dimensionClass(finding.dimension)}">
            <div class="event-row">
                <span class="severity-pill ${severityClass(finding.severity)}">${escapeHtml(finding.severity)}</span>
                <span class="chip dimension-chip ${dimensionClass(finding.dimension)}">${escapeHtml(finding.dimension)}</span>
            </div>
            <div class="event-title">${escapeHtml(finding.issue_type)}</div>
            <div class="muted">${escapeHtml(finding.explanation || 'No explanation provided')}</div>
            ${finding.line ? `<div class="metric-subtle"><code>${escapeHtml(finding.line)}</code></div>` : ''}
        </article>
    `).join('')}</div>`;
}

function timestampLabel(value: string): string {
    try {
        return new Date(value).toLocaleTimeString();
    } catch {
        return value;
    }
}

export function renderTimeline(events: AnalysisEvent[]): string {
    if (events.length === 0) {
        return '<div class="empty-state">Run analysis on a file to build the revision timeline.</div>';
    }

    return `<div class="timeline-list">${events.map((event, index) => {
        const summary = event.summary.vuln_type || 'Clean revision';
        const delta = event.diff.score_delta;
        const deltaLabel = `${delta > 0 ? '+' : ''}${delta}`;
        const deltaClass = delta >= 0 ? 'delta-positive' : 'delta-negative';
        return `
            <article class="timeline-item">
                <div class="event-row">
                    <div>
                        <div class="metric-label">Revision ${escapeHtml(String(events.length - index))}</div>
                        <div class="event-title">${escapeHtml(summary)}</div>
                    </div>
                    <div class="chip-row">
                        <span class="chip">${escapeHtml(timestampLabel(event.timestamp))}</span>
                        <span class="chip ${deltaClass}">Δ ${escapeHtml(deltaLabel)}</span>
                        <span class="chip">${escapeHtml(event.source || 'unknown source')}</span>
                    </div>
                </div>
                <div class="metric-subtle">${escapeHtml(event.summary.status)} • Security ${event.scores.security} • Quality ${event.scores.quality} • Performance ${event.scores.performance}</div>
            </article>`;
    }).join('')}</div>`;
}

export function renderAgentTrace(entries: Array<{ agent: string; stage: string; status: string; model: string; error?: string }>): string {
    if (entries.length === 0) {
        return '<div class="empty-state">Agent trace is empty for this view.</div>';
    }

    return `<details><summary>Agent trace</summary><table><thead><tr><th>Agent</th><th>Stage</th><th>Status</th><th>Model</th><th>Error</th></tr></thead><tbody>${entries.map((entry) => `
        <tr>
            <td>${escapeHtml(entry.agent)}</td>
            <td>${escapeHtml(entry.stage)}</td>
            <td>${escapeHtml(entry.status)}</td>
            <td>${escapeHtml(entry.model)}</td>
            <td>${escapeHtml(entry.error || '')}</td>
        </tr>`).join('')}</tbody></table></details>`;
}

export function renderAnalysisProfile(profile: AnalysisProfile | null): string {
    if (!profile) {
        return '<div class="empty-state">No analysis profile metadata is available for this run.</div>';
    }

    const modelRows = Object.entries(profile.model_profile)
        .map(([stage, model]) => `<div class="profile-row"><span>${escapeHtml(stage)}</span><span>${escapeHtml(model)}</span></div>`)
        .join('');

    return `<article class="profile-card">
        <div class="metric-label">Analysis profile</div>
        <div class="chip-row profile-chips">
            <span class="chip">Provider ${escapeHtml(profile.provider)}</span>
            <span class="chip">Pipeline ${escapeHtml(profile.pipeline_version)}</span>
            <span class="chip">Fingerprint ${escapeHtml(profile.fingerprint)}</span>
        </div>
        <div class="profile-list">${modelRows}</div>
    </article>`;
}

export function renderTrustNarrative(result: AnalysisResponse | null, fileState: FileState | null): string {
    if (!result && !fileState) {
        return '<div class="empty-state">Open a file and let Savier analyze it to build the live trust narrative.</div>';
    }

    const scores = fileState?.scores ?? result?.scores;
    const status = result?.status ?? fileState?.status ?? 'success';
    const narrative = status === 'partial'
        ? 'Savier found part of the picture. The active file needs another pass before trust is settled.'
        : scores && scores.overall >= 85
            ? 'This file is in a recoverable state. Savier is mostly verifying resilience now.'
            : 'This file still carries meaningful trust debt. The revision timeline should show whether the latest change moved risk down.';

    const modeChip = result?.mode ? `<div class="chip-row"><span class="chip">Mode ${escapeHtml(result.mode)}</span></div>` : '';
    const trustExplanation = result?.mode && result.mode !== 'full'
        ? '<p class="metric-subtle">This trust score reflects a single-dimension run. Use <code>full</code> mode for the full security, quality, and performance picture.</p>'
        : '';

    return `<article class="narrative-card">
        <div class="metric-label">Demo narrative</div>
        <p class="hero-copy">${escapeHtml(narrative)}</p>
        ${modeChip}
        ${trustExplanation}
    </article>`;
}

export function findLatestFileEvent(fileState: FileState | null, timeline: AnalysisEvent[]): AnalysisEvent | null {
    if (!fileState) {
        return timeline[0] ?? null;
    }
    return timeline.find((event) => event.event_id === fileState.last_event_id) ?? timeline[0] ?? null;
}

function scoreToneClass(score: number): string {
    if (score >= 85) {
        return 'score-healthy';
    }
    if (score >= 65) {
        return 'score-caution';
    }
    if (score >= 40) {
        return 'score-risk';
    }
    return 'score-critical';
}

function renderParagraphs(value: string): string {
    return value
        .split(/\n{2,}/)
        .map((paragraph) => paragraph.trim())
        .filter(Boolean)
        .map((paragraph) => paragraph.includes('\n') || paragraph.includes('```')
            ? `<pre class="fix-pre">${escapeHtml(paragraph)}</pre>`
            : `<p>${escapeHtml(paragraph)}</p>`)
        .join('');
}

function renderRichText(value: string): string {
    const codeFencePattern = /```([\s\S]*?)```/g;
    const parts: string[] = [];
    let lastIndex = 0;
    for (const match of value.matchAll(codeFencePattern)) {
        const start = match.index ?? 0;
        const end = start + match[0].length;
        if (start > lastIndex) {
            parts.push(renderParagraphs(value.slice(lastIndex, start)));
        }
        parts.push(`<pre class="fix-pre">${escapeHtml(match[1]?.trim() ?? '')}</pre>`);
        lastIndex = end;
    }
    if (lastIndex < value.length) {
        parts.push(renderParagraphs(value.slice(lastIndex)));
    }
    return parts.join('');
}

function renderNarrative(value: string): string {
    const compact = value.trim();
    if (!compact) {
        return '<p>No explanation provided.</p>';
    }

    const cleaned = compact
        .replace(/```[\s\S]*?```/g, '')
        .replace(/\s+/g, ' ')
        .trim();
    const shortened = cleaned.length > 420 ? `${cleaned.slice(0, 417).trim()}...` : cleaned;
    return `<p>${escapeHtml(shortened)}</p>`;
}
