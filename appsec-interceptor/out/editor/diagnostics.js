"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.DiagnosticsManager = void 0;
const vscode = __importStar(require("vscode"));
const diagnosticModel_1 = require("./diagnosticModel");
class DiagnosticsManager {
    collection;
    enrichers;
    constructor(collection, enrichers = []) {
        this.collection = collection;
        this.enrichers = enrichers;
    }
    updateDocument(document, result) {
        const descriptors = (0, diagnosticModel_1.buildDiagnosticDescriptors)(document.getText(), result);
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
    clearDocument(uri) {
        this.collection.delete(uri);
    }
    dispose() {
        this.collection.dispose();
    }
}
exports.DiagnosticsManager = DiagnosticsManager;
//# sourceMappingURL=diagnostics.js.map