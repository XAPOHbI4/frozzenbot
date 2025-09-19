"""Payment utilities and helper functions."""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

from app.config import settings

logger = logging.getLogger(__name__)


class PaymentUtils:
    """Utility class for payment operations."""

    @staticmethod
    def verify_webhook_signature(
        payload: str,
        signature: str,
        secret: Optional[str] = None
    ) -> bool:
        """
        Verify webhook signature for payment providers.

        Args:
            payload: Request payload as string
            signature: Signature from webhook headers
            secret: Secret key for verification (defaults to bot token)

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not secret:
                secret = settings.bot_token

            if not signature or not payload:
                logger.warning("Missing signature or payload for webhook verification")
                return False

            # Remove signature prefix if present (e.g., "sha256=")
            if "=" in signature:
                signature = signature.split("=", 1)[1]

            # Calculate expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Compare signatures securely
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    @staticmethod
    def validate_payment_amount(
        amount: float,
        min_amount: float = 1.0,
        max_amount: float = 1000000.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate payment amount.

        Args:
            amount: Payment amount to validate
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if amount <= 0:
                return False, "Сумма платежа должна быть больше нуля"

            if amount < min_amount:
                return False, f"Минимальная сумма платежа: {min_amount}₽"

            if amount > max_amount:
                return False, f"Максимальная сумма платежа: {max_amount}₽"

            # Check minimum order amount from settings
            if amount < settings.min_order_amount:
                return False, f"Минимальная сумма заказа: {settings.min_order_amount}₽"

            return True, None

        except Exception as e:
            logger.error(f"Error validating payment amount {amount}: {e}")
            return False, "Ошибка валидации суммы платежа"

    @staticmethod
    def normalize_amount(amount: float) -> float:
        """
        Normalize payment amount to 2 decimal places.

        Args:
            amount: Amount to normalize

        Returns:
            Normalized amount
        """
        try:
            return float(Decimal(str(amount)).quantize(Decimal('0.01')))
        except Exception:
            return round(amount, 2)

    @staticmethod
    def kopecks_to_rubles(kopecks: int) -> float:
        """
        Convert kopecks to rubles.

        Args:
            kopecks: Amount in kopecks

        Returns:
            Amount in rubles
        """
        return kopecks / 100.0

    @staticmethod
    def rubles_to_kopecks(rubles: float) -> int:
        """
        Convert rubles to kopecks.

        Args:
            rubles: Amount in rubles

        Returns:
            Amount in kopecks
        """
        return int(rubles * 100)

    @staticmethod
    def format_amount(amount: float, currency: str = "₽") -> str:
        """
        Format payment amount for display.

        Args:
            amount: Amount to format
            currency: Currency symbol

        Returns:
            Formatted amount string
        """
        try:
            normalized_amount = PaymentUtils.normalize_amount(amount)
            if normalized_amount.is_integer():
                return f"{int(normalized_amount)}{currency}"
            else:
                return f"{normalized_amount:.2f}{currency}"
        except Exception:
            return f"{amount}{currency}"

    @staticmethod
    def generate_payment_description(
        order_id: int,
        items_count: int,
        customer_name: Optional[str] = None
    ) -> str:
        """
        Generate payment description for invoices.

        Args:
            order_id: Order ID
            items_count: Number of items in order
            customer_name: Customer name (optional)

        Returns:
            Payment description string
        """
        description = f"Заказ #{order_id}"

        if items_count > 0:
            if items_count == 1:
                description += f" (1 товар)"
            elif items_count < 5:
                description += f" ({items_count} товара)"
            else:
                description += f" ({items_count} товаров)"

        if customer_name:
            description += f" - {customer_name}"

        return description

    @staticmethod
    def extract_error_message(provider_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract human-readable error message from provider data.

        Args:
            provider_data: Provider-specific error data

        Returns:
            Error message or None
        """
        try:
            # Common error field names
            error_fields = [
                'error_message', 'error', 'message', 'description',
                'failure_reason', 'decline_reason', 'error_description'
            ]

            for field in error_fields:
                if field in provider_data and provider_data[field]:
                    return str(provider_data[field])

            # Try nested error objects
            if 'error' in provider_data and isinstance(provider_data['error'], dict):
                error_obj = provider_data['error']
                for field in error_fields:
                    if field in error_obj and error_obj[field]:
                        return str(error_obj[field])

            return None

        except Exception as e:
            logger.error(f"Error extracting error message from provider data: {e}")
            return None

    @staticmethod
    def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata by removing sensitive information.

        Args:
            metadata: Original metadata

        Returns:
            Sanitized metadata
        """
        try:
            if not isinstance(metadata, dict):
                return {}

            # List of sensitive keys to remove
            sensitive_keys = [
                'password', 'token', 'secret', 'key', 'api_key',
                'authorization', 'auth', 'card_number', 'cvv',
                'pin', 'private', 'credential'
            ]

            sanitized = {}
            for key, value in metadata.items():
                # Skip sensitive keys (case-insensitive)
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    continue

                # Recursively sanitize nested dicts
                if isinstance(value, dict):
                    sanitized[key] = PaymentUtils.sanitize_metadata(value)
                else:
                    sanitized[key] = value

            return sanitized

        except Exception as e:
            logger.error(f"Error sanitizing metadata: {e}")
            return {}

    @staticmethod
    def is_test_payment(
        charge_id: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if payment is a test payment.

        Args:
            charge_id: Payment charge ID
            provider_data: Provider-specific data

        Returns:
            True if payment is a test payment
        """
        try:
            # Check charge ID for test indicators
            if charge_id:
                test_indicators = ['test', 'sandbox', 'demo']
                if any(indicator in charge_id.lower() for indicator in test_indicators):
                    return True

            # Check provider data for test mode
            if provider_data:
                if provider_data.get('test_mode') or provider_data.get('is_test'):
                    return True

                # Check if using test provider token
                if settings.payment_provider_token and "TEST" in settings.payment_provider_token:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking if payment is test: {e}")
            return False

    @staticmethod
    def log_payment_event(
        event_type: str,
        payment_id: Optional[int] = None,
        order_id: Optional[int] = None,
        amount: Optional[float] = None,
        status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log payment events for debugging and monitoring.

        Args:
            event_type: Type of payment event
            payment_id: Payment ID
            order_id: Order ID
            amount: Payment amount
            status: Payment status
            details: Additional event details
        """
        try:
            log_data = {
                "event_type": event_type,
                "timestamp": json.dumps({"timestamp": "now"}, default=str),
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "status": status
            }

            if details:
                log_data["details"] = PaymentUtils.sanitize_metadata(details)

            logger.info(f"Payment event: {json.dumps(log_data, ensure_ascii=False)}")

        except Exception as e:
            logger.error(f"Error logging payment event: {e}")