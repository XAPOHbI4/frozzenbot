# FrozenBot API Documentation

Welcome to the FrozenBot API documentation. This API powers the frozen food delivery system, serving three main clients: Telegram Bot, Admin Panel, and Telegram WebApp.

## Quick Links

- [OpenAPI Specification](./openapi.yaml) - Complete API specification
- [Authentication Guide](./authentication.md) - Authentication methods and implementation
- [Error Standards](./error-standards.md) - Error handling and response formats
- [TypeScript Types](./types.ts) - TypeScript type definitions

## Overview

FrozenBot is a comprehensive frozen food delivery system built with:
- **Backend**: FastAPI (Python) - http://localhost:8000
- **Admin Panel**: React - http://localhost:3000
- **WebApp**: Telegram WebApp - http://localhost:8080
- **Bot**: Telegram Bot for customer interactions

## Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://api.frozenbot.com`

## Authentication

The API supports multiple authentication methods:

1. **JWT Tokens** - For admin panel (`Authorization: Bearer <token>`)
2. **Telegram WebApp** - For user interactions (`X-Telegram-Init-Data: <initData>`)
3. **Bot Token** - For internal operations (not public)

See [Authentication Guide](./authentication.md) for detailed implementation.

## API Endpoints Overview

### Authentication
- `POST /auth/login` - Admin login
- `POST /auth/refresh` - Refresh JWT token

### Users
- `GET /api/users/me` - Get current user
- `POST /api/users/` - Register Telegram user
- `GET /api/users/{telegram_id}` - Get user by Telegram ID

### Products & Categories
- `GET /api/products/` - List products (with pagination, filters)
- `GET /api/products/{id}` - Get product details
- `POST /api/products/` - Create product (admin)
- `PUT /api/products/{id}` - Update product (admin)
- `DELETE /api/products/{id}` - Delete product (admin)
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category (admin)
- `PUT /api/categories/{id}` - Update category (admin)
- `DELETE /api/categories/{id}` - Delete category (admin)

### Shopping Cart
- `GET /api/cart/{telegram_id}` - Get user cart
- `POST /api/cart/items` - Add item to cart
- `PUT /api/cart/items/{id}` - Update cart item
- `DELETE /api/cart/items/{id}` - Remove cart item

### Orders
- `GET /api/orders/` - List orders
- `GET /api/orders/{id}` - Get order details
- `POST /api/orders/` - Create order
- `PUT /api/orders/{id}/status` - Update order status (admin)

### Admin & Analytics
- `GET /api/admin/dashboard/stats` - Dashboard statistics
- `GET /api/admin/orders/stats` - Order analytics
- `GET /api/admin/products/stats` - Product analytics

### Notifications
- `POST /api/notifications/send` - Send notification (admin)

### Payments
- `POST /api/payments/webhook` - Payment webhook
- `GET /api/payments/{order_id}/status` - Payment status

## Request/Response Format

All requests and responses use JSON format with `Content-Type: application/json`.

### Standard Response Structure

**Success Response:**
```json
{
  "id": 1,
  "name": "Брокколи замороженная",
  "price": 150.0,
  "formatted_price": "150₽",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Paginated Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "pages": 8,
  "per_page": 20
}
```

**Error Response:**
```json
{
  "error": "not_found",
  "message": "Product not found",
  "details": {
    "product_id": 123
  }
}
```

## Common Query Parameters

### Pagination
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 100)

### Filtering
- `search` - Search term
- `category_id` - Filter by category
- `is_active` - Filter by active status
- `in_stock` - Filter by stock availability

### Sorting
- `sort_by` - Field to sort by
- `sort_order` - `asc` or `desc`

## HTTP Status Codes

- `200` - OK
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

## Rate Limiting

API endpoints are rate limited:
- Admin endpoints: 100 requests/minute
- User endpoints: 60 requests/minute
- Public endpoints: 30 requests/minute

Rate limit headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642678800
```

## Example Usage

### Admin Panel Integration

```typescript
// Login and get JWT token
const auth = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'password' })
});
const { access_token } = await auth.json();

// Get dashboard stats
const stats = await fetch('/api/admin/dashboard/stats', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const dashboardData = await stats.json();

// Create new product
const product = await fetch('/api/products/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Новый продукт',
    price: 200.0,
    category_id: 1
  })
});
```

### Telegram WebApp Integration

```typescript
// Get initData from Telegram WebApp
const initData = window.Telegram.WebApp.initData;

// Get user's cart
const cart = await fetch('/api/cart/123456789', {
  headers: { 'X-Telegram-Init-Data': initData }
});
const cartData = await cart.json();

// Add item to cart
const addItem = await fetch('/api/cart/items', {
  method: 'POST',
  headers: {
    'X-Telegram-Init-Data': initData,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    telegram_id: 123456789,
    product_id: 1,
    quantity: 2
  })
});

// Create order
const order = await fetch('/api/orders/', {
  method: 'POST',
  headers: {
    'X-Telegram-Init-Data': initData,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    telegram_id: 123456789,
    customer_name: 'Иван Иванов',
    customer_phone: '+7900123456',
    delivery_address: 'ул. Пушкина, д. 1'
  })
});
```

### Bot Integration

```python
# Get products for bot menu
async def get_products_for_bot():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/products/",
            params={"is_active": True, "in_stock": True}
        )
        return response.json()

# Create user from Telegram data
async def register_telegram_user(telegram_user):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/users/",
            json={
                "telegram_id": telegram_user.id,
                "username": telegram_user.username,
                "first_name": telegram_user.first_name,
                "last_name": telegram_user.last_name
            }
        )
        return response.json()
```

## Data Models

### User
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_admin": false,
  "is_active": true,
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Product
```json
{
  "id": 1,
  "name": "Брокколи замороженная",
  "description": "Свежая замороженная брокколи",
  "price": 150.0,
  "formatted_price": "150₽",
  "image_url": "https://example.com/broccoli.jpg",
  "is_active": true,
  "in_stock": true,
  "weight": 500,
  "formatted_weight": "500г",
  "sort_order": 0,
  "category_id": 1,
  "category": {
    "id": 1,
    "name": "Замороженные овощи"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Order
```json
{
  "id": 1,
  "user_id": 1,
  "status": "pending",
  "status_display": "Ожидает подтверждения",
  "total_amount": 450.0,
  "formatted_total": "450₽",
  "customer_name": "Иван Иванов",
  "customer_phone": "+7900123456",
  "delivery_address": "ул. Пушкина, д. 1",
  "notes": "Позвонить за 10 минут",
  "payment_method": "card",
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "quantity": 2,
      "price": 150.0,
      "total_price": 300.0,
      "product": {...}
    }
  ],
  "user": {...},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Order Statuses

- `pending` - Ожидает подтверждения
- `confirmed` - Подтвержден
- `preparing` - Готовится
- `ready` - Готов к выдаче
- `completed` - Выполнен
- `cancelled` - Отменен

## Payment Methods

- `card` - Банковская карта
- `cash` - Наличные
- `transfer` - Перевод

## Business Rules

### Order Processing
1. Minimum order amount: 1500₽ (configurable)
2. Cart expires after 24 hours of inactivity
3. Orders can only be cancelled in `pending` or `confirmed` status
4. Payment verification required for card payments

### Product Management
- Products must belong to a category
- Weight should be specified in grams
- Images must be valid URLs (HTTPS recommended)
- Soft delete for products with existing orders

### User Management
- Users auto-registered on first Telegram interaction
- Admin users can access admin endpoints
- Inactive users cannot place orders

## Webhook Events

### Payment Webhooks
The API accepts payment webhooks at `POST /api/payments/webhook`:

```json
{
  "order_id": 1,
  "status": "success",
  "amount": 450.0,
  "transaction_id": "txn_123456789",
  "payment_method": "card"
}
```

## Testing

### Development Environment
- API: http://localhost:8000
- Admin Panel: http://localhost:3000
- WebApp: http://localhost:8080
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Test Data
The development environment includes test data:
- Admin user: username=`admin`, password=`admin123`
- Sample products and categories
- Test Telegram users

### API Testing Tools

**Postman Collection:** Import the OpenAPI spec into Postman for interactive testing.

**curl Examples:**
```bash
# Get products
curl http://localhost:8000/api/products/

# Admin login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Create product (admin)
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": 100.0}'
```

## Error Handling

See [Error Standards](./error-standards.md) for comprehensive error handling guide.

## Support

For API support and questions:
- Documentation: This README and linked guides
- OpenAPI Spec: [openapi.yaml](./openapi.yaml)
- Issues: Report via project issue tracker
- Contact: API team

## Changelog

### v1.0.0 (Current)
- Initial API release
- JWT and Telegram WebApp authentication
- Complete CRUD operations for products, categories, orders
- Admin analytics endpoints
- Payment webhook support
- Rate limiting and security features

---

*This documentation is auto-generated from the OpenAPI specification. For the most up-to-date API details, refer to the [OpenAPI spec](./openapi.yaml).*