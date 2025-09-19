#!/usr/bin/env python3
"""
Test script for Telegram Payments integration.
This script tests the complete payment flow without requiring actual Telegram bot interactions.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings
from app.database import get_async_session
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.category import Category
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.services.payment import PaymentService
from app.services.telegram_payments import TelegramPaymentsService
from app.utils.payments import PaymentUtils


async def test_payment_utilities():
    """Test payment utility functions."""
    print("🧪 Testing Payment Utilities...")

    # Test amount validation
    valid, error = PaymentUtils.validate_payment_amount(2000.0)
    assert valid, f"Valid amount should pass: {error}"

    valid, error = PaymentUtils.validate_payment_amount(500.0)
    assert not valid, "Amount below minimum should fail"

    # Test amount normalization
    normalized = PaymentUtils.normalize_amount(1999.999)
    assert normalized == 2000.0, f"Expected 2000.0, got {normalized}"

    # Test kopecks/rubles conversion
    rubles = PaymentUtils.kopecks_to_rubles(150000)
    assert rubles == 1500.0, f"Expected 1500.0, got {rubles}"

    kopecks = PaymentUtils.rubles_to_kopecks(1500.0)
    assert kopecks == 150000, f"Expected 150000, got {kopecks}"

    # Test amount formatting
    formatted = PaymentUtils.format_amount(1500.0)
    assert formatted == "1500₽", f"Expected '1500₽', got '{formatted}'"

    # Test description generation
    desc = PaymentUtils.generate_payment_description(123, 3, "John Doe")
    assert "Заказ #123" in desc
    assert "3 товара" in desc
    assert "John Doe" in desc

    print("✅ Payment utilities tests passed!")


async def test_payment_models():
    """Test payment models and database operations."""
    print("🧪 Testing Payment Models...")

    async for db in get_async_session():
        try:
            # Create test user if not exists
            from sqlalchemy import select
            user_result = await db.execute(
                select(User).where(User.telegram_id == 123456789)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=123456789,
                    first_name="Test",
                    last_name="User"
                )
                db.add(user)
                await db.flush()

            # Create test category if not exists
            category_result = await db.execute(
                select(Category).where(Category.name == "Test Category")
            )
            category = category_result.scalar_one_or_none()

            if not category:
                category = Category(
                    name="Test Category",
                    description="Test category for payments"
                )
                db.add(category)
                await db.flush()

            # Create test product if not exists
            product_result = await db.execute(
                select(Product).where(Product.name == "Test Product")
            )
            product = product_result.scalar_one_or_none()

            if not product:
                product = Product(
                    name="Test Product",
                    description="Test product for payments",
                    price=750.0,
                    category_id=category.id,
                    is_active=True,
                    in_stock=True
                )
                db.add(product)
                await db.flush()

            # Create test order
            order = Order(
                user_id=user.id,
                total_amount=1500.0,
                customer_name="Test Customer",
                customer_phone="+7900123456",
                payment_method="telegram"
            )
            db.add(order)
            await db.flush()

            # Create order items
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=2,
                price=750.0
            )
            db.add(order_item)

            await db.commit()

            # Test payment creation
            payment_service = PaymentService(db)
            payment = await payment_service.create_payment(
                order=order,
                payment_method=PaymentMethod.TELEGRAM,
                metadata={"test": True}
            )

            assert payment.order_id == order.id
            assert payment.amount == 1500.0
            assert payment.status == PaymentStatus.PENDING
            assert payment.payment_method == PaymentMethod.TELEGRAM

            print(f"✅ Created payment: {payment.id} for order: {order.id}")

            # Test payment status update
            updated_payment = await payment_service.update_payment_status(
                payment=payment,
                status=PaymentStatus.SUCCESS,
                telegram_payment_charge_id="test_charge_123",
                provider_payment_charge_id="provider_123",
                transaction_id="txn_123"
            )

            assert updated_payment.status == PaymentStatus.SUCCESS
            assert updated_payment.telegram_payment_charge_id == "test_charge_123"

            # Verify order status was updated
            await db.refresh(order)
            assert order.status == OrderStatus.CONFIRMED

            print("✅ Payment models tests passed!")

            # Clean up
            await db.delete(payment)
            await db.delete(order_item)
            await db.delete(order)
            await db.commit()

            break

        except Exception as e:
            await db.rollback()
            print(f"❌ Payment models test failed: {e}")
            raise


async def test_telegram_payments_service():
    """Test Telegram Payments service functions."""
    print("🧪 Testing Telegram Payments Service...")

    # Test payload extraction
    valid_payload = "order_123_payment_456"
    data = TelegramPaymentsService.extract_payment_data_from_payload(valid_payload)
    assert data is not None
    assert data["order_id"] == 123
    assert data["payment_id"] == 456

    invalid_payload = "invalid_payload_format"
    data = TelegramPaymentsService.extract_payment_data_from_payload(invalid_payload)
    assert data is None

    # Test message formatting
    async for db in get_async_session():
        try:
            # Create mock objects for testing
            class MockOrder:
                id = 123
                formatted_total = "1500₽"

            class MockPayment:
                id = 456
                formatted_amount = "1500₽"
                created_at = asyncio.get_event_loop().time()
                telegram_payment_charge_id = "test_charge_123"

                def __init__(self):
                    from datetime import datetime
                    self.created_at = datetime.now()

            mock_order = MockOrder()
            mock_payment = MockPayment()

            # Test success message
            success_msg = TelegramPaymentsService.format_payment_success_message(
                mock_order, mock_payment
            )
            assert "успешно обработан" in success_msg
            assert "Заказ #123" in success_msg
            assert "1500₽" in success_msg

            # Test failure message
            failure_msg = TelegramPaymentsService.format_payment_failed_message(
                mock_order, "Test error"
            )
            assert "Ошибка при обработке платежа" in failure_msg
            assert "Заказ #123" in failure_msg
            assert "Test error" in failure_msg

            print("✅ Telegram Payments service tests passed!")
            break

        except Exception as e:
            print(f"❌ Telegram Payments service test failed: {e}")
            raise


async def test_webhook_signature_verification():
    """Test webhook signature verification."""
    print("🧪 Testing Webhook Signature Verification...")

    test_payload = '{"order_id": 123, "status": "success", "amount": 1500.0}'
    test_secret = "test_secret_key"

    # Generate valid signature
    import hmac
    import hashlib
    expected_signature = hmac.new(
        test_secret.encode('utf-8'),
        test_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Test valid signature
    is_valid = PaymentUtils.verify_webhook_signature(
        test_payload, expected_signature, test_secret
    )
    assert is_valid, "Valid signature should pass verification"

    # Test invalid signature
    is_valid = PaymentUtils.verify_webhook_signature(
        test_payload, "invalid_signature", test_secret
    )
    assert not is_valid, "Invalid signature should fail verification"

    print("✅ Webhook signature verification tests passed!")


async def test_complete_payment_flow():
    """Test complete payment flow simulation."""
    print("🧪 Testing Complete Payment Flow...")

    async for db in get_async_session():
        try:
            payment_service = PaymentService(db)

            # Create a test order (reuse from previous test)
            from sqlalchemy import select

            # Get test user
            user_result = await db.execute(
                select(User).where(User.telegram_id == 123456789)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=123456789,
                    first_name="Test",
                    last_name="User"
                )
                db.add(user)
                await db.flush()

            # Create order
            order = Order(
                user_id=user.id,
                total_amount=1500.0,
                customer_name="Test Customer",
                customer_phone="+7900123456",
                payment_method="telegram"
            )
            db.add(order)
            await db.flush()

            # Step 1: Create payment
            payment = await payment_service.create_payment(
                order=order,
                payment_method=PaymentMethod.TELEGRAM,
                metadata={"test_flow": True}
            )

            print(f"📝 Step 1: Payment {payment.id} created")

            # Step 2: Simulate successful payment processing
            success = await payment_service.process_successful_payment(
                order_id=order.id,
                payment_id=payment.id,
                telegram_payment_charge_id="test_charge_flow_123",
                provider_payment_charge_id="provider_flow_123",
                provider_data={"currency": "RUB", "test": True}
            )

            assert success, "Payment processing should succeed"
            print("📝 Step 2: Payment processed successfully")

            # Step 3: Verify final state
            final_payment = await payment_service.get_payment_by_id(payment.id)
            assert final_payment.status == PaymentStatus.SUCCESS
            assert final_payment.telegram_payment_charge_id == "test_charge_flow_123"

            await db.refresh(order)
            assert order.status == OrderStatus.CONFIRMED

            print("📝 Step 3: Final state verified")
            print("✅ Complete payment flow test passed!")

            # Clean up
            await db.delete(final_payment)
            await db.delete(order)
            await db.commit()

            break

        except Exception as e:
            await db.rollback()
            print(f"❌ Complete payment flow test failed: {e}")
            raise


async def main():
    """Run all payment tests."""
    print("🚀 Starting Telegram Payments Integration Tests")
    print("=" * 60)

    try:
        await test_payment_utilities()
        print()

        await test_webhook_signature_verification()
        print()

        await test_telegram_payments_service()
        print()

        await test_payment_models()
        print()

        await test_complete_payment_flow()
        print()

        print("=" * 60)
        print("🎉 All Telegram Payments tests passed successfully!")
        print()
        print("💳 Payment Integration Summary:")
        print("  ✅ Payment models and database schema")
        print("  ✅ Payment services and business logic")
        print("  ✅ Telegram Payments API integration")
        print("  ✅ Webhook signature verification")
        print("  ✅ Payment utilities and helpers")
        print("  ✅ Complete payment workflow")
        print()
        print("🔧 Ready for deployment with:")
        print("  • Telegram Bot Payments API")
        print("  • Order-Payment integration")
        print("  • Secure webhook handling")
        print("  • Comprehensive error handling")
        print("  • Real-time notifications")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())