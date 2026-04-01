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
exports.runWebviewTests = runWebviewTests;
const assert = __importStar(require("assert"));
const historyPanel_1 = require("../ui/historyPanel");
const dashboardPanel_1 = require("../ui/dashboardPanel");
const fileStatePanel_1 = require("../ui/fileStatePanel");
function createState() {
    return {
        dashboard: {
            developer_id: 'parth',
            total_files: 1,
            total_events: 2,
            files_with_findings: 1,
            open_findings: 1,
            average_scores: { overall: 72, security: 48, quality: 84, performance: 86 },
            current_files: [],
            recent_events: [],
            score_trend: [],
        },
        timeline: [{
                event_id: 'evt-2',
                developer_id: 'parth',
                file_uri: 'file:///one.py',
                source: 'ide_extension',
                mode: 'security',
                content_hash: 'hash',
                status: 'success',
                project_id: '',
                timestamp: new Date().toISOString(),
                scores: { overall: 72, security: 48, quality: 84, performance: 86 },
                findings: [],
                diff: {
                    score_delta: 18,
                    fixed_count: 1,
                    new_issue_count: 0,
                    unchanged_count: 0,
                    fixed_findings: ['security:SQL Injection'],
                    new_findings: [],
                    unchanged_findings: [],
                },
                summary: { vuln_type: 'SQL Injection', severity: 'CRITICAL', status: 'success' },
            }],
        fileState: {
            developer_id: 'parth',
            file_uri: 'file:///one.py',
            content_hash: 'hash',
            last_event_id: 'evt-2',
            source: 'ide_extension',
            mode: 'security',
            status: 'success',
            updated_at: new Date().toISOString(),
            project_id: '',
            scores: { overall: 72, security: 48, quality: 84, performance: 86 },
            findings: [{
                    key: 'security:SQL Injection',
                    dimension: 'security',
                    issue_type: '<img />',
                    severity: 'CRITICAL',
                    line: 'query = user_id + raw',
                    explanation: '<script>unsafe</script>',
                }],
        },
        fileUri: 'file:///one.py',
        lastResult: {
            status: 'success',
            developer_id: 'parth',
            mode: 'security',
            vuln_found: true,
            vuln_type: 'SQL Injection',
            severity: 'CRITICAL',
            vulnerable_line: 'query = user_id + raw',
            suggested_fix: 'Use parameters',
            attack_scenario: 'SQLi',
            developer_note: 'Unsafe query',
            full_explanation: 'Unsafe query',
            owasp_category: 'A03:2021 - Injection',
            errors: [],
            warnings: [],
            agent_trace: [{ agent: 'planning', stage: 'planning', status: 'success', model: 'gemma' }],
            file_uri: 'file:///one.py',
            event_id: 'evt-2',
            scores: { overall: 72, security: 48, quality: 84, performance: 86 },
            diff: {
                score_delta: 18,
                fixed_count: 1,
                new_issue_count: 0,
                unchanged_count: 0,
                fixed_findings: ['security:SQL Injection'],
                new_findings: [],
                unchanged_findings: [],
            },
            findings: [{
                    dimension: 'security',
                    vuln_found: true,
                    vuln_type: 'SQL Injection',
                    vulnerable_line: 'query = user_id + raw',
                    pattern: 'raw concat',
                    attack_scenario: 'SQLi',
                    suggested_fix: 'Use parameters',
                    confidence: 0.9,
                    severity: 'CRITICAL',
                }],
            dimensions: {
                security: {
                    dimension: 'security',
                    status: 'success',
                    warnings: [],
                    summary: '1 security issue',
                    finding_count: 1,
                    top_severity: 'CRITICAL',
                    findings: [{
                            dimension: 'security',
                            vuln_found: true,
                            vuln_type: 'SQL Injection',
                            vulnerable_line: 'query = user_id + raw',
                            pattern: 'raw concat',
                            attack_scenario: 'SQLi',
                            suggested_fix: 'Use parameters',
                            confidence: 0.9,
                            severity: 'CRITICAL',
                        }],
                },
            },
            primary_finding: {
                dimension: 'security',
                vuln_type: 'SQL Injection',
                severity: 'CRITICAL',
                vulnerable_line: 'query = user_id + raw',
                pattern: 'raw concat',
                explanation: 'Unsafe query',
                suggested_fix: 'Use parameters',
                confidence: 0.9,
            },
            analysis_profile: {
                pipeline_version: 'v2-specialist-r2',
                provider: 'nvidia',
                enabled_agents: ['planning', 'security_review', 'aggregation'],
                model_profile: { planning: 'gemma', aggregation: 'gpt-oss-120b' },
                fingerprint: 'abc123',
            },
            data_flow: 'input -> query',
            planning: {},
        },
        loading: false,
        error: '',
    };
}
async function runWebviewTests() {
    const historyHtml = (0, historyPanel_1.renderHistoryHtml)([
        {
            vuln_type: '<script>alert(1)</script>',
            timestamp: 'now',
            explanation: '<b>unsafe</b>',
            severity: 'HIGH',
        },
    ], 'parth');
    assert.ok(!historyHtml.includes('<script>alert(1)</script>'));
    assert.ok(historyHtml.includes('&lt;script&gt;alert(1)&lt;/script&gt;'));
    const dashboardHtml = (0, dashboardPanel_1.renderDashboardHtml)(createState());
    assert.ok(dashboardHtml.includes('Savier Trust Cockpit'));
    assert.ok(!dashboardHtml.includes('<img />'));
    assert.ok(dashboardHtml.includes('Primary trust shift'));
    assert.ok(dashboardHtml.includes('Analysis profile'));
    const fileStateHtml = (0, fileStatePanel_1.renderFileStateHtml)(createState());
    assert.ok(fileStateHtml.includes('Active file state'));
    assert.ok(!fileStateHtml.includes('<script>unsafe</script>'));
}
//# sourceMappingURL=webviews.test.js.map