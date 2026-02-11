from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.db.models import User
from app.auth.oauth import get_credentials_for_user
from app.gmail.parser import extract_email_content


async def get_gmail_service(user: User):
    """Build Gmail API service for a user."""
    credentials = get_credentials_for_user(user)

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    return build("gmail", "v1", credentials=credentials)


async def fetch_emails_from_sender(
    user: User,
    sender_email: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Fetch emails from a specific sender.

    Args:
        user: User with OAuth credentials
        sender_email: Email address of the sender to filter by
        max_results: Maximum number of emails to fetch

    Returns:
        List of email dictionaries with subject, date, and body
    """
    service = await get_gmail_service(user)

    # Search for emails from the sender
    query = f"from:{sender_email}"
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    messages = results.get("messages", [])

    if not messages:
        return []

    emails = []
    for message in messages:
        # Get full message details
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message["id"], format="full")
            .execute()
        )

        email_data = extract_email_content(msg)
        emails.append(email_data)

    return emails
