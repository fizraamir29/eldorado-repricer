"""
Security helpers:
  - password hashing (bcrypt via passlib)
  - JWT issuing/verification for dashboard login
  - Fernet encryption for storing the client's marketplace API key at rest

Never store the client's Eldorado API key in plaintext. Encrypt on write,
decrypt only in-memory right before calling the marketplace API.
"""
from datetime import datetime, timedelta, timezone

# pyrefly: ignore [missing-import]
import bcrypt
# pyrefly: ignore [missing-import]
from cryptography.fernet import Fernet
# pyrefly: ignore [missing-source-for-stubs]
from jose import jwt

from app.config import settings

if not settings.encryption_key or len(settings.encryption_key) != 44:
    raise ValueError("A valid 44-character Fernet encryption key must be provided in the ENCRYPTION_KEY environment variable.")
_fernet = Fernet(settings.encryption_key.encode())


def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode('utf-8')[:72]
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return payload["sub"]


def encrypt_secret(raw: str) -> str:
    return _fernet.encrypt(raw.encode()).decode()


def decrypt_secret(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()
