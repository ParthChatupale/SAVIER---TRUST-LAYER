"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolveExtensionSettings = resolveExtensionSettings;
const contracts_1 = require("./contracts");
const DEFAULT_SERVER_URL = 'http://127.0.0.1:5000';
const DEFAULT_LANGUAGES = ['python', 'javascript', 'typescript'];
const DEFAULT_DEBOUNCE_MS = 1200;
const DEFAULT_REQUEST_TIMEOUT_MS = 60000;
const DEFAULT_DASHBOARD_HISTORY_LIMIT = 100;
function normalizeString(value, fallback = '') {
    return typeof value === 'string' ? value.trim() : fallback;
}
function normalizeNumber(value, fallback, minimum) {
    return typeof value === 'number' && Number.isFinite(value) && value >= minimum
        ? value
        : fallback;
}
function normalizeLanguages(value) {
    if (!Array.isArray(value)) {
        return DEFAULT_LANGUAGES;
    }
    const languages = value
        .filter((item) => typeof item === 'string')
        .map((item) => item.trim())
        .filter(Boolean);
    return languages.length > 0 ? Array.from(new Set(languages)) : DEFAULT_LANGUAGES;
}
function resolveDeveloperId(explicitDeveloperId, env) {
    if (explicitDeveloperId) {
        return explicitDeveloperId;
    }
    const fallback = env.USER ?? env.USERNAME ?? env.LOGNAME ?? 'developer';
    return fallback.trim() || 'developer';
}
function resolveExtensionSettings(values, env = process.env) {
    const serverUrl = normalizeString(values.serverUrl, DEFAULT_SERVER_URL).replace(/\/$/, '') || DEFAULT_SERVER_URL;
    const developerId = resolveDeveloperId(normalizeString(values.developerId), env);
    return {
        serverUrl,
        developerId,
        mode: (0, contracts_1.normalizeMode)(values.mode, 'full'),
        debounceMs: normalizeNumber(values.debounceMs, DEFAULT_DEBOUNCE_MS, 100),
        requestTimeoutMs: normalizeNumber(values.requestTimeoutMs, DEFAULT_REQUEST_TIMEOUT_MS, 1000),
        enabledLanguages: normalizeLanguages(values.enabledLanguages),
        autoAnalyze: typeof values.autoAnalyze === 'boolean' ? values.autoAnalyze : true,
        dashboardHistoryLimit: DEFAULT_DASHBOARD_HISTORY_LIMIT,
    };
}
//# sourceMappingURL=config.js.map