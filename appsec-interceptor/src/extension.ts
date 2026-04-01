import * as vscode from 'vscode';
import { resolveExtensionSettings, ExtensionConfigurationValues, ExtensionSettings } from './core/config';
import { DiagnosticsManager } from './editor/diagnostics';
import { AppSecApiClient } from './services/apiClient';
import { DocumentAnalyzer, TextDocumentLike } from './services/analyzer';
import { ActiveDashboardState, ExtensionStateStore } from './services/state';
import { createCommandSpecs } from './commands';
import { renderHistoryHtml } from './ui/historyPanel';
import { renderDashboardHtml } from './ui/dashboardPanel';
import { renderFileStateHtml } from './ui/fileStatePanel';
import { StatusBarController } from './ui/statusBar';

function readConfiguration(): ExtensionSettings {
    const configuration = vscode.workspace.getConfiguration('appsecInterceptor');
    const values: ExtensionConfigurationValues = {
        serverUrl: configuration.get('serverUrl'),
        developerId: configuration.get('developerId'),
        mode: configuration.get('mode'),
        debounceMs: configuration.get('debounceMs'),
        requestTimeoutMs: configuration.get('requestTimeoutMs'),
        enabledLanguages: configuration.get('enabledLanguages'),
        autoAnalyze: configuration.get('autoAnalyze'),
    };
    return resolveExtensionSettings(values, process.env);
}

function toDocumentLike(document: vscode.TextDocument): TextDocumentLike {
    return {
        uri: document.uri.toString(),
        languageId: document.languageId,
        getText: () => document.getText(),
    };
}

export function activate(context: vscode.ExtensionContext): void {
    let settings = readConfiguration();
    let refreshVersion = 0;

    const diagnosticsCollection = vscode.languages.createDiagnosticCollection('appsec-agent');
    const diagnostics = new DiagnosticsManager(diagnosticsCollection);
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    const statusBar = new StatusBarController(statusBarItem);
    const stateStore = new ExtensionStateStore(context.workspaceState, settings.dashboardHistoryLimit);
    const apiClient = new AppSecApiClient(() => settings);

    let historyPanel: vscode.WebviewPanel | undefined;
    let dashboardPanel: vscode.WebviewPanel | undefined;
    let fileStatePanel: vscode.WebviewPanel | undefined;

    const getActiveDocument = () => vscode.window.activeTextEditor?.document;
    const getActiveDocumentLike = () => {
        const document = getActiveDocument();
        return document ? toDocumentLike(document) : undefined;
    };

    const ensurePanel = (
        current: vscode.WebviewPanel | undefined,
        viewType: string,
        title: string,
    ): vscode.WebviewPanel => {
        if (current) {
            current.reveal(vscode.ViewColumn.Beside, true);
            return current;
        }
        const panel = vscode.window.createWebviewPanel(viewType, title, vscode.ViewColumn.Beside, { enableScripts: false, retainContextWhenHidden: true });
        panel.onDidDispose(() => {
            if (viewType === 'appsecHistory') {
                historyPanel = undefined;
            } else if (viewType === 'appsecDashboard') {
                dashboardPanel = undefined;
            } else if (viewType === 'appsecFileState') {
                fileStatePanel = undefined;
            }
        }, null, context.subscriptions);
        return panel;
    };

    const renderOpenPanels = async (): Promise<void> => {
        const activeState = stateStore.getActiveDashboardState();
        if (dashboardPanel) {
            dashboardPanel.webview.html = renderDashboardHtml(activeState);
        }
        if (fileStatePanel) {
            fileStatePanel.webview.html = renderFileStateHtml(activeState);
        }
        if (historyPanel) {
            const history = await apiClient.getDeveloperHistory(settings.developerId);
            historyPanel.webview.html = renderHistoryHtml(history, settings.developerId);
        }
    };

    const refreshDashboardState = async (fileUri: string, result: unknown): Promise<void> => {
        const currentVersion = ++refreshVersion;
        stateStore.startRefresh(fileUri);
        await renderOpenPanels();
        const [dashboard, fileState, timeline] = await Promise.all([
            apiClient.getDashboard(settings.developerId),
            apiClient.getFileState(settings.developerId, fileUri),
            apiClient.getTimeline(settings.developerId, fileUri, 12),
        ]);
        if (currentVersion !== refreshVersion) {
            return;
        }
        const candidateResult = (result as ActiveDashboardState['lastResult']) ?? null;
        const alignedResult = candidateResult?.file_uri === fileUri ? candidateResult : null;
        stateStore.finishRefresh({
            fileUri,
            dashboard,
            fileState,
            timeline,
            lastResult: alignedResult,
            error: dashboard ? '' : 'Dashboard data is not available yet.',
        });
        await renderOpenPanels();
    };

    const openHistory = async () => {
        historyPanel = ensurePanel(historyPanel, 'appsecHistory', 'Savier — Developer History');
        const history = await apiClient.getDeveloperHistory(settings.developerId);
        historyPanel.webview.html = renderHistoryHtml(history, settings.developerId);
    };

    const openDashboard = async () => {
        const activeDocument = getActiveDocument();
        if (activeDocument) {
            await refreshDashboardState(activeDocument.uri.toString(), stateStore.getActiveDashboardState().lastResult);
        }
        dashboardPanel = ensurePanel(dashboardPanel, 'appsecDashboard', 'Savier — Trust Cockpit');
        dashboardPanel.webview.html = renderDashboardHtml(stateStore.getActiveDashboardState());
        await stateStore.markDashboardOpened();
    };

    const openActiveFileState = async () => {
        const activeDocument = getActiveDocument();
        if (activeDocument) {
            await refreshDashboardState(activeDocument.uri.toString(), stateStore.getActiveDashboardState().lastResult);
        }
        fileStatePanel = ensurePanel(fileStatePanel, 'appsecFileState', 'Savier — Active File State');
        fileStatePanel.webview.html = renderFileStateHtml(stateStore.getActiveDashboardState());
    };

    const analyzer = new DocumentAnalyzer(
        () => settings,
        apiClient,
        stateStore,
        {
            onAnalysisStarted: (document) => statusBar.showAnalyzing(document.uri),
            onAnalysisSkipped: (document) => {
                diagnostics.clearDocument(vscode.Uri.parse(document.uri));
                stateStore.clearDocument(document.uri);
                void renderOpenPanels();
                statusBar.showReady();
            },
            onAnalysisCompleted: async (document, result) => {
                const editorDocument = vscode.workspace.textDocuments.find((openDocument) => openDocument.uri.toString() === document.uri);
                if (result.status !== 'failed' && editorDocument) {
                    diagnostics.updateDocument(editorDocument, result);
                }
                if (result.status === 'failed') {
                    stateStore.finishRefresh({
                        fileUri: document.uri,
                        dashboard: stateStore.getActiveDashboardState().dashboard,
                        fileState: stateStore.getActiveDashboardState().fileState,
                        timeline: stateStore.getActiveDashboardState().timeline,
                        lastResult: result,
                        error: result.errors[0] ?? 'Savier backend unavailable',
                    });
                    await renderOpenPanels();
                    statusBar.showResult(result);
                    return;
                }

                await refreshDashboardState(document.uri, result);
                statusBar.showResult(result);

                if (stateStore.shouldAutoOpenDashboard(result)) {
                    await openDashboard();
                }
            },
        },
    );

    const commandSpecs = createCommandSpecs({
        getSettings: () => settings,
        apiClient,
        analyzer,
        stateStore,
        openHistory,
        openDashboard,
        openActiveFileState,
        getActiveDocument: getActiveDocumentLike,
        notifyInfo: (message) => void vscode.window.showInformationMessage(message),
        notifyWarning: (message) => void vscode.window.showWarningMessage(message),
    });

    const disposables = commandSpecs.map((command) => vscode.commands.registerCommand(command.id, command.execute));

    const onDidChangeTextDocument = vscode.workspace.onDidChangeTextDocument((event) => {
        analyzer.schedule(toDocumentLike(event.document));
    });

    const onDidOpenTextDocument = vscode.workspace.onDidOpenTextDocument((document) => {
        stateStore.setActiveFileUri(document.uri.toString());
        analyzer.schedule(toDocumentLike(document));
    });

    const onDidCloseTextDocument = vscode.workspace.onDidCloseTextDocument((document) => {
        analyzer.clearDocument(document.uri.toString());
        diagnostics.clearDocument(document.uri);
        void renderOpenPanels();
    });

    const onDidChangeActiveTextEditor = vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (!editor) {
            return;
        }
        stateStore.setActiveFileUri(editor.document.uri.toString());
        void refreshDashboardState(editor.document.uri.toString(), stateStore.getActiveDashboardState().lastResult);
    });

    const onDidChangeConfiguration = vscode.workspace.onDidChangeConfiguration((event) => {
        if (!event.affectsConfiguration('appsecInterceptor')) {
            return;
        }
        settings = readConfiguration();
        statusBar.showReady();
    });

    context.subscriptions.push(
        diagnosticsCollection,
        statusBarItem,
        ...disposables,
        onDidChangeTextDocument,
        onDidOpenTextDocument,
        onDidCloseTextDocument,
        onDidChangeActiveTextEditor,
        onDidChangeConfiguration,
        { dispose: () => analyzer.dispose() },
    );

    statusBarItem.show();
    statusBar.showReady();

    if (settings.autoAnalyze) {
        for (const document of vscode.workspace.textDocuments) {
            stateStore.setActiveFileUri(document.uri.toString());
            analyzer.schedule(toDocumentLike(document));
        }
    }
}

export function deactivate(): void {
    // VS Code disposes subscriptions for us.
}
