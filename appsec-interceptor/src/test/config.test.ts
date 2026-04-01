import * as assert from 'assert';
import { resolveExtensionSettings } from '../core/config';

export async function runConfigTests(): Promise<void> {
    const settings = resolveExtensionSettings({});
    assert.strictEqual(settings.serverUrl, 'http://127.0.0.1:5000');
    assert.strictEqual(settings.mode, 'full');
    assert.strictEqual(settings.requestTimeoutMs, 60000);
    assert.ok(settings.enabledLanguages.includes('python'));

    const customized = resolveExtensionSettings({
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
