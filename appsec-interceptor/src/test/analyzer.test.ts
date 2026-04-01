import * as assert from 'assert';
import { resolveExtensionSettings } from '../core/config';
import { DocumentAnalyzer, TextDocumentLike } from '../services/analyzer';
import { AppSecApiClient } from '../services/apiClient';
import { ExtensionStateStore, WorkspaceStateLike } from '../services/state';

const memoryState: WorkspaceStateLike = {
    get: <T>(_key: string, defaultValue: T): T => defaultValue,
    update: async () => undefined,
};

function createDocument(uri: string, languageId: string, code: string): TextDocumentLike {
    return {
        uri,
        languageId,
        getText: () => code,
    };
}

export async function runAnalyzerTests(): Promise<void> {
    const settings = resolveExtensionSettings({ developerId: 'parth', mode: 'security', debounceMs: 100 });
    const stateStore = new ExtensionStateStore(memoryState, 20);
    let analyzeCalls = 0;
    const capturedBodies: string[] = [];
    const completedStatuses: string[] = [];
    let resolveCompletion: (() => void) | undefined;
    const completionPromise = new Promise<void>((resolve) => {
        resolveCompletion = resolve;
    });

    const client = new AppSecApiClient(
        () => settings,
        async (_url, init) => {
            analyzeCalls += 1;
            capturedBodies.push(String(init?.body ?? ''));
            await new Promise((resolve) => setTimeout(resolve, init?.body?.toString().includes('second') ? 5 : 30));
            return new Response(JSON.stringify({
                status: 'success',
                developer_id: 'parth',
                mode: 'security',
                vuln_found: false,
                vuln_type: '',
                severity: 'NONE',
                vulnerable_line: '',
                suggested_fix: '',
                attack_scenario: '',
                developer_note: '',
                full_explanation: '',
                owasp_category: '',
                errors: [],
                warnings: [],
                agent_trace: [],
                file_uri: 'file:///one.py',
                event_id: 'evt-1',
                scores: { overall: 100, security: 100, quality: 100, performance: 100 },
                diff: {
                    score_delta: 0,
                    fixed_count: 0,
                    new_issue_count: 0,
                    unchanged_count: 0,
                    fixed_findings: [],
                    new_findings: [],
                    unchanged_findings: [],
                },
                findings: [],
                dimensions: {},
                primary_finding: {
                    dimension: '',
                    vuln_type: '',
                    severity: 'NONE',
                    vulnerable_line: '',
                    pattern: '',
                    explanation: '',
                    suggested_fix: '',
                    confidence: 0,
                },
                analysis_profile: null,
                data_flow: '',
                planning: {},
            }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        },
    );

    const analyzer = new DocumentAnalyzer(
        () => settings,
        client,
        stateStore,
        {
            onAnalysisStarted: () => undefined,
            onAnalysisSkipped: () => undefined,
            onAnalysisCompleted: async (_document, result) => {
                completedStatuses.push(result.status);
                resolveCompletion?.();
            },
        },
    );

    analyzer.schedule(createDocument('file:///one.py', 'python', 'print("first") and more than twenty chars'));
    analyzer.schedule(createDocument('file:///one.py', 'python', 'print("second") and more than twenty chars'));
    await Promise.race([
        completionPromise,
        new Promise<void>((_, reject) => setTimeout(() => reject(new Error('scheduled analysis did not complete in time')), 500)),
    ]);
    assert.strictEqual(analyzeCalls, 1);
    assert.deepStrictEqual(completedStatuses, ['success']);
    assert.ok(capturedBodies[0]?.includes('"file_uri":"file:///one.py"'));
    assert.ok(capturedBodies[0]?.includes('"source":"ide_extension"'));

    const unsupportedAnalyzer = new DocumentAnalyzer(
        () => settings,
        client,
        stateStore,
        {
            onAnalysisStarted: () => assert.fail('unsupported language should not analyze'),
            onAnalysisSkipped: () => undefined,
            onAnalysisCompleted: () => assert.fail('unsupported language should not complete'),
        },
    );
    await unsupportedAnalyzer.analyzeNow(createDocument('file:///file.txt', 'plaintext', 'this is enough content to skip'));
}
