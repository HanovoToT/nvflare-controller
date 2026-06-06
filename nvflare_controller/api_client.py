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
NVFlare CLI Client for Job management.
Uses subprocess to call NVFlare CLI commands instead of REST API.
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime

from .config import get_config


class NVFlareCLIJobClient:
    """Client for NVFlare Job management using CLI."""

    def __init__(self):
        self.config = get_config()

    def get_python_exe(self):
        """Get Python executable path."""
        return self.config.get("python_exe", "/usr/bin/python3")

    def get_nvflare_path(self):
        """Get NVFlare source path."""
        return self.config.get("nvflare_path", "")

    def get_poc_workspace(self):
        """Get POC workspace path."""
        return self.config.get("poc_workspace", "/tmp/nvflare/poc")

    def _prepare_env(self):
        """Prepare environment variables."""
        env = os.environ.copy()
        nvflare_path = self.get_nvflare_path()
        if nvflare_path:
            env["PYTHONPATH"] = nvflare_path
        return env

    def _run_cli(self, args, timeout=60):
        """Run NVFlare CLI command."""
        python_exe = self.get_python_exe()
        cmd = [python_exe, "-m", "nvflare.cli"] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._prepare_env()
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "Command timeout"}
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    def submit_job(self, job_zip_path):
        """Submit a job using CLI."""
        if not os.path.exists(job_zip_path):
            return {"status": "error", "message": f"Job file not found: {job_zip_path}"}

        # First config the workspace
        workspace = self.get_poc_workspace()
        self._run_cli(["poc", "config", "-pw", workspace])

        # Extract zip to temp folder if it's a zip file
        job_folder = job_zip_path
        temp_dir = None
        if job_zip_path.endswith(".zip"):
            import zipfile
            import shutil
            temp_dir = tempfile.mkdtemp()
            job_folder = temp_dir
            with zipfile.ZipFile(job_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            # Get the actual job folder name (remove .zip extension)
            job_folder_name = os.path.splitext(os.path.basename(job_zip_path))[0]
            job_folder = os.path.join(temp_dir, job_folder_name)
            if not os.path.exists(job_folder):
                # If extracted folder has different name, use the temp_dir itself
                job_folder = temp_dir

        # Submit job using CLI
        result = self._run_cli(["job", "submit", "-j", job_folder], timeout=120)

        # Cleanup temp dir
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

        if result["returncode"] == 0:
            # Parse output for job ID
            output = result["stdout"]
            # Look for job ID in output
            job_id = None
            for line in output.split("\n"):
                if "job" in line.lower() and "submitted" in line.lower():
                    # Try to extract job ID
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p.lower() == "job" and i + 1 < len(parts):
                            job_id = parts[i + 1]
                            break
                        if "id:" in p.lower() and i + 1 < len(parts):
                            job_id = parts[i + 1]
                            break
            return {
                "status": "ok",
                "message": "Job submitted successfully",
                "job_id": job_id or "unknown"
            }
        else:
            return {
                "status": "error",
                "message": result["stderr"] or result["stdout"] or "Job submission failed"
            }

    def list_jobs(self):
        """List jobs using CLI."""
        workspace = self.get_poc_workspace()
        self._run_cli(["poc", "config", "-pw", workspace])

        result = self._run_cli(["job", "list"], timeout=30)

        if result["returncode"] == 0:
            # Parse job list from output
            jobs = []
            lines = result["stdout"].split("\n")
            for line in lines:
                if line.strip() and not line.startswith("="):
                    jobs.append({
                        "name": line.strip(),
                        "status": "UNKNOWN",
                        "submit_time": ""
                    })
            return {"status": "ok", "jobs": jobs}
        else:
            # If job list fails, return empty list instead of error
            return {"status": "ok", "jobs": [], "message": result["stderr"] or "No jobs found"}

    def abort_job(self, job_id):
        """"Abort a job using CLI."""
        workspace = self.get_poc_workspace()
        self._run_cli(["poc", "config", "-pw", workspace])

        result = self._run_cli(["job", "abort", "--force", job_id], timeout=30)

        if result["returncode"] == 0:
            return {"status": "ok", "message": f"Job {job_id} abort signal sent"}
        else:
            return {"status": "error", "message": result["stderr"] or "Abort failed"}

    def get_job_log(self, job_id):
        """Get job log."""
        # Try to find log in POC workspace
        workspace = self.get_poc_workspace()

        # Check server log
        server_log = os.path.join(workspace, "example_project", "prod_00", "server", "log.txt")
        if os.path.exists(server_log):
            try:
                with open(server_log, "r") as f:
                    return {"status": "ok", "log": f.read()}
            except Exception:
                pass

        # Check client logs
        prod_dir = os.path.join(workspace, "example_project", "prod_00")
        logs = []
        for site in ["site-1", "site-2"]:
            site_log = os.path.join(prod_dir, site, "log.txt")
            if os.path.exists(site_log):
                try:
                    with open(site_log, "r") as f:
                        logs.append(f"=== {site.upper()} LOG ===\n{f.read()}")
                except Exception:
                    pass

        if logs:
            return {"status": "ok", "log": "\n\n".join(logs)}

        return {"status": "ok", "log": "No log available"}

    def delete_job(self, job_id):
        """Delete a job."""
        # Jobs are stored in workspace, just remove the directory
        workspace = self.get_poc_workspace()
        job_dir = os.path.join(workspace, "example_project", "prod_00", job_id)

        if os.path.exists(job_dir):
            try:
                import shutil
                shutil.rmtree(job_dir)
                return {"status": "ok", "message": f"Job {job_id} deleted"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "ok", "message": "Job directory not found"}


def get_job_client():
    """Get CLI-based job client instance."""
    return NVFlareCLIJobClient()