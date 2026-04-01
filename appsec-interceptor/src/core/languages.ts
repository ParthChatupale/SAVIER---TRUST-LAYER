export interface LanguagePolicy {
    languageId: string;
    minCodeLength: number;
}

const DEFAULT_POLICIES: Record<string, LanguagePolicy> = {
    python: { languageId: 'python', minCodeLength: 20 },
    javascript: { languageId: 'javascript', minCodeLength: 20 },
    typescript: { languageId: 'typescript', minCodeLength: 20 },
};

export function getLanguagePolicy(languageId: string): LanguagePolicy | undefined {
    return DEFAULT_POLICIES[languageId];
}

export function isLanguageEnabled(languageId: string, enabledLanguages: string[]): boolean {
    return enabledLanguages.includes(languageId);
}
