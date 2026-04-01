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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const config_1 = require("./core/config");
const diagnostics_1 = require("./editor/diagnostics");
const apiClient_1 = require("./services/apiClient");
const analyzer_1 = require("./services/analyzer");
const state_1 = require("./services/state");
const commands_1 = require("./commands");
const historyPanel_1 = require("./ui/historyPanel");
const dashboardPanel_1 = require("./ui/dashboardPanel");
const fileStatePanel_1 = require("./ui/fileStatePanel");
const statusBar_1 = require("./ui/statusBar");
function readConfiguration() {
    const configuration = vscode.workspace.getConfiguration('appsecInterceptor');
    const values = {
        serverUrl: configuration.get('serverUrl'),
        developerId: configuration.get('developerId'),
        mode: configuration.get('mode'),
        debounceMs: configuration.get('debounceMs'),
        requestTimeoutMs: configuration.get('requestTimeoutMs'),
        enabledLanguages: configuration.get('enabledLanguages'),
        autoAnalyze: configuration.get('autoAnalyze'),
    };
    return (0, config_1.resolveExtensionSettings)(values, process.env);
}
function toDocumentLike(document) {
    return {
        uri: document.uri.toString(),
        languageId: document.languageId,
        getText: () => document.getText(),
    };
}
function activate(context) {
    let settings = readConfiguration();
    let refreshVersion = 0;
    const diagnosticsCollection = vscode.languages.createDiagnosticCollection('appsec-agent');
    const diagnostics = new diagnostics_1.DiagnosticsManager(diagnosticsCollection);
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    const statusBar = new statusBar_1.StatusBarController(statusBarItem);
    const stateStore = new state_1.ExtensionStateStore(context.workspaceState, settings.dashboardHistoryLimit);
    const apiClient = new apiClient_1.AppSecApiClient(() => settings);
    let historyPanel;
    let dashboardPanel;
    let fileStatePanel;
    const getActiveDocument = () => vscode.window.activeTextEditor?.document;
    const getActiveDocumentLike = () => {
        const document = getActiveDocument();
        return document ? toDocumentLike(document) : undefined;
    };
    const ensurePanel = (current, viewType, title) => {
        if (current) {
            current.reveal(vscode.ViewColumn.Beside, true);
            return current;
        }
        const panel = vscode.window.createWebviewPanel(viewType, title, vscode.ViewColumn.Beside, { enableScripts: false, retainContextWhenHidden: true });
        panel.onDidDispose(() => {
            if (viewType === 'appsecHistory') {
                historyPanel = undefined;
            }
            else if (viewType === 'appsecDashboard') {
                dashboardPanel = undefined;
            }
            else if (viewType === 'appsecFileState') {
                fileStatePanel = undefined;
            }
        }, null, context.subscriptions);
        return panel;
    };
    const renderOpenPanels = async () => {
        const activeState = stateStore.getActiveDashboardState();
        if (dashboardPanel) {
            dashboardPanel.webview.html = (0, dashboardPanel_1.renderDashboardHtml)(activeState);
        }
        if (fileStatePanel) {
            fileStatePanel.webview.html = (0, fileStatePanel_1.renderFileStateHtml)(activeState);
        }
        if (historyPanel) {
            const history = await apiClient.getDeveloperHistory(settings.developerId);
            historyPanel.webview.html = (0, historyPanel_1.renderHistoryHtml)(history, settings.developerId);
        }
    };
    const refreshDashboardState = async (fileUri, result) => {
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
        const candidateResult = result ?? null;
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
        historyPanel.webview.html = (0, historyPanel_1.renderHistoryHtml)(history, settings.developerId);
    };
    const openDashboard = async () => {
        const activeDocument = getActiveDocument();
        if (activeDocument) {
            await refreshDashboardState(activeDocument.uri.toString(), stateStore.getActiveDashboardState().lastResult);
        }
        dashboardPanel = ensurePanel(dashboardPanel, 'appsecDashboard', 'Savier — Trust Cockpit');
        dashboardPanel.webview.html = (0, dashboardPanel_1.renderDashboardHtml)(stateStore.getActiveDashboardState());
        await stateStore.markDashboardOpened();
    };
    const openActiveFileState = async () => {
        const activeDocument = getActiveDocument();
        if (activeDocument) {
            await refreshDashboardState(activeDocument.uri.toString(), stateStore.getActiveDashboardState().lastResult);
        }
        fileStatePanel = ensurePanel(fileStatePanel, 'appsecFileState', 'Savier — Active File State');
        fileStatePanel.webview.html = (0, fileStatePanel_1.renderFileStateHtml)(stateStore.getActiveDashboardState());
    };
    const analyzer = new analyzer_1.DocumentAnalyzer(() => settings, apiClient, stateStore, {
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
    });
    const commandSpecs = (0, commands_1.createCommandSpecs)({
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
    context.subscriptions.push(diagnosticsCollection, statusBarItem, ...disposables, onDidChangeTextDocument, onDidOpenTextDocument, onDidCloseTextDocument, onDidChangeActiveTextEditor, onDidChangeConfiguration, { dispose: () => analyzer.dispose() });
    statusBarItem.show();
    statusBar.showReady();
    if (settings.autoAnalyze) {
        for (const document of vscode.workspace.textDocuments) {
            stateStore.setActiveFileUri(document.uri.toString());
            analyzer.schedule(toDocumentLike(document));
        }
    }
}
function deactivate() {
    // VS Code disposes subscriptions for us.
}
//# sourceMappingURL=extension.js.map