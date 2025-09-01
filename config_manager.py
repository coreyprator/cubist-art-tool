# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: config_manager.py
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:27+02:00
# === CUBIST STAMP END ===

"""
Cubist Art Generator Config Manager

__version__ = "v12d"
__author__ = "Corey Prator"
__date__ = "2025-07-27"
"""

import json
import os

CONFIG_FILE = "last_config.json"


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def load_last_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# Version v12c | Timestamp: 2025-07-27 22:35 UTC | Hash: manual_fix


# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:27+02:00
# === CUBIST FOOTER STAMP END ===
