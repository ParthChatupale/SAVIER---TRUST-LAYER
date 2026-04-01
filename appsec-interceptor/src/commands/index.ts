import { ExtensionSettings } from '../core/config';
import { DocumentAnalyzer, TextDocumentLike } from '../services/analyzer';
import { AppSecApiClient } from '../services/apiClient';
import { ExtensionStateStore } from '../services/state';
import { CommandSpec } from './contracts';

export interface CommandDependencies {
    getSettings(): ExtensionSettings;
    apiClient: AppSecApiClient;
    analyzer: DocumentAnalyzer;
    stateStore: ExtensionStateStore;
    openHistory(): Promise<void> | void;
    openDashboard(): Promise<void> | void;
    openActiveFileState(): Promise<void> | void;
    getActiveDocument(): TextDocumentLike | undefined;
    notifyInfo(message: string): void;
    notifyWarning(message: string): void;
}

export function createCommandSpecs(dependencies: CommandDependencies): CommandSpec[] {
    return [
        {
            id: 'appsec-interceptor.showHistory',
            title: 'Savier: Show Developer History',
            execute: async () => {
                await dependencies.openHistory();
            },
        },
        {
            id: 'appsec-interceptor.showDashboard',
            title: 'Savier: Show Trust Cockpit',
            execute: async () => {
                await dependencies.openDashboard();
            },
        },
        {
            id: 'appsec-interceptor.showFileState',
            title: 'Savier: Show Active File State',
            execute: async () => {
                const activeDocument = dependencies.getActiveDocument();
                if (!activeDocument) {
                    dependencies.notifyWarning('Open a supported file before viewing the active file state.');
                    return;
                }
                await dependencies.openActiveFileState();
            },
        },
        {
            id: 'appsec-interceptor.clearHistory',
            title: 'Savier: Clear Developer History',
            execute: async () => {
                const settings = dependencies.getSettings();
                const result = await dependencies.apiClient.clearDeveloperHistory(settings.developerId);
                await dependencies.stateStore.resetDemoState();
                if (result.status === 'cleared') {
                    dependencies.notifyInfo('AppSec developer history cleared.');
                } else {
                    dependencies.notifyWarning('AppSec could not confirm history clearing.');
                }
            },
        },
        {
            id: 'appsec-interceptor.rerunAnalysis',
            title: 'Savier: Re-run Analysis for Active File',
            execute: async () => {
                const activeDocument = dependencies.getActiveDocument();
                if (!activeDocument) {
                    dependencies.notifyWarning('Open a supported file before re-running AppSec analysis.');
                    return;
                }
                await dependencies.analyzer.analyzeNow(activeDocument);
            },
        },
    ];
}
