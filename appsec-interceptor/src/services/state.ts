import { AnalysisEvent, AnalysisResponse, DashboardSummary, FileState } from '../core/contracts';

export interface WorkspaceStateLike {
    get<T>(key: string, defaultValue: T): T;
    update(key: string, value: unknown): Thenable<void> | Promise<void>;
}

export interface ActiveDashboardState {
    dashboard: DashboardSummary | null;
    timeline: AnalysisEvent[];
    fileState: FileState | null;
    fileUri: string;
    lastResult: AnalysisResponse | null;
    loading: boolean;
    error: string;
}

const PANEL_PREFS_KEY = 'appsecInterceptor.panelPrefs';

export class ExtensionStateStore {
    private readonly requestVersions = new Map<string, number>();
    private dashboardAutoOpened = false;
    private activeState: ActiveDashboardState = {
        dashboard: null,
        timeline: [],
        fileState: null,
        fileUri: '',
        lastResult: null,
        loading: false,
        error: '',
    };

    public constructor(
        private readonly workspaceState: WorkspaceStateLike,
        _snapshotLimit: number,
    ) {
        this.dashboardAutoOpened = workspaceState.get<{ dashboardAutoOpened?: boolean }>(PANEL_PREFS_KEY, {}).dashboardAutoOpened ?? false;
    }

    public nextRequestVersion(uri: string): number {
        const nextVersion = (this.requestVersions.get(uri) ?? 0) + 1;
        this.requestVersions.set(uri, nextVersion);
        return nextVersion;
    }

    public isLatestRequest(uri: string, version: number): boolean {
        return this.requestVersions.get(uri) === version;
    }

    public startRefresh(fileUri: string): void {
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

    public finishRefresh(payload: {
        fileUri: string;
        dashboard: DashboardSummary | null;
        timeline: AnalysisEvent[];
        fileState: FileState | null;
        lastResult: AnalysisResponse | null;
        error?: string;
    }): void {
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

    public setActiveFileUri(fileUri: string): void {
        this.activeState = {
            ...this.activeState,
            fileUri,
        };
    }

    public getActiveDashboardState(): ActiveDashboardState {
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

    public shouldAutoOpenDashboard(result: AnalysisResponse): boolean {
        return result.vuln_found && !this.dashboardAutoOpened;
    }

    public async markDashboardOpened(): Promise<void> {
        if (this.dashboardAutoOpened) {
            return;
        }
        this.dashboardAutoOpened = true;
        await this.workspaceState.update(PANEL_PREFS_KEY, { dashboardAutoOpened: true });
    }

    public async resetDemoState(): Promise<void> {
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

    public clearDocument(uri: string): void {
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
