export function createAppShell(title: string, body: string, extraScripts = ''): string {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            :root {
                --bg: radial-gradient(circle at top left, rgba(61, 132, 255, 0.24), transparent 32%), radial-gradient(circle at 85% 10%, rgba(0, 207, 171, 0.14), transparent 28%), linear-gradient(180deg, #09111f 0%, #060b16 100%);
                --panel: rgba(10, 18, 32, 0.9);
                --panel-soft: rgba(13, 23, 41, 0.76);
                --panel-strong: rgba(16, 29, 50, 0.96);
                --border: rgba(130, 165, 255, 0.14);
                --text: #f5f8ff;
                --muted: #93a4c7;
                --muted-strong: #b8c5e0;
                --accent: #7aa9ff;
                --accent-2: #4fe1bf;
                --critical: #ff6a88;
                --high: #ffb86b;
                --medium: #f2dc7d;
                --low: #86d5ff;
                --none: #58dfc4;
                --shadow: 0 24px 70px rgba(0, 0, 0, 0.38);
                --radius-xl: 26px;
                --radius-lg: 18px;
                --radius-md: 14px;
                --radius-sm: 999px;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                padding: 28px;
                color: var(--text);
                background: var(--bg), var(--vscode-editor-background);
                font-family: 'Segoe UI Variable', 'Aptos', 'Inter', var(--vscode-font-family), sans-serif;
                letter-spacing: 0.01em;
            }
            .shell {
                max-width: 1240px;
                margin: 0 auto;
                display: grid;
                gap: 18px;
            }
            .hero {
                display: flex;
                align-items: end;
                justify-content: space-between;
                gap: 18px;
                padding: 30px;
                border: 1px solid var(--border);
                border-radius: var(--radius-xl);
                background:
                    linear-gradient(160deg, rgba(30, 52, 92, 0.96), rgba(11, 18, 33, 0.92)),
                    radial-gradient(circle at top right, rgba(79, 225, 191, 0.18), transparent 36%);
                box-shadow: var(--shadow);
            }
            .eyebrow {
                color: var(--accent-2);
                text-transform: uppercase;
                font-size: 11px;
                letter-spacing: 0.18em;
                margin-bottom: 12px;
            }
            h1 {
                margin: 0;
                font-size: clamp(30px, 4vw, 48px);
                line-height: 0.96;
                font-weight: 760;
            }
            .subtitle {
                margin-top: 14px;
                max-width: 740px;
                color: var(--muted);
                font-size: 15px;
                line-height: 1.6;
            }
            .chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
            .chip {
                padding: 7px 12px;
                border-radius: var(--radius-sm);
                border: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.04);
                color: var(--muted);
                font-size: 12px;
            }
            .dimension-chip.dimension-security { color: var(--critical); }
            .dimension-chip.dimension-quality { color: var(--accent); }
            .dimension-chip.dimension-performance { color: var(--accent-2); }
            .grid, .two-col, .three-col {
                display: grid;
                gap: 18px;
                grid-template-columns: repeat(12, minmax(0, 1fr));
            }
            .panel {
                grid-column: span 12;
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                background: var(--panel);
                box-shadow: var(--shadow);
                overflow: hidden;
            }
            .panel.soft { background: var(--panel-soft); }
            .panel.strong { background: var(--panel-strong); }
            .panel-header {
                padding: 18px 20px 0;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 12px;
            }
            .panel-body { padding: 18px 20px 20px; }
            .panel-title {
                margin: 0;
                font-size: 18px;
                font-weight: 680;
            }
            .panel-meta {
                color: var(--muted);
                font-size: 12px;
                line-height: 1.5;
            }
            .metric-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 14px;
            }
            .metric-card, .hero-card, .fix-card, .profile-card, .narrative-card, .dimension-card {
                padding: 18px;
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,0.08);
                background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            }
            .metric-card.score-healthy { box-shadow: inset 0 0 0 1px rgba(79, 225, 191, 0.12); }
            .metric-card.score-caution { box-shadow: inset 0 0 0 1px rgba(122, 169, 255, 0.12); }
            .metric-card.score-risk { box-shadow: inset 0 0 0 1px rgba(255, 184, 107, 0.14); }
            .metric-card.score-critical { box-shadow: inset 0 0 0 1px rgba(255, 106, 136, 0.16); }
            .hero-card.dimension-security { background: linear-gradient(180deg, rgba(255, 106, 136, 0.12), rgba(255,255,255,0.03)); }
            .hero-card.dimension-quality { background: linear-gradient(180deg, rgba(122, 169, 255, 0.12), rgba(255,255,255,0.03)); }
            .hero-card.dimension-performance { background: linear-gradient(180deg, rgba(79, 225, 191, 0.12), rgba(255,255,255,0.03)); }
            .metric-label {
                color: var(--muted);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.12em;
            }
            .metric-value {
                margin-top: 12px;
                font-size: clamp(28px, 3vw, 42px);
                font-weight: 760;
                line-height: 1;
            }
            .metric-subtle {
                margin-top: 10px;
                color: var(--muted);
                font-size: 12px;
                line-height: 1.5;
            }
            .hero-copy, .fix-copy {
                margin: 14px 0 0;
                color: var(--muted-strong);
                font-size: 14px;
                line-height: 1.65;
            }
            .hero-footer {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                margin-top: 14px;
                flex-wrap: wrap;
            }
            .score-bar {
                height: 10px;
                width: 100%;
                margin-top: 14px;
                border-radius: 999px;
                background: rgba(255,255,255,0.06);
                overflow: hidden;
            }
            .score-bar > span {
                display: block;
                height: 100%;
                border-radius: 999px;
                background: linear-gradient(90deg, var(--accent), var(--accent-2));
            }
            .dimension-grid, .finding-list, .timeline-list {
                display: grid;
                gap: 12px;
            }
            .finding-item, .timeline-item, .dimension-card {
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.08);
                background: rgba(255,255,255,0.03);
            }
            .finding-item { padding: 16px; }
            .timeline-item { padding: 16px; }
            .dimension-card { padding: 16px; }
            .finding-mini-list {
                display: grid;
                gap: 10px;
                margin-top: 12px;
            }
            .finding-mini-item {
                padding: 12px;
                border-radius: var(--radius-md);
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
            }
            .severity-pill {
                display: inline-flex;
                align-items: center;
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            .severity-NONE { background: rgba(83, 224, 200, 0.16); color: var(--none); }
            .severity-LOW { background: rgba(134, 214, 255, 0.16); color: var(--low); }
            .severity-MEDIUM { background: rgba(249, 226, 125, 0.16); color: var(--medium); }
            .severity-HIGH { background: rgba(255, 184, 107, 0.16); color: var(--high); }
            .severity-CRITICAL { background: rgba(255, 106, 136, 0.16); color: var(--critical); }
            .event-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
                flex-wrap: wrap;
            }
            .event-title {
                font-size: 16px;
                font-weight: 650;
                margin: 10px 0 6px;
                line-height: 1.3;
            }
            .muted { color: var(--muted); }
            .delta-positive { color: var(--accent-2); }
            .delta-negative { color: var(--critical); }
            .span-8 { grid-column: span 8; }
            .span-7 { grid-column: span 7; }
            .span-6 { grid-column: span 6; }
            .span-5 { grid-column: span 5; }
            .span-4 { grid-column: span 4; }
            .empty-state {
                padding: 28px;
                border: 1px dashed rgba(255,255,255,0.14);
                border-radius: 18px;
                color: var(--muted);
                text-align: center;
            }
            .code-block, .fix-pre {
                margin-top: 14px;
                padding: 14px;
                border-radius: 14px;
                background: rgba(2, 6, 14, 0.72);
                border: 1px solid rgba(255,255,255,0.08);
                overflow-x: auto;
                white-space: pre-wrap;
            }
            .fix-copy p { margin: 0 0 12px; }
            .profile-list {
                display: grid;
                gap: 10px;
                margin-top: 14px;
            }
            .profile-row {
                display: flex;
                justify-content: space-between;
                gap: 16px;
                color: var(--muted-strong);
                border-bottom: 1px solid rgba(255,255,255,0.06);
                padding-bottom: 8px;
            }
            .profile-row:last-child { border-bottom: 0; padding-bottom: 0; }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                padding: 12px 10px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.08);
                vertical-align: top;
            }
            th {
                color: var(--muted);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }
            code {
                font-family: 'Cascadia Code', 'JetBrains Mono', var(--vscode-editor-font-family), monospace;
                font-size: 12px;
                color: #d7e4ff;
            }
            details {
                border-top: 1px solid rgba(255,255,255,0.08);
                padding-top: 12px;
            }
            summary {
                cursor: pointer;
                color: var(--accent);
                font-weight: 600;
            }
            @media (max-width: 920px) {
                .span-8, .span-7, .span-6, .span-5, .span-4 { grid-column: span 12; }
                body { padding: 16px; }
                .hero { padding: 22px; }
            }
        </style>
    </head>
    <body>
        <div class="shell">
            <section class="hero">
                <div>
                    <div class="eyebrow">Savier Demo Surface</div>
                    <h1>${title}</h1>
                    <p class="subtitle">Without Savier, risky AI-generated code blends into the editor. With Savier, trust shifts are visible in real time across security, quality, and performance.</p>
                </div>
                <div class="chip-row">
                    <span class="chip">VS Code-first</span>
                    <span class="chip">Backend-driven</span>
                    <span class="chip">Revision-aware</span>
                </div>
            </section>
            ${body}
        </div>
        ${extraScripts}
    </body>
    </html>`;
}
