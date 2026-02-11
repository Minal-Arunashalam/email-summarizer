import anthropic
from app.config import get_settings
from app.summarizer.prompts import get_summarization_prompt, get_system_prompt

settings = get_settings()


class SummarizationError(Exception):
    """Custom exception for summarization errors."""
    pass


async def summarize_emails(
    emails: list[dict],
    num_lines: int,
    sender_email: str,
) -> str:
    """
    Summarize emails using Claude API.

    Args:
        emails: List of email dictionaries
        num_lines: Number of lines for the summary
        sender_email: Email address of the sender

    Returns:
        Summary string

    Raises:
        SummarizationError: If summarization fails
    """
    if not emails:
        return "No emails found from this sender."

    if num_lines < 1 or num_lines > 20:
        raise SummarizationError("Number of lines must be between 1 and 20")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = get_summarization_prompt(emails, num_lines, sender_email)
    system_prompt = get_system_prompt()

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text from response
        if message.content and len(message.content) > 0:
            return message.content[0].text

        raise SummarizationError("Empty response from Claude API")

    except anthropic.APIError as e:
        raise SummarizationError(f"Claude API error: {str(e)}")
    except Exception as e:
        raise SummarizationError(f"Summarization failed: {str(e)}")
