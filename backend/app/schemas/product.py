"""Product schemas."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator
from .category import CategoryResponse


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class ProductSortBy(str, Enum):
    """Product sorting options."""
    NAME = "name"
    PRICE = "price"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    POPULARITY = "popularity_score"
    SORT_ORDER = "sort_order"


class StockStatus(str, Enum):
    """Stock status options."""
    ALL = "all"
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


class ProductFilters(BaseModel):
    """Product filtering parameters."""
    category_id: Optional[int] = Field(None, description="Filter by category ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    in_stock: Optional[bool] = Field(None, description="Filter by stock availability")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")
    is_on_sale: Optional[bool] = Field(None, description="Filter by sale status")
    stock_status: Optional[StockStatus] = Field(StockStatus.ALL, description="Filter by stock status")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    search: Optional[str] = Field(None, max_length=255, description="Search in name and description")

    @validator('max_price')
    def validate_price_range(cls, v, values):
        """Validate price range."""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('Maximum price must be greater than minimum price')
        return v


class ProductSort(BaseModel):
    """Product sorting parameters."""
    sort_by: ProductSortBy = Field(ProductSortBy.SORT_ORDER, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        """Calculate skip offset."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Get limit value."""
        return self.per_page


class BulkOperationType(str, Enum):
    """Bulk operation types."""
    DELETE = "delete"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    SET_IN_STOCK = "set_in_stock"
    SET_OUT_OF_STOCK = "set_out_of_stock"
    SET_FEATURED = "set_featured"
    UNSET_FEATURED = "unset_featured"
    UPDATE_CATEGORY = "update_category"
    UPDATE_PRICES = "update_prices"


class BulkOperationRequest(BaseModel):
    """Bulk operation request schema."""
    product_ids: List[int] = Field(..., min_items=1, description="List of product IDs")
    operation: BulkOperationType = Field(..., description="Operation type")

    # Optional parameters for specific operations
    category_id: Optional[int] = Field(None, description="New category ID (for update_category)")
    price_multiplier: Optional[float] = Field(None, gt=0, description="Price multiplier (for update_prices)")
    discount_percentage: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage (for update_prices)")

    @validator('price_multiplier')
    def validate_price_multiplier(cls, v, values):
        """Validate price multiplier for update_prices operation."""
        if values.get('operation') == BulkOperationType.UPDATE_PRICES and v is None:
            raise ValueError('Price multiplier is required for update_prices operation')
        return v


class BulkOperationResult(BaseModel):
    """Bulk operation result schema."""
    operation: BulkOperationType = Field(..., description="Operation type")
    total_products: int = Field(..., description="Total products requested")
    successful: int = Field(..., description="Successfully processed products")
    failed: int = Field(..., description="Failed to process products")
    errors: List[str] = Field(default=[], description="Error messages")
    updated_product_ids: List[int] = Field(default=[], description="IDs of successfully updated products")


class ProductCreateRequest(BaseModel):
    """Product creation request schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    price: float = Field(..., gt=0, description="Product price in rubles")
    discount_price: Optional[float] = Field(None, gt=0, description="Discounted price in rubles")
    image_url: Optional[str] = Field(None, max_length=500, description="Product image URL")
    is_active: bool = Field(True, description="Product active status")
    in_stock: bool = Field(True, description="Product stock availability")
    weight: Optional[int] = Field(None, gt=0, description="Product weight in grams")
    sort_order: int = Field(0, description="Sort order")
    category_id: Optional[int] = Field(None, description="Category ID")

    # SEO fields
    slug: Optional[str] = Field(None, max_length=255, description="SEO-friendly URL slug")
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")

    # Additional product attributes
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    stock_quantity: int = Field(0, ge=0, description="Available stock quantity")
    min_stock_level: int = Field(0, ge=0, description="Minimum stock level")
    is_featured: bool = Field(False, description="Featured product flag")

    # Nutritional information
    calories_per_100g: Optional[int] = Field(None, ge=0, description="Calories per 100 grams")
    protein_per_100g: Optional[float] = Field(None, ge=0, description="Protein per 100 grams")
    fat_per_100g: Optional[float] = Field(None, ge=0, description="Fat per 100 grams")
    carbs_per_100g: Optional[float] = Field(None, ge=0, description="Carbohydrates per 100 grams")

    @validator('price')
    def validate_price(cls, v):
        """Validate price is positive and reasonable."""
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        if v > 100000:
            raise ValueError('Price seems too high')
        return round(v, 2)

    @validator('discount_price')
    def validate_discount_price(cls, v, values):
        """Validate discount price is less than regular price."""
        if v is not None:
            if v <= 0:
                raise ValueError('Discount price must be greater than 0')
            if v > 100000:
                raise ValueError('Discount price seems too high')
            if 'price' in values and v >= values['price']:
                raise ValueError('Discount price must be less than regular price')
            return round(v, 2)
        return v

    @validator('image_url')
    def validate_image_url(cls, v):
        """Validate image URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Image URL must start with http:// or https://')
        return v

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        if v:
            import re
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v

    @validator('sku')
    def validate_sku(cls, v):
        """Validate SKU format."""
        if v:
            v = v.upper().strip()
            if len(v) < 3:
                raise ValueError('SKU must be at least 3 characters long')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Брокколи замороженная",
                "description": "Свежая замороженная брокколи высокого качества",
                "price": 150.0,
                "discount_price": 120.0,
                "image_url": "https://example.com/broccoli.jpg",
                "is_active": True,
                "in_stock": True,
                "weight": 500,
                "sort_order": 0,
                "category_id": 1,
                "slug": "broccoli-zamorozhennaya",
                "meta_title": "Брокколи замороженная - купить в FrozenBot",
                "meta_description": "Свежая замороженная брокколи высокого качества. Быстрая доставка.",
                "sku": "BROC001",
                "stock_quantity": 50,
                "min_stock_level": 5,
                "is_featured": False,
                "calories_per_100g": 34,
                "protein_per_100g": 2.8,
                "fat_per_100g": 0.4,
                "carbs_per_100g": 7.0
            }
        }


class ProductUpdateRequest(BaseModel):
    """Product update request schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    price: Optional[float] = Field(None, gt=0, description="Product price in rubles")
    discount_price: Optional[float] = Field(None, description="Discounted price in rubles")
    image_url: Optional[str] = Field(None, max_length=500, description="Product image URL")
    is_active: Optional[bool] = Field(None, description="Product active status")
    in_stock: Optional[bool] = Field(None, description="Product stock availability")
    weight: Optional[int] = Field(None, gt=0, description="Product weight in grams")
    sort_order: Optional[int] = Field(None, description="Sort order")
    category_id: Optional[int] = Field(None, description="Category ID")

    # SEO fields
    slug: Optional[str] = Field(None, max_length=255, description="SEO-friendly URL slug")
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")

    # Additional product attributes
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    min_stock_level: Optional[int] = Field(None, ge=0, description="Minimum stock level")
    is_featured: Optional[bool] = Field(None, description="Featured product flag")

    # Nutritional information
    calories_per_100g: Optional[int] = Field(None, ge=0, description="Calories per 100 grams")
    protein_per_100g: Optional[float] = Field(None, ge=0, description="Protein per 100 grams")
    fat_per_100g: Optional[float] = Field(None, ge=0, description="Fat per 100 grams")
    carbs_per_100g: Optional[float] = Field(None, ge=0, description="Carbohydrates per 100 grams")

    @validator('price')
    def validate_price(cls, v):
        """Validate price is positive and reasonable."""
        if v is not None:
            if v <= 0:
                raise ValueError('Price must be greater than 0')
            if v > 100000:
                raise ValueError('Price seems too high')
            return round(v, 2)
        return v

    @validator('discount_price')
    def validate_discount_price(cls, v):
        """Validate discount price is positive."""
        if v is not None:
            if v <= 0:
                raise ValueError('Discount price must be greater than 0')
            if v > 100000:
                raise ValueError('Discount price seems too high')
            return round(v, 2)
        return v

    @validator('image_url')
    def validate_image_url(cls, v):
        """Validate image URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Image URL must start with http:// or https://')
        return v

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        if v:
            import re
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v

    @validator('sku')
    def validate_sku(cls, v):
        """Validate SKU format."""
        if v:
            v = v.upper().strip()
            if len(v) < 3:
                raise ValueError('SKU must be at least 3 characters long')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Брокколи замороженная премиум",
                "description": "Свежая замороженная брокколи высшего качества",
                "price": 180.0,
                "image_url": "https://example.com/broccoli_premium.jpg",
                "is_active": True,
                "in_stock": True,
                "weight": 500,
                "sort_order": 1,
                "category_id": 1
            }
        }


class ProductResponse(BaseModel):
    """Product response schema."""
    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price in rubles")
    discount_price: Optional[float] = Field(None, description="Discounted price in rubles")
    formatted_price: str = Field(..., description="Formatted price with currency")
    formatted_discount_price: str = Field(..., description="Formatted discount price with currency")
    effective_price: float = Field(..., description="Effective price (discount if available)")
    formatted_effective_price: str = Field(..., description="Formatted effective price with currency")
    discount_percentage: int = Field(..., description="Discount percentage")
    is_on_sale: bool = Field(..., description="Whether product is on sale")
    image_url: Optional[str] = Field(None, description="Product image URL")
    is_active: bool = Field(..., description="Product active status")
    in_stock: bool = Field(..., description="Product stock availability")
    weight: Optional[int] = Field(None, description="Product weight in grams")
    formatted_weight: str = Field(..., description="Formatted weight")
    sort_order: int = Field(..., description="Sort order")
    category_id: Optional[int] = Field(None, description="Category ID")
    category: Optional[CategoryResponse] = Field(None, description="Product category")

    # SEO fields
    slug: Optional[str] = Field(None, description="SEO-friendly URL slug")
    meta_title: Optional[str] = Field(None, description="SEO meta title")
    meta_description: Optional[str] = Field(None, description="SEO meta description")

    # Additional product attributes
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    stock_quantity: int = Field(..., description="Available stock quantity")
    min_stock_level: int = Field(..., description="Minimum stock level")
    popularity_score: int = Field(..., description="Product popularity for sorting")
    is_featured: bool = Field(..., description="Featured product flag")
    stock_status: str = Field(..., description="Stock status (in_stock, low_stock, out_of_stock)")
    is_low_stock: bool = Field(..., description="Whether stock is low")

    # Nutritional information
    calories_per_100g: Optional[int] = Field(None, description="Calories per 100 grams")
    protein_per_100g: Optional[float] = Field(None, description="Protein per 100 grams")
    fat_per_100g: Optional[float] = Field(None, description="Fat per 100 grams")
    carbs_per_100g: Optional[float] = Field(None, description="Carbohydrates per 100 grams")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Брокколи замороженная",
                "description": "Свежая замороженная брокколи высокого качества",
                "price": 150.0,
                "formatted_price": "150₽",
                "image_url": "https://example.com/broccoli.jpg",
                "is_active": True,
                "in_stock": True,
                "weight": 500,
                "formatted_weight": "500г",
                "sort_order": 0,
                "category_id": 1,
                "category": {
                    "id": 1,
                    "name": "Замороженные овощи",
                    "description": "Свежие замороженные овощи высокого качества",
                    "image_url": "https://example.com/vegetables.jpg",
                    "is_active": True,
                    "sort_order": 0,
                    "products_count": 15,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ProductListResponse(BaseModel):
    """Paginated product list response schema."""
    items: list[ProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    per_page: int = Field(..., description="Items per page")

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "Брокколи замороженная",
                        "description": "Свежая замороженная брокколи высокого качества",
                        "price": 150.0,
                        "formatted_price": "150₽",
                        "image_url": "https://example.com/broccoli.jpg",
                        "is_active": True,
                        "in_stock": True,
                        "weight": 500,
                        "formatted_weight": "500г",
                        "sort_order": 0,
                        "category_id": 1,
                        "category": {
                            "id": 1,
                            "name": "Замороженные овощи",
                            "description": "Свежие замороженные овощи",
                            "image_url": "https://example.com/vegetables.jpg",
                            "is_active": True,
                            "sort_order": 0,
                            "products_count": 15,
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-01T00:00:00Z"
                        },
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 150,
                "page": 1,
                "pages": 8,
                "per_page": 20
            }
        }