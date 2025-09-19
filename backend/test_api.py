#!/usr/bin/env python3
"""Simple API test script without database."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="FrozenFood Test API",
    description="Test API for frozen food delivery bot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test data
test_products = [
    {
        "id": 1,
        "name": "Замороженные ягоды (микс)",
        "description": "Смесь замороженных ягод: клубника, малина, черника",
        "price": 450.0,
        "formatted_price": "450 ₽",
        "weight": 500,
        "category_id": 1,
        "is_active": True
    },
    {
        "id": 2,
        "name": "Замороженная брокколи",
        "description": "Свежезамороженная брокколи, 400г",
        "price": 320.0,
        "formatted_price": "320 ₽",
        "weight": 400,
        "category_id": 2,
        "is_active": True
    },
    {
        "id": 3,
        "name": "Пельмени домашние",
        "description": "Пельмени ручной лепки с говядиной",
        "price": 680.0,
        "formatted_price": "680 ₽",
        "weight": 800,
        "category_id": 3,
        "is_active": True
    }
]

test_categories = [
    {
        "id": 1,
        "name": "Ягоды и фрукты",
        "description": "Замороженные ягоды и фрукты",
        "is_active": True
    },
    {
        "id": 2,
        "name": "Овощи",
        "description": "Замороженные овощи",
        "is_active": True
    },
    {
        "id": 3,
        "name": "Готовые блюда",
        "description": "Замороженные готовые блюда",
        "is_active": True
    }
]

@app.get("/")
async def root():
    return {"message": "FrozenFood Test API is running"}

@app.get("/api/products/")
async def get_products():
    return {"products": test_products}

@app.get("/api/categories/")
async def get_categories():
    return {"categories": test_categories}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is working"}

if __name__ == "__main__":
    print("Starting Test API server...")
    print("API available at: http://localhost:8000")
    print("Products: http://localhost:8000/api/products/")
    print("Categories: http://localhost:8000/api/categories/")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )