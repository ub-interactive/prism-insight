"""Shared disclaimer/warning text helpers.

Extracted so the trailing-disclaimer regex can be unit-tested without pulling legacy UI code paths.
"""

from __future__ import annotations

import re
from typing import Optional

# Trailing disclaimer-like lines the LLM tends to append on its own (gh #263).
# Matches a final block starting with ⚠️/⚡/❗ and investment-ish English warnings.
# Leading segment allows one or more blank lines between body text and first emoji line.
_TRAILING_DISCLAIMER_RE = re.compile(
    r"(?:(?:\n[ \t]*)+[⚠⚡❗‼️]+[^\n]*?"
    r"(?:investment[^\n]*?(?:reference|decision|responsibility|advice|risk|caution|disclaim)"
    r"|investing[^\n]*?(?:risk|responsibility|decision|caution|disclaim)"
    r"|not\s+(?:a\s+)?(?:financial|investment)\s+advice"
    r"|for\s+(?:informational|educational)\s+purposes"
    r"|[^\n]*\beducational only\b[^\n]*)"
    r"[^\n]*)+\s*\Z",
    re.IGNORECASE | re.MULTILINE,
)


def strip_trailing_disclaimer(text: Optional[str]) -> Optional[str]:
    """Remove any disclaimer-like trailing block emitted by the LLM (gh #263).

    Used before appending a canonical disclaimer in handlers so users do not see
    two near-identical investment warnings.

    Returns ``text`` unchanged when it is empty or ``None``.
    """
    if not text:
        return text
    return _TRAILING_DISCLAIMER_RE.sub("", text).rstrip()
