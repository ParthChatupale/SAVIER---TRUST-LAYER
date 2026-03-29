from __future__ import annotations

from appsec_agent.agents.orchestrator import format_finding, run_appsec_swarm

DEMO_SNIPPETS = {
    "sqli": """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id=" + user_id
    return db.execute(query)
""",
    "secret": """
import requests

API_KEY = "sk-prod-abc123supersecretkey9999"

def fetch_data():
    return requests.get("https://api.example.com/data",
                        headers={"Authorization": API_KEY})
""",
    "quality": """
def do_everything(data, db, cache, logger, config):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j]:
                result.append(data[i])
    db.execute("INSERT INTO log VALUES(" + str(len(result)) + ")")
    logger.log(result)
    cache.set(result)
    return result
""",
    "performance": """
def get_user_orders(user_ids):
    orders = []
    for user_id in user_ids:
        user_orders = db.execute(
            "SELECT * FROM orders WHERE user_id=" + str(user_id)
        )
        orders.extend(user_orders)
    return orders
""",
    "clean": """
def add_numbers(a: int, b: int) -> int:
    return a + b
""",
}


if __name__ == "__main__":
    import sys

    snippet_name = sys.argv[1] if len(sys.argv) > 1 else "sqli"
    developer_id = sys.argv[2] if len(sys.argv) > 2 else "parth"
    mode = sys.argv[3] if len(sys.argv) > 3 else "security"

    code = DEMO_SNIPPETS.get(snippet_name, DEMO_SNIPPETS["sqli"])

    print(f"\nAnalyzing snippet: '{snippet_name}' | mode: '{mode}'")
    print(f"Code:\n{code}")

    result = run_appsec_swarm(code, developer_id, mode)
    print(format_finding(result))
