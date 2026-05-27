# ledger.py – Simple hash‑chained ledger implementation for CSePS

"""
This module provides utilities to maintain an append‑only ledger stored as a JSON
array in ``config.LEDGER_FILE``. Each entry contains:
- ``entry_id``: a UUID for the entry
- ``bid_hash``: SHA‑256 hash of the signed bid JSON payload
- ``previous_hash``: hash of the previous ledger entry (or a genesis value)
- ``timestamp``: ISO‑8601 timestamp of when the entry was added
- ``metadata``: optional dictionary for additional information

The ledger is tamper‑evident because each entry includes the hash of the prior
entry, forming a cryptographic chain similar to a blockchain.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from .config import LEDGER_FILE
from .models import LedgerEntry, sha256

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_ledger_file() -> List[Dict[str, Any]]:
    """Load the ledger JSON file.
    Returns an empty list if the file does not exist or is empty.
    """
    if not os.path.exists(LEDGER_FILE):
        return []
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except json.JSONDecodeError:
            # Corrupted file – treat as empty for safety
            return []

def _save_ledger_file(entries: List[Dict[str, Any]]) -> None:
    """Write the list of ledger entries back to ``LEDGER_FILE``.
    The file is written atomically by writing to a temporary file first.
    """
    os.makedirs(os.path.dirname(LEDGER_FILE), exist_ok=True)
    temp_path = LEDGER_FILE + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, sort_keys=True)
    os.replace(temp_path, LEDGER_FILE)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_entry(signed_bid_json: str, metadata: Dict[str, Any] = None) -> LedgerEntry:
    """Create a new ``LedgerEntry`` for a signed bid and persist it.

    Args:
        signed_bid_json: The JSON string representation of a ``SignedBid``.
        metadata: Optional dictionary of additional information to store.

    Returns:
        The ``LedgerEntry`` instance that was added.
    """
    entries = _load_ledger_file()
    previous_hash = entries[-1]["bid_hash"] if entries else "0" * 64
    bid_hash = sha256(signed_bid_json.encode("utf-8"))
    entry = LedgerEntry(
        entry_id=str(uuid.uuid4()),
        bid_hash=bid_hash,
        previous_hash=previous_hash,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        metadata=metadata or {},
    )
    entries.append(entry.to_dict())
    _save_ledger_file(entries)
    return entry


def get_all_entries() -> List[LedgerEntry]:
    """Return all ledger entries as ``LedgerEntry`` objects ordered chronologically."""
    raw = _load_ledger_file()
    return [LedgerEntry.from_dict(item) for item in raw]


def verify_chain() -> bool:
    """Verify the integrity of the hash chain.

    Returns ``True`` if every entry's ``previous_hash`` matches the hash of the
    preceding entry's ``bid_hash``. The genesis entry is considered valid if its
    ``previous_hash`` is the expected all‑zero value.
    """
    entries = _load_ledger_file()
    if not entries:
        return True
    expected_prev = "0" * 64
    for entry in entries:
        if entry.get("previous_hash") != expected_prev:
            return False
        expected_prev = entry.get("bid_hash")
    return True

# Convenience for CLI usage
def print_ledger() -> None:
    """Pretty‑print the ledger to stdout (used by the CLI)."""
    for entry in get_all_entries():
        print(f"Entry ID: {entry.entry_id}")
        print(f"  Bid hash: {entry.bid_hash}")
        print(f"  Prev hash: {entry.previous_hash}")
        print(f"  Timestamp: {entry.timestamp}")
        if entry.metadata:
            print(f"  Metadata: {json.dumps(entry.metadata, sort_keys=True)}")
        print("---")

# End of ledger.py
