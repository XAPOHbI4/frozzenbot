"""Telegram WebApp utilities."""

import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from urllib.parse import unquote, parse_qsl

from app.config import settings


def parse_telegram_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    """
    Parse and validate Telegram WebApp initData.

    Args:
        init_data: Raw initData string from Telegram WebApp

    Returns:
        Dict with parsed user data if valid, None otherwise
    """
    try:
        # Parse the query string
        data = dict(parse_qsl(init_data))

        # Get the hash from the data
        received_hash = data.pop('hash', None)
        if not received_hash:
            return None

        # Create data string for verification
        data_check_arr = []
        for key, value in sorted(data.items()):
            data_check_arr.append(f"{key}={value}")
        data_check_string = '\n'.join(data_check_arr)

        # Verify the hash
        if not verify_telegram_data(data_check_string, received_hash):
            return None

        # Parse user data
        user_data = data.get('user')
        if not user_data:
            return None

        # Decode user JSON
        user_info = json.loads(unquote(user_data))

        # Validate required fields
        if not all(key in user_info for key in ['id', 'first_name']):
            return None

        return user_info

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        return None


def verify_telegram_data(data_check_string: str, received_hash: str) -> bool:
    """
    Verify Telegram WebApp data hash.

    Args:
        data_check_string: Data string to verify
        received_hash: Hash received from Telegram

    Returns:
        True if hash is valid
    """
    try:
        bot_token = settings.bot_token
        if not bot_token:
            return False

        # Create secret key
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        # Calculate expected hash
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_hash, received_hash)

    except Exception:
        return False


def create_telegram_login_widget_hash(auth_data: Dict[str, Any]) -> str:
    """
    Create hash for Telegram Login Widget data.

    Args:
        auth_data: Telegram login widget data

    Returns:
        Hash string
    """
    bot_token = settings.bot_token
    if not bot_token:
        return ""

    # Remove hash from auth_data if present
    data = {k: v for k, v in auth_data.items() if k != 'hash'}

    # Create data string
    data_check_arr = []
    for key, value in sorted(data.items()):
        data_check_arr.append(f"{key}={value}")
    data_check_string = '\n'.join(data_check_arr)

    # Create secret key
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # Calculate hash
    return hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_telegram_login_widget(auth_data: Dict[str, Any]) -> bool:
    """
    Verify Telegram Login Widget data.

    Args:
        auth_data: Data from Telegram Login Widget

    Returns:
        True if data is valid
    """
    received_hash = auth_data.get('hash')
    if not received_hash:
        return False

    expected_hash = create_telegram_login_widget_hash(auth_data)
    return hmac.compare_digest(expected_hash, received_hash)


def format_telegram_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format Telegram user data for internal use.

    Args:
        user_data: Raw Telegram user data

    Returns:
        Formatted user data
    """
    return {
        'id': user_data.get('id'),
        'first_name': user_data.get('first_name', '').strip(),
        'last_name': user_data.get('last_name', '').strip() if user_data.get('last_name') else None,
        'username': user_data.get('username', '').strip() if user_data.get('username') else None,
        'language_code': user_data.get('language_code'),
        'is_premium': user_data.get('is_premium', False),
        'photo_url': user_data.get('photo_url')
    }


def sanitize_telegram_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize Telegram data for safe storage.

    Args:
        data: Raw Telegram data

    Returns:
        Sanitized data
    """
    from app.utils.security import security_utils

    sanitized = {}

    # Sanitize string fields
    string_fields = ['first_name', 'last_name', 'username']
    for field in string_fields:
        if field in data and data[field]:
            sanitized[field] = security_utils.sanitize_input(str(data[field]), 255)

    # Copy safe fields as-is
    safe_fields = ['id', 'is_premium', 'language_code']
    for field in safe_fields:
        if field in data:
            sanitized[field] = data[field]

    # Validate photo URL if present
    if 'photo_url' in data and data['photo_url']:
        photo_url = str(data['photo_url'])
        # Basic URL validation
        if photo_url.startswith(('http://', 'https://')) and len(photo_url) < 2048:
            sanitized['photo_url'] = photo_url

    return sanitized