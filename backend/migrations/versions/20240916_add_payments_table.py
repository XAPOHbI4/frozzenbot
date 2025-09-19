"""Add payments table

Revision ID: 20240916_add_payments
Revises:
Create Date: 2024-09-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20240916_add_payments'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create payments table and related enums."""

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED', name='paymentstatus'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False, comment='Payment amount in rubles'),
        sa.Column('payment_method', sa.Enum('TELEGRAM', 'CARD', 'CASH', name='paymentmethod'), nullable=False),
        sa.Column('telegram_payment_charge_id', sa.String(length=255), nullable=True, comment='Telegram payment charge ID'),
        sa.Column('provider_payment_charge_id', sa.String(length=255), nullable=True, comment='Provider payment charge ID'),
        sa.Column('transaction_id', sa.String(length=255), nullable=True, comment='External transaction ID'),
        sa.Column('provider_data', sa.JSON(), nullable=True, comment='Provider specific data'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if payment failed'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='Additional payment metadata'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )

    # Create index on order_id for performance
    op.create_index('ix_payments_order_id', 'payments', ['order_id'])

    # Create index on status for filtering
    op.create_index('ix_payments_status', 'payments', ['status'])

    # Create index on telegram_payment_charge_id for lookups
    op.create_index('ix_payments_telegram_charge_id', 'payments', ['telegram_payment_charge_id'])


def downgrade() -> None:
    """Drop payments table and related indexes."""

    # Drop indexes
    op.drop_index('ix_payments_telegram_charge_id', table_name='payments')
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_order_id', table_name='payments')

    # Drop table
    op.drop_table('payments')

    # Drop enums (they will be dropped automatically when the table is dropped)
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS paymentmethod")