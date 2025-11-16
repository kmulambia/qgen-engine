from typing import Any, Tuple
import hashlib
import json
import secrets
from base64 import b64encode, b64decode


class HashingError(Exception):
    pass


def encrypt(value: str, rounds: int = 100_000) -> Tuple[str, str]:
    """Hash value using PBKDF2-HMAC-SHA256 with random salt."""
    if not isinstance(value, str):
        raise TypeError("Value must be a string")
    if not value:
        raise HashingError("Value cannot be empty")

    try:
        salt = secrets.token_bytes(32)
        dk = hashlib.pbkdf2_hmac(
            hash_name='sha256',
            password=value.encode('utf-8'),
            salt=salt,
            iterations=rounds
        )
        return b64encode(dk).decode('utf-8'), b64encode(salt).decode('utf-8')

    except Exception as e:
        raise HashingError(f"Encryption failed: {str(e)}")


def verify(value: str, hashed_value: str, salt: str, rounds: int = 100_000) -> bool:
    """Verify if provided value matches stored hash."""
    if not all(isinstance(x, str) for x in (value, hashed_value, salt)):
        raise TypeError("All inputs must be strings")
    if not all((value, hashed_value, salt)):
        raise HashingError("Inputs cannot be empty")
    try:
        # decoded_hash = b64decode(hashed_value)
        decoded_salt = b64decode(salt)
        dk = hashlib.pbkdf2_hmac(
            hash_name='sha256',
            password=value.encode('utf-8'),
            salt=decoded_salt,
            iterations=rounds
        )
        return secrets.compare_digest(b64encode(dk), hashed_value.encode('utf-8'))
    except Exception as e:
        raise HashingError(f"Verification failed: {str(e)}")


def generate_hash(*args: Any) -> str:
    """Generate SHA-256 hash of given arguments."""
    if not args:
        raise HashingError("At least one argument must be provided")
    hasher = hashlib.sha256()
    try:
        for arg in args:
            if isinstance(arg, (dict, list)):
                arg_str = json.dumps(arg, sort_keys=True, separators=(',', ':'))
            else:
                arg_str = str(arg)
            hasher.update(arg_str.encode('utf-8'))
        return hasher.hexdigest()
    except (TypeError, ValueError, json.JSONDecodeError) as e:
        raise HashingError(f"Failed to generate hash: {str(e)}")
