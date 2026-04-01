export interface CommandSpec {
    id: string;
    title: string;
    execute(): Promise<void> | void;
}
