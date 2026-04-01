"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DocumentAnalyzer = void 0;
const contracts_1 = require("../core/contracts");
const languages_1 = require("../core/languages");
class DocumentAnalyzer {
    getSettings;
    apiClient;
    stateStore;
    callbacks;
    timers = new Map();
    constructor(getSettings, apiClient, stateStore, callbacks) {
        this.getSettings = getSettings;
        this.apiClient = apiClient;
        this.stateStore = stateStore;
        this.callbacks = callbacks;
    }
    schedule(document) {
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
    async analyzeNow(document) {
        this.clearScheduled(document.uri);
        const settings = this.getSettings();
        const policy = (0, languages_1.getLanguagePolicy)(document.languageId);
        const code = document.getText();
        if (!policy || !(0, languages_1.isLanguageEnabled)(document.languageId, settings.enabledLanguages) || code.trim().length < policy.minCodeLength) {
            this.callbacks.onAnalysisSkipped(document);
            return;
        }
        this.callbacks.onAnalysisStarted(document);
        const requestVersion = this.stateStore.nextRequestVersion(document.uri);
        this.stateStore.setActiveFileUri(document.uri);
        let result;
        try {
            const request = {
                code,
                developer_id: settings.developerId,
                mode: settings.mode,
                file_uri: document.uri,
                source: 'ide_extension',
            };
            result = await this.apiClient.analyzeCode(request);
        }
        catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown AppSec extension error';
            result = (0, contracts_1.createFailedAnalysisResponse)(settings.developerId, settings.mode, message);
        }
        if (!this.stateStore.isLatestRequest(document.uri, requestVersion)) {
            return;
        }
        await this.callbacks.onAnalysisCompleted(document, result);
    }
    clearDocument(uri) {
        this.clearScheduled(uri);
        this.stateStore.clearDocument(uri);
    }
    dispose() {
        for (const timer of this.timers.values()) {
            clearTimeout(timer);
        }
        this.timers.clear();
    }
    clearScheduled(uri) {
        const existingTimer = this.timers.get(uri);
        if (!existingTimer) {
            return;
        }
        clearTimeout(existingTimer);
        this.timers.delete(uri);
    }
}
exports.DocumentAnalyzer = DocumentAnalyzer;
//# sourceMappingURL=analyzer.js.map