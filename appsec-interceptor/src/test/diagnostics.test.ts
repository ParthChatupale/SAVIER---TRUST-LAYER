import * as assert from 'assert';
import { buildDiagnosticDescriptor, locateVulnerableLine, severityToDiagnosticSeverity } from '../editor/diagnosticModel';

export async function runDiagnosticTests(): Promise<void> {
    const code = [
        'def get_user(user_id):',
        '    query = "SELECT * FROM users WHERE id=" + user_id',
        '    return db.execute(query)',
    ].join('\n');

    const lineIndex = locateVulnerableLine(code, 'query = "SELECT * FROM users WHERE id=" + user_id', 'SQL Injection');
    assert.strictEqual(lineIndex, 1);
    assert.strictEqual(severityToDiagnosticSeverity('CRITICAL'), 'error');
    assert.strictEqual(severityToDiagnosticSeverity('MEDIUM'), 'warning');
    assert.strictEqual(severityToDiagnosticSeverity('LOW'), 'information');

    const descriptor = buildDiagnosticDescriptor(code, {
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
