"""Base Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CreateSchema(BaseModel):
    """Base schema for create operations."""
    model_config = ConfigDict(from_attributes=True)


class UpdateSchema(BaseModel):
    """Base schema for update operations."""
    model_config = ConfigDict(from_attributes=True)