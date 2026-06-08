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
Process management for NVFlare Controller.
Manages Dashboard, Server, and Client subprocesses.
"""

import os
import signal
import subprocess
import time
from datetime import datetime

from .config import get_config


class ProcessManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Initialize process manager."""
        self.dashboard_process = None
        self.server_process = None
        self.client_processes = {}
        self.poc_process = None

    def get_dashboard_url(self):
        """Get Dashboard URL."""
        port = get_config().get("dashboard_port", 8443)
        return f"http://localhost:{port}"

    def get_poc_workspace(self):
        """Get POC workspace path."""
        return get_config().get("poc_workspace", "/tmp/nvflare/poc")

    def get_python_exe(self):
        """Get Python executable path."""
        return get_config().get("python_exe", "/usr/bin/python3")

    def get_nvflare_path(self):
        """Get NVFlare source path."""
        return get_config().get("nvflare_path", "")

    def is_process_alive(self, pid):
        """Check if process is alive."""
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _prepare_env(self):
        """Prepare environment variables."""
        env = os.environ.copy()
        nvflare_path = self.get_nvflare_path()
        if nvflare_path:
            env["PYTHONPATH"] = nvflare_path
        return env

    # Dashboard management
    def start_dashboard(self):
        """Start Dashboard subprocess."""
        if self.dashboard_process and self.is_process_alive(self.dashboard_process.pid):
            return {"status": "ok", "message": "Dashboard already running"}

        config = get_config()
        port = config.get("dashboard_port", 8443)
        credential = config.get("credential", "admin@example.com:123456:org")

        python_exe = self.get_python_exe()
        nvflare_path = self.get_nvflare_path()

        # Check if credential changed, if so delete old database
        db_dir = "/var/tmp/nvflare/dashboard"
        db_sqlite = os.path.join(db_dir, "db.sqlite")
        db_init_done = os.path.join(db_dir, ".db_init_done")
        cred_file = os.path.join(db_dir, ".last_credential")

        # Read last credential
        last_credential = None
        if os.path.exists(cred_file):
            with open(cred_file, "r") as f:
                last_credential = f.read().strip()

        # If credential changed, delete database to reinitialize with new user
        if last_credential and last_credential != credential:
            if os.path.exists(db_sqlite):
                os.remove(db_sqlite)
            if os.path.exists(db_init_done):
                os.remove(db_init_done)

        # Save current credential
        os.makedirs(db_dir, exist_ok=True)
        with open(cred_file, "w") as f:
            f.write(credential)

        cmd = [python_exe, "-c", f"from nvflare.dashboard.application import init_app; app = init_app(); app.run(host='0.0.0.0', port={port}, debug=False)"]
        env = self._prepare_env()
        env["PORT"] = str(port)
        env["NVFL_CREDENTIAL"] = credential

        try:
            self.dashboard_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return {"status": "ok", "message": f"Dashboard starting on port {port}", "pid": self.dashboard_process.pid}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_dashboard(self):
        """Stop Dashboard subprocess."""
        if not self.dashboard_process:
            return {"status": "ok", "message": "Dashboard not running"}

        try:
            self.dashboard_process.terminate()
            self.dashboard_process.wait(timeout=10)
            self.dashboard_process = None
            return {"status": "ok", "message": "Dashboard stopped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_dashboard_status(self):
        """Get Dashboard status."""
        if self.dashboard_process and self.is_process_alive(self.dashboard_process.pid):
            return {"running": True, "pid": self.dashboard_process.pid}
        return {"running": False, "pid": None}

    # POC management
    def prepare_poc(self, num_clients=2):
        """Prepare POC environment."""
        python_exe = self.get_python_exe()
        workspace = self.get_poc_workspace()
        nvflare_path = self.get_nvflare_path()

        try:
            env = self._prepare_env()

            # Config workspace
            config_cmd = [python_exe, "-m", "nvflare.cli", "poc", "config", "-pw", workspace]
            subprocess.run(config_cmd, capture_output=True, text=True, env=env)

            # Prepare
            cmd = [python_exe, "-m", "nvflare.cli", "poc", "prepare", "-n", str(num_clients), "--force"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)

            if result.returncode != 0:
                return {"status": "error", "message": result.stderr}

            return {"status": "ok", "message": f"POC prepared with {num_clients} clients"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "POC prepare timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def start_poc(self):
        """Start POC (server + clients) with --no-wait."""
        python_exe = self.get_python_exe()
        workspace = self.get_poc_workspace()

        try:
            env = self._prepare_env()

            # Kill existing server/client processes first
            subprocess.run(["pkill", "-f", "fed_server.json"], capture_output=True, text=True)
            subprocess.run(["pkill", "-f", "fed_client.json"], capture_output=True, text=True)
            subprocess.run(["pkill", "-f", "server_train"], capture_output=True, text=True)
            subprocess.run(["pkill", "-f", "client_train"], capture_output=True, text=True)
            time.sleep(1)

            # Config workspace
            config_cmd = [python_exe, "-m", "nvflare.cli", "poc", "config", "-pw", workspace]
            subprocess.run(config_cmd, capture_output=True, text=True, env=env)

            # Start with --no-wait
            cmd = [python_exe, "-m", "nvflare.cli", "poc", "start", "--no-wait"]
            self.poc_process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            return {"status": "ok", "message": "POC starting"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_poc(self):
        """Stop POC (server + all clients)."""
        try:
            # Kill all server/client processes
            subprocess.run(["pkill", "-f", "fed_server.json"], capture_output=True, text=True)
            subprocess.run(["pkill", "-f", "fed_client.json"], capture_output=True, text=True)
            subprocess.run(["pkill", "-f", "server_train"], capture_output=True, text=True)
            subprocess.run(["pkill", "-f", "client_train"], capture_output=True, text=True)
            time.sleep(1)
            return {"status": "ok", "message": "POC stopping"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_poc_status(self):
        """Get POC status (server + clients from pid.fl files)."""
        workspace = self.get_poc_workspace()
        prod_dir = os.path.join(workspace, "example_project", "prod_00")

        server_info = {"running": False, "pid": None}
        clients = []

        if not os.path.exists(prod_dir):
            return {"server": server_info, "clients": clients}

        # Check server
        server_dir = os.path.join(prod_dir, "server")
        if os.path.exists(server_dir):
            pid_file = os.path.join(server_dir, "pid.fl")
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    if self.is_process_alive(pid):
                        server_info = {"running": True, "pid": pid}
                except Exception:
                    pass

        # Check clients
        for item in os.listdir(prod_dir):
            item_path = os.path.join(prod_dir, item)
            if not os.path.isdir(item_path) or item == "server":
                continue

            fed_client_json = os.path.join(item_path, "startup", "fed_client.json")
            if not os.path.exists(fed_client_json):
                continue

            mtime = os.path.getmtime(item_path)
            pid_file = os.path.join(item_path, "pid.fl")
            running = False
            pid = None
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    if pid and self.is_process_alive(pid):
                        running = True
                except Exception:
                    pass

            clients.append({
                "name": item,
                "running": running,
                "pid": pid,
                "created": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

        # Sort by mtime (newest first)
        clients.sort(key=lambda x: x.get("created", ""), reverse=True)

        return {"server": server_info, "clients": clients}

    # Server management
    def start_server(self):
        """Start Server only."""
        workspace = self.get_poc_workspace()
        startup_sh = os.path.join(workspace, "example_project", "prod_00", "server", "startup", "start.sh")

        if not os.path.exists(startup_sh):
            return {"status": "error", "message": "Server startup script not found"}

        try:
            env = self._prepare_env()
            self.server_process = subprocess.Popen(
                [startup_sh],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(startup_sh)
            )
            return {"status": "ok", "message": "Server starting", "pid": self.server_process.pid}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_server(self):
        """Stop Server."""
        workspace = self.get_poc_workspace()
        server_dir = os.path.join(workspace, "example_project", "prod_00", "server")

        if not os.path.exists(server_dir):
            return {"status": "error", "message": "Server directory not found"}

        pid_file = os.path.join(server_dir, "pid.fl")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                if pid and self.is_process_alive(pid):
                    os.kill(pid, signal.SIGTERM)
                    return {"status": "ok", "message": "Server stopping"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "ok", "message": "Server not running"}

    # Client management
    def add_client(self, name, org="nvidia"):
        """Add a new client."""
        python_exe = self.get_python_exe()
        workspace = self.get_poc_workspace()

        try:
            env = self._prepare_env()

            # Config workspace
            config_cmd = [python_exe, "-m", "nvflare.cli", "poc", "config", "-pw", workspace]
            subprocess.run(config_cmd, capture_output=True, text=True, env=env)

            # Add site
            cmd = [python_exe, "-m", "nvflare.cli", "poc", "add-site", name, "--org", org]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)

            if result.returncode != 0:
                return {"status": "error", "message": result.stderr}

            return {"status": "ok", "message": f"Client {name} added"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def start_client(self, name):
        """Start a specific client."""
        workspace = self.get_poc_workspace()
        startup_sh = os.path.join(workspace, "example_project", "prod_00", name, "startup", "start.sh")

        if not os.path.exists(startup_sh):
            return {"status": "error", "message": f"Client {name} startup script not found"}

        try:
            env = self._prepare_env()
            process = subprocess.Popen(
                [startup_sh],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(startup_sh)
            )
            return {"status": "ok", "message": f"Client {name} starting", "pid": process.pid}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_client(self, name):
        """Stop a specific client."""
        try:
            result = subprocess.run(["pkill", "-f", name], capture_output=True, text=True)
            return {"status": "ok", "message": f"Client {name} stopping"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def start_clients_by_count(self, count):
        """Start N newest clients."""
        workspace = self.get_poc_workspace()
        prod_dir = os.path.join(workspace, "example_project", "prod_00")

        if not os.path.exists(prod_dir):
            return {"status": "error", "message": "POC not prepared"}

        # Collect clients with mtime
        client_items = []
        for item in os.listdir(prod_dir):
            item_path = os.path.join(prod_dir, item)
            if not os.path.isdir(item_path) or item == "server":
                continue
            fed_client_json = os.path.join(item_path, "startup", "fed_client.json")
            if not os.path.exists(fed_client_json):
                continue
            mtime = os.path.getmtime(item_path)
            client_items.append((mtime, item, item_path))

        # Sort by mtime (newest first)
        client_items.sort(key=lambda x: x[0], reverse=True)

        started = []
        for mtime, item, item_path in client_items:
            if len(started) >= count:
                break
            startup_sh = os.path.join(item_path, "startup", "start.sh")
            if os.path.exists(startup_sh):
                try:
                    env = self._prepare_env()
                    subprocess.Popen(
                        [startup_sh],
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.dirname(startup_sh)
                    )
                    started.append(item)
                except Exception:
                    pass

        return {"status": "ok", "message": f"Started {len(started)} clients", "started": started}

    def stop_all_clients(self):
        """Stop all clients."""
        try:
            subprocess.run(["pkill", "-f", "fed_client.json"], capture_output=True, text=True)
            return {"status": "ok", "message": "All clients stopping"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_all(self):
        """Stop all processes."""
        self.stop_dashboard()
        self.stop_all_clients()
        self.stop_server()
        self.stop_poc()
        return {"status": "ok", "message": "All processes stopped"}


def get_process_manager():
    """Get singleton process manager instance."""
    return ProcessManager()