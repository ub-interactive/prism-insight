"""OpenAI quota / billing error helpers (no Telegram side effects)."""


def is_openai_quota_error(error: Exception) -> bool:
    """Return True when ``error`` looks like OpenAI insufficient_quota / 429 exhaustion."""

    error_str = str(error)
    return "insufficient_quota" in error_str or (
        "429" in error_str and "exceeded" in error_str.lower() and "quota" in error_str.lower()
    )
