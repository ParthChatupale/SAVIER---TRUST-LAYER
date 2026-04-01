export const ANALYSIS_MODES = ['security', 'quality', 'performance', 'full'] as const;
export type AnalysisMode = typeof ANALYSIS_MODES[number];

export const ANALYSIS_STATUSES = ['success', 'partial', 'failed'] as const;
export type AnalysisStatus = typeof ANALYSIS_STATUSES[number];

export const FINDING_SEVERITIES = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;
export type FindingSeverity = typeof FINDING_SEVERITIES[number];

export interface AnalyzeCodeRequest {
    code: string;
    developer_id: string;
    mode: AnalysisMode;
    file_uri?: string;
    source?: string;
    debug?: boolean;
}

export interface AgentTraceEntry {
    agent: string;
    stage: string;
    status: AnalysisStatus | 'skipped';
    model: string;
    error?: string;
}

export interface AnalysisScores {
    overall: number;
    security: number;
    quality: number;
    performance: number;
}

export interface AnalysisDiff {
    score_delta: number;
    fixed_count: number;
    new_issue_count: number;
    unchanged_count: number;
    fixed_findings: string[];
    new_findings: string[];
    unchanged_findings: string[];
}

export interface DimensionFinding {
    dimension: 'security' | 'quality' | 'performance';
    vuln_found: boolean;
    vuln_type: string;
    vulnerable_line: string;
    pattern: string;
    attack_scenario: string;
    suggested_fix: string;
    confidence: number;
    severity?: FindingSeverity;
}

export interface DimensionAnalysisResult {
    dimension: 'security' | 'quality' | 'performance';
    status: AnalysisStatus | 'skipped';
    warnings: string[];
    summary: string;
    finding_count: number;
    top_severity: FindingSeverity;
    findings: DimensionFinding[];
}

export interface PrimaryFinding {
    dimension: 'security' | 'quality' | 'performance' | '';
    vuln_type: string;
    severity: FindingSeverity;
    vulnerable_line: string;
    pattern: string;
    explanation: string;
    suggested_fix: string;
    confidence: number;
}

export interface AnalysisProfile {
    pipeline_version: string;
    provider: string;
    enabled_agents: string[];
    model_profile: Record<string, string>;
    fingerprint: string;
}

export interface FindingRecord {
    key: string;
    dimension: 'security' | 'quality' | 'performance';
    issue_type: string;
    severity: FindingSeverity;
    line: string;
    explanation: string;
}

export interface AnalysisEvent {
    event_id: string;
    developer_id: string;
    file_uri: string;
    source: string;
    mode: AnalysisMode;
    content_hash: string;
    status: AnalysisStatus;
    project_id: string;
    timestamp: string;
    scores: AnalysisScores;
    findings: FindingRecord[];
    diff: AnalysisDiff;
    summary: {
        vuln_type: string;
        severity: FindingSeverity;
        status: AnalysisStatus;
    };
}

export interface FileState {
    developer_id: string;
    file_uri: string;
    content_hash: string;
    last_event_id: string;
    source: string;
    mode: AnalysisMode;
    status: AnalysisStatus;
    updated_at: string;
    project_id: string;
    scores: AnalysisScores;
    findings: FindingRecord[];
}

export interface DashboardSummary {
    developer_id: string;
    total_files: number;
    total_events: number;
    files_with_findings: number;
    open_findings: number;
    average_scores: AnalysisScores;
    current_files: FileState[];
    recent_events: AnalysisEvent[];
    score_trend: Array<{
        event_id: string;
        file_uri: string;
        overall_score: number;
        timestamp: string;
    }>;
}

export interface AnalysisResponse {
    status: AnalysisStatus;
    developer_id: string;
    mode: AnalysisMode;
    vuln_found: boolean;
    vuln_type: string;
    severity: FindingSeverity;
    vulnerable_line: string;
    suggested_fix: string;
    attack_scenario: string;
    developer_note: string;
    full_explanation: string;
    owasp_category: string;
    errors: string[];
    warnings: string[];
    agent_trace: AgentTraceEntry[];
    file_uri: string;
    event_id: string;
    scores: AnalysisScores;
    diff: AnalysisDiff;
    findings: DimensionFinding[];
    dimensions: Partial<Record<'security' | 'quality' | 'performance', DimensionAnalysisResult>>;
    primary_finding: PrimaryFinding;
    analysis_profile: AnalysisProfile | null;
    data_flow: string;
    planning: Record<string, unknown>;
}

export interface HistoryEntry {
    vuln_type: string;
    timestamp: string;
    explanation: string;
    severity: FindingSeverity;
}

function isObject(value: unknown): value is Record<string, unknown> {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function asString(value: unknown, fallback = ''): string {
    return typeof value === 'string' ? value : fallback;
}

function asBoolean(value: unknown, fallback = false): boolean {
    return typeof value === 'boolean' ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
    return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function asStringArray(value: unknown): string[] {
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

export function normalizeMode(value: unknown, fallback: AnalysisMode = 'security'): AnalysisMode {
    return typeof value === 'string' && ANALYSIS_MODES.includes(value as AnalysisMode)
        ? value as AnalysisMode
        : fallback;
}

export function normalizeSeverity(value: unknown, fallback: FindingSeverity = 'NONE'): FindingSeverity {
    if (typeof value !== 'string') {
        return fallback;
    }

    const normalized = value.trim().toUpperCase();
    return FINDING_SEVERITIES.includes(normalized as FindingSeverity)
        ? normalized as FindingSeverity
        : fallback;
}

function parseScores(value: unknown): AnalysisScores {
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

function parseDimensionFinding(value: unknown): DimensionFinding | null {
    if (!isObject(value)) {
        return null;
    }

    const dimension = asString(value.dimension);
    if (!['security', 'quality', 'performance'].includes(dimension)) {
        return null;
    }

    return {
        dimension: dimension as DimensionFinding['dimension'],
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

function parseDimensionFindings(value: unknown): DimensionFinding[] {
    if (!Array.isArray(value)) {
        return [];
    }

    return value
        .map((item) => parseDimensionFinding(item))
        .filter((item): item is DimensionFinding => Boolean(item));
}

function parseDimensionResult(value: unknown): DimensionAnalysisResult | null {
    if (!isObject(value)) {
        return null;
    }

    const dimension = asString(value.dimension);
    if (!['security', 'quality', 'performance'].includes(dimension)) {
        return null;
    }

    const status = asString(value.status);
    return {
        dimension: dimension as DimensionAnalysisResult['dimension'],
        status: ['success', 'partial', 'failed', 'skipped'].includes(status)
            ? status as DimensionAnalysisResult['status']
            : 'failed',
        warnings: asStringArray(value.warnings),
        summary: asString(value.summary),
        finding_count: asNumber(value.finding_count),
        top_severity: normalizeSeverity(value.top_severity),
        findings: parseDimensionFindings(value.findings),
    };
}

function parseDimensions(value: unknown): Partial<Record<'security' | 'quality' | 'performance', DimensionAnalysisResult>> {
    if (!isObject(value)) {
        return {};
    }

    const entries = Object.entries(value)
        .map(([key, entry]) => [key, parseDimensionResult(entry)] as const)
        .filter((entry): entry is readonly ['security' | 'quality' | 'performance', DimensionAnalysisResult] => {
            return ['security', 'quality', 'performance'].includes(entry[0]) && Boolean(entry[1]);
        });

    return Object.fromEntries(entries);
}

function parsePrimaryFinding(value: unknown): PrimaryFinding {
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
            ? dimension as PrimaryFinding['dimension']
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

function parseAnalysisProfile(value: unknown): AnalysisProfile | null {
    if (!isObject(value)) {
        return null;
    }

    const modelProfile = isObject(value.model_profile)
        ? Object.fromEntries(
            Object.entries(value.model_profile)
                .filter((entry): entry is [string, string] => typeof entry[0] === 'string' && typeof entry[1] === 'string'),
        )
        : {};

    return {
        pipeline_version: asString(value.pipeline_version),
        provider: asString(value.provider),
        enabled_agents: asStringArray(value.enabled_agents),
        model_profile: modelProfile,
        fingerprint: asString(value.fingerprint),
    };
}

function parseDiff(value: unknown): AnalysisDiff {
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

function parseFindingRecord(value: unknown): FindingRecord | null {
    if (!isObject(value)) {
        return null;
    }

    const dimension = asString(value.dimension);
    if (!['security', 'quality', 'performance'].includes(dimension)) {
        return null;
    }

    return {
        key: asString(value.key),
        dimension: dimension as FindingRecord['dimension'],
        issue_type: asString(value.issue_type),
        severity: normalizeSeverity(value.severity),
        line: asString(value.line),
        explanation: asString(value.explanation),
    };
}

function parseFindingRecords(value: unknown): FindingRecord[] {
    if (!Array.isArray(value)) {
        return [];
    }

    return value
        .map((item) => parseFindingRecord(item))
        .filter((item): item is FindingRecord => Boolean(item));
}

export function parseAgentTrace(value: unknown): AgentTraceEntry[] {
    if (!Array.isArray(value)) {
        return [];
    }

    return value
        .filter(isObject)
        .map((entry) => ({
            agent: asString(entry.agent || entry.name, 'unknown'),
            stage: asString(entry.stage, 'unknown'),
            status: ['success', 'partial', 'failed', 'skipped'].includes(asString(entry.status))
                ? asString(entry.status) as AgentTraceEntry['status']
                : 'failed',
            model: asString(entry.model),
            error: asString(entry.error) || undefined,
        }));
}

export function createFailedAnalysisResponse(
    developerId: string,
    mode: AnalysisMode,
    message: string,
): AnalysisResponse {
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

export function parseAnalysisResponse(
    value: unknown,
    developerId: string,
    mode: AnalysisMode,
): AnalysisResponse | null {
    if (!isObject(value)) {
        return null;
    }

    const status = asString(value.status);
    if (!ANALYSIS_STATUSES.includes(status as AnalysisStatus)) {
        return null;
    }

    return {
        status: status as AnalysisStatus,
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

export function parseHistoryEntries(value: unknown): HistoryEntry[] {
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

export function parseAnalysisEvent(value: unknown): AnalysisEvent | null {
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
        status: ANALYSIS_STATUSES.includes(asString(value.status) as AnalysisStatus)
            ? asString(value.status) as AnalysisStatus
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
                status: ANALYSIS_STATUSES.includes(asString(value.summary.status) as AnalysisStatus)
                    ? asString(value.summary.status) as AnalysisStatus
                    : 'failed',
            }
            : { vuln_type: '', severity: 'NONE', status: 'failed' },
    };
}

export function parseAnalysisTimeline(value: unknown): AnalysisEvent[] {
    if (!Array.isArray(value)) {
        return [];
    }
    return value
        .map((entry) => parseAnalysisEvent(entry))
        .filter((entry): entry is AnalysisEvent => Boolean(entry));
}

export function parseFileState(value: unknown): FileState | null {
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
        status: ANALYSIS_STATUSES.includes(asString(value.status) as AnalysisStatus)
            ? asString(value.status) as AnalysisStatus
            : 'failed',
        updated_at: asString(value.updated_at),
        project_id: asString(value.project_id),
        scores: parseScores(value.scores),
        findings: parseFindingRecords(value.findings),
    };
}

export function parseDashboardSummary(value: unknown): DashboardSummary | null {
    if (!isObject(value)) {
        return null;
    }

    const currentFiles = Array.isArray(value.current_files)
        ? value.current_files.map((item) => parseFileState(item)).filter((item): item is FileState => Boolean(item))
        : [];
    const recentEvents = Array.isArray(value.recent_events)
        ? value.recent_events.map((item) => parseAnalysisEvent(item)).filter((item): item is AnalysisEvent => Boolean(item))
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
