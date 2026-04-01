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
exports.runConfigTests = runConfigTests;
const assert = __importStar(require("assert"));
const config_1 = require("../core/config");
async function runConfigTests() {
    const settings = (0, config_1.resolveExtensionSettings)({});
    assert.strictEqual(settings.serverUrl, 'http://127.0.0.1:5000');
    assert.strictEqual(settings.mode, 'full');
    assert.strictEqual(settings.requestTimeoutMs, 60000);
    assert.ok(settings.enabledLanguages.includes('python'));
    const customized = (0, config_1.resolveExtensionSettings)({
        serverUrl: 'http://localhost:9999/',
        developerId: 'alice',
        mode: 'full',
        debounceMs: 400,
        requestTimeoutMs: 45000,
        enabledLanguages: ['typescript'],
        autoAnalyze: false,
    });
    assert.strictEqual(customized.serverUrl, 'http://localhost:9999');
    assert.strictEqual(customized.developerId, 'alice');
    assert.strictEqual(customized.mode, 'full');
    assert.strictEqual(customized.debounceMs, 400);
    assert.strictEqual(customized.requestTimeoutMs, 45000);
    assert.deepStrictEqual(customized.enabledLanguages, ['typescript']);
    assert.strictEqual(customized.autoAnalyze, false);
}
//# sourceMappingURL=config.test.js.map