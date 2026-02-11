def get_summarization_prompt(emails: list[dict], num_lines: int, sender_email: str) -> str:
    """
    Generate prompt for individual email summarization.

    Args:
        emails: List of email dictionaries
        num_lines: Number of lines for each email's summary
        sender_email: Email address of the sender

    Returns:
        Formatted prompt string
    """
    # Format emails for the prompt
    email_texts = []
    for i, email in enumerate(emails, 1):
        email_text = f"""
[EMAIL {i}]
Subject: {email.get('subject', 'No Subject')}
Date: {email.get('date', 'Unknown')}
Content:
{email.get('body', email.get('snippet', 'No content'))}
[/EMAIL {i}]
"""
        email_texts.append(email_text)

    all_emails = "\n".join(email_texts)

    prompt = f"""Summarize each of the following {len(emails)} emails from {sender_email} INDIVIDUALLY.

For EACH email, provide exactly {num_lines} line(s) of summary.

Output format - use this EXACT format for each email:
[SUMMARY 1]
(your {num_lines}-line summary for email 1)
[/SUMMARY 1]

[SUMMARY 2]
(your {num_lines}-line summary for email 2)
[/SUMMARY 2]

...and so on for all {len(emails)} emails.

Instructions:
- Summarize EACH email separately - do NOT combine emails
- Each summary should be exactly {num_lines} line(s)
- Focus on the key point, action items, or important information
- Use bullet points (•) if multiple lines

CRITICAL - Be SPECIFIC, not vague:
- NEVER say "discusses X" or "covers X" - instead STATE what X actually is
- NEVER say "presents a solution" - STATE what the solution is
- NEVER say "mentions N techniques/tips/steps" - LIST them by name
- NEVER reference the email itself - just state the information directly
- Extract and state ACTUAL content: specific names, techniques, steps, numbers, recommendations

BAD (vague): "Discusses 4 parallel processing techniques for Python"
GOOD (specific): "Python parallel processing: use multiprocessing for CPU-bound tasks, threading for I/O-bound, asyncio for concurrent I/O, and concurrent.futures for simple parallelism"

BAD (vague): "Presents a solution for handling API rate limits"
GOOD (specific): "Handle API rate limits with exponential backoff: start at 1s delay, double after each 429 response, cap at 60s"

BAD (vague): "Covers best practices for code reviews"
GOOD (specific): "Code review tips: keep PRs under 400 lines, review for logic not style, use checklists, respond within 24 hours"

Emails to summarize:
{all_emails}

Provide individual summaries for all {len(emails)} emails:"""

    return prompt


def get_system_prompt() -> str:
    """Get the system prompt for the summarization task."""
    return """You are a professional email assistant specializing in creating clear, actionable summaries.

Your task is to summarize EACH email individually - one separate summary per email.

CRITICAL RULE: Your summaries must contain SPECIFIC information, not meta-descriptions.

NEVER use vague phrases like:
- "discusses..." / "covers..." / "talks about..."
- "presents a solution..." / "offers tips..."
- "mentions N things..." / "includes several..."
- "the email explains..." / "the author describes..."

INSTEAD, directly state the actual content:
- The specific techniques, steps, or methods mentioned
- The actual recommendations or action items
- The concrete details, names, numbers, and facts

EXAMPLES:

BAD: "The newsletter discusses productivity techniques and mentions 3 key strategies."
GOOD: "Boost productivity with time-blocking, the 2-minute rule for quick tasks, and weekly reviews every Friday."

BAD: "Presents a new approach to error handling in distributed systems."
GOOD: "Use circuit breakers with 5-failure threshold, implement retry with jittered backoff, and add correlation IDs to all requests."

BAD: "Covers updates to the Python ecosystem and new library releases."
GOOD: "Python 3.13 adds JIT compiler, Pydantic v2 is 5-17x faster, and uv replaces pip with 10-100x speed improvement."

Your summaries are:
- Specific and information-dense (state facts, not that facts exist)
- Focused on extracting actual content, not describing it
- Direct statements of information, never referencing "the email" or "the author"
- Professional in tone

Always use the exact output format requested with [SUMMARY N] tags.
Always output exactly the number of lines requested per email, no more and no less."""
