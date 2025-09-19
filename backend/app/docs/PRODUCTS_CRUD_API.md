# Products CRUD API Documentation (BE-005)

## Overview

This document describes the complete Products CRUD API implementation for FrozenBot. The API provides comprehensive product management functionality including creation, reading, updating, deletion, search, filtering, sorting, and bulk operations.

## Base URL

```
/api/products
```

## Authentication

Currently, all endpoints are public. In production, consider adding authentication for admin operations.

## Data Models

### Product Model

```python
{
    "id": int,
    "name": str,
    "description": str | null,
    "price": float,
    "discount_price": float | null,
    "formatted_price": str,
    "formatted_discount_price": str,
    "effective_price": float,
    "formatted_effective_price": str,
    "discount_percentage": int,
    "is_on_sale": bool,
    "image_url": str | null,
    "is_active": bool,
    "in_stock": bool,
    "weight": int | null,
    "formatted_weight": str,
    "sort_order": int,
    "category_id": int | null,
    "category": CategoryResponse | null,

    # SEO fields
    "slug": str | null,
    "meta_title": str | null,
    "meta_description": str | null,

    # Additional attributes
    "sku": str | null,
    "stock_quantity": int,
    "min_stock_level": int,
    "popularity_score": int,
    "is_featured": bool,
    "stock_status": str,  # "in_stock", "low_stock", "out_of_stock"
    "is_low_stock": bool,

    # Nutritional information
    "calories_per_100g": int | null,
    "protein_per_100g": float | null,
    "fat_per_100g": float | null,
    "carbs_per_100g": float | null,

    "created_at": datetime,
    "updated_at": datetime
}
```

## API Endpoints

### 1. List Products with Filtering, Sorting, and Pagination

**GET** `/api/products`

Get a paginated list of products with optional filtering and sorting.

#### Query Parameters

**Filtering:**
- `category_id` (int, optional): Filter by category ID
- `is_active` (bool, optional): Filter by active status
- `in_stock` (bool, optional): Filter by stock availability
- `is_featured` (bool, optional): Filter by featured status
- `is_on_sale` (bool, optional): Filter by sale status
- `stock_status` (enum, optional): Filter by stock status (`all`, `in_stock`, `low_stock`, `out_of_stock`)
- `min_price` (float, optional): Minimum price filter
- `max_price` (float, optional): Maximum price filter
- `search` (str, optional): Search in name, description, and SKU

**Sorting:**
- `sort_by` (enum): Field to sort by (`name`, `price`, `created_at`, `updated_at`, `popularity_score`, `sort_order`)
- `sort_order` (enum): Sort order (`asc`, `desc`)

**Pagination:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

#### Response

```json
{
    "items": [ProductResponse],
    "total": 150,
    "page": 1,
    "pages": 8,
    "per_page": 20
}
```

#### Examples

```bash
# Get first page of active products
GET /api/products?is_active=true&page=1&per_page=10

# Get featured products on sale
GET /api/products?is_featured=true&is_on_sale=true

# Search for products
GET /api/products?search=брокколи&sort_by=price&sort_order=asc

# Get products in price range
GET /api/products?min_price=50&max_price=200&sort_by=popularity_score&sort_order=desc
```

### 2. Create Product

**POST** `/api/products`

Create a new product.

#### Request Body

```json
{
    "name": "Брокколи замороженная премиум",
    "description": "Свежая замороженная брокколи высшего качества",
    "price": 180.0,
    "discount_price": 150.0,
    "image_url": "https://example.com/broccoli.jpg",
    "is_active": true,
    "in_stock": true,
    "weight": 500,
    "sort_order": 1,
    "category_id": 1,
    "slug": "broccoli-premium",
    "meta_title": "Брокколи замороженная премиум - купить в FrozenBot",
    "meta_description": "Высококачественная замороженная брокколи с доставкой",
    "sku": "BROC001",
    "stock_quantity": 100,
    "min_stock_level": 10,
    "is_featured": true,
    "calories_per_100g": 34,
    "protein_per_100g": 2.8,
    "fat_per_100g": 0.4,
    "carbs_per_100g": 7.0
}
```

#### Response

```json
{
    "id": 123,
    // ... full product object
}
```

**Status Codes:**
- `201`: Product created successfully
- `400`: Validation error
- `500`: Server error

### 3. Get Product by ID

**GET** `/api/products/{product_id}`

Get detailed information about a specific product.

#### Parameters
- `product_id` (int): Product ID

#### Response

```json
{
    "id": 123,
    "name": "Брокколи замороженная премиум",
    // ... full product object
}
```

**Status Codes:**
- `200`: Product found
- `404`: Product not found

### 4. Update Product

**PUT** `/api/products/{product_id}`

Update an existing product. All fields are optional.

#### Parameters
- `product_id` (int): Product ID

#### Request Body

```json
{
    "name": "Updated Product Name",
    "price": 200.0,
    "discount_price": 180.0,
    "is_featured": false
    // ... any other fields to update
}
```

#### Response

```json
{
    "id": 123,
    // ... updated product object
}
```

**Status Codes:**
- `200`: Product updated successfully
- `400`: Validation error
- `404`: Product not found
- `500`: Server error

### 5. Delete Product

**DELETE** `/api/products/{product_id}`

Delete a product (soft delete by default).

#### Parameters
- `product_id` (int): Product ID

#### Query Parameters
- `hard_delete` (bool, optional): Perform hard delete instead of soft delete (default: false)

**Status Codes:**
- `204`: Product deleted successfully
- `404`: Product not found

### 6. Get Product by Slug

**GET** `/api/products/slug/{slug}`

Get product by SEO-friendly slug.

#### Parameters
- `slug` (str): Product slug

#### Response

Same as Get Product by ID

### 7. Get Product by SKU

**GET** `/api/products/sku/{sku}`

Get product by Stock Keeping Unit.

#### Parameters
- `sku` (str): Product SKU

#### Response

Same as Get Product by ID

### 8. Search Products

**GET** `/api/products/search`

Search products by term.

#### Query Parameters
- `q` (str, required): Search query
- `limit` (int, optional): Maximum results (default: 50, max: 100)

#### Response

```json
[
    {
        "id": 123,
        "name": "Брокколи замороженная",
        // ... product objects
    }
]
```

### 9. Get Featured Products

**GET** `/api/products/featured`

Get featured products.

#### Query Parameters
- `limit` (int, optional): Maximum results (default: 10, max: 50)

#### Response

Array of product objects.

### 10. Get Products on Sale

**GET** `/api/products/sale`

Get products currently on sale.

#### Query Parameters
- `limit` (int, optional): Maximum results (default: 20, max: 100)

#### Response

Array of product objects.

### 11. Bulk Operations

**POST** `/api/products/bulk`

Perform bulk operations on multiple products.

#### Request Body

```json
{
    "product_ids": [123, 124, 125],
    "operation": "activate",
    // Optional parameters based on operation
    "category_id": 2,  // for update_category
    "price_multiplier": 1.1,  // for update_prices
    "discount_percentage": 15  // for update_prices
}
```

#### Operations
- `delete`: Soft delete products
- `activate`: Activate products
- `deactivate`: Deactivate products
- `set_in_stock`: Mark as in stock
- `set_out_of_stock`: Mark as out of stock
- `set_featured`: Mark as featured
- `unset_featured`: Remove featured status
- `update_category`: Change category
- `update_prices`: Update prices (requires price_multiplier or discount_percentage)

#### Response

```json
{
    "operation": "activate",
    "total_products": 3,
    "successful": 3,
    "failed": 0,
    "errors": [],
    "updated_product_ids": [123, 124, 125]
}
```

### 12. Upload Product Image

**POST** `/api/products/{product_id}/upload-image`

Upload an image for a product.

#### Parameters
- `product_id` (int): Product ID

#### Request Body (multipart/form-data)
- `file`: Image file (jpg, jpeg, png, webp, gif)
- `create_thumbnails` (bool, optional): Create thumbnail versions (default: true)

#### Response

```json
{
    "message": "Image uploaded successfully",
    "images": {
        "original": "http://localhost:8000/uploads/products/product_123_abc123.jpg",
        "small": "http://localhost:8000/uploads/products/product_123_abc123_small.jpg",
        "medium": "http://localhost:8000/uploads/products/product_123_abc123_medium.jpg",
        "large": "http://localhost:8000/uploads/products/product_123_abc123_large.jpg",
        "file_size": 245760
    }
}
```

**Status Codes:**
- `200`: Image uploaded successfully
- `400`: Invalid file format or size
- `404`: Product not found
- `500`: Upload failed

### 13. Delete Product Image

**DELETE** `/api/products/{product_id}/image`

Delete all images associated with a product.

#### Parameters
- `product_id` (int): Product ID

#### Response

```json
{
    "message": "Image deleted successfully"
}
```

### 14. Get Product Statistics

**GET** `/api/products/stats`

Get product statistics.

#### Response

```json
{
    "total_products": 150,
    "active_products": 140,
    "inactive_products": 10,
    "in_stock": 130,
    "out_of_stock": 20,
    "featured": 25,
    "on_sale": 40
}
```

### 15. Get Products by Category (Legacy)

**GET** `/api/products/category/{category_id}`

Legacy endpoint for backward compatibility.

#### Parameters
- `category_id` (int): Category ID

#### Response

Array of product objects from specified category.

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

```json
{
    "detail": "Product not found"
}
```

Common error codes:
- `400`: Bad Request (validation errors)
- `404`: Not Found
- `422`: Unprocessable Entity (Pydantic validation)
- `500`: Internal Server Error

## Validation Rules

### Product Creation/Update
- `name`: Required, 1-255 characters
- `price`: Required, > 0, < 100000
- `discount_price`: Optional, > 0, < price
- `slug`: Optional, lowercase letters, numbers, and hyphens only
- `sku`: Optional, min 3 characters, automatically uppercased
- `weight`: Optional, > 0 (in grams)
- `stock_quantity`: >= 0
- `min_stock_level`: >= 0
- `image_url`: Optional, must start with http:// or https://

### File Upload
- Supported formats: JPG, JPEG, PNG, WEBP, GIF
- Max file size: 10MB
- Max dimensions: 2048x2048 pixels
- Automatic optimization and thumbnail generation

## Database Indexes

The following indexes are created for optimal performance:
- `slug` (unique)
- `sku` (unique)
- `price`
- `is_active`
- `in_stock`
- `category_id`
- Composite indexes for common filter combinations

## Rate Limiting

Consider implementing rate limiting in production:
- Search endpoints: 100 requests/minute
- Create/Update operations: 60 requests/minute
- Image upload: 10 requests/minute

## Testing

Use the provided test suite to verify API functionality:

```bash
python tests/test_products_crud.py
```

The test suite covers:
- CRUD operations
- Filtering and sorting
- Search functionality
- Bulk operations
- Image upload
- Error handling
- Edge cases

## Migration

To apply the new database schema:

```bash
# Apply migration
alembic upgrade head

# Or run specific migration
alembic upgrade extended_product_fields
```

## Performance Considerations

1. **Database Indexes**: All frequently queried fields are indexed
2. **Pagination**: Always use pagination for large datasets
3. **Image Optimization**: Images are automatically optimized and resized
4. **Caching**: Consider implementing Redis caching for frequently accessed products
5. **Database Connection Pooling**: Use connection pooling in production

## Security Considerations

1. **Input Validation**: All inputs are validated using Pydantic
2. **File Upload Security**: File types and sizes are strictly validated
3. **SQL Injection**: Protected by SQLAlchemy ORM
4. **Authentication**: Add authentication for admin operations in production
5. **Rate Limiting**: Implement rate limiting to prevent abuse

## Monitoring and Logging

1. **API Metrics**: Track response times and error rates
2. **Database Performance**: Monitor slow queries
3. **Storage Usage**: Monitor image storage space
4. **Error Logging**: Log all errors with stack traces
5. **Audit Trail**: Log all product modifications

## Future Enhancements

1. **Product Variants**: Support for product variants (size, color, etc.)
2. **Inventory Management**: Advanced stock tracking
3. **Product Reviews**: Customer reviews and ratings
4. **Product Recommendations**: AI-powered recommendations
5. **Multi-language Support**: Internationalization
6. **Product Analytics**: Detailed analytics dashboard
7. **Import/Export**: Bulk CSV import/export functionality