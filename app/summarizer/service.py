import re
import asyncio
import anthropic
from app.config import get_settings
from app.summarizer.prompts import get_summarization_prompt, get_system_prompt

settings = get_settings()

# Truncate email bodies to reduce token usage
MAX_BODY_LENGTH = 1000


class SummarizationError(Exception):
    """Custom exception for summarization errors."""
    pass


def parse_summaries(response_text: str, expected_count: int) -> list[str]:
    """Parse individual summaries from Claude's response."""
    summaries = []

    # Try to extract summaries using the [SUMMARY N] format
    pattern = r'\[SUMMARY \d+\]\s*(.*?)\s*\[/SUMMARY \d+\]'
    matches = re.findall(pattern, response_text, re.DOTALL)

    if matches:
        summaries = [match.strip() for match in matches]
    else:
        # Fallback: split by numbered patterns like "1.", "2.", etc.
        lines = response_text.strip().split('\n')
        current_summary = []

        for line in lines:
            # Check if line starts a new summary (e.g., "1.", "Email 1:", etc.)
            if re.match(r'^(\d+[\.\):]|Email \d+)', line.strip()):
                if current_summary:
                    summaries.append('\n'.join(current_summary).strip())
                current_summary = [re.sub(r'^(\d+[\.\):]|Email \d+:?\s*)', '', line).strip()]
            elif line.strip():
                current_summary.append(line.strip())

        if current_summary:
            summaries.append('\n'.join(current_summary).strip())

    return summaries


async def summarize_emails(
    emails: list[dict],
    num_lines: int,
    sender_email: str,
) -> list[dict]:
    """
    Summarize each email individually using Claude API.

    Args:
        emails: List of email dictionaries
        num_lines: Number of lines for each email's summary
        sender_email: Email address of the sender

    Returns:
        List of dicts with email metadata and individual summaries

    Raises:
        SummarizationError: If summarization fails
    """
    if not emails:
        return []

    if num_lines < 1 or num_lines > 10:
        raise SummarizationError("Number of lines must be between 1 and 10")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    system_prompt = get_system_prompt()

    # Truncate email bodies to reduce token usage
    truncated_emails = []
    for email in emails:
        truncated = email.copy()
        body = truncated.get("body", truncated.get("snippet", ""))
        if len(body) > MAX_BODY_LENGTH:
            truncated["body"] = body[:MAX_BODY_LENGTH] + "..."
        truncated_emails.append(truncated)

    # Process in small batches to avoid rate limits
    batch_size = 5  # Smaller batches to stay under rate limit
    all_results = []

    for batch_start in range(0, len(truncated_emails), batch_size):
        batch_emails = truncated_emails[batch_start:batch_start + batch_size]
        prompt = get_summarization_prompt(batch_emails, num_lines, sender_email)

        # Add delay between batches to avoid rate limits (except for first batch)
        if batch_start > 0:
            await asyncio.sleep(5)  # 5 seconds to let rate limit reset

        try:
            # Adjust max_tokens based on batch size and num_lines
            max_tokens = min(4096, len(batch_emails) * num_lines * 100)

            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            if not message.content or len(message.content) == 0:
                raise SummarizationError("Empty response from Claude API")

            response_text = message.content[0].text
            summaries = parse_summaries(response_text, len(batch_emails))

            # Match summaries with emails
            for i, email in enumerate(batch_emails):
                summary = summaries[i] if i < len(summaries) else "Summary unavailable"
                all_results.append({
                    "subject": email.get("subject", "No Subject"),
                    "date": email.get("date", "Unknown"),
                    "snippet": email.get("snippet", ""),
                    "summary": summary,
                })

        except anthropic.APIError as e:
            raise SummarizationError(f"Claude API error: {str(e)}")
        except SummarizationError:
            raise
        except Exception as e:
            raise SummarizationError(f"Summarization failed: {str(e)}")

    return all_results
