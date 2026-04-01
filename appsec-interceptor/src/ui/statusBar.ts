import * as vscode from 'vscode';
import { AnalysisResponse } from '../core/contracts';

export class StatusBarController {
    public constructor(private readonly item: vscode.StatusBarItem) {}

    public showReady(): void {
        this.item.text = '$(shield) Savier: Ready';
        this.item.tooltip = 'Savier is ready to evaluate code trust.';
        this.item.backgroundColor = undefined;
        this.item.command = 'appsec-interceptor.showDashboard';
    }

    public showAnalyzing(documentLabel: string): void {
        this.item.text = '$(sync~spin) Savier: Reading trust...';
        this.item.tooltip = `Analyzing ${documentLabel}`;
        this.item.backgroundColor = undefined;
        this.item.command = 'appsec-interceptor.showDashboard';
    }

    public showResult(result: AnalysisResponse): void {
        const delta = result.diff?.score_delta ?? 0;
        const deltaLabel = delta > 0 ? ` • +${delta}` : delta < 0 ? ` • ${delta}` : '';
        const scoreLabel = result.scores?.overall ? ` • ${result.scores.overall}` : '';

        if (result.status === 'failed') {
            this.showUnavailable(result.errors[0] ?? 'Savier service unavailable');
            return;
        }

        if (delta > 0 && !result.vuln_found) {
            this.item.text = `$(graph) Savier: Trust up${deltaLabel}${scoreLabel}`;
            this.item.tooltip = 'This revision improved the active file score.';
            this.item.backgroundColor = undefined;
            this.item.command = 'appsec-interceptor.showDashboard';
            return;
        }

        if (result.vuln_found) {
            const icon = result.severity === 'CRITICAL' ? '$(error)' : result.severity === 'HIGH' ? '$(warning)' : '$(info)';
            const suffix = result.status === 'partial' ? ' (partial)' : '';
            this.item.text = `${icon} Savier: ${result.severity} — ${result.vuln_type}${deltaLabel}${scoreLabel}${suffix}`;
            this.item.tooltip = result.warnings.join('\n') || result.full_explanation || result.developer_note;
            this.item.backgroundColor = new vscode.ThemeColor(
                result.severity === 'CRITICAL' ? 'statusBarItem.errorBackground' : 'statusBarItem.warningBackground',
            );
            this.item.command = 'appsec-interceptor.showDashboard';
            return;
        }

        if (result.status === 'partial') {
            this.item.text = `$(info) Savier: Partial${deltaLabel}${scoreLabel}`;
            this.item.tooltip = result.warnings.join('\n') || 'Analysis completed with warnings';
            this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            this.item.command = 'appsec-interceptor.showDashboard';
            return;
        }

        this.item.text = `$(sparkle) Savier: Clean${deltaLabel}${scoreLabel}`;
        this.item.tooltip = 'No active issues in the latest analysis';
        this.item.backgroundColor = undefined;
        this.item.command = 'appsec-interceptor.showDashboard';
    }

    public showUnavailable(message: string): void {
        this.item.text = '$(plug) Savier: Backend unavailable';
        this.item.tooltip = message;
        this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        this.item.command = 'appsec-interceptor.showDashboard';
    }
}
