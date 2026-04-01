"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtensionStateStore = void 0;
const PANEL_PREFS_KEY = 'appsecInterceptor.panelPrefs';
class ExtensionStateStore {
    workspaceState;
    requestVersions = new Map();
    dashboardAutoOpened = false;
    activeState = {
        dashboard: null,
        timeline: [],
        fileState: null,
        fileUri: '',
        lastResult: null,
        loading: false,
        error: '',
    };
    constructor(workspaceState, _snapshotLimit) {
        this.workspaceState = workspaceState;
        this.dashboardAutoOpened = workspaceState.get(PANEL_PREFS_KEY, {}).dashboardAutoOpened ?? false;
    }
    nextRequestVersion(uri) {
        const nextVersion = (this.requestVersions.get(uri) ?? 0) + 1;
        this.requestVersions.set(uri, nextVersion);
        return nextVersion;
    }
    isLatestRequest(uri, version) {
        return this.requestVersions.get(uri) === version;
    }
    startRefresh(fileUri) {
        const isSameFile = this.activeState.fileUri === fileUri;
        this.activeState = {
            ...this.activeState,
            timeline: isSameFile ? this.activeState.timeline : [],
            fileState: isSameFile ? this.activeState.fileState : null,
            fileUri,
            lastResult: isSameFile ? this.activeState.lastResult : null,
            loading: true,
            error: '',
        };
    }
    finishRefresh(payload) {
        this.activeState = {
            dashboard: payload.dashboard,
            timeline: payload.timeline,
            fileState: payload.fileState,
            fileUri: payload.fileUri,
            lastResult: payload.lastResult,
            loading: false,
            error: payload.error ?? '',
        };
    }
    setActiveFileUri(fileUri) {
        this.activeState = {
            ...this.activeState,
            fileUri,
        };
    }
    getActiveDashboardState() {
        return {
            dashboard: this.activeState.dashboard,
            timeline: [...this.activeState.timeline],
            fileState: this.activeState.fileState,
            fileUri: this.activeState.fileUri,
            lastResult: this.activeState.lastResult,
            loading: this.activeState.loading,
            error: this.activeState.error,
        };
    }
    shouldAutoOpenDashboard(result) {
        return result.vuln_found && !this.dashboardAutoOpened;
    }
    async markDashboardOpened() {
        if (this.dashboardAutoOpened) {
            return;
        }
        this.dashboardAutoOpened = true;
        await this.workspaceState.update(PANEL_PREFS_KEY, { dashboardAutoOpened: true });
    }
    async resetDemoState() {
        this.dashboardAutoOpened = false;
        this.activeState = {
            dashboard: null,
            timeline: [],
            fileState: null,
            fileUri: '',
            lastResult: null,
            loading: false,
            error: '',
        };
        await this.workspaceState.update(PANEL_PREFS_KEY, { dashboardAutoOpened: false });
    }
    clearDocument(uri) {
        this.requestVersions.delete(uri);
        if (this.activeState.fileUri === uri) {
            this.activeState = {
                dashboard: this.activeState.dashboard,
                timeline: [],
                fileState: null,
                fileUri: '',
                lastResult: null,
                loading: false,
                error: '',
            };
        }
    }
}
exports.ExtensionStateStore = ExtensionStateStore;
//# sourceMappingURL=state.js.map