"""Cryptographic engine for Pharaoh Cryption.

The format is intentionally small and versioned so ciphertexts can be parsed by
future versions without guessing their parameters.
"""

from __future__ import annotations

import base64
import binascii
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


CIPHERTEXT_PREFIX = "PHARAOH-AES256-GCM:v1:"
KEY_PREFIX = "PHARAOH-KEY:v1:"
AAD = b"PHARAOH-AES256-GCM:v1"
KEY_BYTES = 32  # 256 bits
NONCE_BYTES = 12  # 96 bits, the recommended GCM nonce size
TAG_BYTES = 16  # AES-GCM authentication tag length


class PharaohCryptionError(Exception):
    """Base exception for expected Pharaoh Cryption errors."""


class InvalidCiphertextError(PharaohCryptionError):
    """Ciphertext is malformed, incomplete, or from an unsupported version."""


class InvalidKeyError(PharaohCryptionError):
    """The supplied key is malformed or has the wrong size."""


class DecryptionError(PharaohCryptionError):
    """Authentication failed or the decrypted bytes are not valid UTF-8."""


@dataclass(frozen=True, slots=True)
class EncryptionResult:
    """Ciphertext and its separately encoded decryption key."""

    ciphertext: str
    key: str


def _encode(data: bytes) -> str:
    """Encode bytes using URL-safe Base64 (padding retained for portability)."""

    return base64.urlsafe_b64encode(data).decode("ascii")


def _decode(value: str, *, field_name: str) -> bytes:
    """Strictly decode URL-safe Base64 and raise a useful domain error."""

    try:
        encoded = value.encode("ascii")
        return base64.b64decode(encoded, altchars=b"-_", validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        error_type = InvalidKeyError if field_name == "key" else InvalidCiphertextError
        raise error_type(f"The {field_name} contains invalid Base64 data.") from exc


def encrypt_text(plaintext: str) -> EncryptionResult:
    """Encrypt UTF-8 text using a fresh AES-256-GCM key and nonce.

    A new random 256-bit key is generated for every message. The returned key
    is not embedded in the ciphertext and must be stored separately.
    """

    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")

    key_bytes = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(NONCE_BYTES)
    encrypted = AESGCM(key_bytes).encrypt(nonce, plaintext.encode("utf-8"), AAD)

    ciphertext = CIPHERTEXT_PREFIX + _encode(nonce + encrypted)
    key = KEY_PREFIX + _encode(key_bytes)
    return EncryptionResult(ciphertext=ciphertext, key=key)


def decrypt_text(ciphertext: str, key: str) -> str:
    """Authenticate and decrypt a Pharaoh Cryption text envelope."""

    if not isinstance(ciphertext, str) or not ciphertext.startswith(CIPHERTEXT_PREFIX):
        raise InvalidCiphertextError(
            "This is not a supported Pharaoh Cryption v1 ciphertext."
        )
    if not isinstance(key, str) or not key.startswith(KEY_PREFIX):
        raise InvalidKeyError("This is not a supported Pharaoh Cryption v1 key.")

    encoded_payload = ciphertext[len(CIPHERTEXT_PREFIX) :]
    encoded_key = key[len(KEY_PREFIX) :]
    payload = _decode(encoded_payload, field_name="ciphertext")
    key_bytes = _decode(encoded_key, field_name="key")

    if len(key_bytes) != KEY_BYTES:
        raise InvalidKeyError("AES-256 requires an exactly 32-byte (256-bit) key.")
    if len(payload) < NONCE_BYTES + TAG_BYTES:
        raise InvalidCiphertextError("The ciphertext is too short to be valid.")

    nonce, encrypted = payload[:NONCE_BYTES], payload[NONCE_BYTES:]
    try:
        plaintext = AESGCM(key_bytes).decrypt(nonce, encrypted, AAD)
    except InvalidTag as exc:
        raise DecryptionError(
            "Authentication failed. The key is incorrect or the ciphertext was changed."
        ) from exc

    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DecryptionError("The decrypted content is not valid UTF-8 text.") from exc
