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

"""Job management routes using CLI."""

import os
import tempfile
from flask import Blueprint, jsonify, request

from ..api_client import get_job_client
from ..process_manager import get_process_manager

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """Get list of jobs."""
    client = get_job_client()
    result = client.list_jobs()
    return jsonify(result)


@jobs_bp.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    """Get job details."""
    # CLI doesn't provide detailed job info, return basic structure
    return jsonify({
        "status": "ok",
        "job_id": job_id,
        "message": "Job details not available via CLI"
    })


@jobs_bp.route("/jobs/<job_id>/log", methods=["GET"])
def get_job_log(job_id):
    """Get job log."""
    client = get_job_client()
    result = client.get_job_log(job_id)
    return jsonify(result)


@jobs_bp.route("/jobs", methods=["POST"])
def submit_job():
    """Submit a new job (ZIP file upload)."""
    if "job" not in request.files:
        return jsonify({"status": "error", "message": "No job file provided"}), 400

    job_file = request.files["job"]
    if not job_file.filename.endswith(".zip"):
        return jsonify({"status": "error", "message": "Job file must be .zip"}), 400

    # Save to temp file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, job_file.filename)
    job_file.save(temp_path)

    try:
        client = get_job_client()
        result = client.submit_job(temp_path)
        return jsonify(result), 201 if result.get("status") == "ok" else 400
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_path)
            os.rmdir(temp_dir)
        except Exception:
            pass


@jobs_bp.route("/jobs/<job_id>/abort", methods=["POST"])
def abort_job(job_id):
    """Abort a running job."""
    client = get_job_client()
    result = client.abort_job(job_id)
    return jsonify(result)


@jobs_bp.route("/jobs/<job_id>", methods=["DELETE"])
def delete_job(job_id):
    """Delete a job."""
    client = get_job_client()
    result = client.delete_job(job_id)
    return jsonify(result)


@jobs_bp.route("/jobs/batch-delete", methods=["POST"])
def batch_delete_jobs():
    """Batch delete jobs."""
    data = request.get_json()
    if not data or not data.get("job_ids"):
        return jsonify({"status": "error", "message": "No job IDs provided"}), 400

    # CLI doesn't support batch delete, delete one by one
    client = get_job_client()
    results = []
    for job_id in data["job_ids"]:
        results.append(client.delete_job(job_id))
    return jsonify({"status": "ok", "results": results})