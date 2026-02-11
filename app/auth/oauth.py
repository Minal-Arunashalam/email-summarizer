from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.config import get_settings
from app.db.models import User

settings = get_settings()


def create_oauth_flow() -> Flow:
    """Create Google OAuth flow."""
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=settings.gmail_scopes,
        redirect_uri=settings.google_redirect_uri,
    )
    return flow


def get_authorization_url() -> str:
    """Generate authorization URL for Google OAuth."""
    flow = create_oauth_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent to get refresh token
    )
    return authorization_url


async def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange authorization code for tokens.
    Returns user info and tokens.
    """
    flow = create_oauth_flow()
    flow.fetch_token(code=code)

    credentials = flow.credentials

    # Get user info from Google
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        response.raise_for_status()
        user_info = response.json()

    return {
        "google_id": user_info["id"],
        "email": user_info["email"],
        "name": user_info.get("name"),
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_expiry": credentials.expiry,
    }


async def get_or_create_user(db: AsyncSession, user_data: dict) -> User:
    """Get existing user or create new one."""
    stmt = select(User).where(User.google_id == user_data["google_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Update tokens
        user.access_token = user_data["access_token"]
        if user_data.get("refresh_token"):
            user.refresh_token = user_data["refresh_token"]
        user.token_expiry = user_data.get("token_expiry")
        user.updated_at = datetime.utcnow()
    else:
        # Create new user
        user = User(
            google_id=user_data["google_id"],
            email=user_data["email"],
            name=user_data.get("name"),
        )
        user.access_token = user_data["access_token"]
        user.refresh_token = user_data.get("refresh_token")
        user.token_expiry = user_data.get("token_expiry")
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Get user by ID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def refresh_access_token(user: User, db: AsyncSession) -> str:
    """Refresh the access token if expired."""
    if not user.refresh_token:
        raise ValueError("No refresh token available")

    credentials = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )

    if credentials.expired or not credentials.valid:
        credentials.refresh(Request())
        user.access_token = credentials.token
        user.token_expiry = credentials.expiry
        await db.commit()

    return user.access_token


def get_credentials_for_user(user: User) -> Credentials:
    """Get Google credentials object for a user."""
    return Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        expiry=user.token_expiry,
    )
