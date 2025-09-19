"""Payment handlers for Telegram bot."""

import logging
from typing import Dict, Any
from aiogram import Router, F
from aiogram.types import (
    PreCheckoutQuery, SuccessfulPayment, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, Message
)
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.payment import PaymentService
from app.services.telegram_payments import TelegramPaymentsService
from app.bot.bot import bot

logger = logging.getLogger(__name__)
router = Router()


@router.pre_checkout_query()
async def handle_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """
    Handle pre-checkout query - validate payment before processing.

    This handler is called right before the payment is processed.
    It's the last chance to validate the payment and reject it if needed.
    """
    try:
        logger.info(f"Pre-checkout query received: {pre_checkout_query.id}")

        # Extract payment data from invoice payload
        payment_data = TelegramPaymentsService.extract_payment_data_from_payload(
            pre_checkout_query.invoice_payload
        )

        if not payment_data:
            logger.error(f"Invalid payload in pre-checkout query: {pre_checkout_query.invoice_payload}")
            await TelegramPaymentsService(bot).answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="Неверные данные платежа"
            )
            return

        # Get database session
        async for db in get_async_session():
            try:
                payment_service = PaymentService(db)

                # Get payment by ID
                payment = await payment_service.get_payment_by_id(payment_data["payment_id"])
                if not payment:
                    logger.error(f"Payment {payment_data['payment_id']} not found")
                    await TelegramPaymentsService(bot).answer_pre_checkout_query(
                        pre_checkout_query.id,
                        ok=False,
                        error_message="Платёж не найден"
                    )
                    return

                # Verify payment is still pending
                if payment.status != PaymentStatus.PENDING:
                    logger.warning(f"Payment {payment.id} is not pending: {payment.status}")
                    await TelegramPaymentsService(bot).answer_pre_checkout_query(
                        pre_checkout_query.id,
                        ok=False,
                        error_message="Платёж уже обработан"
                    )
                    return

                # Verify order exists and is valid
                if not payment.order:
                    logger.error(f"Order {payment.order_id} not found for payment {payment.id}")
                    await TelegramPaymentsService(bot).answer_pre_checkout_query(
                        pre_checkout_query.id,
                        ok=False,
                        error_message="Заказ не найден"
                    )
                    return

                # Verify amount matches
                total_amount_kopecks = int(payment.amount * 100)
                if pre_checkout_query.total_amount != total_amount_kopecks:
                    logger.error(
                        f"Amount mismatch for payment {payment.id}: "
                        f"expected {total_amount_kopecks}, got {pre_checkout_query.total_amount}"
                    )
                    await TelegramPaymentsService(bot).answer_pre_checkout_query(
                        pre_checkout_query.id,
                        ok=False,
                        error_message="Неверная сумма платежа"
                    )
                    return

                # All checks passed - approve payment
                await TelegramPaymentsService(bot).answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=True
                )

                logger.info(f"Pre-checkout query approved for payment {payment.id}")
                break

            except Exception as e:
                logger.error(f"Database error in pre-checkout handler: {e}")
                await TelegramPaymentsService(bot).answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=False,
                    error_message="Внутренняя ошибка сервера"
                )
                return

    except Exception as e:
        logger.error(f"Error in pre-checkout query handler: {e}")
        await TelegramPaymentsService(bot).answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Ошибка обработки платежа"
        )


@router.message(F.content_type.in_({'successful_payment'}))
async def handle_successful_payment(message: Message):
    """
    Handle successful payment notification from Telegram.

    This handler is called when a payment is successfully processed
    and updates the payment and order status accordingly.
    """
    try:
        payment_info = message.successful_payment
        logger.info(f"Successful payment received: {payment_info.telegram_payment_charge_id}")

        # Extract payment data from invoice payload
        payment_data = TelegramPaymentsService.extract_payment_data_from_payload(
            payment_info.invoice_payload
        )

        if not payment_data:
            logger.error(f"Invalid payload in successful payment: {payment_info.invoice_payload}")
            await message.answer(
                "❌ Ошибка обработки платежа. Обратитесь в поддержку.",
                parse_mode="HTML"
            )
            return

        # Get database session
        async for db in get_async_session():
            try:
                payment_service = PaymentService(db)

                # Process successful payment
                success = await payment_service.process_successful_payment(
                    order_id=payment_data["order_id"],
                    payment_id=payment_data["payment_id"],
                    telegram_payment_charge_id=payment_info.telegram_payment_charge_id,
                    provider_payment_charge_id=payment_info.provider_payment_charge_id,
                    provider_data={
                        "currency": payment_info.currency,
                        "total_amount": payment_info.total_amount,
                        "order_info": payment_info.order_info.__dict__ if payment_info.order_info else None,
                        "shipping_option_id": payment_info.shipping_option_id
                    }
                )

                if success:
                    # Get updated payment details for response
                    payment = await payment_service.get_payment_by_id(payment_data["payment_id"])
                    if payment and payment.order:
                        # Send success message
                        success_message = TelegramPaymentsService.format_payment_success_message(
                            payment.order, payment
                        )
                        await message.answer(success_message, parse_mode="HTML")
                    else:
                        await message.answer(
                            "✅ Платёж успешно обработан! Спасибо за покупку!",
                            parse_mode="HTML"
                        )
                else:
                    await message.answer(
                        "❌ Ошибка при обработке платежа. Обратитесь в поддержку.",
                        parse_mode="HTML"
                    )

                break

            except Exception as e:
                logger.error(f"Database error in successful payment handler: {e}")
                await message.answer(
                    "❌ Ошибка при обработке платежа. Обратитесь в поддержку.",
                    parse_mode="HTML"
                )
                return

    except Exception as e:
        logger.error(f"Error in successful payment handler: {e}")
        await message.answer(
            "❌ Ошибка при обработке платежа. Обратитесь в поддержку.",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("cancel_payment_"))
async def handle_cancel_payment(callback_query: CallbackQuery):
    """Handle payment cancellation."""
    try:
        # Extract payment ID from callback data
        payment_id = int(callback_query.data.split("_")[-1])

        async for db in get_async_session():
            try:
                payment_service = PaymentService(db)

                # Get payment
                payment = await payment_service.get_payment_by_id(payment_id)
                if not payment:
                    await callback_query.answer("Платёж не найден", show_alert=True)
                    return

                if payment.status != PaymentStatus.PENDING:
                    await callback_query.answer("Платёж уже обработан", show_alert=True)
                    return

                # Mark payment as failed (cancelled by user)
                await payment_service.process_failed_payment(
                    payment_id=payment_id,
                    error_message="Отменено пользователем"
                )

                # Send cancellation message
                if payment.order:
                    cancel_message = (
                        f"❌ <b>Платёж отменён</b>\n\n"
                        f"📦 <b>Заказ:</b> #{payment.order.id}\n"
                        f"💳 <b>Сумма:</b> {payment.formatted_amount}\n\n"
                        f"Вы можете оформить заказ заново в любое время."
                    )
                else:
                    cancel_message = "❌ Платёж отменён"

                await callback_query.message.edit_text(
                    cancel_message,
                    parse_mode="HTML"
                )
                await callback_query.answer("Платёж отменён")

                break

            except Exception as e:
                logger.error(f"Database error in cancel payment handler: {e}")
                await callback_query.answer("Ошибка отмены платежа", show_alert=True)
                return

    except Exception as e:
        logger.error(f"Error in cancel payment handler: {e}")
        await callback_query.answer("Ошибка отмены платежа", show_alert=True)


@router.message(Command("pay"))
async def handle_pay_command(message: Message):
    """
    Handle /pay command - create payment for the latest pending order.

    This command allows users to pay for their latest pending order
    if it doesn't have a payment yet.
    """
    try:
        user_id = message.from_user.id

        async for db in get_async_session():
            try:
                # Get user
                from sqlalchemy import select
                user_result = await db.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    await message.answer(
                        "❌ Пользователь не найден. Пожалуйста, запустите бота командой /start"
                    )
                    return

                # Get latest pending order without payment
                from sqlalchemy.orm import selectinload
                order_result = await db.execute(
                    select(Order)
                    .options(selectinload(Order.items), selectinload(Order.payment))
                    .where(
                        Order.user_id == user.id,
                        Order.status == OrderStatus.PENDING,
                        Order.is_deleted == False
                    )
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                order = order_result.scalar_one_or_none()

                if not order:
                    await message.answer(
                        "❌ У вас нет ожидающих оплаты заказов.\n"
                        "Оформите заказ через веб-приложение бота."
                    )
                    return

                # Check if order already has a payment
                if order.payment and order.payment.status == PaymentStatus.PENDING:
                    await message.answer(
                        f"💳 У заказа #{order.id} уже создан платёж.\n"
                        f"Сумма: {order.payment.formatted_amount}\n"
                        f"Статус: {order.payment.status_display}"
                    )
                    return

                # Create payment for the order
                payment_service = PaymentService(db)
                payment = await payment_service.create_payment(
                    order=order,
                    payment_method=PaymentMethod.TELEGRAM
                )

                # Send invoice
                telegram_payments = TelegramPaymentsService(bot)
                invoice_sent = await telegram_payments.create_invoice(
                    chat_id=message.chat.id,
                    order=order,
                    payment=payment
                )

                if invoice_sent:
                    await message.answer(
                        f"💳 <b>Счёт для оплаты создан!</b>\n\n"
                        f"📦 <b>Заказ:</b> #{order.id}\n"
                        f"💰 <b>Сумма:</b> {payment.formatted_amount}\n\n"
                        f"Нажмите кнопку ниже для оплаты ⬇️",
                        parse_mode="HTML"
                    )
                else:
                    await message.answer(
                        "❌ Ошибка создания счёта для оплаты. Попробуйте позже."
                    )

                break

            except Exception as e:
                logger.error(f"Database error in pay command handler: {e}")
                await message.answer(
                    "❌ Ошибка при создании платежа. Попробуйте позже."
                )
                return

    except Exception as e:
        logger.error(f"Error in pay command handler: {e}")
        await message.answer(
            "❌ Ошибка при создании платежа. Попробуйте позже."
        )


@router.message(Command("payment_status"))
async def handle_payment_status_command(message: Message):
    """Handle /payment_status command - show payment status for recent orders."""
    try:
        user_id = message.from_user.id

        async for db in get_async_session():
            try:
                # Get user
                from sqlalchemy import select
                user_result = await db.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    await message.answer(
                        "❌ Пользователь не найден. Пожалуйста, запустите бота командой /start"
                    )
                    return

                # Get recent orders with payments
                from sqlalchemy.orm import selectinload
                orders_result = await db.execute(
                    select(Order)
                    .options(selectinload(Order.payment))
                    .where(
                        Order.user_id == user.id,
                        Order.is_deleted == False
                    )
                    .order_by(Order.created_at.desc())
                    .limit(5)
                )
                orders = orders_result.scalars().all()

                if not orders:
                    await message.answer("❌ У вас пока нет заказов.")
                    return

                # Format response
                response = "<b>💳 Статус платежей по вашим заказам:</b>\n\n"

                for order in orders:
                    response += f"📦 <b>Заказ #{order.id}</b>\n"
                    response += f"💰 Сумма: {order.formatted_total}\n"
                    response += f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"

                    if order.payment:
                        response += f"💳 Платёж: {order.payment.status_display}\n"
                        if order.payment.telegram_payment_charge_id:
                            response += f"🔗 ID: <code>{order.payment.telegram_payment_charge_id}</code>\n"
                    else:
                        response += "💳 Платёж: Не создан\n"

                    response += f"🏷 Статус заказа: {order.status_display}\n\n"

                await message.answer(response, parse_mode="HTML")

                break

            except Exception as e:
                logger.error(f"Database error in payment status handler: {e}")
                await message.answer(
                    "❌ Ошибка при получении статуса платежей."
                )
                return

    except Exception as e:
        logger.error(f"Error in payment status handler: {e}")
        await message.answer(
            "❌ Ошибка при получении статуса платежей."
        )