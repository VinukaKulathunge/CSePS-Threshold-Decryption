# Cryptographically Secure Government e‑Procurement System (CSePS)

## Overview

CSePS is a prototype command‑line application that demonstrates a secure e‑procurement workflow using modern cryptographic primitives:

- **ECC** key pairs for digital signatures (ECDSA)
- **AES‑GCM** symmetric encryption for bid confidentiality
- **Shamir Secret Sharing** to split the encryption key among evaluators (threshold decryption)
- **Hash‑chained ledger** (append‑only JSON) providing tamper‑evidence and auditability

The system ensures:
- **Bid integrity** – signatures guarantee authenticity and non‑repudiation.
- **Bid anonymity** – bids are encrypted and cannot be read before the deadline.
- **Fairness** – a threshold key is required to decrypt, preventing a single party from opening bids early.
- **Transparency** – an immutable ledger records each submission.

## Project Structure

```
CSePS/
├─ cseps/
│  ├─ __init__.py
│  ├─ crypto.py      # ECC, signing, encryption, secret sharing
│  ├─ config.py      # Paths, cryptographic parameters, deadline
│  ├─ models.py      # Data classes for Bid, SignedBid, LedgerEntry
│  ├─ ledger.py      # Append‑only hash‑chained ledger utilities
│  └─ cli.py         # Click‑based CLI (submit, reveal, ledger)
├─ tests/            # Unit and integration tests (pytest)
├─ requirements.txt  # Python dependencies
└─ README.md         # This file
```

## Installation

1. **Clone the repository** (or copy the files into a directory).
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The CLI is built with **click**. Run the entry point with Python:

```bash
python -m cseps.cli --help
```

### Submit a bid
Create a JSON file describing a bid, e.g. `sample_bid.json`:
```json
{
  "bidder_id": "company_123",
  "amount": 250000.0,
  "description": "Supply of office chairs"
}
```
Submit it:
```bash
python -m cseps.cli submit sample_bid.json
```
The command will:
- Generate a temporary ECC key pair (in a real deployment keys would be persisted).
- Sign the bid.
- Encrypt the signed payload.
- Store the encrypted payload under `cseps/bids/`.
- Append a ledger entry.

### Reveal bids (after deadline)
```bash
python -m cseps.cli reveal
```
If the configured deadline (24 h from first run) has passed, the command reconstructs the AES key from the stored Shamir shares, decrypts each bid, and prints the original bid data.

### View the ledger
```bash
python -m cseps.cli ledger
```
The ledger is a JSON array (`cseps/ledger.json`). The command verifies the hash chain and pretty‑prints each entry.

## Configuration

Adjust parameters in `cseps/config.py`:
- `THRESHOLD` – minimum number of shares required to reconstruct the AES key.
- `NUM_SHARES` – total number of shares generated.
- `DEADLINE` – deadline for bid submission (default: 24 h from first run). You can set a fixed datetime for testing.

## Testing

A test suite is provided under `tests/`. Run it with:
```bash
pytest -q
```
The tests cover key generation, signing, encryption/decryption, secret sharing, and ledger integrity.

## Extending the Prototype

- Persist ECC key pairs per bidder instead of generating them on each submission.
- Replace the simple JSON ledger with a lightweight database.
- Add network APIs (e.g., FastAPI) for remote submission.
- Integrate a real threshold decryption protocol (e.g., Feldman VSS) for stronger security guarantees.

---

*This prototype is intended for educational and demonstration purposes and should not be used in production without a thorough security review.*
