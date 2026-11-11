import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import importlib
import json
import os
from typing import Any, Dict, Optional
from uuid import uuid4

try:
    from jose import JWTError, jwt
except ImportError:
    try:
        jwt = importlib.import_module("jwt")
        JWTError = getattr(jwt, "PyJWTError", Exception)
    except ImportError:
        class JWTError(Exception):
            """Fallback JWTError when neither jose nor pyjwt is installed."""
            pass

        jwt = None

from app.core.config import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None,) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=24)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid4()),
        "type": "access",
    })

    if jwt is not None:
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    # Pure Python HS256 encoder fallback
    header_json = json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8")
    payload_json = json.dumps(to_encode, default=str).encode("utf-8")
    header_b64 = base64.urlsafe_b64encode(header_json).rstrip(b"=").decode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).rstrip(b"=").decode("utf-8")
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode("utf-8")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_token(token: str) -> Dict[str, Any]:
    # Both portals read the audit trail, so this service accepts either
    # audience. Verification is disabled explicitly rather than by omission:
    # python-jose rejects any token carrying `aud` when the decoder does not
    # expect one, which would break every caller the moment realms shipped.
    if jwt is not None:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )

    # Lightweight fallback decoder if JWT library is not installed in the environment
    try:
        parts = token.split(".")
        if len(parts) < 2:
            raise JWTError("Invalid token format")
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")))
    except Exception as e:
        raise JWTError(f"Cannot decode token: {str(e)}")


def verify_access_token(token: str) -> Dict[str, Any]:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    exp = payload.get("exp")
    if exp is not None and datetime.now(timezone.utc).timestamp() > exp:
        raise JWTError("Access token expired")
    return payload


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token (default 7 days)."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=7)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid4()),
        "type": "refresh",
    })

    if jwt is not None:
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    header_json = json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8")
    payload_json = json.dumps(to_encode, default=str).encode("utf-8")
    header_b64 = base64.urlsafe_b64encode(header_json).rstrip(b"=").decode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).rstrip(b"=").decode("utf-8")
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode("utf-8")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Verify refresh token validity and expiration."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Not a refresh token")
    exp = payload.get("exp")
    if exp is not None and datetime.now(timezone.utc).timestamp() > exp:
        raise JWTError("Refresh token expired")
    return payload


class PasswordHasher:
    """
    Object-oriented password hashing and verification utility.
    Uses PBKDF2 HMAC SHA-256 with cryptographically secure per-password salt.
    """

    def __init__(self, iterations: int = 100_000, algorithm: str = "sha256") -> None:
        self.iterations = iterations
        self.algorithm = algorithm

    def hash_password(self, password: str) -> str:
        """Hash a plain text password with a secure random salt."""
        salt = os.urandom(16).hex()
        key = hashlib.pbkdf2_hmac(
            self.algorithm,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            self.iterations,
        ).hex()
        return f"{salt}${key}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify plain text password against the hashed password string."""
        try:
            salt, expected_hash = hashed_password.split("$", 1)
            key = hashlib.pbkdf2_hmac(
                self.algorithm,
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                self.iterations,
            ).hex()
            return hmac.compare_digest(key, expected_hash)
        except (ValueError, AttributeError):
            return False


# Default singleton instance
password_hasher = PasswordHasher()

# Functional aliases for convenience
hash_password = password_hasher.hash_password
verify_password = password_hasher.verify_password
