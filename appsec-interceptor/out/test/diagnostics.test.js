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
exports.runDiagnosticTests = runDiagnosticTests;
const assert = __importStar(require("assert"));
const diagnosticModel_1 = require("../editor/diagnosticModel");
async function runDiagnosticTests() {
    const code = [
        'def get_user(user_id):',
        '    query = "SELECT * FROM users WHERE id=" + user_id',
        '    return db.execute(query)',
    ].join('\n');
    const lineIndex = (0, diagnosticModel_1.locateVulnerableLine)(code, 'query = "SELECT * FROM users WHERE id=" + user_id', 'SQL Injection');
    assert.strictEqual(lineIndex, 1);
    assert.strictEqual((0, diagnosticModel_1.severityToDiagnosticSeverity)('CRITICAL'), 'error');
    assert.strictEqual((0, diagnosticModel_1.severityToDiagnosticSeverity)('MEDIUM'), 'warning');
    assert.strictEqual((0, diagnosticModel_1.severityToDiagnosticSeverity)('LOW'), 'information');
    const descriptor = (0, diagnosticModel_1.buildDiagnosticDescriptor)(code, {
        status: 'success',
        developer_id: 'parth',
        mode: 'security',
        vuln_found: true,
        vuln_type: 'SQL Injection',
        severity: 'CRITICAL',
        vulnerable_line: 'query = "SELECT * FROM users WHERE id=" + user_id',
        suggested_fix: 'Use a parameterized query.',
        attack_scenario: 'An attacker can inject SQL.',
        developer_note: 'Do not concatenate user input.',
        full_explanation: '',
        owasp_category: 'A03:2021 - Injection',
        errors: [],
        warnings: [],
        agent_trace: [],
        file_uri: 'file:///one.py',
        event_id: 'evt-1',
        scores: { overall: 55, security: 20, quality: 90, performance: 88 },
        diff: {
            score_delta: -45,
            fixed_count: 0,
            new_issue_count: 1,
            unchanged_count: 0,
            fixed_findings: [],
            new_findings: ['security:SQL Injection'],
            unchanged_findings: [],
        },
        findings: [],
        dimensions: {},
        primary_finding: {
            dimension: 'security',
            vuln_type: 'SQL Injection',
            severity: 'CRITICAL',
            vulnerable_line: 'query = "SELECT * FROM users WHERE id=" + user_id',
            pattern: 'raw SQL concat',
            explanation: 'unsafe query',
            suggested_fix: 'Use a parameterized query.',
            confidence: 0.9,
        },
        analysis_profile: null,
        data_flow: '',
        planning: {},
    });
    assert.ok(descriptor);
    assert.strictEqual(descriptor?.line, 1);
    assert.ok(descriptor?.message.includes('Use a parameterized query.'));
}
//# sourceMappingURL=diagnostics.test.js.map