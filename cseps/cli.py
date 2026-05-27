# cli.py – Interactive menu‑driven CLI for CSePS prototype

"""
Provides an interactive text‑based menu (and retains the original Click commands
for advanced usage) that allows users to:

1. Submit a new bid
2. Reveal bids after the deadline
3. View the tamper‑proof ledger
4. Exit

The menu minimizes the need to remember command‑line arguments. Users can simply
run the module:

```bash
python -m cseps.cli
```

and follow the on‑screen prompts.
"""

import json
import sys
from pathlib import Path
import click

from . import crypto, config, models, ledger

# ---------------------------------------------------------------------------
# Helper functions (same as before)
# ---------------------------------------------------------------------------

def _load_bid_file(bid_path: str) -> models.Bid:
    """Load a bid JSON file and return a ``Bid`` instance."""
    with open(bid_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return models.Bid(**data)

import uuid

def _submit_bid_interactive() -> None:
    """Interactively ask for bid details and process the submission."""
    print("--- Create a new bid ---")
    bidder_id = input("Enter bidder ID: ").strip()
    amount_str = input("Enter bid amount: ").strip()
    try:
        amount = float(amount_str)
    except ValueError:
        print("Invalid amount. Must be a number.")
        return
    description = input("Enter bid description: ").strip()

    if not bidder_id or not description:
        print("Bidder ID and description cannot be empty.")
        return

    bid = models.Bid(bidder_id=bidder_id, amount=amount, description=description)
    
    # Generate a fresh ECC key pair (in a real system this would be persisted)
    priv_key, pub_key = crypto.generate_ecc_keypair()
    pub_pem = crypto.serialize_public_key(pub_key).decode("utf-8")
    
    # Sign the bid
    signature = crypto.sign_message(priv_key, bid.to_json().encode()).hex()
    signed_bid = models.SignedBid(bid=bid, signature=signature, public_key_pem=pub_pem)
    signed_bid_json = signed_bid.to_json()
    
    # Encrypt the signed bid
    aes_key = crypto.generate_aes_key()
    nonce, ciphertext = crypto.encrypt_bid(aes_key, signed_bid_json.encode())
    
    # Split the AES key (dummy shares)
    shares = crypto.split_key(aes_key, config.THRESHOLD, config.NUM_SHARES)
    payload = {
        "nonce": nonce.hex(),
        "ciphertext": ciphertext.hex(),
        "shares": shares,
    }
    
    bid_id = str(uuid.uuid4())
    out_path = Path(config.BIDS_DIR) / f"{bid_id}_enc.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    
    entry = ledger.add_entry(signed_bid_json)
    print(f"Bid successfully created and submitted. Ledger entry ID: {entry.entry_id}\n")

def _reveal_bids_interactive() -> None:
    """Decrypt and display all bids after the deadline."""
    if not config.deadline_passed():
        print("Deadline has not passed yet. Cannot reveal bids.")
        return
    enc_files = list(Path(config.BIDS_DIR).glob("*_enc.json"))
    if not enc_files:
        print("No encrypted bids found.")
        return
    for enc_path in enc_files:
        with open(enc_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        nonce = bytes.fromhex(payload["nonce"])
        ciphertext = bytes.fromhex(payload["ciphertext"])
        shares = payload["shares"]
        try:
            aes_key = crypto.reconstruct_key(shares[: config.THRESHOLD])
            decrypted = crypto.decrypt_bid(aes_key, nonce, ciphertext)
            signed_bid = models.SignedBid.from_json(decrypted.decode())
            print(f"--- Bid from {signed_bid.bid.bidder_id} ---")
            print(json.dumps(signed_bid.bid.__dict__, indent=2))
        except Exception as e:
            print(f"Failed to process {enc_path.name}: {e}")

def _show_ledger_interactive() -> None:
    """Verify the ledger integrity and pretty‑print its entries."""
    if not ledger.verify_chain():
        print("Ledger integrity check FAILED! The chain is broken.")
        return
    ledger.print_ledger()

def _menu() -> None:
    """Simple text‑based menu loop."""
    while True:
        print("\nCSePS Menu")
        print("1) Submit a bid")
        print("2) Reveal bids (after deadline)")
        print("3) View ledger")
        print("4) Launch Web Dashboard (Flask)")
        print("5) Exit")
        choice = input("Select an option [1-5]: ").strip()
        if choice == "1":
            _submit_bid_interactive()
        elif choice == "2":
            _reveal_bids_interactive()
        elif choice == "3":
            _show_ledger_interactive()
        elif choice == "4":
            print("Starting CSePS Web Dashboard on http://127.0.0.1:5000/ ...")
            from .web import app
            app.run(host="127.0.0.1", port=5000)
            break
        elif choice == "5":
            print("Good‑bye!")
            break
        else:
            print("Invalid choice. Please try again.")

# ---------------------------------------------------------------------------
# Click entry points (retain for power users)
# ---------------------------------------------------------------------------
@click.group()
def cli():
    """CSePS – Cryptographically Secure e‑Procurement System (CLI)"""
    pass

@cli.command()
@click.argument("bid_file", type=click.Path(exists=True, dir_okay=False))
def submit(bid_file: str):
    """Submit a new bid (non‑interactive version)."""
    # Re‑use the interactive implementation logic
    bid = _load_bid_file(bid_file)
    priv_key, pub_key = crypto.generate_ecc_keypair()
    pub_pem = crypto.serialize_public_key(pub_key).decode()
    signature = crypto.sign_message(priv_key, bid.to_json().encode()).hex()
    signed_bid = models.SignedBid(bid=bid, signature=signature, public_key_pem=pub_pem)
    signed_bid_json = signed_bid.to_json()
    aes_key = crypto.generate_aes_key()
    nonce, ciphertext = crypto.encrypt_bid(aes_key, signed_bid_json.encode())
    shares = crypto.split_key(aes_key, config.THRESHOLD, config.NUM_SHARES)
    payload = {"nonce": nonce.hex(), "ciphertext": ciphertext.hex(), "shares": shares}
    out_path = Path(config.BIDS_DIR) / f"{Path(bid_file).stem}_enc.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    entry = ledger.add_entry(signed_bid_json)
    click.echo(f"Bid submitted successfully. Ledger entry ID: {entry.entry_id}")

@cli.command()
def reveal():
    """Reveal all bids after the deadline."""
    _reveal_bids_interactive()

@cli.command(name="ledger")
def ledger_cmd():
    """Display the ledger."""
    _show_ledger_interactive()

@cli.command()
def web():
    """Launch the Web Dashboard (Flask server)."""
    click.echo("Starting CSePS Web Dashboard on http://127.0.0.1:5000/ ...")
    from .web import app
    app.run(host="127.0.0.1", port=5000)

# When the module is executed directly, launch the menu or the Click CLI based on arguments
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        _menu()

# End of cli.py
