import {
    AnalysisEvent,
    AnalysisResponse,
    AnalyzeCodeRequest,
    DashboardSummary,
    FileState,
    HistoryEntry,
    createFailedAnalysisResponse,
    parseAnalysisResponse,
    parseAnalysisTimeline,
    parseDashboardSummary,
    parseFileState,
    parseHistoryEntries,
} from '../core/contracts';
import { ExtensionSettings } from '../core/config';

export interface FetchLike {
    (input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
}

export interface ClearHistoryResult {
    status: string;
    developer_id: string;
}

export class AppSecApiClient {
    public constructor(
        private readonly getSettings: () => ExtensionSettings,
        private readonly fetchImpl: FetchLike = globalThis.fetch.bind(globalThis),
    ) {}

    public async analyzeCode(request: AnalyzeCodeRequest): Promise<AnalysisResponse> {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(`${this.getSettings().serverUrl}/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(request),
                    signal,
                });

                if (!response.ok) {
                    return createFailedAnalysisResponse(
                        request.developer_id,
                        request.mode,
                        `AppSec service returned ${response.status}`,
                    );
                }

                const body = await response.json() as unknown;
                return parseAnalysisResponse(body, request.developer_id, request.mode)
                    ?? createFailedAnalysisResponse(request.developer_id, request.mode, 'AppSec service returned an invalid response shape');
            });
        } catch (error) {
            const message = error instanceof Error && error.name === 'AbortError'
                ? 'AppSec service timed out'
                : `AppSec service unavailable: ${error instanceof Error ? error.message : 'unknown error'}`;
            return createFailedAnalysisResponse(request.developer_id, request.mode, message);
        }
    }

    public async getDeveloperHistory(developerId: string): Promise<HistoryEntry[]> {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(
                    `${this.getSettings().serverUrl}/history?developer_id=${encodeURIComponent(developerId)}`,
                    { signal },
                );
                if (!response.ok) {
                    return [];
                }

                const body = await response.json() as unknown;
                return parseHistoryEntries(body);
            });
        } catch {
            return [];
        }
    }

    public async getDashboard(developerId: string): Promise<DashboardSummary | null> {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(
                    `${this.getSettings().serverUrl}/dashboard?developer_id=${encodeURIComponent(developerId)}`,
                    { signal },
                );
                if (!response.ok) {
                    return null;
                }

                const body = await response.json() as unknown;
                return parseDashboardSummary(body);
            });
        } catch {
            return null;
        }
    }

    public async getTimeline(developerId: string, fileUri: string, limit = 20): Promise<AnalysisEvent[]> {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(
                    `${this.getSettings().serverUrl}/timeline?developer_id=${encodeURIComponent(developerId)}&file_uri=${encodeURIComponent(fileUri)}&limit=${limit}`,
                    { signal },
                );
                if (!response.ok) {
                    return [];
                }

                const body = await response.json() as unknown;
                return parseAnalysisTimeline(body);
            });
        } catch {
            return [];
        }
    }

    public async getFileState(developerId: string, fileUri: string): Promise<FileState | null> {
        try {
            return await this.withTimeout(async (signal) => {
                const response = await this.fetchImpl(
                    `${this.getSettings().serverUrl}/file-state?developer_id=${encodeURIComponent(developerId)}&file_uri=${encodeURIComponent(fileUri)}`,
                    { signal },
                );
                if (response.status === 404 || !response.ok) {
                    return null;
                }

                const body = await response.json() as unknown;
                return parseFileState(body);
            });
        } catch {
            return null;
        }
    }

    public async clearDeveloperHistory(developerId: string): Promise<ClearHistoryResult> {
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

                const body = await response.json() as Record<string, unknown>;
                return {
                    status: typeof body.status === 'string' ? body.status : 'unknown',
                    developer_id: typeof body.developer_id === 'string' ? body.developer_id : developerId,
                };
            });
        } catch {
            return { status: 'failed', developer_id: developerId };
        }
    }

    private async withTimeout<T>(operation: (signal: AbortSignal) => Promise<T>): Promise<T> {
        const controller = new AbortController();
        const timeoutHandle = setTimeout(() => controller.abort(), this.getSettings().requestTimeoutMs);

        try {
            return await operation(controller.signal);
        } finally {
            clearTimeout(timeoutHandle);
        }
    }
}
