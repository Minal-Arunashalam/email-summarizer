from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from itsdangerous import URLSafeTimedSerializer

from app.config import get_settings
from app.db.database import get_db
from app.auth.oauth import (
    get_authorization_url,
    exchange_code_for_tokens,
    get_or_create_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Serializer for session cookies
serializer = URLSafeTimedSerializer(settings.secret_key)


def get_session_user_id(request: Request) -> int | None:
    """Extract user ID from session cookie."""
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return None
    try:
        data = serializer.loads(session_cookie, max_age=86400 * 7)  # 7 days
        return data.get("user_id")
    except Exception:
        return None


@router.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login."""
    authorization_url, state = get_authorization_url()

    response = RedirectResponse(url=authorization_url)
    # Store state in cookie for CSRF protection
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=600,  # 10 minutes
    )
    return response


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Verify state for CSRF protection
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        # Exchange code for tokens
        user_data = await exchange_code_for_tokens(code)

        # Get or create user
        user = await get_or_create_user(db, user_data)

        # Create session
        session_data = {"user_id": user.id}
        session_token = serializer.dumps(session_data)

        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="session",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400 * 7,  # 7 days
        )
        # Clear oauth state cookie
        response.delete_cookie("oauth_state")

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/logout")
async def logout(request: Request):
    """Log out the user."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session")
    return response
