from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.config import get_settings
from app.db.database import init_db, get_db
from app.auth.router import router as auth_router, get_session_user_id
from app.auth.oauth import get_user_by_id
from app.gmail.service import fetch_emails_from_sender
from app.summarizer.service import summarize_emails, SummarizationError


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Email Summarizer",
    description="Summarize emails from any sender using AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include auth router
app.include_router(auth_router)


# Request/Response models
class SummarizeRequest(BaseModel):
    sender_email: EmailStr
    num_lines: int = 5
    max_emails: int = 10


class SummarizeResponse(BaseModel):
    summary: str
    email_count: int
    sender_email: str


# Dependency to get current user
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user or None."""
    user_id = get_session_user_id(request)
    if not user_id:
        return None
    return await get_user_by_id(db, user_id)


async def require_auth(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Require authenticated user or redirect to login."""
    user = await get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    user=Depends(get_current_user),
):
    """Home page - show login or redirect to dashboard."""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": None},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Dashboard page - main form for summarization."""
    user_id = get_session_user_id(request)
    if not user_id:
        return RedirectResponse(url="/", status_code=302)

    user = await get_user_by_id(db, user_id)
    if not user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user},
    )


@app.post("/api/summarize", response_model=SummarizeResponse)
async def api_summarize(
    request: Request,
    data: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
):
    """API endpoint to summarize emails."""
    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Validate num_lines
    if data.num_lines < 1 or data.num_lines > 20:
        raise HTTPException(
            status_code=400,
            detail="Number of lines must be between 1 and 20",
        )

    # Validate max_emails
    if data.max_emails < 1 or data.max_emails > 100:
        raise HTTPException(
            status_code=400,
            detail="Max emails must be between 1 and 100",
        )

    try:
        # Fetch emails
        emails = await fetch_emails_from_sender(
            user=user,
            sender_email=data.sender_email,
            max_results=data.max_emails,
        )

        if not emails:
            raise HTTPException(
                status_code=404,
                detail=f"No emails found from {data.sender_email}",
            )

        # Summarize
        summary = await summarize_emails(
            emails=emails,
            num_lines=data.num_lines,
            sender_email=data.sender_email,
        )

        return SummarizeResponse(
            summary=summary,
            email_count=len(emails),
            sender_email=data.sender_email,
        )

    except SummarizationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        )


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
