# crypto.py – Core cryptographic utilities for CSePS
"""
This module provides:
- ECC key pair generation (using SECP256R1 curve)
- ECDSA signing and verification
- Symmetric encryption/decryption of bids (AES‑GCM)
- Simple threshold key splitting/reconstruction (Shamir Secret Sharing)
"""

import os
import json
from dataclasses import dataclass
from typing import Tuple, List

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------------------------
# ECC key management
# ---------------------------------------------------------------------------

def generate_ecc_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """Generate a new ECC private/public key pair using SECP256R1."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

def serialize_private_key(private_key: ec.EllipticCurvePrivateKey, password: bytes = None) -> bytes:
    """Serialize a private key to PEM. If a password is supplied, the key is encrypted."""
    encryption = serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption()
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )

def serialize_public_key(public_key: ec.EllipticCurvePublicKey) -> bytes:
    """Serialize a public key to PEM."""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

def load_private_key(pem_data: bytes, password: bytes = None) -> ec.EllipticCurvePrivateKey:
    return serialization.load_pem_private_key(pem_data, password=password)

def load_public_key(pem_data: bytes) -> ec.EllipticCurvePublicKey:
    return serialization.load_pem_public_key(pem_data)

# ---------------------------------------------------------------------------
# Signing utilities
# ---------------------------------------------------------------------------

def sign_message(private_key: ec.EllipticCurvePrivateKey, message: bytes) -> bytes:
    """Create an ECDSA signature for *message* using SHA256."""
    signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    return signature

def verify_signature(public_key: ec.EllipticCurvePublicKey, message: bytes, signature: bytes) -> bool:
    """Verify an ECDSA signature. Returns True if valid, else False."""
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Symmetric encryption (AES‑GCM)
# ---------------------------------------------------------------------------

def encrypt_bid(key: bytes, plaintext: bytes, associated_data: bytes = b"cseps") -> Tuple[bytes, bytes, bytes]:
    """Encrypt *plaintext* with AES‑GCM.
    Returns (nonce, ciphertext, tag). The tag is appended to ciphertext by AESGCM.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce, ct

def decrypt_bid(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes = b"cseps") -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data)

# ---------------------------------------------------------------------------
# Threshold key handling (Shamir Secret Sharing)
# ---------------------------------------------------------------------------

# Use a prime larger than 2^256 to ensure any 256-bit AES key can be shared
# without modulo reduction issues. 2^256 + 297 is prime.
PRIME = 2**256 + 297

def split_key(key: bytes, threshold: int, num_shares: int) -> List[str]:
    """Split *key* into *num_shares* pieces, requiring *threshold* to reconstruct.
    Returns a list of share strings in the format 'x-y_hex'.
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes (256 bits)")
    
    secret = int.from_bytes(key, byteorder="big")
    if secret >= PRIME:
        raise ValueError("Secret is too large for the prime field")

    # Generate random coefficients for the polynomial of degree threshold - 1:
    # f(x) = secret + a_1 * x + a_2 * x^2 + ... + a_{t-1} * x^{t-1}
    coefficients = [secret]
    for _ in range(threshold - 1):
        # Generate 32 bytes of secure randomness and convert to integer mod PRIME
        rand_bytes = os.urandom(32)
        coeff = int.from_bytes(rand_bytes, byteorder="big") % PRIME
        coefficients.append(coeff)

    shares = []
    for x in range(1, num_shares + 1):
        # Evaluate polynomial f(x) mod PRIME
        y = 0
        x_pow = 1
        for coeff in coefficients:
            y = (y + coeff * x_pow) % PRIME
            x_pow = (x_pow * x) % PRIME
        
        # Represent y as a 32-byte hex string (64 characters)
        y_bytes = y.to_bytes(32, byteorder="big")
        shares.append(f"{x}-{y_bytes.hex()}")
    
    return shares

def reconstruct_key(shares: List[str]) -> bytes:
    """Reconstruct the original key from a list of share strings.
    Each share string must be in the format 'x-y_hex'.
    """
    if len(shares) < 1:
        raise RuntimeError("No shares provided for reconstruction.")
    
    # Parse the shares
    parsed_shares = []
    for share in shares:
        if "-" not in share:
            # Fallback/compatibility check: if it is a pure hex string,
            # we assume it is the old dummy format or raw key.
            try:
                raw_bytes = bytes.fromhex(share)
                if len(raw_bytes) == 32:
                    return raw_bytes
            except Exception:
                pass
            raise ValueError(f"Invalid share format: {share}")
        
        x_str, y_hex = share.split("-", 1)
        x = int(x_str)
        y = int.from_bytes(bytes.fromhex(y_hex), byteorder="big")
        parsed_shares.append((x, y))

    # Perform Lagrange interpolation at x = 0 to find the constant term (the secret)
    # L(x) = sum_{i} y_i * prod_{j != i} (x - x_j) / (x_i - x_j)
    # For L(0):
    # L(0) = sum_{i} y_i * prod_{j != i} (-x_j) / (xi - xj) mod PRIME
    secret = 0
    for i, (xi, yi) in enumerate(parsed_shares):
        numerator = 1
        denominator = 1
        for j, (xj, _) in enumerate(parsed_shares):
            if i == j:
                continue
            numerator = (numerator * (-xj)) % PRIME
            denominator = (denominator * (xi - xj)) % PRIME
        
        # Compute modular inverse of denominator modulo PRIME
        # Using Fermat's Little Theorem: inv = pow(denominator, PRIME - 2, PRIME)
        inv = pow(denominator, PRIME - 2, PRIME)
        term = (yi * numerator * inv) % PRIME
        secret = (secret + term) % PRIME

    secret_bytes = secret.to_bytes(32, byteorder="big")
    return secret_bytes

# ---------------------------------------------------------------------------
# Helper for generating a random AES‑256 key
# ---------------------------------------------------------------------------

def generate_aes_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)

# End of crypto.py
