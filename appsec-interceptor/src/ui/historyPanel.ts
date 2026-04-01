import { HistoryEntry } from '../core/contracts';
import { escapeHtml } from './html';
import { createAppShell } from './theme';

export function renderHistoryHtml(history: HistoryEntry[], developerId: string): string {
    const body = history.length === 0
        ? '<section class="grid"><article class="panel"><div class="panel-body"><div class="empty-state">No findings recorded yet for this developer. Analyze risky code to start the history trail.</div></div></article></section>'
        : `<section class="grid"><article class="panel"><div class="panel-header"><h2 class="panel-title">Developer history</h2><div class="panel-meta">${escapeHtml(developerId)}</div></div><div class="panel-body"><table><thead><tr><th>Issue</th><th>Severity</th><th>When</th><th>Why it mattered</th></tr></thead><tbody>${history.map((entry) => `
            <tr>
                <td>${escapeHtml(entry.vuln_type || 'Unknown')}</td>
                <td><span class="severity-pill severity-${escapeHtml(entry.severity)}">${escapeHtml(entry.severity)}</span></td>
                <td>${escapeHtml(entry.timestamp || 'Unknown')}</td>
                <td>${escapeHtml(entry.explanation || 'No explanation provided')}</td>
            </tr>`).join('')}</tbody></table></div></article></section>`;

    return createAppShell('Developer History', body);
}
