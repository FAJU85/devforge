"""Encryption/decryption for sensitive user data (API keys, tokens)."""

import os
import base64
import hashlib

# Try to import cryptography, but allow graceful degradation for dev
_cipher = None
try:
    from cryptography.fernet import Fernet

    # Derive encryption key from environment or use default (for dev)
    _ENCRYPTION_KEY_ENV = os.environ.get("ENCRYPTION_KEY")

    if _ENCRYPTION_KEY_ENV:
        # Use provided key (must be 32 bytes base64-encoded)
        try:
            _encryption_key = base64.urlsafe_b64encode(
                _ENCRYPTION_KEY_ENV.encode()[:32].ljust(32, b'\0')
            )
        except Exception:
            raise ValueError("ENCRYPTION_KEY must be a valid string for derivation")
    else:
        # Development default: derive from a fixed phrase
        _dev_phrase = b"devforge-dev-secret-do-not-use-in-production"
        _encryption_key = base64.urlsafe_b64encode(
            hashlib.sha256(_dev_phrase).digest()
        )

    _cipher = Fernet(_encryption_key)
except ImportError:
    print("[WARN] cryptography not available, using plaintext for secrets (dev mode)")
    _cipher = None


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret string (or return plaintext if encryption unavailable)."""
    if _cipher:
        encrypted = _cipher.encrypt(plaintext.encode())
        return f"encrypted:{encrypted.decode()}"
    return f"plaintext:{plaintext}"


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a secret string (or return plaintext if encryption unavailable)."""
    if ciphertext.startswith("plaintext:"):
        return ciphertext[10:]
    if ciphertext.startswith("encrypted:"):
        if _cipher:
            try:
                decrypted = _cipher.decrypt(ciphertext[10:].encode())
                return decrypted.decode()
            except Exception as e:
                raise ValueError(f"Failed to decrypt secret: {e}")
        else:
            raise ValueError("Encryption not available but encrypted secret provided")
    # Legacy: try to decrypt as-is if no prefix
    if _cipher:
        try:
            decrypted = _cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception:
            pass
    return ciphertext


def hash_token(token: str) -> str:
    """Hash a session token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()
