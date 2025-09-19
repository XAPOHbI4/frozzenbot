"""Seed database with test data."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.category import Category
from app.models.product import Product


async def seed_database():
    """Seed database with test products."""
    async with AsyncSessionLocal() as db:
        # Create category
        category = Category(
            name="Готовые блюда",
            description="Замороженные готовые блюда высокого качества",
            is_active=True,
            sort_order=1
        )
        db.add(category)
        await db.flush()  # Get category ID

        # Test products data
        products_data = [
            {
                "name": "Плов с говядиной",
                "description": "Ароматный плов с нежной говядиной и специями. Готов к употреблению за 5 минут.",
                "price": 450.0,
                "weight": 400,
                "image_url": "https://example.com/images/plov.jpg"
            },
            {
                "name": "Паста Болоньезе",
                "description": "Классическая паста с мясным соусом болоньезе. Идеально для быстрого ужина.",
                "price": 380.0,
                "weight": 350,
                "image_url": "https://example.com/images/pasta.jpg"
            },
            {
                "name": "Лазанья мясная",
                "description": "Многослойная лазанья с мясным фаршем, сыром и соусом бешамель.",
                "price": 520.0,
                "weight": 450,
                "image_url": "https://example.com/images/lasagna.jpg"
            },
            {
                "name": "Гуляш с картофелем",
                "description": "Сытный гуляш из говядины с молодым картофелем и овощами.",
                "price": 420.0,
                "weight": 400,
                "image_url": "https://example.com/images/goulash.jpg"
            },
            {
                "name": "Курица в сливочном соусе",
                "description": "Нежная курица в ароматном сливочном соусе с травами.",
                "price": 390.0,
                "weight": 350,
                "image_url": "https://example.com/images/chicken.jpg"
            },
            {
                "name": "Рагу овощное с мясом",
                "description": "Домашнее рагу с сезонными овощами и кусочками мяса.",
                "price": 360.0,
                "weight": 380,
                "image_url": "https://example.com/images/ragu.jpg"
            },
            {
                "name": "Бефстроганов",
                "description": "Классический бефстроганов с грибами в сметанном соусе.",
                "price": 480.0,
                "weight": 400,
                "image_url": "https://example.com/images/beef.jpg"
            },
            {
                "name": "Солянка мясная",
                "description": "Густая солянка с копченостями, колбасой и солеными огурцами.",
                "price": 350.0,
                "weight": 400,
                "image_url": "https://example.com/images/solyanka.jpg"
            }
        ]

        # Create products
        for i, product_data in enumerate(products_data, 1):
            product = Product(
                category_id=category.id,
                sort_order=i,
                is_active=True,
                in_stock=True,
                **product_data
            )
            db.add(product)

        await db.commit()
        print(f"✅ Created {len(products_data)} test products in category '{category.name}'")


if __name__ == "__main__":
    print("🌱 Seeding database with test data...")
    asyncio.run(seed_database())
    print("✅ Database seeding completed!")