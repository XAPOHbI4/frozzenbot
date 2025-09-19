"""Add extended product fields

Revision ID: extended_product_fields
Revises: add_payments_table
Create Date: 2024-09-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'extended_product_fields'
down_revision = 'add_payments_table'
branch_labels = None
depends_on = None


def upgrade():
    """Add extended product fields."""

    # Add new columns to products table
    op.add_column('products', sa.Column('discount_price', sa.Float(), nullable=True, comment='Discounted price if applicable'))
    op.add_column('products', sa.Column('slug', sa.String(255), nullable=True, comment='SEO-friendly URL slug'))
    op.add_column('products', sa.Column('meta_title', sa.String(255), nullable=True, comment='SEO meta title'))
    op.add_column('products', sa.Column('meta_description', sa.Text(), nullable=True, comment='SEO meta description'))
    op.add_column('products', sa.Column('sku', sa.String(100), nullable=True, comment='Stock Keeping Unit'))
    op.add_column('products', sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0', comment='Available stock quantity'))
    op.add_column('products', sa.Column('min_stock_level', sa.Integer(), nullable=False, server_default='0', comment='Minimum stock level'))
    op.add_column('products', sa.Column('popularity_score', sa.Integer(), nullable=False, server_default='0', comment='Product popularity for sorting'))
    op.add_column('products', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false', comment='Featured product flag'))
    op.add_column('products', sa.Column('calories_per_100g', sa.Integer(), nullable=True, comment='Calories per 100 grams'))
    op.add_column('products', sa.Column('protein_per_100g', sa.Float(), nullable=True, comment='Protein per 100 grams'))
    op.add_column('products', sa.Column('fat_per_100g', sa.Float(), nullable=True, comment='Fat per 100 grams'))
    op.add_column('products', sa.Column('carbs_per_100g', sa.Float(), nullable=True, comment='Carbohydrates per 100 grams'))

    # Create indexes for better performance
    op.create_index('ix_products_slug', 'products', ['slug'], unique=True)
    op.create_index('ix_products_sku', 'products', ['sku'], unique=True)
    op.create_index('ix_products_price', 'products', ['price'])
    op.create_index('ix_products_is_active', 'products', ['is_active'])
    op.create_index('ix_products_in_stock', 'products', ['in_stock'])
    op.create_index('ix_products_category_id', 'products', ['category_id'])

    # Create composite indexes
    op.create_index('ix_product_category_active', 'products', ['category_id', 'is_active'])
    op.create_index('ix_product_stock_active', 'products', ['in_stock', 'is_active'])
    op.create_index('ix_product_featured_active', 'products', ['is_featured', 'is_active'])
    op.create_index('ix_product_popularity_order', 'products', ['popularity_score', 'sort_order'])


def downgrade():
    """Remove extended product fields."""

    # Drop indexes
    op.drop_index('ix_product_popularity_order', 'products')
    op.drop_index('ix_product_featured_active', 'products')
    op.drop_index('ix_product_stock_active', 'products')
    op.drop_index('ix_product_category_active', 'products')
    op.drop_index('ix_products_category_id', 'products')
    op.drop_index('ix_products_in_stock', 'products')
    op.drop_index('ix_products_is_active', 'products')
    op.drop_index('ix_products_price', 'products')
    op.drop_index('ix_products_sku', 'products')
    op.drop_index('ix_products_slug', 'products')

    # Remove columns
    op.drop_column('products', 'carbs_per_100g')
    op.drop_column('products', 'fat_per_100g')
    op.drop_column('products', 'protein_per_100g')
    op.drop_column('products', 'calories_per_100g')
    op.drop_column('products', 'is_featured')
    op.drop_column('products', 'popularity_score')
    op.drop_column('products', 'min_stock_level')
    op.drop_column('products', 'stock_quantity')
    op.drop_column('products', 'sku')
    op.drop_column('products', 'meta_description')
    op.drop_column('products', 'meta_title')
    op.drop_column('products', 'slug')
    op.drop_column('products', 'discount_price')