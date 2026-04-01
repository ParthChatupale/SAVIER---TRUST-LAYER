"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.renderHistoryHtml = renderHistoryHtml;
const html_1 = require("./html");
const theme_1 = require("./theme");
function renderHistoryHtml(history, developerId) {
    const body = history.length === 0
        ? '<section class="grid"><article class="panel"><div class="panel-body"><div class="empty-state">No findings recorded yet for this developer. Analyze risky code to start the history trail.</div></div></article></section>'
        : `<section class="grid"><article class="panel"><div class="panel-header"><h2 class="panel-title">Developer history</h2><div class="panel-meta">${(0, html_1.escapeHtml)(developerId)}</div></div><div class="panel-body"><table><thead><tr><th>Issue</th><th>Severity</th><th>When</th><th>Why it mattered</th></tr></thead><tbody>${history.map((entry) => `
            <tr>
                <td>${(0, html_1.escapeHtml)(entry.vuln_type || 'Unknown')}</td>
                <td><span class="severity-pill severity-${(0, html_1.escapeHtml)(entry.severity)}">${(0, html_1.escapeHtml)(entry.severity)}</span></td>
                <td>${(0, html_1.escapeHtml)(entry.timestamp || 'Unknown')}</td>
                <td>${(0, html_1.escapeHtml)(entry.explanation || 'No explanation provided')}</td>
            </tr>`).join('')}</tbody></table></div></article></section>`;
    return (0, theme_1.createAppShell)('Developer History', body);
}
//# sourceMappingURL=historyPanel.js.map