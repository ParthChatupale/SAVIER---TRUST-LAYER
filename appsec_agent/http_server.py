from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    REPO_ROOT = Path(__file__).resolve().parents[1]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

from flask import Flask, jsonify, request

from appsec_agent.bootstrap import get_analysis_service, get_repository
from appsec_agent.transports.common import (
    clear_history_payload,
    http_status_for_result,
    parse_analysis_request,
    serialize_history,
    serialize_result,
)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/analyze", methods=["POST"])
    def analyze():
        payload = request.get_json(silent=True) or {}
        analysis_request, error_result = parse_analysis_request(payload)
        if error_result is not None:
            return jsonify(serialize_result(error_result)), http_status_for_result(error_result)

        result = get_analysis_service().analyze(analysis_request)
        return jsonify(serialize_result(result)), http_status_for_result(result)

    @app.route("/history", methods=["GET"])
    def history():
        developer_id = request.args.get("developer_id", "anonymous")
        history_items = get_repository().get_developer_history(developer_id)
        return jsonify(serialize_history(history_items))

    @app.route("/clear", methods=["POST"])
    def clear():
        payload = request.get_json(silent=True) or {}
        developer_id = str(payload.get("developer_id", "anonymous"))
        get_repository().clear_developer_history(developer_id)
        return jsonify(clear_history_payload(developer_id))

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "running", "agent": "appsec-agent"})

    return app


app = create_app()


if __name__ == "__main__":
    print("AppSec Agent HTTP server starting on http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
