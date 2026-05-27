# models.py – Data classes for CSePS

"""
Defines the core data structures used throughout the prototype:
- Bid: raw bid data submitted by a bidder
- SignedBid: a Bid together with its digital signature and the bidder's public key
- LedgerEntry: an immutable record stored in the tamper‑proof ledger
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class Bid:
    """Raw bid information provided by a bidder.
    The fields can be extended as needed for the procurement scenario.
    """
    bidder_id: str
    amount: float
    description: str
    timestamp: str = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_json(data: str) -> "Bid":
        obj = json.loads(data)
        return Bid(**obj)


@dataclass
class SignedBid:
    """A bid together with its ECDSA signature and the signer's public key (PEM)."""
    bid: Bid
    signature: str  # hex‑encoded signature
    public_key_pem: str

    def to_json(self) -> str:
        payload = {
            "bid": json.loads(self.bid.to_json()),
            "signature": self.signature,
            "public_key_pem": self.public_key_pem,
        }
        return json.dumps(payload, sort_keys=True)

    @staticmethod
    def from_json(data: str) -> "SignedBid":
        obj = json.loads(data)
        bid = Bid(**obj["bid"])
        return SignedBid(bid=bid, signature=obj["signature"], public_key_pem=obj["public_key_pem"])


@dataclass
class LedgerEntry:
    """Immutable entry stored in the ledger.
    Each entry contains a hash of the previous entry to create a hash chain.
    """
    entry_id: str
    bid_hash: str
    previous_hash: str
    timestamp: str = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LedgerEntry":
        return LedgerEntry(**data)

"""Utility functions for hashing"""
import hashlib

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
