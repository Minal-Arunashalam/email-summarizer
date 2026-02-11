def get_summarization_prompt(emails: list[dict], num_lines: int, sender_email: str) -> str:
    """
    Generate prompt for email summarization.

    Args:
        emails: List of email dictionaries
        num_lines: Number of lines for the summary
        sender_email: Email address of the sender

    Returns:
        Formatted prompt string
    """
    # Format emails for the prompt
    email_texts = []
    for i, email in enumerate(emails, 1):
        email_text = f"""
--- Email {i} ---
Subject: {email.get('subject', 'No Subject')}
Date: {email.get('date', 'Unknown')}
Content:
{email.get('body', email.get('snippet', 'No content'))}
"""
        email_texts.append(email_text)

    all_emails = "\n".join(email_texts)

    prompt = f"""You are an expert email summarizer. Summarize the following emails from {sender_email} in exactly {num_lines} lines.

Instructions:
- Create exactly {num_lines} concise summary lines
- Each line should capture a key point, action item, or important information
- Focus on actionable items, deadlines, decisions, and key updates
- Use bullet points (•) at the start of each line
- Be specific and include relevant details like dates, names, or numbers when important
- Prioritize the most recent and important information
- If there are recurring themes, consolidate them

Emails to summarize:
{all_emails}

Provide your {num_lines}-line summary:"""

    return prompt


def get_system_prompt() -> str:
    """Get the system prompt for the summarization task."""
    return """You are a professional email assistant specializing in creating clear, actionable summaries.
Your summaries are:
- Concise and to the point
- Focused on key information and action items
- Well-organized and easy to scan
- Professional in tone

Always output exactly the number of lines requested, no more and no less."""
