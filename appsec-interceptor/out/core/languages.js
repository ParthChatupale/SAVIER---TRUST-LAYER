"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getLanguagePolicy = getLanguagePolicy;
exports.isLanguageEnabled = isLanguageEnabled;
const DEFAULT_POLICIES = {
    python: { languageId: 'python', minCodeLength: 20 },
    javascript: { languageId: 'javascript', minCodeLength: 20 },
    typescript: { languageId: 'typescript', minCodeLength: 20 },
};
function getLanguagePolicy(languageId) {
    return DEFAULT_POLICIES[languageId];
}
function isLanguageEnabled(languageId, enabledLanguages) {
    return enabledLanguages.includes(languageId);
}
//# sourceMappingURL=languages.js.map