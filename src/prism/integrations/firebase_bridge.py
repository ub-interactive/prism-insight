"""
Firebase Bridge for PRISM-Mobile

Saves message metadata to Firestore and sends FCM push notifications when
configured. Failures are logged and ignored so core batch jobs keep running.

FCM payloads and mirrored Firestore documents use ``report_link`` / ``pdf_report_link``.

IMPORTANT: This module is opt-in and disabled by default.
Set FIREBASE_BRIDGE_ENABLED=true in .env to activate.
This is a PRISM-Mobile specific feature, not required for core prism-insight usage.
"""

import json
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy initialization - only import firebase when actually needed
_db = None
_messaging = None
_initialized = False
_checked_enabled = False
_enabled = False


def _is_enabled() -> bool:
    """Check if Firebase Bridge is enabled via environment variable."""
    global _checked_enabled, _enabled
    if _checked_enabled:
        return _enabled
    _checked_enabled = True
    _enabled = os.environ.get('FIREBASE_BRIDGE_ENABLED', '').lower() in ('true', '1', 'yes')
    if not _enabled:
        logger.debug("Firebase Bridge disabled (set FIREBASE_BRIDGE_ENABLED=true to enable)")
    return _enabled


def _initialize():
    """Lazy initialize Firebase Admin SDK."""
    global _db, _messaging, _initialized
    if _initialized:
        return _initialized

    if not _is_enabled():
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, messaging

        # Check if already initialized
        try:
            app = firebase_admin.get_app()
        except ValueError:
            # Not yet initialized
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if not cred_path:
                logger.warning("Firebase not configured: GOOGLE_APPLICATION_CREDENTIALS not set")
                _initialized = False
                return False

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        _db = firestore.client()
        _messaging = messaging
        _initialized = True
        logger.info("Firebase Bridge initialized successfully")
        return True
    except ImportError:
        logger.warning("firebase-admin not installed. Firebase Bridge disabled.")
        _initialized = False
        return False
    except Exception as e:
        logger.warning(f"Firebase Bridge initialization failed: {e}")
        _initialized = False
        return False


def _notification_lang() -> str:
    """Prefer explicit FCM routing language; defaults to ``en`` for the US workflow."""
    return (os.environ.get("PRISM_FCM_DEFAULT_LANG") or "en").lower()


def detect_market(message: str) -> str:
    """US-only runtime market detection."""
    _ = message
    return "us"


def detect_type(message: str) -> str:
    """Detect message type from content.

    Priority order: portfolio summary > embedded PDF cues > prism/trigger wording >
    generic analysis language > standalone ``report`` phrasing > default trigger.

    Directional verbs like ``buy`` appear in both scans and chatter, so prism/trigger
    keywords are evaluated **before** the broad ``analysis`` bucket whenever possible.
    """
    msg_lower = message.lower()

    if any(kw in msg_lower for kw in [
        'portfolio summary', 'portfolio status', 'portfolio report', 'holdings',
        'positions overview', 'account snapshot',
    ]):
        return 'portfolio'

    if any(kw in msg_lower for kw in ['.pdf', 'pdf report']):
        return 'pdf'

    if any(kw in msg_lower for kw in [
        'trigger', 'signal alert', 'prism signal', 'morning prism', 'afternoon prism',
        'scanner hit', 'surge detection', 'volume surge alert',
    ]):
        return 'trigger'

    if any(kw in msg_lower for kw in [
        'analysis', 'summary', 'outlook', 'review', 'market note',
        'buy', 'sell', 'hold', 'long thesis', 'short thesis',
    ]):
        return 'analysis'

    if any(kw in msg_lower for kw in ['research note', 'report']):
        return 'pdf'

    return 'trigger'


def _clean_filename(text: str) -> str:
    """Clean a raw filename into a human-readable title.

    'pdfreports/AAPL_Apple Inc_20260210_afternoon.pdf'
    → 'AAPL Apple Inc 20260210 afternoon'
    """
    # Extract filename from path
    name = text.split('/')[-1]
    # Remove file extension
    name = re.sub(r'\.\w{2,4}$', '', name)
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    return name.strip()


def _looks_like_filepath(text: str) -> bool:
    """Check if text looks like a file path or raw filename."""
    return bool(
        '/' in text
        or text.endswith('.pdf')
        or re.match(r'^[\w._-]+\.\w{2,4}$', text)
    )


def extract_title(message: str, max_length: int = 80) -> str:
    """Extract title from message - first meaningful line."""
    lines = message.strip().split('\n')
    for line in lines:
        cleaned = line.strip()
        # Skip empty lines, emoji-only lines, separator lines
        if not cleaned:
            continue
        if cleaned.startswith('---') or cleaned.startswith('==='):
            continue
        if len(cleaned) < 3:
            continue
        # Check filepath BEFORE removing markdown (preserves underscores in filenames).
        # e.g. "AAPL_Apple_20260219.pdf" must not have _ stripped before filepath check.
        if _looks_like_filepath(cleaned):
            return _clean_filename(cleaned)[:max_length]
        # Remove markdown formatting
        cleaned = re.sub(r'[*_`#]', '', cleaned).strip()
        if cleaned:
            return cleaned[:max_length]
    return message[:max_length].strip()


def extract_preview(message: str, max_length: int = 100) -> str:
    """Extract preview text from message."""
    # Remove markdown formatting
    text = re.sub(r'[*_`#]', '', message)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Don't expose raw file paths as preview
    if _looks_like_filepath(text.split(' ')[0]):
        text = _clean_filename(text.split(' ')[0])
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def extract_stock_info(message: str) -> tuple:
    """Extract stock code and name from message.

    Returns:
        tuple: (stock_code, stock_name) or (None, None)
    """
    us_match = re.search(r"\b([A-Z]{1,5})\b\s*[\(\[]?\$?", message)
    stock_code = us_match.group(1) if us_match else None
    return stock_code, None


async def notify(
    message: str,
    market: Optional[str] = None,
    msg_type: Optional[str] = None,
    channel_id: Optional[str] = None,
    has_pdf: bool = False,
    report_link: str = "",
    pdf_report_link: Optional[str] = None,
):
    """
    Save message metadata to Firestore and send FCM push.

    This function NEVER raises exceptions—for errors are logged and ignored.

    Args:
        message: Human-readable plaintext that originated the notification
        market: Market identifier (`us` only). Auto-detected if None.
        msg_type: Message type. Auto-detected if None.
        channel_id: Routing hint stored when provided
        has_pdf: Whether this message references an associated PDF asset
        report_link: Optional URL or deep link to the originating asset (often empty).
        pdf_report_link: Optional direct link to PDF when ``has_pdf`` is true (often empty).
    """
    try:
        if not _initialize():
            return

        # Auto-detect if not provided
        if not market:
            market = detect_market(message)
        if not msg_type:
            msg_type = detect_type(message)

        title = extract_title(message)
        preview = extract_preview(message)
        stock_code, stock_name = extract_stock_info(message)

        lang = _notification_lang()
        link = report_link or ""
        pdf_link = pdf_report_link or ""

        # Save to Firestore
        from google.cloud.firestore import SERVER_TIMESTAMP

        doc_data = {
            'type': msg_type,
            'market': market,
            'lang': lang,
            'title': title,
            'preview': preview,
            'report_link': link,
            'channel_id': channel_id,
            'stock_code': stock_code,
            'stock_name': stock_name,
            'has_pdf': has_pdf,
            'pdf_report_link': pdf_link,
            'created_at': SERVER_TIMESTAMP,
        }

        _db.collection('messages').add(doc_data)
        logger.info(f"Firebase: Saved {msg_type}/{market} message to Firestore")

        # Send FCM push notification
        await _send_push(title, preview, msg_type, market, lang, link, pdf_link)

    except Exception as e:
        logger.warning(f"Firebase Bridge notify failed (ignored): {e}")


async def _send_push(
    title: str,
    body: str,
    msg_type: str,
    market: str,
    lang: str = "ko",
    report_link: str = "",
    pdf_report_link: str = "",
):
    """Send FCM push notification to subscribed devices."""
    try:
        if not _messaging:
            return

        # Query devices matching preferences, tracking doc refs for cleanup
        devices_ref = _db.collection('devices')
        docs = devices_ref.stream()

        token_to_ref: dict = {}  # token -> Firestore doc ref (for invalid token cleanup)
        for doc in docs:
            device = doc.to_dict()
            prefs = device.get('preferences', {})

            # Check market preference
            pref_markets = prefs.get('markets', ['us'])
            if market not in pref_markets:
                continue

            # Check type preference
            pref_types = prefs.get('types', ['trigger', 'analysis', 'portfolio', 'pdf'])
            if msg_type not in pref_types:
                continue

            # Check lang preference: only filter if device has explicit lang set
            pref_lang = prefs.get('lang')  # None if not set → receives all notifications
            if lang and pref_lang and pref_lang != lang:
                continue

            token = device.get('token')
            if token:
                token_to_ref[token] = doc.reference

        if not token_to_ref:
            logger.info("Firebase: No matching devices for push notification")
            return

        tokens = list(token_to_ref.keys())

        # FCM error codes that indicate a permanently invalid token
        _INVALID_TOKEN_CODES = {
            'registration-token-not-registered',  # app uninstalled / token revoked
            'invalid-registration-token',          # malformed token
            'NOT_FOUND',                           # FCM v1 API: token not found / app uninstalled
        }

        # Send in batches of 500 (FCM limit)
        for i in range(0, len(tokens), 500):
            batch_tokens = tokens[i:i + 500]
            message = _messaging.MulticastMessage(
                notification=_messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    'type': msg_type,
                    'market': market,
                    'lang': lang,
                    'report_link': report_link,
                    'pdf_report_link': pdf_report_link,
                },
                tokens=batch_tokens,
            )

            response = _messaging.send_each_for_multicast(message)
            logger.info(
                f"Firebase: FCM sent to {response.success_count}/{len(batch_tokens)} devices"
            )

            # Clean up permanently invalid tokens from Firestore
            cleaned = 0
            for idx, resp in enumerate(response.responses):
                if resp.success:
                    continue
                token = batch_tokens[idx]
                error_code = getattr(resp.exception, 'code', '') or ''
                # Strip 'messaging/' prefix if present
                short_code = error_code.replace('messaging/', '')
                if short_code in _INVALID_TOKEN_CODES:
                    try:
                        token_to_ref[token].delete()
                        cleaned += 1
                        logger.info(f"Firebase: Removed invalid token [{short_code}]")
                    except Exception as del_err:
                        logger.warning(f"Firebase: Failed to delete invalid token: {del_err}")
                else:
                    logger.warning(f"Firebase: FCM send failed for token (kept): {short_code or error_code}")

            if cleaned:
                logger.info(f"Firebase: Cleaned up {cleaned} invalid device token(s)")

    except Exception as e:
        logger.warning(f"Firebase: FCM push failed (ignored): {e}")
