"""Product category model."""

from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship

from .base import BaseModel


class Category(BaseModel):
    """Product category model."""
    __tablename__ = "categories"

    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    products = relationship("Product", back_populates="category")

    def __str__(self) -> str:
        return f"Category(name={self.name})"