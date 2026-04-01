import * as assert from 'assert';
import { ExtensionStateStore, WorkspaceStateLike } from '../services/state';

const memoryState: WorkspaceStateLike = {
    get: <T>(_key: string, defaultValue: T): T => defaultValue,
    update: async () => undefined,
};

export async function runStateTests(): Promise<void> {
    const store = new ExtensionStateStore(memoryState, 10);

    store.finishRefresh({
        fileUri: 'file:///one.py',
        dashboard: null,
        timeline: [{
            event_id: 'evt-1',
            developer_id: 'parth',
            file_uri: 'file:///one.py',
            source: 'ide_extension',
            mode: 'full',
            content_hash: 'hash-1',
            status: 'success',
            project_id: '',
            timestamp: new Date().toISOString(),
            scores: { overall: 48, security: 0, quality: 85, performance: 60 },
            findings: [],
            diff: {
                score_delta: 0,
                fixed_count: 0,
                new_issue_count: 4,
                unchanged_count: 0,
                fixed_findings: [],
                new_findings: ['security:SQL Injection'],
                unchanged_findings: [],
            },
            summary: { vuln_type: 'SQL Injection', severity: 'CRITICAL', status: 'success' },
        }],
        fileState: {
            developer_id: 'parth',
            file_uri: 'file:///one.py',
            content_hash: 'hash-1',
            last_event_id: 'evt-1',
            source: 'ide_extension',
            mode: 'full',
            status: 'success',
            updated_at: new Date().toISOString(),
            project_id: '',
            scores: { overall: 48, security: 0, quality: 85, performance: 60 },
            findings: [{
                key: 'security:SQL Injection:query',
                dimension: 'security',
                issue_type: 'SQL Injection',
                severity: 'CRITICAL',
                line: 'query = user_input',
                explanation: 'Unsafe SQL concatenation',
            }],
        },
        lastResult: {
            status: 'success',
            developer_id: 'parth',
            mode: 'full',
            vuln_found: true,
            vuln_type: 'SQL Injection',
            severity: 'CRITICAL',
            vulnerable_line: 'query = user_input',
            suggested_fix: 'Use parameters',
            attack_scenario: 'Unsafe SQL concatenation',
            developer_note: 'Unsafe SQL concatenation',
            full_explanation: 'Unsafe SQL concatenation',
            owasp_category: 'A03:2021 - Injection',
            errors: [],
            warnings: [],
            agent_trace: [],
            file_uri: 'file:///one.py',
            event_id: 'evt-1',
            scores: { overall: 48, security: 0, quality: 85, performance: 60 },
            diff: {
                score_delta: 0,
                fixed_count: 0,
                new_issue_count: 4,
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
                vulnerable_line: 'query = user_input',
                pattern: 'Unsafe SQL concatenation',
                explanation: 'Unsafe SQL concatenation',
                suggested_fix: 'Use parameters',
                confidence: 0.9,
            },
            analysis_profile: null,
            data_flow: '',
            planning: {},
        },
    });

    store.startRefresh('file:///two.py');
    const refreshed = store.getActiveDashboardState();

    assert.strictEqual(refreshed.fileUri, 'file:///two.py');
    assert.strictEqual(refreshed.loading, true);
    assert.strictEqual(refreshed.fileState, null);
    assert.deepStrictEqual(refreshed.timeline, []);
    assert.strictEqual(refreshed.lastResult, null);
}
