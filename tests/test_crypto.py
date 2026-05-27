import json
import os
import pytest
from cseps import crypto, models, config

def test_key_generation_and_signing():
    priv, pub = crypto.generate_ecc_keypair()
    message = b"test message"
    signature = crypto.sign_message(priv, message)
    assert crypto.verify_signature(pub, message, signature)

def test_encryption_decryption_cycle():
    key = crypto.generate_aes_key()
    plaintext = b"sample bid data"
    nonce, ciphertext = crypto.encrypt_bid(key, plaintext)
    decrypted = crypto.decrypt_bid(key, nonce, ciphertext)
    assert decrypted == plaintext

def test_secret_sharing_roundtrip():
    key = crypto.generate_aes_key()
    shares = crypto.split_key(key, config.THRESHOLD, config.NUM_SHARES)
    recovered = crypto.reconstruct_key(shares[:config.THRESHOLD])
    assert recovered == key

def test_secret_sharing_various_subsets():
    key = crypto.generate_aes_key()
    shares = crypto.split_key(key, config.THRESHOLD, config.NUM_SHARES)
    
    # We should be able to reconstruct using any subset of size THRESHOLD (2)
    # Test using shares [0, 2]
    recovered1 = crypto.reconstruct_key([shares[0], shares[2]])
    assert recovered1 == key
    
    # Test using shares [1, 2] out of order
    recovered2 = crypto.reconstruct_key([shares[2], shares[1]])
    assert recovered2 == key

def test_secret_sharing_insufficient_shares():
    key = crypto.generate_aes_key()
    plaintext = b"critical bid information"
    nonce, ciphertext = crypto.encrypt_bid(key, plaintext)
    
    shares = crypto.split_key(key, config.THRESHOLD, config.NUM_SHARES)
    
    # Reconstruction with fewer than THRESHOLD (2) shares should yield a wrong key
    insufficient_shares = [shares[0]]
    bad_key = crypto.reconstruct_key(insufficient_shares)
    
    assert bad_key != key
    
    # Attempting to decrypt the ciphertext using the bad key must fail
    with pytest.raises(Exception):
        crypto.decrypt_bid(bad_key, nonce, ciphertext)
