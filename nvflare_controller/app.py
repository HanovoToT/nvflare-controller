# Copyright (c) 2026, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
NVFlare Controller - Flask application entry point.
"""

import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .config import get_config
from .process_manager import get_process_manager
from .routes import dashboard, jobs, poc, settings


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder="static", static_url_path="")
    CORS(app)

    # Register blueprints
    app.register_blueprint(dashboard.dashboard_bp, url_prefix="/api/v1")
    app.register_blueprint(poc.poc_bp, url_prefix="/api/v1")
    app.register_blueprint(jobs.jobs_bp, url_prefix="/api/v1")
    app.register_blueprint(settings.settings_bp, url_prefix="/api/v1")

    # Serve static HTML
    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    # Status endpoint
    @app.route("/api/v1/status")
    def status():
        pm = get_process_manager()
        config = get_config()

        dashboard_status = pm.get_dashboard_status()
        poc_status = pm.get_poc_status()

        return jsonify({
            "status": "ok",
            "controller": {
                "port": os.environ.get("NVFLARE_CONTROLLER_PORT", 8080)
            },
            "dashboard": dashboard_status,
            "poc": poc_status,
            "config": {
                "dashboard_port": config.get("dashboard_port"),
                "poc_workspace": config.get("poc_workspace")
            }
        })

    return app


def main():
    """Main entry point."""
    port = int(os.environ.get("NVFLARE_CONTROLLER_PORT", 8080))
    app = create_app()

    config = get_config()
    port_dashboard = config.get("dashboard_port", 8443)

    print(f"NVFlare Controller starting on port {port}")
    print(f"Dashboard URL: http://localhost:{port_dashboard}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()