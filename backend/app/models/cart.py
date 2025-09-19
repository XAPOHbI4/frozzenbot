"""Shopping cart models."""

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class Cart(BaseModel):
    """User shopping cart."""
    __tablename__ = "carts"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return f"Cart(user_id={self.user_id}, items_count={len(self.items)})"

    @property
    def total_amount(self) -> float:
        """Calculate total cart amount."""
        return sum(item.total_price for item in self.items if not item.is_deleted)

    @property
    def total_items(self) -> int:
        """Get total items count."""
        return sum(item.quantity for item in self.items if not item.is_deleted)

    def is_expired(self) -> bool:
        """Check if cart is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class CartItem(BaseModel):
    """Cart item."""
    __tablename__ = "cart_items"

    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")

    def __str__(self) -> str:
        return f"CartItem(product_id={self.product_id}, quantity={self.quantity})"

    @property
    def total_price(self) -> float:
        """Calculate total price for this item."""
        return self.product.price * self.quantity if self.product else 0