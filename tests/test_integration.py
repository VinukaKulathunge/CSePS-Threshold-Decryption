import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from cseps import crypto, config, models, ledger, cli

@pytest.fixture
def temp_env(tmp_path):
    # Backup original config paths
    orig_ledger = config.LEDGER_FILE
    orig_ledger_module = ledger.LEDGER_FILE
    orig_bids_dir = config.BIDS_DIR
    orig_deadline = config.DEADLINE

    # Set up temp paths
    temp_ledger = tmp_path / "ledger.json"
    temp_bids_dir = tmp_path / "bids"
    temp_bids_dir.mkdir()

    config.LEDGER_FILE = str(temp_ledger)
    ledger.LEDGER_FILE = str(temp_ledger)
    config.BIDS_DIR = str(temp_bids_dir)
    config.DEADLINE = config.START_TIME + timedelta(hours=24)

    yield tmp_path

    # Restore original config paths
    config.LEDGER_FILE = orig_ledger
    ledger.LEDGER_FILE = orig_ledger_module
    config.BIDS_DIR = orig_bids_dir
    config.DEADLINE = orig_deadline

    # Clean up temp files if they exist
    if temp_ledger.exists():
        temp_ledger.unlink()
    if temp_bids_dir.exists():
        shutil.rmtree(temp_bids_dir)

def test_end_to_end_flow(temp_env):
    # 1. Create a bid
    bid_data = models.Bid(
        bidder_id="company_test_99",
        amount=12345.67,
        description="High-performance server hardware"
    )

    # 2. Submit the bid (similar to the CLI submission logic)
    priv_key, pub_key = crypto.generate_ecc_keypair()
    pub_pem = crypto.serialize_public_key(pub_key).decode("utf-8")
    signature = crypto.sign_message(priv_key, bid_data.to_json().encode()).hex()
    signed_bid = models.SignedBid(bid=bid_data, signature=signature, public_key_pem=pub_pem)
    signed_bid_json = signed_bid.to_json()

    aes_key = crypto.generate_aes_key()
    nonce, ciphertext = crypto.encrypt_bid(aes_key, signed_bid_json.encode())
    shares = crypto.split_key(aes_key, config.THRESHOLD, config.NUM_SHARES)
    
    payload = {
        "nonce": nonce.hex(),
        "ciphertext": ciphertext.hex(),
        "shares": shares,
    }

    bid_id = "test_bid"
    out_path = Path(config.BIDS_DIR) / f"{bid_id}_enc.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    entry = ledger.add_entry(signed_bid_json)

    # Assert ledger entry was written correctly
    assert Path(config.LEDGER_FILE).exists()
    assert out_path.exists()
    assert ledger.verify_chain() is True

    # 3. Try to decrypt before deadline has passed (should fail in CLI checks)
    assert config.deadline_passed() is False

    # 4. Advance deadline past "now" to simulate passage of time
    config.DEADLINE = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    assert config.deadline_passed() is True

    # 5. Perform reconstruction and decryption of bid
    with open(out_path, "r", encoding="utf-8") as f:
        loaded_payload = json.load(f)
    
    loaded_nonce = bytes.fromhex(loaded_payload["nonce"])
    loaded_ciphertext = bytes.fromhex(loaded_payload["ciphertext"])
    loaded_shares = loaded_payload["shares"]

    # Reconstruct the AES key using threshold shares (e.g. shares [0, 2])
    reconstructed_key = crypto.reconstruct_key([loaded_shares[0], loaded_shares[2]])
    assert reconstructed_key == aes_key

    # Decrypt and verify bid contents
    decrypted_json = crypto.decrypt_bid(reconstructed_key, loaded_nonce, loaded_ciphertext).decode("utf-8")
    reconstructed_signed_bid = models.SignedBid.from_json(decrypted_json)

    assert reconstructed_signed_bid.bid.bidder_id == "company_test_99"
    assert reconstructed_signed_bid.bid.amount == 12345.67
    assert reconstructed_signed_bid.bid.description == "High-performance server hardware"
    
    # Verify the signature
    reconstructed_pub_key = crypto.load_public_key(reconstructed_signed_bid.public_key_pem.encode("utf-8"))
    reconstructed_sig = bytes.fromhex(reconstructed_signed_bid.signature)
    assert crypto.verify_signature(reconstructed_pub_key, reconstructed_signed_bid.bid.to_json().encode(), reconstructed_sig) is True
