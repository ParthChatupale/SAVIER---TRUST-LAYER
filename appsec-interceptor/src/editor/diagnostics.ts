import * as vscode from 'vscode';
import { AnalysisResponse } from '../core/contracts';
import { buildDiagnosticDescriptors } from './diagnosticModel';

export interface DiagnosticEnricher {
    enrich(diagnostic: vscode.Diagnostic, result: AnalysisResponse): vscode.Diagnostic;
}

export class DiagnosticsManager {
    public constructor(
        private readonly collection: vscode.DiagnosticCollection,
        private readonly enrichers: DiagnosticEnricher[] = [],
    ) {}

    public updateDocument(document: vscode.TextDocument, result: AnalysisResponse): void {
        const descriptors = buildDiagnosticDescriptors(document.getText(), result);
        if (descriptors.length === 0) {
            this.collection.set(document.uri, []);
            return;
        }

        const diagnostics = descriptors.map((descriptor) => {
            const targetLine = Math.min(descriptor.line, document.lineCount - 1);
            const line = document.lineAt(targetLine);
            const range = new vscode.Range(targetLine, 0, targetLine, line.text.length);

            const severity = descriptor.severity === 'error'
                ? vscode.DiagnosticSeverity.Error
                : descriptor.severity === 'warning'
                    ? vscode.DiagnosticSeverity.Warning
                    : vscode.DiagnosticSeverity.Information;

            let diagnostic = new vscode.Diagnostic(range, descriptor.message, severity);
            diagnostic.source = 'Savier';
            diagnostic.code = descriptor.code;

            for (const enricher of this.enrichers) {
                diagnostic = enricher.enrich(diagnostic, result);
            }

            return diagnostic;
        });

        this.collection.set(document.uri, diagnostics);
    }

    public clearDocument(uri: vscode.Uri): void {
        this.collection.delete(uri);
    }

    public dispose(): void {
        this.collection.dispose();
    }
}
