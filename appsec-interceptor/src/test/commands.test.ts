import * as assert from 'assert';
import { createCommandSpecs } from '../commands';
import { resolveExtensionSettings } from '../core/config';
import { AppSecApiClient } from '../services/apiClient';
import { DocumentAnalyzer } from '../services/analyzer';
import { ExtensionStateStore, WorkspaceStateLike } from '../services/state';

const memoryState: WorkspaceStateLike = {
    get: <T>(_key: string, defaultValue: T): T => defaultValue,
    update: async () => undefined,
};

export async function runCommandTests(): Promise<void> {
    const settings = resolveExtensionSettings({ developerId: 'parth' });
    const apiClient = new AppSecApiClient(
        () => settings,
        async (_url, init) => new Response(JSON.stringify(
            typeof init?.body === 'string' && init.body.includes('developer_id')
                ? { status: 'cleared', developer_id: 'parth' }
                : []
        ), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );
    const analyzer = new DocumentAnalyzer(
        () => settings,
        apiClient,
        new ExtensionStateStore(memoryState, 10),
        {
            onAnalysisStarted: () => undefined,
            onAnalysisSkipped: () => undefined,
            onAnalysisCompleted: async () => undefined,
        },
    );
    const stateStore = new ExtensionStateStore(memoryState, 10);

    let historyOpened = false;
    let dashboardOpened = false;
    let fileStateOpened = false;
    let warningMessage = '';

    const commands = createCommandSpecs({
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

    assert.deepStrictEqual(
        commands.map((command) => command.id),
        [
            'appsec-interceptor.showHistory',
            'appsec-interceptor.showDashboard',
            'appsec-interceptor.showFileState',
            'appsec-interceptor.clearHistory',
            'appsec-interceptor.rerunAnalysis',
        ],
    );

    await commands[0]?.execute();
    await commands[1]?.execute();
    await commands[2]?.execute();
    await commands[4]?.execute();

    assert.strictEqual(historyOpened, true);
    assert.strictEqual(dashboardOpened, true);
    assert.strictEqual(fileStateOpened, false);
    assert.ok(warningMessage.includes('Open a supported file'));
}
