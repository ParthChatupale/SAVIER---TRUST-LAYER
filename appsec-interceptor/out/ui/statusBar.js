"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.StatusBarController = void 0;
const vscode = __importStar(require("vscode"));
class StatusBarController {
    item;
    constructor(item) {
        this.item = item;
    }
    showReady() {
        this.item.text = '$(shield) Savier: Ready';
        this.item.tooltip = 'Savier is ready to evaluate code trust.';
        this.item.backgroundColor = undefined;
        this.item.command = 'appsec-interceptor.showDashboard';
    }
    showAnalyzing(documentLabel) {
        this.item.text = '$(sync~spin) Savier: Reading trust...';
        this.item.tooltip = `Analyzing ${documentLabel}`;
        this.item.backgroundColor = undefined;
        this.item.command = 'appsec-interceptor.showDashboard';
    }
    showResult(result) {
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
            this.item.backgroundColor = new vscode.ThemeColor(result.severity === 'CRITICAL' ? 'statusBarItem.errorBackground' : 'statusBarItem.warningBackground');
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
    showUnavailable(message) {
        this.item.text = '$(plug) Savier: Backend unavailable';
        this.item.tooltip = message;
        this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        this.item.command = 'appsec-interceptor.showDashboard';
    }
}
exports.StatusBarController = StatusBarController;
//# sourceMappingURL=statusBar.js.map