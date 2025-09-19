"""Add order status management features

Revision ID: 20250916_1722_add_order_status_management
Revises: 20240916_add_payments_table
Create Date: 2025-09-16 17:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250916_1722_add_order_status_management'
down_revision = '20240916_add_payments_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced order status management features."""

    # Add new order statuses to enum
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'refunded'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'failed'")

    # Create order priority enum
    order_priority_enum = sa.Enum('LOW', 'NORMAL', 'HIGH', 'VIP', name='orderpriority')
    order_priority_enum.create(op.get_bind())

    # Add enhanced fields to orders table
    with op.batch_alter_table('orders', schema=None) as batch_op:
        # Priority and timing fields
        batch_op.add_column(sa.Column('priority', sa.Enum('LOW', 'NORMAL', 'HIGH', 'VIP', name='orderpriority'),
                                     nullable=False, server_default='NORMAL'))
        batch_op.add_column(sa.Column('estimated_preparation_time', sa.Integer(), nullable=True,
                                     comment='Estimated preparation time in minutes'))
        batch_op.add_column(sa.Column('estimated_delivery_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('actual_preparation_start', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('actual_preparation_end', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('delivery_scheduled_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('delivery_completed_at', sa.DateTime(), nullable=True))

        # Status timestamps
        batch_op.add_column(sa.Column('status_pending_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        batch_op.add_column(sa.Column('status_confirmed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status_preparing_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status_ready_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status_completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status_cancelled_at', sa.DateTime(), nullable=True))

        # Kitchen integration
        batch_op.add_column(sa.Column('kitchen_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('requires_special_handling', sa.Boolean(), nullable=False, server_default='false'))

        # Delivery details
        batch_op.add_column(sa.Column('delivery_type', sa.String(length=20), nullable=False, server_default='delivery'))
        batch_op.add_column(sa.Column('delivery_instructions', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('courier_assigned', sa.String(length=100), nullable=True))

        # Cancellation and refund
        batch_op.add_column(sa.Column('cancellation_reason', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('cancelled_by_user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('refund_amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('refund_reason', sa.String(length=255), nullable=True))

        # Business metrics
        batch_op.add_column(sa.Column('preparation_duration', sa.Integer(), nullable=True,
                                     comment='Actual preparation time in minutes'))
        batch_op.add_column(sa.Column('total_duration', sa.Integer(), nullable=True,
                                     comment='Total order completion time in minutes'))

        # Metadata for automation
        batch_op.add_column(sa.Column('automation_flags', sa.JSON(), nullable=False, server_default='{}'))
        batch_op.add_column(sa.Column('workflow_metadata', sa.JSON(), nullable=False, server_default='{}'))

        # Foreign key constraints
        batch_op.create_foreign_key('fk_orders_cancelled_by_user_id', 'users', ['cancelled_by_user_id'], ['id'])

    # Create order status history table
    op.create_table(
        'order_status_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('from_status', sa.String(length=20), nullable=True),
        sa.Column('to_status', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=False, server_default='manual_admin'),
        sa.Column('changed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('system_message', sa.Text(), nullable=True),
        sa.Column('workflow_data', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('duration_from_previous', sa.Integer(), nullable=True,
                 comment='Duration from previous status in minutes'),
        sa.Column('triggered_by_event', sa.String(length=100), nullable=True),
        sa.Column('external_reference_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name='fk_order_status_history_order_id'),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], name='fk_order_status_history_changed_by_user_id'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better performance
    op.create_index('ix_order_status_history_order_id', 'order_status_history', ['order_id'], unique=False)
    op.create_index('ix_order_status_history_changed_at', 'order_status_history', ['changed_at'], unique=False)
    op.create_index('ix_orders_priority', 'orders', ['priority'], unique=False)
    op.create_index('ix_orders_status_priority', 'orders', ['status', 'priority'], unique=False)
    op.create_index('ix_orders_estimated_delivery_time', 'orders', ['estimated_delivery_time'], unique=False)
    op.create_index('ix_orders_courier_assigned', 'orders', ['courier_assigned'], unique=False)


def downgrade() -> None:
    """Remove order status management features."""

    # Drop indexes
    op.drop_index('ix_orders_courier_assigned', table_name='orders')
    op.drop_index('ix_orders_estimated_delivery_time', table_name='orders')
    op.drop_index('ix_orders_status_priority', table_name='orders')
    op.drop_index('ix_orders_priority', table_name='orders')
    op.drop_index('ix_order_status_history_changed_at', table_name='order_status_history')
    op.drop_index('ix_order_status_history_order_id', table_name='order_status_history')

    # Drop order status history table
    op.drop_table('order_status_history')

    # Remove enhanced fields from orders table
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_orders_cancelled_by_user_id', type_='foreignkey')

        # Remove all new columns
        batch_op.drop_column('workflow_metadata')
        batch_op.drop_column('automation_flags')
        batch_op.drop_column('total_duration')
        batch_op.drop_column('preparation_duration')
        batch_op.drop_column('refund_reason')
        batch_op.drop_column('refund_amount')
        batch_op.drop_column('cancelled_by_user_id')
        batch_op.drop_column('cancellation_reason')
        batch_op.drop_column('courier_assigned')
        batch_op.drop_column('delivery_instructions')
        batch_op.drop_column('delivery_type')
        batch_op.drop_column('requires_special_handling')
        batch_op.drop_column('kitchen_notes')
        batch_op.drop_column('status_cancelled_at')
        batch_op.drop_column('status_completed_at')
        batch_op.drop_column('status_ready_at')
        batch_op.drop_column('status_preparing_at')
        batch_op.drop_column('status_confirmed_at')
        batch_op.drop_column('status_pending_at')
        batch_op.drop_column('delivery_completed_at')
        batch_op.drop_column('delivery_scheduled_at')
        batch_op.drop_column('actual_preparation_end')
        batch_op.drop_column('actual_preparation_start')
        batch_op.drop_column('estimated_delivery_time')
        batch_op.drop_column('estimated_preparation_time')
        batch_op.drop_column('priority')

    # Drop order priority enum
    order_priority_enum = sa.Enum('LOW', 'NORMAL', 'HIGH', 'VIP', name='orderpriority')
    order_priority_enum.drop(op.get_bind())

    # Note: We don't remove the enum values from orderstatus as they might be in use
    # Manual cleanup may be required if needed