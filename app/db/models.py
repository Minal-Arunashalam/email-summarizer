from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from cryptography.fernet import Fernet
import base64
import hashlib

from app.db.database import Base
from app.config import get_settings


def get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    settings = get_settings()
    # Derive a valid Fernet key from the encryption key
    key = hashlib.sha256(settings.token_encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


class User(Base):
    """User model storing OAuth tokens."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)

    # Encrypted OAuth tokens
    _access_token = Column("access_token", Text, nullable=True)
    _refresh_token = Column("refresh_token", Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def access_token(self) -> str | None:
        """Decrypt and return access token."""
        if self._access_token:
            fernet = get_fernet()
            return fernet.decrypt(self._access_token.encode()).decode()
        return None

    @access_token.setter
    def access_token(self, value: str | None):
        """Encrypt and store access token."""
        if value:
            fernet = get_fernet()
            self._access_token = fernet.encrypt(value.encode()).decode()
        else:
            self._access_token = None

    @property
    def refresh_token(self) -> str | None:
        """Decrypt and return refresh token."""
        if self._refresh_token:
            fernet = get_fernet()
            return fernet.decrypt(self._refresh_token.encode()).decode()
        return None

    @refresh_token.setter
    def refresh_token(self, value: str | None):
        """Encrypt and store refresh token."""
        if value:
            fernet = get_fernet()
            self._refresh_token = fernet.encrypt(value.encode()).decode()
        else:
            self._refresh_token = None
