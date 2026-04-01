import { runApiClientTests } from './apiClient.test';
import { runAnalyzerTests } from './analyzer.test';
import { runCommandTests } from './commands.test';
import { runConfigTests } from './config.test';
import { runDiagnosticTests } from './diagnostics.test';
import { runStateTests } from './state.test';
import { runWebviewTests } from './webviews.test';

const suites: Array<[string, () => Promise<void>]> = [
    ['config', runConfigTests],
    ['apiClient', runApiClientTests],
    ['analyzer', runAnalyzerTests],
    ['diagnostics', runDiagnosticTests],
    ['state', runStateTests],
    ['webviews', runWebviewTests],
    ['commands', runCommandTests],
];

async function main(): Promise<void> {
    for (const [name, suite] of suites) {
        await suite();
        console.log(`PASS ${name}`);
    }
    console.log(`PASS ${suites.length} suites`);
}

void main().catch((error) => {
    console.error('Unit tests failed');
    console.error(error);
    process.exitCode = 1;
});
