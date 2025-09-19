"""Payment API endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order
from app.services.payment import PaymentService
from app.schemas.payment import PaymentWebhookRequest, PaymentStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/webhook", response_model=Dict[str, Any])
async def payment_webhook(
    webhook_data: PaymentWebhookRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Handle payment webhook from external providers or internal payment processing.

    This endpoint processes payment status updates and updates the corresponding
    order and payment records in the database.
    """
    try:
        logger.info(f"Payment webhook received for order {webhook_data.order_id}")

        payment_service = PaymentService(db)

        # Get payment by order ID
        payment = await payment_service.get_payment_by_order_id(webhook_data.order_id)
        if not payment:
            logger.error(f"Payment not found for order {webhook_data.order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment not found for order {webhook_data.order_id}"
            )

        # Validate that payment is still pending
        if payment.status != PaymentStatus.PENDING:
            logger.warning(
                f"Payment {payment.id} is not pending (status: {payment.status}), "
                f"ignoring webhook"
            )
            return {
                "success": True,
                "message": f"Payment already processed with status: {payment.status.value}"
            }

        # Validate amount matches
        if abs(payment.amount - webhook_data.amount) > 0.01:
            logger.error(
                f"Amount mismatch for payment {payment.id}: "
                f"expected {payment.amount}, got {webhook_data.amount}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount mismatch"
            )

        # Process payment based on status
        if webhook_data.status == "success":
            success = await payment_service.process_successful_payment(
                order_id=webhook_data.order_id,
                payment_id=payment.id,
                telegram_payment_charge_id=webhook_data.transaction_id or "",
                provider_payment_charge_id=webhook_data.transaction_id or "",
                provider_data=webhook_data.metadata
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process successful payment"
                )

            logger.info(f"Payment {payment.id} processed successfully via webhook")
            return {
                "success": True,
                "message": "Payment processed successfully",
                "payment_id": payment.id,
                "order_id": webhook_data.order_id
            }

        elif webhook_data.status == "failed":
            error_message = webhook_data.metadata.get("error_message", "Payment failed") if webhook_data.metadata else "Payment failed"

            success = await payment_service.process_failed_payment(
                payment_id=payment.id,
                error_message=error_message
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process failed payment"
                )

            logger.info(f"Payment {payment.id} marked as failed via webhook")
            return {
                "success": True,
                "message": "Payment failure processed",
                "payment_id": payment.id,
                "order_id": webhook_data.order_id
            }

        else:
            # For pending status, just log it
            logger.info(f"Payment {payment.id} webhook received with pending status")
            return {
                "success": True,
                "message": "Payment status updated to pending",
                "payment_id": payment.id,
                "order_id": webhook_data.order_id
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed for order {webhook_data.order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/{order_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> PaymentStatusResponse:
    """
    Get payment status for an order.

    Returns the current payment status and details for the specified order.
    """
    try:
        payment_service = PaymentService(db)

        # Get payment by order ID
        payment = await payment_service.get_payment_by_order_id(order_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment not found for order {order_id}"
            )

        return PaymentStatusResponse(
            order_id=order_id,
            status=payment.status,
            amount=payment.amount,
            transaction_id=payment.telegram_payment_charge_id,
            payment_method=payment.method_display,
            created_at=payment.created_at.isoformat(),
            updated_at=payment.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment status for order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment status: {str(e)}"
        )


@router.get("/{payment_id}/details", response_model=Dict[str, Any])
async def get_payment_details(
    payment_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get detailed payment information by payment ID.

    This endpoint provides comprehensive payment details including
    transaction IDs, provider data, and associated order information.
    """
    try:
        payment_service = PaymentService(db)

        # Get payment by ID
        payment = await payment_service.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )

        # Format response
        response = {
            "id": payment.id,
            "order_id": payment.order_id,
            "status": payment.status.value,
            "status_display": payment.status_display,
            "amount": payment.amount,
            "formatted_amount": payment.formatted_amount,
            "payment_method": payment.payment_method.value,
            "method_display": payment.method_display,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat()
        }

        # Add transaction details if available
        if payment.telegram_payment_charge_id:
            response["telegram_payment_charge_id"] = payment.telegram_payment_charge_id

        if payment.provider_payment_charge_id:
            response["provider_payment_charge_id"] = payment.provider_payment_charge_id

        if payment.transaction_id:
            response["transaction_id"] = payment.transaction_id

        if payment.error_message:
            response["error_message"] = payment.error_message

        if payment.provider_data:
            response["provider_data"] = payment.provider_data

        if payment.payment_metadata:
            response["metadata"] = payment.payment_metadata

        # Add order details if loaded
        if payment.order:
            response["order"] = {
                "id": payment.order.id,
                "status": payment.order.status.value,
                "status_display": payment.order.status_display,
                "total_amount": payment.order.total_amount,
                "formatted_total": payment.order.formatted_total,
                "customer_name": payment.order.customer_name,
                "customer_phone": payment.order.customer_phone
            }

        return {
            "success": True,
            "payment": response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment details for payment {payment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment details: {str(e)}"
        )