"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppSecApiClient = void 0;
const contracts_1 = require("../core/contracts");
class AppSecApiClient {
    getSettings;
    fetchImpl;
    constructor(getSettings, fetchImpl = globalThis.fetch.bind(globalThis)) {
        this.getSettings = getSettings;
        this.fetchImpl = fetchImpl;
    }
    async analyzeCode(request) {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(`${this.getSettings().serverUrl}/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(request),
                    signal,
                });
                if (!response.ok) {
                    return (0, contracts_1.createFailedAnalysisResponse)(request.developer_id, request.mode, `AppSec service returned ${response.status}`);
                }
                const body = await response.json();
                return (0, contracts_1.parseAnalysisResponse)(body, request.developer_id, request.mode)
                    ?? (0, contracts_1.createFailedAnalysisResponse)(request.developer_id, request.mode, 'AppSec service returned an invalid response shape');
            });
        }
        catch (error) {
            const message = error instanceof Error && error.name === 'AbortError'
                ? 'AppSec service timed out'
                : `AppSec service unavailable: ${error instanceof Error ? error.message : 'unknown error'}`;
            return (0, contracts_1.createFailedAnalysisResponse)(request.developer_id, request.mode, message);
        }
    }
    async getDeveloperHistory(developerId) {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(`${this.getSettings().serverUrl}/history?developer_id=${encodeURIComponent(developerId)}`, { signal });
                if (!response.ok) {
                    return [];
                }
                const body = await response.json();
                return (0, contracts_1.parseHistoryEntries)(body);
            });
        }
        catch {
            return [];
        }
    }
    async getDashboard(developerId) {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(`${this.getSettings().serverUrl}/dashboard?developer_id=${encodeURIComponent(developerId)}`, { signal });
                if (!response.ok) {
                    return null;
                }
                const body = await response.json();
                return (0, contracts_1.parseDashboardSummary)(body);
            });
        }
        catch {
            return null;
        }
    }
    async getTimeline(developerId, fileUri, limit = 20) {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(`${this.getSettings().serverUrl}/timeline?developer_id=${encodeURIComponent(developerId)}&file_uri=${encodeURIComponent(fileUri)}&limit=${limit}`, { signal });
                if (!response.ok) {
                    return [];
                }
                const body = await response.json();
                return (0, contracts_1.parseAnalysisTimeline)(body);
            });
        }
        catch {
            return [];
        }
    }
    async getFileState(developerId, fileUri) {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(`${this.getSettings().serverUrl}/file-state?developer_id=${encodeURIComponent(developerId)}&file_uri=${encodeURIComponent(fileUri)}`, { signal });
                if (response.status === 404 || !response.ok) {
                    return null;
                }
                const body = await response.json();
                return (0, contracts_1.parseFileState)(body);
            });
        }
        catch {
            return null;
        }
    }
    async clearDeveloperHistory(developerId) {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(`${this.getSettings().serverUrl}/clear`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ developer_id: developerId }),
                    signal,
                });
                if (!response.ok) {
                    return { status: 'failed', developer_id: developerId };
                }
                const body = await response.json();
                return {
                    status: typeof body.status === 'string' ? body.status : 'unknown',
                    developer_id: typeof body.developer_id === 'string' ? body.developer_id : developerId,
                };
            });
        }
        catch {
            return { status: 'failed', developer_id: developerId };
        }
    }
    async withTimeout(operation) {
        const controller = new AbortController();
        const timeoutHandle = setTimeout(() => controller.abort(), this.getSettings().requestTimeoutMs);
        try {
            return await operation(controller.signal);
        }
        finally {
            clearTimeout(timeoutHandle);
        }
    }
}
exports.AppSecApiClient = AppSecApiClient;
//# sourceMappingURL=apiClient.js.map