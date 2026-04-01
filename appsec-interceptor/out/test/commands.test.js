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
exports.runCommandTests = runCommandTests;
const assert = __importStar(require("assert"));
const commands_1 = require("../commands");
const config_1 = require("../core/config");
const apiClient_1 = require("../services/apiClient");
const analyzer_1 = require("../services/analyzer");
const state_1 = require("../services/state");
const memoryState = {
    get: (_key, defaultValue) => defaultValue,
    update: async () => undefined,
};
async function runCommandTests() {
    const settings = (0, config_1.resolveExtensionSettings)({ developerId: 'parth' });
    const apiClient = new apiClient_1.AppSecApiClient(() => settings, async (_url, init) => new Response(JSON.stringify(typeof init?.body === 'string' && init.body.includes('developer_id')
        ? { status: 'cleared', developer_id: 'parth' }
        : []), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    const analyzer = new analyzer_1.DocumentAnalyzer(() => settings, apiClient, new state_1.ExtensionStateStore(memoryState, 10), {
        onAnalysisStarted: () => undefined,
        onAnalysisSkipped: () => undefined,
        onAnalysisCompleted: async () => undefined,
    });
    const stateStore = new state_1.ExtensionStateStore(memoryState, 10);
    let historyOpened = false;
    let dashboardOpened = false;
    let fileStateOpened = false;
    let warningMessage = '';
    const commands = (0, commands_1.createCommandSpecs)({
        getSettings: () => settings,
        apiClient,
        analyzer,
        stateStore,
        openHistory: async () => { historyOpened = true; },
        openDashboard: async () => { dashboardOpened = true; },
        openActiveFileState: async () => { fileStateOpened = true; },
        getActiveDocument: () => undefined,
        notifyInfo: () => undefined,
        notifyWarning: (message) => { warningMessage = message; },
    });
    assert.deepStrictEqual(commands.map((command) => command.id), [
        'appsec-interceptor.showHistory',
        'appsec-interceptor.showDashboard',
        'appsec-interceptor.showFileState',
        'appsec-interceptor.clearHistory',
        'appsec-interceptor.rerunAnalysis',
    ]);
    await commands[0]?.execute();
    await commands[1]?.execute();
    await commands[2]?.execute();
    await commands[4]?.execute();
    assert.strictEqual(historyOpened, true);
    assert.strictEqual(dashboardOpened, true);
    assert.strictEqual(fileStateOpened, false);
    assert.ok(warningMessage.includes('Open a supported file'));
}
//# sourceMappingURL=commands.test.js.map