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

"""Dashboard management routes."""

from flask import Blueprint, jsonify

from ..process_manager import get_process_manager

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard/start", methods=["POST"])
def start_dashboard():
    """Start Dashboard subprocess."""
    pm = get_process_manager()
    result = pm.start_dashboard()
    return jsonify(result)


@dashboard_bp.route("/dashboard/stop", methods=["POST"])
def stop_dashboard():
    """Stop Dashboard subprocess."""
    pm = get_process_manager()
    result = pm.stop_dashboard()
    return jsonify(result)


@dashboard_bp.route("/dashboard/status", methods=["GET"])
def get_dashboard_status():
    """Get Dashboard status."""
    pm = get_process_manager()
    status = pm.get_dashboard_status()
    return jsonify({"status": "ok", "dashboard": status})