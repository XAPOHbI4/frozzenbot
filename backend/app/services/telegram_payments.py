"""Telegram Payments service for handling payment operations."""

import logging
from typing import Dict, Any, Optional, List
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot

from app.config import settings
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus

logger = logging.getLogger(__name__)


class TelegramPaymentsService:
    """Service for handling Telegram Payments."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.provider_token = settings.payment_provider_token

    async def create_invoice(
        self,
        chat_id: int,
        order: Order,
        payment: Payment
    ) -> bool:
        """
        Create and send payment invoice to user.

        Args:
            chat_id: Telegram chat ID
            order: Order to pay for
            payment: Payment instance

        Returns:
            True if invoice sent successfully, False otherwise
        """
        try:
            # Create price breakdown
            prices = []

            # Add each order item as separate price
            for item in order.items:
                price_amount = int(item.total_price * 100)  # Convert to kopecks
                prices.append(LabeledPrice(
                    label=f"{item.product.name} x{item.quantity}",
                    amount=price_amount
                ))

            # Invoice details
            title = "Оплата заказа в FrozenBot"
            description = f"Заказ #{order.id}\n"
            description += f"Товаров: {len(order.items)}\n"
            description += f"Сумма: {order.formatted_total}"

            payload = f"order_{order.id}_payment_{payment.id}"
            currency = "RUB"

            # Additional invoice parameters
            start_parameter = f"pay_order_{order.id}"

            # Create invoice keyboard
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="💳 Оплатить",
                    pay=True
                )],
                [InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"cancel_payment_{payment.id}"
                )]
            ])

            # Send invoice
            await self.bot.send_invoice(
                chat_id=chat_id,
                title=title,
                description=description,
                payload=payload,
                provider_token=self.provider_token,
                currency=currency,
                prices=prices,
                start_parameter=start_parameter,
                reply_markup=keyboard
            )

            logger.info(f"Invoice created for order {order.id}, payment {payment.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create invoice for order {order.id}: {e}")
            return False

    async def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Answer pre-checkout query.

        Args:
            pre_checkout_query_id: Pre-checkout query ID
            ok: Whether to approve the payment
            error_message: Error message if payment is rejected

        Returns:
            True if answered successfully, False otherwise
        """
        try:
            await self.bot.answer_pre_checkout_query(
                pre_checkout_query_id=pre_checkout_query_id,
                ok=ok,
                error_message=error_message
            )
            logger.info(f"Pre-checkout query {pre_checkout_query_id} answered: ok={ok}")
            return True

        except Exception as e:
            logger.error(f"Failed to answer pre-checkout query {pre_checkout_query_id}: {e}")
            return False

    async def refund_payment(
        self,
        telegram_payment_charge_id: str,
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment (Note: Telegram Payments doesn't support refunds directly).
        This is a placeholder for future implementation with payment providers.

        Args:
            telegram_payment_charge_id: Telegram payment charge ID
            amount: Amount to refund in kopecks (None for full refund)

        Returns:
            Dictionary with refund result
        """
        try:
            # Note: Telegram Payments API doesn't support direct refunds
            # This would require integration with the actual payment provider
            logger.warning(
                f"Refund requested for charge {telegram_payment_charge_id}, "
                f"but Telegram Payments doesn't support direct refunds. "
                f"Manual refund required through payment provider."
            )

            return {
                "success": False,
                "error": "Manual refund required through payment provider",
                "charge_id": telegram_payment_charge_id
            }

        except Exception as e:
            logger.error(f"Refund attempt failed for charge {telegram_payment_charge_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "charge_id": telegram_payment_charge_id
            }

    @staticmethod
    def extract_payment_data_from_payload(payload: str) -> Optional[Dict[str, int]]:
        """
        Extract order and payment IDs from invoice payload.

        Args:
            payload: Invoice payload string

        Returns:
            Dictionary with order_id and payment_id, or None if invalid
        """
        try:
            # Expected format: "order_{order_id}_payment_{payment_id}"
            parts = payload.split("_")
            if len(parts) == 4 and parts[0] == "order" and parts[2] == "payment":
                return {
                    "order_id": int(parts[1]),
                    "payment_id": int(parts[3])
                }
        except (ValueError, IndexError):
            pass

        logger.warning(f"Invalid payment payload format: {payload}")
        return None

    @staticmethod
    def format_payment_success_message(order: Order, payment: Payment) -> str:
        """
        Format payment success message for user.

        Args:
            order: Paid order
            payment: Payment details

        Returns:
            Formatted success message
        """
        message = "✅ <b>Платёж успешно обработан!</b>\n\n"
        message += f"💰 <b>Заказ:</b> #{order.id}\n"
        message += f"💳 <b>Сумма:</b> {payment.formatted_amount}\n"
        message += f"📅 <b>Дата:</b> {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

        if payment.telegram_payment_charge_id:
            message += f"🔗 <b>ID транзакции:</b> <code>{payment.telegram_payment_charge_id}</code>\n\n"

        message += "📦 <b>Ваш заказ принят в обработку!</b>\n"
        message += "🕐 Мы уведомим вас о готовности заказа."

        return message

    @staticmethod
    def format_payment_failed_message(order: Order, error_message: Optional[str] = None) -> str:
        """
        Format payment failed message for user.

        Args:
            order: Failed order
            error_message: Optional error details

        Returns:
            Formatted failure message
        """
        message = "❌ <b>Ошибка при обработке платежа</b>\n\n"
        message += f"💰 <b>Заказ:</b> #{order.id}\n"
        message += f"💳 <b>Сумма:</b> {order.formatted_total}\n\n"

        if error_message:
            message += f"❗ <b>Причина:</b> {error_message}\n\n"

        message += "🔄 <b>Попробуйте ещё раз или обратитесь в поддержку.</b>"

        return message