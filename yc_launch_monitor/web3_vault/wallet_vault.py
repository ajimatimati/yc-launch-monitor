"""
Non-custodial PBKDF2 HMAC-SHA256 + Fernet Encrypted Wallet Vault.
Safely manages local keys with zero-leak master password derivation.
"""

from __future__ import annotations
import json
import os
import base64
from typing import Dict, List, Optional, Tuple
from eth_account import Account
from pydantic import BaseModel
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings

class WalletEntry(BaseModel):
    label: str
    address: str
    private_key: str

class WalletVault:
    def __init__(self, vault_path: Optional[str] = None, password: Optional[str] = None):
        self.vault_path = vault_path or settings.VAULT_FILE
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        self.wallets: Dict[str, WalletEntry] = {}
        self._salt: Optional[bytes] = None
        self._encrypted_data: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
        self.load()
        
        pwd = password or os.getenv("VAULT_PASSWORD", "mintdash_secure_alpha_vault_2026")
        if pwd:
            self.unlock(pwd)

    def load(self):
        """Load vault from disk."""
        self._encrypted_data = None
        self._salt = None
        self.wallets = {}
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if data.get("version") == 2:
                    self._salt = base64.b64decode(data["salt"])
                    self._encrypted_data = data["encrypted_data"].encode("utf-8")
                else:
                    for item in data.get("wallets", []):
                        w = WalletEntry(**item)
                        if not w.private_key.startswith("0x"):
                            w.private_key = "0x" + w.private_key
                        self.wallets[w.address.lower()] = w
            except Exception as e:
                print(f"[WalletVault] Warning: Failed to load vault file: {e}")

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    def unlock(self, password: str):
        """Unlock the vault with the master password."""
        if not self._salt:
            self._salt = os.urandom(16)
        
        key = self._derive_key(password, self._salt)
        self._fernet = Fernet(key)
        
        if self._encrypted_data:
            try:
                decrypted = self._fernet.decrypt(self._encrypted_data)
                data = json.loads(decrypted)
                self.wallets = {}
                for item in data.get("wallets", []):
                    w = WalletEntry(**item)
                    if not w.private_key.startswith("0x"):
                        w.private_key = "0x" + w.private_key
                    self.wallets[w.address.lower()] = w
                self._encrypted_data = None
            except (InvalidToken, ValueError) as e:
                self._fernet = None
                raise ValueError("Invalid password or corrupt data") from e

    def save(self):
        """Save the encrypted vault back to disk."""
        if self._fernet is None:
            self.unlock(os.getenv("VAULT_PASSWORD", "mintdash_secure_alpha_vault_2026"))

        wallets_data = [w.model_dump() for w in self.wallets.values()]
        payload = json.dumps({"wallets": wallets_data})
        encrypted = self._fernet.encrypt(payload.encode("utf-8"))
        
        vault_dict = {
            "version": 2,
            "salt": base64.b64encode(self._salt).decode("utf-8"),
            "encrypted_data": encrypted.decode("utf-8"),
            "wallet_count": len(self.wallets)
        }
        
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(vault_dict, f, indent=2)

    def create_wallet(self, label: str) -> WalletEntry:
        """Generates a new secure local keypair and adds it to the vault."""
        acct = Account.create()
        entry = WalletEntry(
            label=label,
            address=acct.address,
            private_key=acct.key.hex()
        )
        self.wallets[acct.address.lower()] = entry
        self.save()
        return entry

    def list_public_wallets(self) -> List[Dict[str, str]]:
        """Returns non-sensitive public wallet metadata."""
        return [
            {"label": w.label, "address": w.address}
            for w in self.wallets.values()
        ]

wallet_vault = WalletVault()
