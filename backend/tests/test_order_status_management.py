"""Comprehensive tests for order status management (BE-015)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.models.order import Order, OrderStatus, OrderPriority
from app.models.order_status_history import OrderStatusHistory, StatusChangeReason
from app.models.user import User, UserRole
from app.services.order import OrderService
from app.services.order_workflow import OrderWorkflow, StatusTransitionError
from app.services.notification import NotificationService


class TestOrderModel:
    """Test enhanced Order model functionality."""

    def test_order_status_enum_values(self):
        """Test that all expected status values exist."""
        expected_statuses = {
            'pending', 'confirmed', 'preparing', 'ready',
            'completed', 'cancelled', 'refunded', 'failed'
        }
        actual_statuses = {status.value for status in OrderStatus}
        assert actual_statuses == expected_statuses

    def test_order_priority_enum_values(self):
        """Test that all expected priority values exist."""
        expected_priorities = {'low', 'normal', 'high', 'vip'}
        actual_priorities = {priority.value for priority in OrderPriority}
        assert actual_priorities == expected_priorities

    def test_order_status_display_mapping(self, sample_order):
        """Test human-readable status display."""
        sample_order.status = OrderStatus.PENDING
        assert sample_order.status_display == "Ожидает подтверждения"

        sample_order.status = OrderStatus.REFUNDED
        assert sample_order.status_display == "Возврат средств"

    def test_order_priority_display_mapping(self, sample_order):
        """Test human-readable priority display."""
        sample_order.priority = OrderPriority.VIP
        assert sample_order.priority_display == "VIP"

        sample_order.priority = OrderPriority.LOW
        assert sample_order.priority_display == "Низкий"

    def test_order_state_properties(self, sample_order):
        """Test order state checking properties."""
        # Test active state
        sample_order.status = OrderStatus.PREPARING
        assert sample_order.is_active is True
        assert sample_order.is_completed_state is False

        # Test completed state
        sample_order.status = OrderStatus.COMPLETED
        assert sample_order.is_active is False
        assert sample_order.is_completed_state is True

    def test_order_cancellation_properties(self, sample_order):
        """Test order cancellation checking properties."""
        # Can be cancelled
        sample_order.status = OrderStatus.CONFIRMED
        assert sample_order.can_be_cancelled is True

        # Cannot be cancelled
        sample_order.status = OrderStatus.COMPLETED
        assert sample_order.can_be_cancelled is False

    def test_order_refund_properties(self, sample_order):
        """Test order refund checking properties."""
        # Can be refunded
        sample_order.status = OrderStatus.COMPLETED
        assert sample_order.can_be_refunded is True

        # Cannot be refunded
        sample_order.status = OrderStatus.PREPARING
        assert sample_order.can_be_refunded is False

    def test_order_timing_calculations(self, sample_order):
        """Test order timing calculation methods."""
        # Set preparation times
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=30)

        sample_order.actual_preparation_start = start_time
        sample_order.actual_preparation_end = end_time

        duration = sample_order.calculate_preparation_duration()
        assert duration == 30

    def test_order_estimated_completion_time(self, sample_order):
        """Test estimated completion time calculation."""
        sample_order.estimated_preparation_time = 45
        sample_order.status_confirmed_at = datetime.utcnow()

        estimated = sample_order.get_estimated_completion_time()
        assert estimated is not None
        assert (estimated - sample_order.status_confirmed_at).total_seconds() / 60 == 45

    def test_order_overdue_check(self, sample_order):
        """Test overdue order detection."""
        # Not overdue
        sample_order.estimated_preparation_time = 30
        sample_order.status_confirmed_at = datetime.utcnow()
        sample_order.status = OrderStatus.PREPARING
        assert sample_order.is_overdue() is False

        # Overdue
        sample_order.status_confirmed_at = datetime.utcnow() - timedelta(hours=2)
        assert sample_order.is_overdue() is True

    def test_workflow_metadata_operations(self, sample_order):
        """Test workflow metadata operations."""
        sample_order.set_workflow_metadata_value('test_key', 'test_value')
        assert sample_order.get_workflow_metadata_value('test_key') == 'test_value'
        assert sample_order.get_workflow_metadata_value('nonexistent', 'default') == 'default'

    def test_automation_flags_operations(self, sample_order):
        """Test automation flags operations."""
        sample_order.set_automation_flag('processed', True)
        assert sample_order.get_automation_flag('processed') is True
        assert sample_order.get_automation_flag('nonexistent') is False


class TestOrderStatusHistory:
    """Test OrderStatusHistory model functionality."""

    def test_status_history_creation(self):
        """Test creating status history record."""
        history = OrderStatusHistory.create_status_change(
            order_id=1,
            from_status='pending',
            to_status='confirmed',
            reason=StatusChangeReason.MANUAL_ADMIN,
            changed_by_user_id=1,
            notes="Test transition"
        )

        assert history.order_id == 1
        assert history.from_status == 'pending'
        assert history.to_status == 'confirmed'
        assert history.reason == StatusChangeReason.MANUAL_ADMIN.value
        assert history.notes == "Test transition"

    def test_status_history_displays(self, sample_status_history):
        """Test display methods."""
        sample_status_history.from_status = 'pending'
        sample_status_history.to_status = 'confirmed'
        sample_status_history.reason = StatusChangeReason.MANUAL_ADMIN.value
        sample_status_history.duration_from_previous = 30

        assert 'Pending' in sample_status_history.from_status_display
        assert 'Confirmed' in sample_status_history.to_status_display
        assert 'администратором' in sample_status_history.reason_display
        assert '30 мин' in sample_status_history.duration_display

    def test_workflow_data_operations(self, sample_status_history):
        """Test workflow data operations."""
        sample_status_history.set_workflow_data('step', 'validation')
        assert sample_status_history.get_workflow_data('step') == 'validation'


class TestOrderWorkflow:
    """Test OrderWorkflow service functionality."""

    @pytest.mark.asyncio
    async def test_valid_status_transitions(self, db_session, sample_order):
        """Test valid status transition validation."""
        workflow = OrderWorkflow(db_session)

        # Valid transitions
        workflow._validate_transition(OrderStatus.PENDING, OrderStatus.CONFIRMED)
        workflow._validate_transition(OrderStatus.CONFIRMED, OrderStatus.PREPARING)
        workflow._validate_transition(OrderStatus.PREPARING, OrderStatus.READY)
        workflow._validate_transition(OrderStatus.READY, OrderStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_invalid_status_transitions(self, db_session):
        """Test invalid status transition validation."""
        workflow = OrderWorkflow(db_session)

        # Invalid transitions should raise exceptions
        with pytest.raises(StatusTransitionError):
            workflow._validate_transition(OrderStatus.COMPLETED, OrderStatus.PENDING)

        with pytest.raises(StatusTransitionError):
            workflow._validate_transition(OrderStatus.PENDING, OrderStatus.READY)

    @pytest.mark.asyncio
    async def test_status_transition_with_history(self, db_session, sample_order, sample_user):
        """Test status transition with history creation."""
        workflow = OrderWorkflow(db_session)

        updated_order, history = await workflow.transition_status(
            order=sample_order,
            new_status=OrderStatus.CONFIRMED,
            reason=StatusChangeReason.MANUAL_ADMIN,
            changed_by_user_id=sample_user.id,
            notes="Test transition",
            validate=True
        )

        assert updated_order.status == OrderStatus.CONFIRMED
        assert history.from_status == OrderStatus.PENDING.value
        assert history.to_status == OrderStatus.CONFIRMED.value
        assert history.changed_by_user_id == sample_user.id
        assert history.notes == "Test transition"

    @pytest.mark.asyncio
    async def test_automatic_timestamp_updates(self, db_session, sample_order):
        """Test automatic timestamp updates during transitions."""
        workflow = OrderWorkflow(db_session)

        # Transition to confirmed should update confirmed timestamp
        updated_order, _ = await workflow.transition_status(
            order=sample_order,
            new_status=OrderStatus.CONFIRMED,
            validate=True,
            auto_calculate_times=True
        )

        assert updated_order.status_confirmed_at is not None
        assert updated_order.estimated_preparation_time is not None

    @pytest.mark.asyncio
    async def test_bulk_status_update(self, db_session, sample_orders):
        """Test bulk status updates."""
        workflow = OrderWorkflow(db_session)

        order_ids = [order.id for order in sample_orders]
        results = await workflow.bulk_transition_orders(
            order_ids=order_ids,
            new_status=OrderStatus.CONFIRMED,
            reason=StatusChangeReason.MANUAL_ADMIN,
            notes="Bulk confirmation"
        )

        assert results['success_count'] == len(sample_orders)
        assert results['failure_count'] == 0
        assert len(results['successful']) == len(sample_orders)

    @pytest.mark.asyncio
    async def test_automatic_transition_conditions(self, db_session, sample_vip_order):
        """Test automatic transition condition checking."""
        workflow = OrderWorkflow(db_session)

        # Mock successful payment
        with patch.object(workflow, '_get_order_payment') as mock_payment:
            from app.models.payment import Payment, PaymentStatus
            mock_payment_obj = AsyncMock()
            mock_payment_obj.status = PaymentStatus.SUCCESS
            mock_payment.return_value = mock_payment_obj

            target_status = await workflow._check_auto_confirm_conditions(sample_vip_order)
            assert target_status == OrderStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_overdue_orders_detection(self, db_session, sample_overdue_order):
        """Test overdue orders detection."""
        workflow = OrderWorkflow(db_session)

        overdue_orders = await workflow.get_overdue_orders(threshold_minutes=30)
        assert len(overdue_orders) > 0
        assert sample_overdue_order.id in [order.id for order in overdue_orders]

    @pytest.mark.asyncio
    async def test_order_timeline_generation(self, db_session, sample_order_with_history):
        """Test order timeline generation."""
        workflow = OrderWorkflow(db_session)

        timeline = await workflow.get_order_timeline(sample_order_with_history.id)

        assert len(timeline) >= 2  # Creation + at least one status change
        assert timeline[0]['event_type'] == 'order_created'
        assert any(event['event_type'] == 'status_change' for event in timeline)


class TestOrderService:
    """Test enhanced OrderService functionality."""

    @pytest.mark.asyncio
    async def test_enhanced_order_stats(self, db_session, sample_orders_various_statuses):
        """Test enhanced order statistics."""
        service = OrderService(db_session)
        stats = await service.get_orders_stats()

        assert 'total' in stats
        assert 'status_counts' in stats
        assert 'priority_counts' in stats
        assert 'overdue_count' in stats
        assert 'today_orders' in stats

        # Check status counts
        assert stats['status_counts']['pending'] >= 0
        assert stats['status_counts']['completed'] >= 0

    @pytest.mark.asyncio
    async def test_order_priority_update(self, db_session, sample_order, sample_admin):
        """Test order priority updates."""
        service = OrderService(db_session)

        updated_order = await service.update_order_priority(
            order_id=sample_order.id,
            new_priority=OrderPriority.HIGH,
            changed_by_user_id=sample_admin.id,
            reason="High priority customer",
            db=db_session
        )

        assert updated_order.priority == OrderPriority.HIGH

    @pytest.mark.asyncio
    async def test_courier_assignment(self, db_session, sample_delivery_order, sample_admin):
        """Test courier assignment."""
        service = OrderService(db_session)

        updated_order = await service.assign_courier(
            order_id=sample_delivery_order.id,
            courier_name="Ivan Petrov",
            changed_by_user_id=sample_admin.id,
            db=db_session
        )

        assert updated_order.courier_assigned == "Ivan Petrov"

    @pytest.mark.asyncio
    async def test_delivery_scheduling(self, db_session, sample_order, sample_admin):
        """Test delivery scheduling."""
        service = OrderService(db_session)

        scheduled_time = datetime.utcnow() + timedelta(hours=2)
        updated_order = await service.schedule_delivery(
            order_id=sample_order.id,
            scheduled_time=scheduled_time,
            changed_by_user_id=sample_admin.id,
            db=db_session
        )

        assert updated_order.delivery_scheduled_at == scheduled_time

    @pytest.mark.asyncio
    async def test_enhanced_order_cancellation(self, db_session, sample_order, sample_admin):
        """Test enhanced order cancellation with refund."""
        service = OrderService(db_session)

        success = await service.cancel_order(
            order_id=sample_order.id,
            db=db_session,
            cancelled_by_user_id=sample_admin.id,
            reason="Customer request",
            refund_amount=sample_order.total_amount
        )

        assert success is True
        # Refresh order to check changes
        await db_session.refresh(sample_order)
        assert sample_order.status == OrderStatus.CANCELLED
        assert sample_order.cancelled_by_user_id == sample_admin.id
        assert sample_order.cancellation_reason == "Customer request"

    @pytest.mark.asyncio
    async def test_dashboard_data_generation(self, db_session, sample_orders_various_statuses):
        """Test dashboard data generation."""
        service = OrderService(db_session)
        dashboard_data = await service.get_dashboard_data(db_session)

        assert 'stats' in dashboard_data
        assert 'overdue_orders' in dashboard_data
        assert 'vip_orders' in dashboard_data
        assert 'recent_orders' in dashboard_data
        assert 'performance' in dashboard_data

        # Check performance metrics
        assert 'avg_preparation_time_today' in dashboard_data['performance']
        assert 'overdue_count' in dashboard_data['performance']


class TestOrderAPI:
    """Test order API endpoints."""

    @pytest.mark.asyncio
    async def test_update_order_status_endpoint(self, client, sample_order, admin_headers):
        """Test order status update endpoint."""
        response = await client.put(
            f"/api/orders/{sample_order.id}/status",
            json={
                "status": "confirmed",
                "reason": "manual_admin",
                "notes": "Confirmed by admin"
            },
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['order']['status'] == 'confirmed'

    @pytest.mark.asyncio
    async def test_order_timeline_endpoint(self, client, sample_order_with_history, admin_headers):
        """Test order timeline endpoint."""
        response = await client.get(
            f"/api/orders/{sample_order_with_history.id}/timeline",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['order_id'] == sample_order_with_history.id
        assert len(data['timeline']) >= 1

    @pytest.mark.asyncio
    async def test_bulk_status_update_endpoint(self, client, sample_orders, admin_headers):
        """Test bulk status update endpoint."""
        order_ids = [order.id for order in sample_orders[:2]]

        response = await client.post(
            "/api/orders/bulk-status",
            json={
                "order_ids": order_ids,
                "status": "confirmed",
                "reason": "manual_admin",
                "notes": "Bulk confirmation"
            },
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success_count'] == 2
        assert data['failure_count'] == 0

    @pytest.mark.asyncio
    async def test_dashboard_endpoint(self, client, admin_headers):
        """Test dashboard endpoint."""
        response = await client.get("/api/orders/dashboard", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert 'stats' in data
        assert 'overdue_orders' in data
        assert 'vip_orders' in data
        assert 'recent_orders' in data

    @pytest.mark.asyncio
    async def test_overdue_orders_endpoint(self, client, admin_headers):
        """Test overdue orders endpoint."""
        response = await client.get("/api/orders/overdue?threshold_minutes=60", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_cancel_order_endpoint(self, client, sample_order, admin_headers):
        """Test order cancellation endpoint."""
        response = await client.post(
            f"/api/orders/{sample_order.id}/cancel",
            json={
                "reason": "Customer request",
                "refund_amount": sample_order.total_amount
            },
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['reason'] == "Customer request"

    @pytest.mark.asyncio
    async def test_update_priority_endpoint(self, client, sample_order, admin_headers):
        """Test order priority update endpoint."""
        response = await client.put(
            f"/api/orders/{sample_order.id}/priority",
            json={
                "priority": "high",
                "reason": "VIP customer"
            },
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['order']['priority'] == 'high'

    @pytest.mark.asyncio
    async def test_assign_courier_endpoint(self, client, sample_delivery_order, admin_headers):
        """Test courier assignment endpoint."""
        response = await client.put(
            f"/api/orders/{sample_delivery_order.id}/courier",
            json={"courier_name": "Ivan Petrov"},
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['order']['courier_assigned'] == "Ivan Petrov"

    @pytest.mark.asyncio
    async def test_schedule_delivery_endpoint(self, client, sample_order, admin_headers):
        """Test delivery scheduling endpoint."""
        scheduled_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()

        response = await client.put(
            f"/api/orders/{sample_order.id}/schedule",
            json={"scheduled_time": scheduled_time},
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    @pytest.mark.asyncio
    async def test_automation_processing_endpoint(self, client, admin_headers):
        """Test automation processing endpoint."""
        response = await client.post("/api/orders/automation/process", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert 'processed_orders' in data
        assert 'transitions_made' in data
        assert 'errors' in data


class TestOrderAutomation:
    """Test order automation tasks."""

    @pytest.mark.asyncio
    async def test_automatic_transitions_task(self):
        """Test automatic transitions background task."""
        from app.tasks.order_automation import OrderAutomationTasks

        with patch.object(OrderAutomationTasks, 'process_automatic_transitions') as mock_process:
            mock_process.return_value = {
                'processed_orders': 5,
                'transitions_made': 2,
                'errors': []
            }

            result = await OrderAutomationTasks.process_automatic_transitions()
            assert result['processed_orders'] == 5
            assert result['transitions_made'] == 2

    @pytest.mark.asyncio
    async def test_overdue_monitoring_task(self):
        """Test overdue orders monitoring task."""
        from app.tasks.order_automation import OrderAutomationTasks

        with patch('app.tasks.order_automation.get_async_session'), \
             patch('app.tasks.order_automation.OrderService') as mock_service:

            mock_service_instance = AsyncMock()
            mock_service_instance.get_overdue_orders.return_value = []
            mock_service.return_value = mock_service_instance

            result = await OrderAutomationTasks.process_overdue_orders()
            assert 'overdue_orders_found' in result
            assert 'notifications_sent' in result

    @pytest.mark.asyncio
    async def test_maintenance_tasks_runner(self):
        """Test maintenance tasks runner."""
        from app.tasks.order_automation import OrderAutomationTasks

        with patch.multiple(OrderAutomationTasks,
                          process_automatic_transitions=AsyncMock(return_value={'errors': []}),
                          process_overdue_orders=AsyncMock(return_value={'errors': []}),
                          process_scheduled_notifications=AsyncMock(return_value={'errors': []}),
                          retry_failed_notifications=AsyncMock(return_value={'errors': []}),
                          calculate_order_metrics=AsyncMock(return_value={'errors': []}),
                          cleanup_old_records=AsyncMock(return_value={'errors': []})):

            result = await OrderAutomationTasks.run_all_maintenance_tasks()
            assert 'maintenance_started_at' in result
            assert 'tasks' in result
            assert result['total_errors'] == 0


class TestIntegrations:
    """Test integrations with notification and payment systems."""

    @pytest.mark.asyncio
    async def test_notification_integration_on_status_change(self, db_session, sample_order):
        """Test notification integration during status changes."""
        workflow = OrderWorkflow(db_session)

        with patch('app.services.order_workflow.NotificationService') as mock_notification:
            mock_service = AsyncMock()
            mock_notification.return_value = mock_service

            await workflow.transition_status(
                order=sample_order,
                new_status=OrderStatus.CONFIRMED,
                validate=True
            )

            mock_service.notify_order_status_change.assert_called_once()

    @pytest.mark.asyncio
    async def test_payment_integration_automatic_confirmation(self, db_session, sample_vip_order):
        """Test automatic order confirmation on payment success."""
        workflow = OrderWorkflow(db_session)

        # Mock successful payment
        with patch.object(workflow, '_get_order_payment') as mock_payment:
            from app.models.payment import Payment, PaymentStatus
            mock_payment_obj = AsyncMock()
            mock_payment_obj.status = PaymentStatus.SUCCESS
            mock_payment.return_value = mock_payment_obj

            # Process automatic transitions
            await workflow.process_automatic_transitions()

            # VIP order with successful payment should be auto-confirmed
            mock_payment.assert_called()


# Fixtures for tests
@pytest.fixture
def sample_order(db_session, sample_user):
    """Create a sample order for testing."""
    order = Order(
        user_id=sample_user.id,
        status=OrderStatus.PENDING,
        priority=OrderPriority.NORMAL,
        total_amount=1500.0,
        customer_name="Test Customer",
        customer_phone="+7900123456",
        delivery_address="Test Address",
        payment_method="card",
        delivery_type="delivery"
    )
    db_session.add(order)
    db_session.commit()
    return order


@pytest.fixture
def sample_vip_order(db_session, sample_user):
    """Create a VIP order for testing."""
    order = Order(
        user_id=sample_user.id,
        status=OrderStatus.PENDING,
        priority=OrderPriority.VIP,
        total_amount=3000.0,
        customer_name="VIP Customer",
        customer_phone="+7900123456",
        payment_method="card"
    )
    db_session.add(order)
    db_session.commit()
    return order


@pytest.fixture
def sample_delivery_order(db_session, sample_user):
    """Create a delivery order for testing."""
    order = Order(
        user_id=sample_user.id,
        status=OrderStatus.READY,
        total_amount=2000.0,
        customer_name="Delivery Customer",
        customer_phone="+7900123456",
        delivery_address="Delivery Address",
        delivery_type="delivery"
    )
    db_session.add(order)
    db_session.commit()
    return order


@pytest.fixture
def sample_overdue_order(db_session, sample_user):
    """Create an overdue order for testing."""
    order = Order(
        user_id=sample_user.id,
        status=OrderStatus.PREPARING,
        total_amount=1800.0,
        customer_name="Overdue Customer",
        customer_phone="+7900123456",
        estimated_preparation_time=30,
        status_confirmed_at=datetime.utcnow() - timedelta(hours=2)
    )
    order.estimated_delivery_time = order.status_confirmed_at + timedelta(minutes=30)
    db_session.add(order)
    db_session.commit()
    return order


@pytest.fixture
def sample_orders(db_session, sample_user):
    """Create multiple sample orders."""
    orders = []
    for i in range(3):
        order = Order(
            user_id=sample_user.id,
            status=OrderStatus.PENDING,
            total_amount=1500.0 + i * 100,
            customer_name=f"Customer {i}",
            customer_phone="+7900123456",
            payment_method="card"
        )
        db_session.add(order)
        orders.append(order)
    db_session.commit()
    return orders


@pytest.fixture
def sample_orders_various_statuses(db_session, sample_user):
    """Create orders with various statuses."""
    orders = []
    statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.COMPLETED, OrderStatus.CANCELLED]

    for i, status in enumerate(statuses):
        order = Order(
            user_id=sample_user.id,
            status=status,
            priority=OrderPriority.NORMAL,
            total_amount=1500.0 + i * 100,
            customer_name=f"Customer {i}",
            customer_phone="+7900123456"
        )
        db_session.add(order)
        orders.append(order)

    db_session.commit()
    return orders


@pytest.fixture
def sample_status_history(db_session, sample_order):
    """Create a sample status history record."""
    history = OrderStatusHistory.create_status_change(
        order_id=sample_order.id,
        from_status='pending',
        to_status='confirmed',
        reason=StatusChangeReason.MANUAL_ADMIN,
        notes="Test history"
    )
    db_session.add(history)
    db_session.commit()
    return history


@pytest.fixture
def sample_order_with_history(db_session, sample_user):
    """Create an order with status history."""
    order = Order(
        user_id=sample_user.id,
        status=OrderStatus.CONFIRMED,
        total_amount=1500.0,
        customer_name="Customer with History",
        customer_phone="+7900123456"
    )
    db_session.add(order)
    db_session.flush()

    # Add status history
    history = OrderStatusHistory.create_status_change(
        order_id=order.id,
        from_status='pending',
        to_status='confirmed',
        reason=StatusChangeReason.MANUAL_ADMIN,
        notes="Order confirmed"
    )
    db_session.add(history)
    db_session.commit()

    return order


@pytest.fixture
def sample_admin(db_session):
    """Create a sample admin user."""
    admin = User(
        telegram_id=999999999,
        username="admin",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN
    )
    db_session.add(admin)
    db_session.commit()
    return admin