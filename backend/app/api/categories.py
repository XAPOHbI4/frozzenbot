"""Categories API endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.models.category import Category

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_categories(db: AsyncSession = Depends(get_async_session)):
    """Get all categories."""
    result = await db.execute(
        select(Category)
        .where(Category.is_deleted == False, Category.is_active == True)
        .order_by(Category.sort_order, Category.name)
    )
    categories = result.scalars().all()

    return [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description
        }
        for category in categories
    ]