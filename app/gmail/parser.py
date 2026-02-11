import base64
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime


def extract_email_content(message: dict) -> dict:
    """
    Extract relevant content from a Gmail API message.

    Args:
        message: Raw message from Gmail API

    Returns:
        Dictionary with subject, date, sender, and body
    """
    headers = message.get("payload", {}).get("headers", [])

    # Extract headers
    subject = ""
    date = ""
    sender = ""

    for header in headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")

        if name == "subject":
            subject = value
        elif name == "date":
            try:
                date = parsedate_to_datetime(value).isoformat()
            except Exception:
                date = value
        elif name == "from":
            sender = value

    # Extract body
    body = extract_body(message.get("payload", {}))

    return {
        "id": message.get("id"),
        "subject": subject,
        "date": date,
        "sender": sender,
        "body": body,
        "snippet": message.get("snippet", ""),
    }


def extract_body(payload: dict) -> str:
    """
    Extract plain text body from email payload.
    Handles multipart messages and HTML content.
    """
    body_text = ""

    # Check for direct body data
    if "body" in payload and payload["body"].get("data"):
        body_text = decode_base64(payload["body"]["data"])
        mime_type = payload.get("mimeType", "")
        if "html" in mime_type:
            body_text = html_to_text(body_text)
        return body_text

    # Handle multipart messages
    parts = payload.get("parts", [])
    if not parts:
        return body_text

    # First, try to find plain text part
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            if part.get("body", {}).get("data"):
                return decode_base64(part["body"]["data"])

    # Fall back to HTML part
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/html":
            if part.get("body", {}).get("data"):
                html_content = decode_base64(part["body"]["data"])
                return html_to_text(html_content)

    # Handle nested multipart
    for part in parts:
        if part.get("mimeType", "").startswith("multipart/"):
            nested_body = extract_body(part)
            if nested_body:
                return nested_body

    return body_text


def decode_base64(data: str) -> str:
    """Decode base64 URL-safe encoded string."""
    try:
        # Gmail uses URL-safe base64 encoding
        decoded = base64.urlsafe_b64decode(data)
        return decoded.decode("utf-8", errors="replace")
    except Exception:
        return ""


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "head", "meta", "link"]):
            element.decompose()

        # Get text
        text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        text = "\n".join(line for line in lines if line)

        return text
    except Exception:
        return html
