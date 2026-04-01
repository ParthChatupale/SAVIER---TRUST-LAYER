export interface ViewSpec<TData> {
    id: string;
    title: string;
    render(data: TData): string;
}

export class ViewRegistry {
    private readonly views = new Map<string, ViewSpec<unknown>>();

    public register<TData>(view: ViewSpec<TData>): void {
        this.views.set(view.id, view as ViewSpec<unknown>);
    }

    public get<TData>(id: string): ViewSpec<TData> | undefined {
        return this.views.get(id) as ViewSpec<TData> | undefined;
    }
}
