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

"""POC/Server/Client management routes."""

from flask import Blueprint, jsonify, request

from ..process_manager import get_process_manager

poc_bp = Blueprint("poc", __name__)


@poc_bp.route("/poc/prepare", methods=["POST"])
def prepare_poc():
    """Prepare POC environment."""
    data = request.get_json() or {}
    num_clients = data.get("num_clients", 2)

    pm = get_process_manager()
    result = pm.prepare_poc(num_clients)
    return jsonify(result)


@poc_bp.route("/poc/start", methods=["POST"])
def start_poc():
    """Start POC (server + clients)."""
    pm = get_process_manager()
    result = pm.start_poc()
    return jsonify(result)


@poc_bp.route("/poc/stop", methods=["POST"])
def stop_poc():
    """Stop POC."""
    pm = get_process_manager()
    result = pm.stop_poc()
    return jsonify(result)


@poc_bp.route("/poc/status", methods=["GET"])
def get_poc_status():
    """Get POC status."""
    pm = get_process_manager()
    status = pm.get_poc_status()
    return jsonify({"status": "ok", "poc_status": status})


@poc_bp.route("/poc/server/start", methods=["POST"])
def start_server():
    """Start Server only."""
    pm = get_process_manager()
    result = pm.start_server()
    return jsonify(result)


@poc_bp.route("/poc/server/stop", methods=["POST"])
def stop_server():
    """Stop Server."""
    pm = get_process_manager()
    result = pm.stop_server()
    return jsonify(result)


@poc_bp.route("/poc/clients", methods=["POST"])
def add_client():
    """Add a new client."""
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"status": "error", "message": "Client name required"}), 400

    name = data["name"]
    org = data.get("org", "nvidia")

    pm = get_process_manager()
    result = pm.add_client(name, org)
    return jsonify(result)


@poc_bp.route("/poc/clients/<name>/start", methods=["POST"])
def start_client(name):
    """Start a specific client."""
    pm = get_process_manager()
    result = pm.start_client(name)
    return jsonify(result)


@poc_bp.route("/poc/clients/<name>/stop", methods=["POST"])
def stop_client(name):
    """Stop a specific client."""
    pm = get_process_manager()
    result = pm.stop_client(name)
    return jsonify(result)


@poc_bp.route("/poc/clients/start-n", methods=["POST"])
def start_clients_by_count():
    """Start N newest clients."""
    data = request.get_json() or {}
    count = data.get("count", 2)

    pm = get_process_manager()
    result = pm.start_clients_by_count(count)
    return jsonify(result)


@poc_bp.route("/poc/clients/stop-all", methods=["POST"])
def stop_all_clients():
    """Stop all clients."""
    pm = get_process_manager()
    result = pm.stop_all_clients()
    return jsonify(result)