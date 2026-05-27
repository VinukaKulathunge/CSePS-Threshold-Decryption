# config.py – Configuration for CSePS prototype

import os
import json
from datetime import datetime, timedelta, timezone

# Base directory for the project (adjust if moved)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Paths
LEDGER_FILE = os.path.join(BASE_DIR, "ledger.json")
BIDS_DIR = os.path.join(BASE_DIR, "bids")

# Ensure directories exist
os.makedirs(BIDS_DIR, exist_ok=True)

# Cryptographic parameters
AES_KEY_SIZE = 32  # 256-bit
THRESHOLD = 2      # Minimum shares required to reconstruct key
NUM_SHARES = 3     # Total shares generated

# Deadline duration for bid submission (e.g. timedelta(hours=24), timedelta(seconds=30), etc.)
DEADLINE_DURATION = timedelta(hours=24)

# Record start time for fallback (first run of this instance)
# Use timezone-naive UTC to maintain database and models compatibility
START_TIME = datetime.now(timezone.utc).replace(tzinfo=None)

# Deadline for bid submission (default: 24 hours from first run)
# We dynamically check the ledger to find the absolute first submission timestamp
# to respect the "24 hours from first run" specification.
DEADLINE = START_TIME + DEADLINE_DURATION

# Helper to check if deadline passed
def deadline_passed() -> bool:
    # If DEADLINE was manually overridden (e.g. for testing), respect the override
    if DEADLINE != START_TIME + DEADLINE_DURATION:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return now >= DEADLINE

    # Otherwise, check the ledger to find the first submission timestamp
    first_run_time = START_TIME
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    ts_str = data[0].get("timestamp")
                    if ts_str:
                        if ts_str.endswith("Z"):
                            ts_str = ts_str[:-1]
                        first_run_time = datetime.fromisoformat(ts_str)
        except Exception:
            pass

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now >= (first_run_time + DEADLINE_DURATION)

# Exported symbols
__all__ = [
    "BASE_DIR",
    "LEDGER_FILE",
    "BIDS_DIR",
    "AES_KEY_SIZE",
    "THRESHOLD",
    "NUM_SHARES",
    "DEADLINE",
    "deadline_passed",
]
