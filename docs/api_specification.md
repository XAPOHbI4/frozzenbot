# FrozenFoodBot API Specification

## Base URL
`http://localhost:8000`

## Products API

### Get All Products
```http
GET /api/products/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Плов с говядиной",
    "description": "Ароматный плов с нежной говядиной и специями.",
    "price": 450.0,
    "formatted_price": "450₽",
    "image_url": "https://example.com/images/plov.jpg",
    "weight": 400,
    "formatted_weight": "400г",
    "category": {
      "id": 1,
      "name": "Готовые блюда"
    }
  }
]
```

### Get Product by ID
```http
GET /api/products/{product_id}
```

### Get Products by Category
```http
GET /api/products/category/{category_id}
```

## Categories API

### Get All Categories
```http
GET /api/categories/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Готовые блюда",
    "description": "Замороженные готовые блюда высокого качества"
  }
]
```

## Business Logic

### Cart Rules
- Minimum order amount: **1500₽**
- Currency: **RUB (₽)**

### Available Products (Test Data)
1. Плов с говядиной - 450₽
2. Паста Болоньезе - 380₽
3. Лазанья мясная - 520₽
4. Гуляш с картофелем - 420₽
5. Курица в сливочном соусе - 390₽
6. Рагу овощное с мясом - 360₽
7. Бефстроганов - 480₽
8. Солянка мясная - 350₽

### WebApp Integration
- Bot token: `7933395395:AAHjSgRfqeFXZC0h89JY3NA11sy6mpOML10`
- WebApp URL will be provided by Frontend team
- Telegram WebApp API validation required