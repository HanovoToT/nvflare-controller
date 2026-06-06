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

"""Settings management routes."""

from flask import Blueprint, jsonify, request

from ..config import get_config

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET"])
def get_settings():
    """Get all settings."""
    config = get_config()
    return jsonify({"status": "ok", "settings": config.get_all()})


@settings_bp.route("/settings", methods=["POST"])
def save_settings():
    """Save settings."""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    config = get_config()
    config.update(data)

    return jsonify({"status": "ok", "message": "Settings saved. Restart Dashboard to apply new credential."})