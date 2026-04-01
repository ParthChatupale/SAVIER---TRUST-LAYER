import { AnalysisMode, normalizeMode } from './contracts';

export interface ExtensionConfigurationValues {
    serverUrl?: unknown;
    developerId?: unknown;
    mode?: unknown;
    debounceMs?: unknown;
    requestTimeoutMs?: unknown;
    enabledLanguages?: unknown;
    autoAnalyze?: unknown;
}

export interface ExtensionSettings {
    serverUrl: string;
    developerId: string;
    mode: AnalysisMode;
    debounceMs: number;
    enabledLanguages: string[];
    autoAnalyze: boolean;
    requestTimeoutMs: number;
    dashboardHistoryLimit: number;
}

const DEFAULT_SERVER_URL = 'http://127.0.0.1:5000';
const DEFAULT_LANGUAGES = ['python', 'javascript', 'typescript'];
const DEFAULT_DEBOUNCE_MS = 1200;
const DEFAULT_REQUEST_TIMEOUT_MS = 60000;
const DEFAULT_DASHBOARD_HISTORY_LIMIT = 100;

function normalizeString(value: unknown, fallback = ''): string {
    return typeof value === 'string' ? value.trim() : fallback;
}

function normalizeNumber(value: unknown, fallback: number, minimum: number): number {
    return typeof value === 'number' && Number.isFinite(value) && value >= minimum
        ? value
        : fallback;
}

function normalizeLanguages(value: unknown): string[] {
    if (!Array.isArray(value)) {
        return DEFAULT_LANGUAGES;
    }

    const languages = value
        .filter((item): item is string => typeof item === 'string')
        .map((item) => item.trim())
        .filter(Boolean);

    return languages.length > 0 ? Array.from(new Set(languages)) : DEFAULT_LANGUAGES;
}

function resolveDeveloperId(explicitDeveloperId: string, env: NodeJS.ProcessEnv): string {
    if (explicitDeveloperId) {
        return explicitDeveloperId;
    }

    const fallback = env.USER ?? env.USERNAME ?? env.LOGNAME ?? 'developer';
    return fallback.trim() || 'developer';
}

export function resolveExtensionSettings(
    values: ExtensionConfigurationValues,
    env: NodeJS.ProcessEnv = process.env,
): ExtensionSettings {
    const serverUrl = normalizeString(values.serverUrl, DEFAULT_SERVER_URL).replace(/\/$/, '') || DEFAULT_SERVER_URL;
    const developerId = resolveDeveloperId(normalizeString(values.developerId), env);

    return {
        serverUrl,
        developerId,
        mode: normalizeMode(values.mode, 'full'),
        debounceMs: normalizeNumber(values.debounceMs, DEFAULT_DEBOUNCE_MS, 100),
        requestTimeoutMs: normalizeNumber(values.requestTimeoutMs, DEFAULT_REQUEST_TIMEOUT_MS, 1000),
        enabledLanguages: normalizeLanguages(values.enabledLanguages),
        autoAnalyze: typeof values.autoAnalyze === 'boolean' ? values.autoAnalyze : true,
        dashboardHistoryLimit: DEFAULT_DASHBOARD_HISTORY_LIMIT,
    };
}
