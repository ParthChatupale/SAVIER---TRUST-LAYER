from __future__ import annotations

from flask import Flask, jsonify, request

from appsec_agent.bootstrap import get_analysis_service, get_repository
from appsec_agent.core.models import AnalysisRequest


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/analyze", methods=["POST"])
    def analyze():
        payload = request.get_json(silent=True) or {}
        analysis_request = AnalysisRequest.from_mapping(payload)
        result = get_analysis_service().analyze(analysis_request)
        status_code = 200 if result.status != "failed" else 400
        return jsonify(result.to_dict()), status_code

    @app.route("/history", methods=["GET"])
    def history():
        developer_id = request.args.get("developer_id", "anonymous")
        history_items = get_repository().get_developer_history(developer_id)
        return jsonify([item.to_dict() for item in history_items])

    @app.route("/clear", methods=["POST"])
    def clear():
        payload = request.get_json(silent=True) or {}
        developer_id = str(payload.get("developer_id", "anonymous"))
        get_repository().clear_developer_history(developer_id)
        return jsonify({"status": "cleared", "developer_id": developer_id})

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "running", "agent": "appsec-agent"})

    return app


app = create_app()


if __name__ == "__main__":
    print("AppSec Agent HTTP server starting on http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
