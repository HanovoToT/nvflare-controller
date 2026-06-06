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
Configuration management for NVFlare Controller.
"""

import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "dashboard_port": 8443,
    "credential": "admin@example.com:123456:org",
    "nvflare_path": "",
    "python_exe": "/usr/bin/python3",
    "poc_workspace": "/tmp/nvflare/poc"
}


class Config:
    _instance = None
    _config_path = Path.home() / ".nvflare-controller" / "config.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from file."""
        self.config = DEFAULT_CONFIG.copy()

        # Ensure config directory exists
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        if self._config_path.exists():
            try:
                with open(self._config_path, "r") as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except Exception:
                pass

    def _save_config(self):
        """Save configuration to file."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def get(self, key, default=None):
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set configuration value."""
        self.config[key] = value
        self._save_config()

    def get_all(self):
        """Get all configuration."""
        return self.config.copy()

    def update(self, config_dict):
        """Update configuration with dict."""
        self.config.update(config_dict)
        self._save_config()


def get_config():
    """Get singleton config instance."""
    return Config()