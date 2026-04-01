import { AnalysisResponse, AnalyzeCodeRequest, createFailedAnalysisResponse } from '../core/contracts';
import { ExtensionSettings } from '../core/config';
import { getLanguagePolicy, isLanguageEnabled } from '../core/languages';
import { AppSecApiClient } from './apiClient';
import { ExtensionStateStore } from './state';

export interface TextDocumentLike {
    readonly uri: string;
    readonly languageId: string;
    getText(): string;
}

export interface AnalyzerCallbacks {
    onAnalysisStarted(document: TextDocumentLike): void;
    onAnalysisSkipped(document: TextDocumentLike): void;
    onAnalysisCompleted(document: TextDocumentLike, result: AnalysisResponse): Promise<void> | void;
}

export class DocumentAnalyzer {
    private readonly timers = new Map<string, NodeJS.Timeout>();

    public constructor(
        private readonly getSettings: () => ExtensionSettings,
        private readonly apiClient: AppSecApiClient,
        private readonly stateStore: ExtensionStateStore,
        private readonly callbacks: AnalyzerCallbacks,
    ) {}

    public schedule(document: TextDocumentLike): void {
        const settings = this.getSettings();
        if (!settings.autoAnalyze) {
            return;
        }

        const existingTimer = this.timers.get(document.uri);
        if (existingTimer) {
            clearTimeout(existingTimer);
        }

        const timer = setTimeout(() => {
            void this.analyzeNow(document);
        }, settings.debounceMs);
        this.timers.set(document.uri, timer);
    }

    public async analyzeNow(document: TextDocumentLike): Promise<void> {
        this.clearScheduled(document.uri);

        const settings = this.getSettings();
        const policy = getLanguagePolicy(document.languageId);
        const code = document.getText();

        if (!policy || !isLanguageEnabled(document.languageId, settings.enabledLanguages) || code.trim().length < policy.minCodeLength) {
            this.callbacks.onAnalysisSkipped(document);
            return;
        }

        this.callbacks.onAnalysisStarted(document);
        const requestVersion = this.stateStore.nextRequestVersion(document.uri);
        this.stateStore.setActiveFileUri(document.uri);

        let result: AnalysisResponse;
        try {
            const request: AnalyzeCodeRequest = {
                code,
                developer_id: settings.developerId,
                mode: settings.mode,
                file_uri: document.uri,
                source: 'ide_extension',
            };
            result = await this.apiClient.analyzeCode(request);
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown AppSec extension error';
            result = createFailedAnalysisResponse(settings.developerId, settings.mode, message);
        }

        if (!this.stateStore.isLatestRequest(document.uri, requestVersion)) {
            return;
        }

        await this.callbacks.onAnalysisCompleted(document, result);
    }

    public clearDocument(uri: string): void {
        this.clearScheduled(uri);
        this.stateStore.clearDocument(uri);
    }

    public dispose(): void {
        for (const timer of this.timers.values()) {
            clearTimeout(timer);
        }
        this.timers.clear();
    }

    private clearScheduled(uri: string): void {
        const existingTimer = this.timers.get(uri);
        if (!existingTimer) {
            return;
        }

        clearTimeout(existingTimer);
        this.timers.delete(uri);
    }
}
