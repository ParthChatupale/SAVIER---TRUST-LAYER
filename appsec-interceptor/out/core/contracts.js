"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FINDING_SEVERITIES = exports.ANALYSIS_STATUSES = exports.ANALYSIS_MODES = void 0;
exports.normalizeMode = normalizeMode;
exports.normalizeSeverity = normalizeSeverity;
exports.parseAgentTrace = parseAgentTrace;
exports.createFailedAnalysisResponse = createFailedAnalysisResponse;
exports.parseAnalysisResponse = parseAnalysisResponse;
exports.parseHistoryEntries = parseHistoryEntries;
exports.parseAnalysisEvent = parseAnalysisEvent;
exports.parseAnalysisTimeline = parseAnalysisTimeline;
exports.parseFileState = parseFileState;
exports.parseDashboardSummary = parseDashboardSummary;
exports.ANALYSIS_MODES = ['security', 'quality', 'performance', 'full'];
exports.ANALYSIS_STATUSES = ['success', 'partial', 'failed'];
exports.FINDING_SEVERITIES = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
function isObject(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}
function asString(value, fallback = '') {
    return typeof value === 'string' ? value : fallback;
}
function asBoolean(value, fallback = false) {
    return typeof value === 'boolean' ? value : fallback;
}
function asNumber(value, fallback = 0) {
    return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}
function asStringArray(value) {
    return Array.isArray(value) ? value.filter((item) => typeof item === 'string') : [];
}
function normalizeMode(value, fallback = 'security') {
    return typeof value === 'string' && exports.ANALYSIS_MODES.includes(value)
        ? value
        : fallback;
}
function normalizeSeverity(value, fallback = 'NONE') {
    if (typeof value !== 'string') {
        return fallback;
    }
    const normalized = value.trim().toUpperCase();
    return exports.FINDING_SEVERITIES.includes(normalized)
        ? normalized
        : fallback;
}
function parseScores(value) {
    if (!isObject(value)) {
        return { overall: 0, security: 0, quality: 0, performance: 0 };
    }
    return {
        overall: asNumber(value.overall),
        security: asNumber(value.security),
        quality: asNumber(value.quality),
        performance: asNumber(value.performance),
    };
}
function parseDimensionFinding(value) {
    if (!isObject(value)) {
        return null;
    }
    const dimension = asString(value.dimension);
    if (!['security', 'quality', 'performance'].includes(dimension)) {
        return null;
    }
    return {
        dimension: dimension,
        vuln_found: asBoolean(value.vuln_found, false),
        vuln_type: asString(value.vuln_type),
        vulnerable_line: asString(value.vulnerable_line),
        pattern: asString(value.pattern),
        attack_scenario: asString(value.attack_scenario),
        suggested_fix: asString(value.suggested_fix),
        confidence: asNumber(value.confidence),
        severity: normalizeSeverity(value.severity),
    };
}
function parseDimensionFindings(value) {
    if (!Array.isArray(value)) {
        return [];
    }
    return value
        .map((item) => parseDimensionFinding(item))
        .filter((item) => Boolean(item));
}
function parseDimensionResult(value) {
    if (!isObject(value)) {
        return null;
    }
    const dimension = asString(value.dimension);
    if (!['security', 'quality', 'performance'].includes(dimension)) {
        return null;
    }
    const status = asString(value.status);
    return {
        dimension: dimension,
        status: ['success', 'partial', 'failed', 'skipped'].includes(status)
            ? status
            : 'failed',
        warnings: asStringArray(value.warnings),
        summary: asString(value.summary),
        finding_count: asNumber(value.finding_count),
        top_severity: normalizeSeverity(value.top_severity),
        findings: parseDimensionFindings(value.findings),
    };
}
function parseDimensions(value) {
    if (!isObject(value)) {
        return {};
    }
    const entries = Object.entries(value)
        .map(([key, entry]) => [key, parseDimensionResult(entry)])
        .filter((entry) => {
        return ['security', 'quality', 'performance'].includes(entry[0]) && Boolean(entry[1]);
    });
    return Object.fromEntries(entries);
}
function parsePrimaryFinding(value) {
    if (!isObject(value)) {
        return {
            dimension: '',
            vuln_type: '',
            severity: 'NONE',
            vulnerable_line: '',
            pattern: '',
            explanation: '',
            suggested_fix: '',
            confidence: 0,
        };
    }
    const dimension = asString(value.dimension);
    return {
        dimension: ['security', 'quality', 'performance'].includes(dimension)
            ? dimension
            : '',
        vuln_type: asString(value.vuln_type),
        severity: normalizeSeverity(value.severity),
        vulnerable_line: asString(value.vulnerable_line),
        pattern: asString(value.pattern),
        explanation: asString(value.explanation),
        suggested_fix: asString(value.suggested_fix),
        confidence: asNumber(value.confidence),
    };
}
function parseAnalysisProfile(value) {
    if (!isObject(value)) {
        return null;
    }
    const modelProfile = isObject(value.model_profile)
        ? Object.fromEntries(Object.entries(value.model_profile)
            .filter((entry) => typeof entry[0] === 'string' && typeof entry[1] === 'string'))
        : {};
    return {
        pipeline_version: asString(value.pipeline_version),
        provider: asString(value.provider),
        enabled_agents: asStringArray(value.enabled_agents),
        model_profile: modelProfile,
        fingerprint: asString(value.fingerprint),
    };
}
function parseDiff(value) {
    if (!isObject(value)) {
        return {
            score_delta: 0,
            fixed_count: 0,
            new_issue_count: 0,
            unchanged_count: 0,
            fixed_findings: [],
            new_findings: [],
            unchanged_findings: [],
        };
    }
    return {
        score_delta: asNumber(value.score_delta),
        fixed_count: asNumber(value.fixed_count),
        new_issue_count: asNumber(value.new_issue_count),
        unchanged_count: asNumber(value.unchanged_count),
        fixed_findings: asStringArray(value.fixed_findings),
        new_findings: asStringArray(value.new_findings),
        unchanged_findings: asStringArray(value.unchanged_findings),
    };
}
function parseFindingRecord(value) {
    if (!isObject(value)) {
        return null;
    }
    const dimension = asString(value.dimension);
    if (!['security', 'quality', 'performance'].includes(dimension)) {
        return null;
    }
    return {
        key: asString(value.key),
        dimension: dimension,
        issue_type: asString(value.issue_type),
        severity: normalizeSeverity(value.severity),
        line: asString(value.line),
        explanation: asString(value.explanation),
    };
}
function parseFindingRecords(value) {
    if (!Array.isArray(value)) {
        return [];
    }
    return value
        .map((item) => parseFindingRecord(item))
        .filter((item) => Boolean(item));
}
function parseAgentTrace(value) {
    if (!Array.isArray(value)) {
        return [];
    }
    return value
        .filter(isObject)
        .map((entry) => ({
        agent: asString(entry.agent || entry.name, 'unknown'),
        stage: asString(entry.stage, 'unknown'),
        status: ['success', 'partial', 'failed', 'skipped'].includes(asString(entry.status))
            ? asString(entry.status)
            : 'failed',
        model: asString(entry.model),
        error: asString(entry.error) || undefined,
    }));
}
function createFailedAnalysisResponse(developerId, mode, message) {
    return {
        status: 'failed',
        developer_id: developerId,
        mode,
        vuln_found: false,
        vuln_type: '',
        severity: 'NONE',
        vulnerable_line: '',
        suggested_fix: '',
        attack_scenario: '',
        developer_note: '',
        full_explanation: '',
        owasp_category: '',
        errors: [message],
        warnings: [],
        agent_trace: [],
        file_uri: '',
        event_id: '',
        scores: { overall: 0, security: 0, quality: 0, performance: 0 },
        diff: {
            score_delta: 0,
            fixed_count: 0,
            new_issue_count: 0,
            unchanged_count: 0,
            fixed_findings: [],
            new_findings: [],
            unchanged_findings: [],
        },
        findings: [],
        dimensions: {},
        primary_finding: {
            dimension: '',
            vuln_type: '',
            severity: 'NONE',
            vulnerable_line: '',
            pattern: '',
            explanation: '',
            suggested_fix: '',
            confidence: 0,
        },
        analysis_profile: null,
        data_flow: '',
        planning: {},
    };
}
function parseAnalysisResponse(value, developerId, mode) {
    if (!isObject(value)) {
        return null;
    }
    const status = asString(value.status);
    if (!exports.ANALYSIS_STATUSES.includes(status)) {
        return null;
    }
    return {
        status: status,
        developer_id: asString(value.developer_id, developerId),
        mode: normalizeMode(value.mode, mode),
        vuln_found: asBoolean(value.vuln_found, false),
        vuln_type: asString(value.vuln_type),
        severity: normalizeSeverity(value.severity),
        vulnerable_line: asString(value.vulnerable_line),
        suggested_fix: asString(value.suggested_fix),
        attack_scenario: asString(value.attack_scenario),
        developer_note: asString(value.developer_note),
        full_explanation: asString(value.full_explanation),
        owasp_category: asString(value.owasp_category),
        errors: asStringArray(value.errors),
        warnings: asStringArray(value.warnings),
        agent_trace: parseAgentTrace(value.agent_trace),
        file_uri: asString(value.file_uri),
        event_id: asString(value.event_id),
        scores: parseScores(value.scores),
        diff: parseDiff(value.diff),
        findings: parseDimensionFindings(value.findings),
        dimensions: parseDimensions(value.dimensions),
        primary_finding: parsePrimaryFinding(value.primary_finding),
        analysis_profile: parseAnalysisProfile(value.analysis_profile),
        data_flow: asString(value.data_flow),
        planning: isObject(value.planning) ? value.planning : {},
    };
}
function parseHistoryEntries(value) {
    if (!Array.isArray(value)) {
        return [];
    }
    return value
        .filter(isObject)
        .map((entry) => ({
        vuln_type: asString(entry.vuln_type),
        timestamp: asString(entry.timestamp),
        explanation: asString(entry.explanation),
        severity: normalizeSeverity(entry.severity, 'NONE'),
    }));
}
function parseAnalysisEvent(value) {
    if (!isObject(value)) {
        return null;
    }
    return {
        event_id: asString(value.event_id),
        developer_id: asString(value.developer_id),
        file_uri: asString(value.file_uri),
        source: asString(value.source),
        mode: normalizeMode(value.mode),
        content_hash: asString(value.content_hash),
        status: exports.ANALYSIS_STATUSES.includes(asString(value.status))
            ? asString(value.status)
            : 'failed',
        project_id: asString(value.project_id),
        timestamp: asString(value.timestamp),
        scores: parseScores(value.scores),
        findings: parseFindingRecords(value.findings),
        diff: parseDiff(value.diff),
        summary: isObject(value.summary)
            ? {
                vuln_type: asString(value.summary.vuln_type),
                severity: normalizeSeverity(value.summary.severity),
                status: exports.ANALYSIS_STATUSES.includes(asString(value.summary.status))
                    ? asString(value.summary.status)
                    : 'failed',
            }
            : { vuln_type: '', severity: 'NONE', status: 'failed' },
    };
}
function parseAnalysisTimeline(value) {
    if (!Array.isArray(value)) {
        return [];
    }
    return value
        .map((entry) => parseAnalysisEvent(entry))
        .filter((entry) => Boolean(entry));
}
function parseFileState(value) {
    if (!isObject(value)) {
        return null;
    }
    return {
        developer_id: asString(value.developer_id),
        file_uri: asString(value.file_uri),
        content_hash: asString(value.content_hash),
        last_event_id: asString(value.last_event_id),
        source: asString(value.source),
        mode: normalizeMode(value.mode),
        status: exports.ANALYSIS_STATUSES.includes(asString(value.status))
            ? asString(value.status)
            : 'failed',
        updated_at: asString(value.updated_at),
        project_id: asString(value.project_id),
        scores: parseScores(value.scores),
        findings: parseFindingRecords(value.findings),
    };
}
function parseDashboardSummary(value) {
    if (!isObject(value)) {
        return null;
    }
    const currentFiles = Array.isArray(value.current_files)
        ? value.current_files.map((item) => parseFileState(item)).filter((item) => Boolean(item))
        : [];
    const recentEvents = Array.isArray(value.recent_events)
        ? value.recent_events.map((item) => parseAnalysisEvent(item)).filter((item) => Boolean(item))
        : [];
    const scoreTrend = Array.isArray(value.score_trend)
        ? value.score_trend.filter(isObject).map((entry) => ({
            event_id: asString(entry.event_id),
            file_uri: asString(entry.file_uri),
            overall_score: asNumber(entry.overall_score),
            timestamp: asString(entry.timestamp),
        }))
        : [];
    return {
        developer_id: asString(value.developer_id),
        total_files: asNumber(value.total_files),
        total_events: asNumber(value.total_events),
        files_with_findings: asNumber(value.files_with_findings),
        open_findings: asNumber(value.open_findings),
        average_scores: parseScores(value.average_scores),
        current_files: currentFiles,
        recent_events: recentEvents,
        score_trend: scoreTrend,
    };
}
//# sourceMappingURL=contracts.js.map