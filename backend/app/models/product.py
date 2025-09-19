"""Product model."""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class Product(BaseModel):
    """Product model."""
    __tablename__ = "products"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, index=True)
    discount_price = Column(Float, nullable=True, comment="Discounted price if applicable")
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    in_stock = Column(Boolean, default=True, nullable=False, index=True)
    weight = Column(Integer, nullable=True, comment="Weight in grams")
    sort_order = Column(Integer, default=0, nullable=False)

    # SEO fields
    slug = Column(String(255), nullable=True, unique=True, index=True, comment="SEO-friendly URL slug")
    meta_title = Column(String(255), nullable=True, comment="SEO meta title")
    meta_description = Column(Text, nullable=True, comment="SEO meta description")

    # Additional product attributes
    sku = Column(String(100), nullable=True, unique=True, index=True, comment="Stock Keeping Unit")
    stock_quantity = Column(Integer, default=0, nullable=False, comment="Available stock quantity")
    min_stock_level = Column(Integer, default=0, nullable=False, comment="Minimum stock level")
    popularity_score = Column(Integer, default=0, nullable=False, comment="Product popularity for sorting")
    is_featured = Column(Boolean, default=False, nullable=False, comment="Featured product flag")

    # Nutritional information
    calories_per_100g = Column(Integer, nullable=True, comment="Calories per 100 grams")
    protein_per_100g = Column(Float, nullable=True, comment="Protein per 100 grams")
    fat_per_100g = Column(Float, nullable=True, comment="Fat per 100 grams")
    carbs_per_100g = Column(Float, nullable=True, comment="Carbohydrates per 100 grams")

    # Foreign Keys
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)

    # Relationships
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    # Database indexes for performance
    __table_args__ = (
        Index('ix_product_category_active', 'category_id', 'is_active'),
        Index('ix_product_stock_active', 'in_stock', 'is_active'),
        Index('ix_product_featured_active', 'is_featured', 'is_active'),
        Index('ix_product_popularity_order', 'popularity_score', 'sort_order'),
    )

    def __str__(self) -> str:
        return f"Product(name={self.name}, price={self.price})"

    @property
    def formatted_price(self) -> str:
        """Get formatted price with currency."""
        return f"{int(self.price)}₽"

    @property
    def formatted_discount_price(self) -> str:
        """Get formatted discount price with currency."""
        if self.discount_price:
            return f"{int(self.discount_price)}₽"
        return ""

    @property
    def effective_price(self) -> float:
        """Get effective price (discount price if available, otherwise regular price)."""
        return self.discount_price if self.discount_price else self.price

    @property
    def formatted_effective_price(self) -> str:
        """Get formatted effective price with currency."""
        return f"{int(self.effective_price)}₽"

    @property
    def discount_percentage(self) -> int:
        """Get discount percentage if discount is active."""
        if self.discount_price and self.discount_price < self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def formatted_weight(self) -> str:
        """Get formatted weight."""
        if self.weight:
            if self.weight >= 1000:
                return f"{self.weight // 1000}кг"
            return f"{self.weight}г"
        return ""

    @property
    def is_on_sale(self) -> bool:
        """Check if product is on sale."""
        return bool(self.discount_price and self.discount_price < self.price)

    @property
    def stock_status(self) -> str:
        """Get stock status string."""
        if not self.in_stock:
            return "out_of_stock"
        elif self.stock_quantity <= self.min_stock_level:
            return "low_stock"
        return "in_stock"

    @property
    def is_low_stock(self) -> bool:
        """Check if product has low stock."""
        return self.stock_quantity <= self.min_stock_level

    def generate_slug(self) -> str:
        """Generate SEO-friendly slug from product name."""
        import re
        import unicodedata

        # Normalize unicode characters
        slug = unicodedata.normalize('NFKD', self.name)
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug

    def update_slug(self):
        """Update slug if not set."""
        if not self.slug:
            self.slug = self.generate_slug()