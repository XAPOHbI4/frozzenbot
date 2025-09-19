"""Products API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil

from app.database import get_async_session
from app.services.product import ProductService
from app.models.product import Product
from app.schemas.product import (
    ProductResponse, ProductCreateRequest, ProductUpdateRequest,
    ProductListResponse, ProductFilters, ProductSort, PaginationParams,
    BulkOperationRequest, BulkOperationResult,
    ProductSortBy, SortOrder, StockStatus
)
from app.utils.image import ImageUploadService
from app.middleware.auth import require_manager_or_admin, get_current_user, api_rate_limit
from app.models.user import User

router = APIRouter()


# GET /products - List products with filtering, sorting, and pagination
@router.get("/", response_model=ProductListResponse)
async def get_products(
    # Filtering parameters
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    is_on_sale: Optional[bool] = Query(None, description="Filter by sale status"),
    stock_status: Optional[StockStatus] = Query(StockStatus.ALL, description="Filter by stock status"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    search: Optional[str] = Query(None, max_length=255, description="Search in name, description, SKU"),

    # Sorting parameters
    sort_by: ProductSortBy = Query(ProductSortBy.SORT_ORDER, description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.ASC, description="Sort order"),

    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),

    db: AsyncSession = Depends(get_async_session)
):
    """Get products with filtering, sorting, and pagination."""
    service = ProductService(db)

    # Build filters
    filters = ProductFilters(
        category_id=category_id,
        is_active=is_active,
        in_stock=in_stock,
        is_featured=is_featured,
        is_on_sale=is_on_sale,
        stock_status=stock_status,
        min_price=min_price,
        max_price=max_price,
        search=search
    )

    # Build sort
    sort = ProductSort(sort_by=sort_by, sort_order=sort_order)

    # Build pagination
    pagination = PaginationParams(page=page, per_page=per_page)

    # Get products
    products, total_count = await service.get_products(filters, sort, pagination)

    # Convert to response models
    product_responses = [ProductResponse.from_orm(product) for product in products]

    return ProductListResponse(
        items=product_responses,
        total=total_count,
        page=page,
        pages=ceil(total_count / per_page) if total_count > 0 else 1,
        per_page=per_page
    )


# POST /products - Create new product
@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreateRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """Create new product."""
    service = ProductService(db)

    try:
        product = await service.create_product(product_data)
        return ProductResponse.from_orm(product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")


# GET /products/{product_id} - Get product by ID
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get product by ID."""
    service = ProductService(db)
    product = await service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update popularity score when viewing product
    await service.update_popularity_score(product_id)

    return ProductResponse.from_orm(product)


# PUT /products/{product_id} - Update product
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdateRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """Update existing product."""
    service = ProductService(db)

    try:
        product = await service.update_product(product_id, product_data)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return ProductResponse.from_orm(product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


# DELETE /products/{product_id} - Delete product (soft delete)
@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete product."""
    service = ProductService(db)

    success = await service.delete_product(product_id, soft_delete=not hard_delete)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")


# GET /products/slug/{slug} - Get product by slug
@router.get("/slug/{slug}", response_model=ProductResponse)
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get product by slug."""
    service = ProductService(db)
    product = await service.get_product_by_slug(slug)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update popularity score when viewing product
    await service.update_popularity_score(product.id)

    return ProductResponse.from_orm(product)


# GET /products/sku/{sku} - Get product by SKU
@router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get product by SKU."""
    service = ProductService(db)
    product = await service.get_product_by_sku(sku)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse.from_orm(product)


# GET /products/search - Search products
@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_async_session)
):
    """Search products."""
    service = ProductService(db)
    products = await service.search_products(q, limit)

    return [ProductResponse.from_orm(product) for product in products]


# GET /products/featured - Get featured products
@router.get("/featured", response_model=List[ProductResponse])
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get featured products."""
    service = ProductService(db)
    products = await service.get_featured_products(limit)

    return [ProductResponse.from_orm(product) for product in products]


# GET /products/sale - Get products on sale
@router.get("/sale", response_model=List[ProductResponse])
async def get_on_sale_products(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get products on sale."""
    service = ProductService(db)
    products = await service.get_on_sale_products(limit)

    return [ProductResponse.from_orm(product) for product in products]


# POST /products/bulk - Bulk operations
@router.post("/bulk", response_model=BulkOperationResult)
async def bulk_operation(
    request: BulkOperationRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """Perform bulk operations on products."""
    service = ProductService(db)

    try:
        result = await service.bulk_operation(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")


# POST /products/{product_id}/upload-image - Upload product image
@router.post("/{product_id}/upload-image")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    create_thumbnails: bool = Form(True),
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """Upload product image."""
    # Check if product exists
    service = ProductService(db)
    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Upload image
    image_service = ImageUploadService()
    try:
        result = await image_service.upload_product_image(
            product_id=product_id,
            file=file,
            create_thumbnails=create_thumbnails
        )

        # Update product with new image URL
        from app.schemas.product import ProductUpdateRequest
        update_data = ProductUpdateRequest(image_url=result['original'])
        await service.update_product(product_id, update_data)

        return {
            "message": "Image uploaded successfully",
            "images": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


# DELETE /products/{product_id}/image - Delete product image
@router.delete("/{product_id}/image")
async def delete_product_image(
    product_id: int,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete product image."""
    # Check if product exists
    service = ProductService(db)
    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete image files
    image_service = ImageUploadService()
    try:
        await image_service.delete_product_image(product_id)

        # Update product to remove image URL
        from app.schemas.product import ProductUpdateRequest
        update_data = ProductUpdateRequest(image_url=None)
        await service.update_product(product_id, update_data)

        return {"message": "Image deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")


# GET /products/stats - Get product statistics
@router.get("/stats")
async def get_product_stats(
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    """Get product statistics."""
    service = ProductService(db)

    try:
        # Get various counts
        total_products = await service.get_products_count()
        active_products = await service.get_products_count(ProductFilters(is_active=True))
        inactive_products = await service.get_products_count(ProductFilters(is_active=False))
        in_stock = await service.get_products_count(ProductFilters(in_stock=True))
        out_of_stock = await service.get_products_count(ProductFilters(in_stock=False))
        featured = await service.get_products_count(ProductFilters(is_featured=True))
        on_sale = await service.get_products_count(ProductFilters(is_on_sale=True))

        return {
            "total_products": total_products,
            "active_products": active_products,
            "inactive_products": inactive_products,
            "in_stock": in_stock,
            "out_of_stock": out_of_stock,
            "featured": featured,
            "on_sale": on_sale
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# Legacy endpoint for backward compatibility
@router.get("/category/{category_id}", response_model=List[ProductResponse])
async def get_products_by_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get products by category (legacy endpoint)."""
    service = ProductService(db)
    products = await service.get_products_by_category(category_id)

    return [ProductResponse.from_orm(product) for product in products]