"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.locateVulnerableLine = locateVulnerableLine;
exports.severityToDiagnosticSeverity = severityToDiagnosticSeverity;
exports.buildDiagnosticDescriptors = buildDiagnosticDescriptors;
exports.buildDiagnosticDescriptor = buildDiagnosticDescriptor;
const VULNERABILITY_PATTERNS = {
    'SQL Injection': /query\s*=.*[+]|execute\s*\(.*[+]/i,
    'Hardcoded Secret': /api_key\s*=\s*['"]|secret\s*=\s*['"]|password\s*=\s*['"]|token\s*=\s*['"]/i,
    'Insecure Deserialization': /pickle\.loads|yaml\.load\s*\(/i,
    'Path Traversal': /open\s*\(\s*[a-z_][a-z0-9_]*\s*,/i,
    'Command Injection': /os\.system\s*\(|subprocess\./i,
    'Nested Loop': /for .*:\n(\s+)for .*:/i,
    'Unbounded Memory Growth': /\.append\s*\(/i,
    'Global State Misuse': /\bglobal\s+[a-z_][a-z0-9_]*/i,
};
function normalizeSnippet(value) {
    return value.replace(/[`'"]/g, '').trim();
}
function locateVulnerableLine(code, vulnerableLine, vulnType) {
    const lines = code.split(/\r?\n/);
    const cleanedSnippet = normalizeSnippet(vulnerableLine);
    if (cleanedSnippet) {
        const exactIndex = lines.findIndex((line) => normalizeSnippet(line) === cleanedSnippet);
        if (exactIndex >= 0) {
            return exactIndex;
        }
        const partialIndex = lines.findIndex((line) => normalizeSnippet(line).includes(cleanedSnippet));
        if (partialIndex >= 0) {
            return partialIndex;
        }
        const keyFragment = cleanedSnippet.split('=')[0]?.trim();
        if (keyFragment) {
            const fragmentIndex = lines.findIndex((line) => line.includes(keyFragment));
            if (fragmentIndex >= 0) {
                return fragmentIndex;
            }
        }
    }
    const pattern = VULNERABILITY_PATTERNS[vulnType];
    if (pattern) {
        const patternIndex = lines.findIndex((line) => pattern.test(line));
        if (patternIndex >= 0) {
            return patternIndex;
        }
    }
    const fallbackIndex = lines.findIndex((line) => line.trim() && !line.trim().startsWith('#') && !line.trim().startsWith('//'));
    return fallbackIndex >= 0 ? fallbackIndex : 0;
}
function severityToDiagnosticSeverity(severity) {
    if (severity === 'CRITICAL' || severity === 'HIGH') {
        return 'error';
    }
    if (severity === 'MEDIUM') {
        return 'warning';
    }
    return 'information';
}
function buildDiagnosticDescriptors(code, result) {
    const findings = result.findings.length > 0
        ? result.findings
        : result.vuln_found
            ? [{
                    dimension: result.primary_finding.dimension || 'security',
                    vuln_found: true,
                    vuln_type: result.vuln_type,
                    vulnerable_line: result.vulnerable_line,
                    pattern: result.primary_finding.pattern,
                    attack_scenario: result.attack_scenario,
                    suggested_fix: result.suggested_fix,
                    confidence: result.primary_finding.confidence,
                    severity: result.severity,
                }]
            : [];
    return findings.map((finding) => {
        const messageParts = [
            `[${finding.severity ?? result.severity}] ${finding.vuln_type}`,
            finding.attack_scenario ? `Attack: ${finding.attack_scenario}` : '',
            finding.suggested_fix ? `Fix: ${finding.suggested_fix}` : '',
            result.warnings.length > 0 ? `Warnings: ${result.warnings.join('; ')}` : '',
        ].filter(Boolean);
        return {
            line: locateVulnerableLine(code, finding.vulnerable_line, finding.vuln_type),
            message: messageParts.join('\n'),
            severity: severityToDiagnosticSeverity(finding.severity ?? result.severity),
            code: finding.dimension ? `${finding.dimension}:${finding.vuln_type}` : result.owasp_category || undefined,
        };
    });
}
function buildDiagnosticDescriptor(code, result) {
    return buildDiagnosticDescriptors(code, result)[0] ?? null;
}
//# sourceMappingURL=diagnosticModel.js.map