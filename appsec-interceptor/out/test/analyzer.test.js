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
exports.runAnalyzerTests = runAnalyzerTests;
const assert = __importStar(require("assert"));
const config_1 = require("../core/config");
const analyzer_1 = require("../services/analyzer");
const apiClient_1 = require("../services/apiClient");
const state_1 = require("../services/state");
const memoryState = {
    get: (_key, defaultValue) => defaultValue,
    update: async () => undefined,
};
function createDocument(uri, languageId, code) {
    return {
        uri,
        languageId,
        getText: () => code,
    };
}
async function runAnalyzerTests() {
    const settings = (0, config_1.resolveExtensionSettings)({ developerId: 'parth', mode: 'security', debounceMs: 100 });
    const stateStore = new state_1.ExtensionStateStore(memoryState, 20);
    let analyzeCalls = 0;
    const capturedBodies = [];
    const completedStatuses = [];
    let resolveCompletion;
    const completionPromise = new Promise((resolve) => {
        resolveCompletion = resolve;
    });
    const client = new apiClient_1.AppSecApiClient(() => settings, async (_url, init) => {
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
    });
    const analyzer = new analyzer_1.DocumentAnalyzer(() => settings, client, stateStore, {
        onAnalysisStarted: () => undefined,
        onAnalysisSkipped: () => undefined,
        onAnalysisCompleted: async (_document, result) => {
            completedStatuses.push(result.status);
            resolveCompletion?.();
        },
    });
    analyzer.schedule(createDocument('file:///one.py', 'python', 'print("first") and more than twenty chars'));
    analyzer.schedule(createDocument('file:///one.py', 'python', 'print("second") and more than twenty chars'));
    await Promise.race([
        completionPromise,
        new Promise((_, reject) => setTimeout(() => reject(new Error('scheduled analysis did not complete in time')), 500)),
    ]);
    assert.strictEqual(analyzeCalls, 1);
    assert.deepStrictEqual(completedStatuses, ['success']);
    assert.ok(capturedBodies[0]?.includes('"file_uri":"file:///one.py"'));
    assert.ok(capturedBodies[0]?.includes('"source":"ide_extension"'));
    const unsupportedAnalyzer = new analyzer_1.DocumentAnalyzer(() => settings, client, stateStore, {
        onAnalysisStarted: () => assert.fail('unsupported language should not analyze'),
        onAnalysisSkipped: () => undefined,
        onAnalysisCompleted: () => assert.fail('unsupported language should not complete'),
    });
    await unsupportedAnalyzer.analyzeNow(createDocument('file:///file.txt', 'plaintext', 'this is enough content to skip'));
}
//# sourceMappingURL=analyzer.test.js.map