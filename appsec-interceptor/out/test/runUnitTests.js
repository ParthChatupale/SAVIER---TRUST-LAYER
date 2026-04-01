"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const apiClient_test_1 = require("./apiClient.test");
const analyzer_test_1 = require("./analyzer.test");
const commands_test_1 = require("./commands.test");
const config_test_1 = require("./config.test");
const diagnostics_test_1 = require("./diagnostics.test");
const state_test_1 = require("./state.test");
const webviews_test_1 = require("./webviews.test");
const suites = [
    ['config', config_test_1.runConfigTests],
    ['apiClient', apiClient_test_1.runApiClientTests],
    ['analyzer', analyzer_test_1.runAnalyzerTests],
    ['diagnostics', diagnostics_test_1.runDiagnosticTests],
    ['state', state_test_1.runStateTests],
    ['webviews', webviews_test_1.runWebviewTests],
    ['commands', commands_test_1.runCommandTests],
];
async function main() {
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
//# sourceMappingURL=runUnitTests.js.map