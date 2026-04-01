import * as assert from 'assert';
import { resolveExtensionSettings } from '../core/config';
import { AppSecApiClient } from '../services/apiClient';

function createResponse(status: number, body: unknown): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json' },
    });
}

export async function runApiClientTests(): Promise<void> {
    const settings = resolveExtensionSettings({ developerId: 'parth', mode: 'security' });

    const successfulClient = new AppSecApiClient(
        () => settings,
        async (input) => {
            const url = String(input);
            if (url.endsWith('/analyze')) {
                return createResponse(200, {
                    status: 'success',
                    developer_id: 'parth',
                    mode: 'security',
                    vuln_found: true,
                    vuln_type: 'SQL Injection',
                    severity: 'CRITICAL',
                    vulnerable_line: 'query = "SELECT * FROM users WHERE id=" + user_id',
                    suggested_fix: 'Use a parameterized query.',
                    attack_scenario: 'An attacker can inject SQL.',
                    developer_note: 'Concatenating raw input is unsafe.',
                    full_explanation: 'The query is built from user-controlled input.',
                    owasp_category: 'A03:2021 - Injection',
                    errors: [],
                    warnings: [],
                    agent_trace: [],
                    file_uri: 'file:///demo.py',
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
                    findings: [{
                        dimension: 'security',
                        vuln_found: true,
                        vuln_type: 'SQL Injection',
                        vulnerable_line: 'query = "SELECT * FROM users WHERE id=" + user_id',
                        pattern: 'raw SQL concat',
                        attack_scenario: 'An attacker can inject SQL.',
                        suggested_fix: 'Use a parameterized query.',
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
                                vulnerable_line: 'query = "SELECT * FROM users WHERE id=" + user_id',
                                pattern: 'raw SQL concat',
                                attack_scenario: 'An attacker can inject SQL.',
                                suggested_fix: 'Use a parameterized query.',
                                confidence: 0.9,
                                severity: 'CRITICAL',
                            }],
                        },
                    },
                    primary_finding: {
                        dimension: 'security',
                        vuln_type: 'SQL Injection',
                        severity: 'CRITICAL',
                        vulnerable_line: 'query = "SELECT * FROM users WHERE id=" + user_id',
                        pattern: 'raw SQL concat',
                        explanation: 'The query is built from user-controlled input.',
                        suggested_fix: 'Use a parameterized query.',
                        confidence: 0.9,
                    },
                    analysis_profile: {
                        pipeline_version: 'v2-specialist-r2',
                        provider: 'nvidia',
                        enabled_agents: ['planning', 'security_review', 'aggregation'],
                        model_profile: { planning: 'gemma', aggregation: 'gpt-oss-120b' },
                        fingerprint: 'abc123',
                    },
                    data_flow: 'input -> db.execute',
                    planning: {},
                });
            }
            if (url.includes('/dashboard')) {
                return createResponse(200, {
                    developer_id: 'parth',
                    total_files: 1,
                    total_events: 2,
                    files_with_findings: 1,
                    open_findings: 1,
                    average_scores: { overall: 70, security: 40, quality: 90, performance: 80 },
                    current_files: [],
                    recent_events: [],
                    score_trend: [],
                });
            }
            if (url.includes('/timeline')) {
                return createResponse(200, [{
                    event_id: 'evt-1',
                    developer_id: 'parth',
                    file_uri: 'file:///demo.py',
                    source: 'ide_extension',
                    mode: 'security',
                    content_hash: 'hash',
                    status: 'success',
                    project_id: '',
                    timestamp: 'now',
                    scores: { overall: 55, security: 20, quality: 90, performance: 88 },
                    findings: [],
                    diff: {
                        score_delta: -45,
                        fixed_count: 0,
                        new_issue_count: 1,
                        unchanged_count: 0,
                        fixed_findings: [],
                        new_findings: ['security:SQL Injection'],
                        unchanged_findings: [],
                    },
                    summary: { vuln_type: 'SQL Injection', severity: 'CRITICAL', status: 'success' },
                }]);
            }
            if (url.includes('/file-state')) {
                return createResponse(200, {
                    developer_id: 'parth',
                    file_uri: 'file:///demo.py',
                    content_hash: 'hash',
                    last_event_id: 'evt-1',
                    source: 'ide_extension',
                    mode: 'security',
                    status: 'success',
                    updated_at: 'now',
                    project_id: '',
                    scores: { overall: 55, security: 20, quality: 90, performance: 88 },
                    findings: [],
                });
            }
            return createResponse(200, [{ vuln_type: 'SQL Injection', timestamp: 'now', explanation: 'unsafe query', severity: 'HIGH' }]);
        },
    );

    const successResult = await successfulClient.analyzeCode({
        code: 'query = "SELECT * FROM users WHERE id=" + user_id',
        developer_id: 'parth',
        mode: 'security',
        file_uri: 'file:///demo.py',
        source: 'ide_extension',
    });
    assert.strictEqual(successResult.status, 'success');
    assert.strictEqual(successResult.vuln_type, 'SQL Injection');
    assert.strictEqual(successResult.scores.security, 20);
    assert.strictEqual(successResult.diff.new_issue_count, 1);
    assert.strictEqual(successResult.primary_finding.vuln_type, 'SQL Injection');
    assert.strictEqual(successResult.analysis_profile?.provider, 'nvidia');

    const dashboard = await successfulClient.getDashboard('parth');
    assert.strictEqual(dashboard?.total_events, 2);

    const timeline = await successfulClient.getTimeline('parth', 'file:///demo.py');
    assert.strictEqual(timeline.length, 1);
    assert.strictEqual(timeline[0]?.summary.vuln_type, 'SQL Injection');

    const fileState = await successfulClient.getFileState('parth', 'file:///demo.py');
    assert.strictEqual(fileState?.last_event_id, 'evt-1');

    const invalidClient = new AppSecApiClient(() => settings, async () => createResponse(200, { bad: 'shape' }));
    const invalidResult = await invalidClient.analyzeCode({
        code: 'print("hello")',
        developer_id: 'parth',
        mode: 'security',
    });
    assert.strictEqual(invalidResult.status, 'failed');
    assert.ok(invalidResult.errors[0]?.includes('invalid response shape'));

    const historyClient = new AppSecApiClient(
        () => settings,
        async () => createResponse(200, [{ vuln_type: 'SQL Injection', timestamp: 'now', explanation: 'unsafe query', severity: 'HIGH' }]),
    );
    const history = await historyClient.getDeveloperHistory('parth');
    assert.strictEqual(history.length, 1);
    assert.strictEqual(history[0]?.severity, 'HIGH');
}
