#!/usr/bin/env python3
"""
Telegram configuration and utility module

Telegram outbound messaging is disabled unless explicitly opted in via
``PRISM_ENABLE_TELEGRAM`` (truthy env) or an explicit CLI ``--telegram`` flag
wired through ``TelegramConfig(use_telegram=True|False|None)``.

Encapsulates telegram usage settings following SOLID principles
and minimizes redundant conditional processing.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_TRUTHY_ENV = frozenset({"1", "true", "yes", "on"})


def telegram_opt_in_requested() -> bool:
    """Return True when env PRISM_ENABLE_TELEGRAM is set to a truthy value."""

    return os.getenv("PRISM_ENABLE_TELEGRAM", "").strip().lower() in _TRUTHY_ENV


def resolve_telegram_flag(explicit: Optional[bool]) -> bool:
    """Combine CLI/env overrides into a single on/off toggle.

    - explicit True → enabled
    - explicit False → disabled
    - None → follow PRISM_ENABLE_TELEGRAM (default off when unset)

    Args:
        explicit: Caller intent (typically from argparse), or ``None`` for env-only resolution.
    """
    if explicit is True:
        return True
    if explicit is False:
        return False
    return telegram_opt_in_requested()


class TelegramConfig:
    """
    Telegram configuration management class

    Centralizes telegram usage and related settings management.
    Also manages multi-language channel IDs.
    """

    def __init__(self, use_telegram: Optional[bool] = None, channel_id: Optional[str] = None, bot_token: Optional[str] = None, broadcast_languages: list = None):
        """
        Initialize telegram configuration.

        Args:
            use_telegram: Explicit True/False, or ``None`` to follow PRISM_ENABLE_TELEGRAM (default off).
            channel_id: Telegram channel ID (auto-loaded from environment variables if not provided)
            bot_token: Telegram bot token (auto-loaded from environment variables if not provided)
            broadcast_languages: List of languages to broadcast in parallel (e.g., ['en', 'ja'])
        """
        self._use_telegram = resolve_telegram_flag(use_telegram)
        self._channel_id = channel_id
        self._bot_token = bot_token
        self._broadcast_languages = broadcast_languages or []
        self._broadcast_channel_ids = {}

        # Load .env file
        self._load_env()

        # Auto-load from environment variables (if not explicitly provided)
        if not self._channel_id:
            self._channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
        if not self._bot_token:
            self._bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

        # Load broadcast channel IDs per language
        self._load_broadcast_channels()
    
    def _load_env(self):
        """
        Load environment variables from .env file
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.debug(".env file loaded successfully")
        except ImportError:
            logger.warning("python-dotenv is not installed. Please set environment variables manually.")
        except Exception as e:
            logger.warning(f"Error loading .env file: {str(e)}")

    def _load_broadcast_channels(self):
        """
        Load telegram channel IDs for broadcast languages
        Loads from .env file in TELEGRAM_CHANNEL_ID_{LANG} format
        """
        for lang in self._broadcast_languages:
            lang_upper = lang.upper()
            env_key = f"TELEGRAM_CHANNEL_ID_{lang_upper}"
            channel_id = os.getenv(env_key)

            if channel_id:
                self._broadcast_channel_ids[lang] = channel_id
                logger.info(f"Broadcast channel loaded: {lang} -> {channel_id[:10]}...")
            else:
                logger.warning(f"Broadcast channel ID not configured for language: {lang} (env var: {env_key})")
    
    @property
    def use_telegram(self) -> bool:
        """Return whether telegram is enabled"""
        return self._use_telegram

    @property
    def channel_id(self) -> Optional[str]:
        """Return telegram channel ID"""
        return self._channel_id

    @property
    def bot_token(self) -> Optional[str]:
        """Return telegram bot token"""
        return self._bot_token

    @property
    def broadcast_languages(self) -> list:
        """Return list of broadcast languages"""
        return self._broadcast_languages

    def get_broadcast_channel_id(self, language: str) -> Optional[str]:
        """
        Return broadcast channel ID for a specific language

        Args:
            language: Language code (e.g., 'en', 'ja')

        Returns:
            Channel ID for the language, or None if not configured
        """
        return self._broadcast_channel_ids.get(language)
    
    def is_configured(self) -> bool:
        """
        Check if telegram is properly configured

        Returns:
            bool: True if telegram is enabled and all required settings are present
        """
        if not self._use_telegram:
            return True  # Consider configured when intentionally disabled

        return bool(self._channel_id and self._bot_token)

    def validate_or_raise(self) -> None:
        """
        Validate telegram configuration (only when enabled)

        Raises:
            ValueError: When telegram is enabled but required settings are missing
        """
        if not self._use_telegram:
            logger.info("Telegram is disabled.")
            return

        if not self._channel_id:
            raise ValueError(
                "Telegram channel ID is not configured. "
                "Set TELEGRAM_CHANNEL_ID or disable Telegram with PRISM_ENABLE_TELEGRAM unset / --no-telegram."
            )

        if not self._bot_token:
            raise ValueError(
                "Telegram bot token is not configured. "
                "Set TELEGRAM_BOT_TOKEN or disable Telegram with PRISM_ENABLE_TELEGRAM unset / --no-telegram."
            )

        logger.info(f"Telegram configuration validated (channel: {self._channel_id[:10]}...)")

    def log_status(self) -> None:
        """Log current telegram configuration status"""
        if self._use_telegram:
            logger.info("Telegram messaging enabled for this configuration")
            cid = self._channel_id[:10] if self._channel_id else "None"
            logger.info(f"   - Channel ID prefix: {cid}...")
            logger.info(f"   - Bot token: {'configured' if self._bot_token else 'missing'}")
        else:
            logger.info("Telegram messaging disabled for this configuration")
    
    def __repr__(self) -> str:
        return (
            f"TelegramConfig(use_telegram={self._use_telegram}, "
            f"channel_id={'***' if self._channel_id else None}, "
            f"bot_token={'***' if self._bot_token else None})"
        )


def is_openai_quota_error(error: Exception) -> bool:
    """
    Check if an exception is an OpenAI insufficient_quota error (429).

    Args:
        error: The caught exception

    Returns:
        True if this is an OpenAI quota exceeded error
    """
    error_str = str(error)
    return "insufficient_quota" in error_str or (
        "429" in error_str and "exceeded" in error_str.lower() and "quota" in error_str.lower()
    )


async def send_openai_quota_alert(telegram_config: "TelegramConfig", market: str = "US"):
    """
    Send a Telegram alert when OpenAI API quota is exceeded.

    Args:
        telegram_config: TelegramConfig instance
        market: Market identifier ("US")
    """
    if not telegram_config or not telegram_config.use_telegram:
        return

    try:
        from telegram import Bot
        from telegram.request import HTTPXRequest

        request = HTTPXRequest(connect_timeout=10.0, read_timeout=10.0)
        bot = Bot(token=telegram_config.bot_token, request=request)

        alert_message = (
            f"🚨 [{market}] OpenAI quota exhausted\n\n"
            f"The analysis pipeline stopped because the OpenAI API reported insufficient quota.\n\n"
            f"• Error: insufficient_quota (HTTP 429)\n"
            f"• Action: Top up credits or raise the org budget in OpenAI Platform → Billing\n"
            f"• https://platform.openai.com/settings/organization/billing"
        )

        await bot.send_message(
            chat_id=telegram_config.channel_id,
            text=alert_message
        )
        logger.info(f"[{market}] OpenAI quota alert sent to Telegram")
    except Exception as e:
        logger.error(f"[{market}] Failed to send OpenAI quota alert: {e}")
