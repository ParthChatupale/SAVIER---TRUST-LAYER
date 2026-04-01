from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from appsec_agent.agents.orchestrator import format_finding, run_appsec_swarm


EXAMPLE_DIR = Path(__file__).resolve().parent
CASES = {
    "security": EXAMPLE_DIR / "flawed_security.py",
    "quality": EXAMPLE_DIR / "flawed_quality.py",
    "performance": EXAMPLE_DIR / "flawed_performance.py",
    "full": EXAMPLE_DIR / "flawed_full.py",
}


def main() -> int:
    case = sys.argv[1] if len(sys.argv) > 1 else "security"
    developer_id = sys.argv[2] if len(sys.argv) > 2 else "manual-tester"
    mode = sys.argv[3] if len(sys.argv) > 3 else case

    if case not in CASES:
        available = ", ".join(sorted(CASES))
        print(f"Unknown case '{case}'. Choose one of: {available}")
        return 1

    code = CASES[case].read_text()
    print(f"\nRunning case '{case}' with mode '{mode}' for developer '{developer_id}'")
    print(f"Loaded sample: {CASES[case]}")
    result = run_appsec_swarm(code, developer_id, mode)
    print(format_finding(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
