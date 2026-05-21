#!/usr/bin/env python3
"""Stub for the deprecated Telegram conversational entrypoint."""

import logging
import sys

_LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Explain that Telegram bot integrations were truncated from this variant."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    _LOGGER.error(
        "telegram_ai_bot is disabled — interactive Telegram commands (/report, /evaluate, journaling, …) "
        "were truncated from this codebase. Use orchestrator tooling directly or revert this stub to "
        "restore the historical bot loop."
    )
    return 3


if __name__ == "__main__":
    sys.exit(main())
