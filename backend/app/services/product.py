"""Product service."""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, or_, and_, desc, asc
from sqlalchemy.orm import selectinload
from math import ceil

from app.database import get_async_session
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import (
    ProductCreateRequest, ProductUpdateRequest, ProductFilters,
    ProductSort, ProductSortBy, SortOrder, PaginationParams,
    BulkOperationRequest, BulkOperationType, BulkOperationResult,
    StockStatus
)


class ProductService:
    """Product service for managing products."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def _get_session(self):
        """Get database session."""
        if self.db:
            yield self.db
        else:
            async for session in get_async_session():
                yield session

    def _build_filters_query(self, query, filters: ProductFilters):
        """Build query with filters."""
        # Always exclude soft-deleted items
        query = query.where(Product.is_deleted == False)

        if filters.category_id is not None:
            query = query.where(Product.category_id == filters.category_id)

        if filters.is_active is not None:
            query = query.where(Product.is_active == filters.is_active)

        if filters.in_stock is not None:
            query = query.where(Product.in_stock == filters.in_stock)

        if filters.is_featured is not None:
            query = query.where(Product.is_featured == filters.is_featured)

        if filters.is_on_sale is not None:
            if filters.is_on_sale:
                query = query.where(
                    and_(
                        Product.discount_price.is_not(None),
                        Product.discount_price < Product.price
                    )
                )
            else:
                query = query.where(
                    or_(
                        Product.discount_price.is_(None),
                        Product.discount_price >= Product.price
                    )
                )

        if filters.stock_status != StockStatus.ALL:
            if filters.stock_status == StockStatus.IN_STOCK:
                query = query.where(Product.in_stock == True)
            elif filters.stock_status == StockStatus.LOW_STOCK:
                query = query.where(
                    and_(
                        Product.in_stock == True,
                        Product.stock_quantity <= Product.min_stock_level
                    )
                )
            elif filters.stock_status == StockStatus.OUT_OF_STOCK:
                query = query.where(Product.in_stock == False)

        if filters.min_price is not None:
            # Consider discount price if available
            query = query.where(
                or_(
                    and_(
                        Product.discount_price.is_not(None),
                        Product.discount_price >= filters.min_price
                    ),
                    and_(
                        Product.discount_price.is_(None),
                        Product.price >= filters.min_price
                    )
                )
            )

        if filters.max_price is not None:
            # Consider discount price if available
            query = query.where(
                or_(
                    and_(
                        Product.discount_price.is_not(None),
                        Product.discount_price <= filters.max_price
                    ),
                    and_(
                        Product.discount_price.is_(None),
                        Product.price <= filters.max_price
                    )
                )
            )

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            )

        return query

    def _build_sort_query(self, query, sort: ProductSort):
        """Build query with sorting."""
        sort_column = Product.sort_order  # default

        if sort.sort_by == ProductSortBy.NAME:
            sort_column = Product.name
        elif sort.sort_by == ProductSortBy.PRICE:
            # Use effective price (discount price if available, otherwise regular price)
            sort_column = func.coalesce(Product.discount_price, Product.price)
        elif sort.sort_by == ProductSortBy.CREATED_AT:
            sort_column = Product.created_at
        elif sort.sort_by == ProductSortBy.UPDATED_AT:
            sort_column = Product.updated_at
        elif sort.sort_by == ProductSortBy.POPULARITY:
            sort_column = Product.popularity_score
        elif sort.sort_by == ProductSortBy.SORT_ORDER:
            sort_column = Product.sort_order

        if sort.sort_order == SortOrder.DESC:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return query

    async def get_products_count(self, filters: Optional[ProductFilters] = None) -> int:
        """Get total products count with optional filters."""
        if not filters:
            filters = ProductFilters()

        async for db in self._get_session():
            query = select(func.count(Product.id))
            query = self._build_filters_query(query, filters)

            result = await db.execute(query)
            return result.scalar() or 0

    async def get_products(
        self,
        filters: Optional[ProductFilters] = None,
        sort: Optional[ProductSort] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[Product], int]:
        """
        Get products with filtering, sorting and pagination.

        Returns:
            Tuple of (products_list, total_count)
        """
        if not filters:
            filters = ProductFilters()
        if not sort:
            sort = ProductSort()
        if not pagination:
            pagination = PaginationParams()

        async for db in self._get_session():
            # Build base query
            query = select(Product).options(selectinload(Product.category))

            # Apply filters
            query = self._build_filters_query(query, filters)

            # Get total count before pagination
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0

            # Apply sorting
            query = self._build_sort_query(query, sort)

            # Apply pagination
            query = query.offset(pagination.skip).limit(pagination.limit)

            # Execute query
            result = await db.execute(query)
            products = result.scalars().all()

            return products, total_count

    async def get_product_by_id(self, product_id: int, include_inactive: bool = False) -> Optional[Product]:
        """Get product by ID."""
        async for db in self._get_session():
            query = select(Product).options(selectinload(Product.category)).where(Product.id == product_id)

            if not include_inactive:
                query = query.where(Product.is_deleted == False)

            result = await db.execute(query)
            return result.scalar_one_or_none()

    async def get_product_by_slug(self, slug: str) -> Optional[Product]:
        """Get product by slug."""
        async for db in self._get_session():
            result = await db.execute(
                select(Product)
                .options(selectinload(Product.category))
                .where(
                    Product.slug == slug,
                    Product.is_deleted == False,
                    Product.is_active == True
                )
            )
            return result.scalar_one_or_none()

    async def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        async for db in self._get_session():
            result = await db.execute(
                select(Product)
                .options(selectinload(Product.category))
                .where(Product.sku == sku.upper(), Product.is_deleted == False)
            )
            return result.scalar_one_or_none()

    async def create_product(self, product_data: ProductCreateRequest) -> Product:
        """Create new product."""
        async for db in self._get_session():
            # Convert schema to dict
            product_dict = product_data.dict(exclude_unset=True)

            # Create product instance
            product = Product(**product_dict)

            # Generate slug if not provided
            if not product.slug:
                product.update_slug()

            # Ensure unique slug
            if product.slug:
                existing = await self.get_product_by_slug(product.slug)
                if existing:
                    product.slug = f"{product.slug}-{product.id or ''}"

            # Ensure unique SKU
            if product.sku:
                existing = await self.get_product_by_sku(product.sku)
                if existing:
                    raise ValueError(f"Product with SKU '{product.sku}' already exists")

            db.add(product)
            await db.commit()
            await db.refresh(product)

            # Load category relationship
            await db.refresh(product, ['category'])

            return product

    async def update_product(self, product_id: int, product_data: ProductUpdateRequest) -> Optional[Product]:
        """Update existing product."""
        async for db in self._get_session():
            # Get existing product
            product = await self.get_product_by_id(product_id, include_inactive=True)
            if not product:
                return None

            # Update fields
            update_data = product_data.dict(exclude_unset=True)

            # Handle slug update
            if 'name' in update_data and not update_data.get('slug'):
                # Auto-generate slug from new name
                old_name = product.name
                product.name = update_data['name']
                product.update_slug()
                update_data['slug'] = product.slug
                product.name = old_name  # Restore old name temporarily

            # Check unique constraints
            if 'slug' in update_data and update_data['slug']:
                existing = await self.get_product_by_slug(update_data['slug'])
                if existing and existing.id != product_id:
                    raise ValueError(f"Product with slug '{update_data['slug']}' already exists")

            if 'sku' in update_data and update_data['sku']:
                existing = await self.get_product_by_sku(update_data['sku'])
                if existing and existing.id != product_id:
                    raise ValueError(f"Product with SKU '{update_data['sku']}' already exists")

            # Apply updates
            for field, value in update_data.items():
                setattr(product, field, value)

            await db.commit()
            await db.refresh(product)

            # Load category relationship
            await db.refresh(product, ['category'])

            return product

    async def delete_product(self, product_id: int, soft_delete: bool = True) -> bool:
        """Delete product (soft delete by default)."""
        async for db in self._get_session():
            if soft_delete:
                # Soft delete
                result = await db.execute(
                    update(Product)
                    .where(Product.id == product_id)
                    .values(is_deleted=True, is_active=False)
                )
                await db.commit()
                return result.rowcount > 0
            else:
                # Hard delete
                result = await db.execute(
                    delete(Product).where(Product.id == product_id)
                )
                await db.commit()
                return result.rowcount > 0

    async def search_products(self, search_term: str, limit: int = 50) -> List[Product]:
        """Search products by term."""
        filters = ProductFilters(search=search_term, is_active=True)
        sort = ProductSort(sort_by=ProductSortBy.POPULARITY, sort_order=SortOrder.DESC)
        pagination = PaginationParams(page=1, per_page=limit)

        products, _ = await self.get_products(filters, sort, pagination)
        return products

    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products."""
        filters = ProductFilters(is_featured=True, is_active=True)
        sort = ProductSort(sort_by=ProductSortBy.POPULARITY, sort_order=SortOrder.DESC)
        pagination = PaginationParams(page=1, per_page=limit)

        products, _ = await self.get_products(filters, sort, pagination)
        return products

    async def get_on_sale_products(self, limit: int = 20) -> List[Product]:
        """Get products on sale."""
        filters = ProductFilters(is_on_sale=True, is_active=True)
        sort = ProductSort(sort_by=ProductSortBy.POPULARITY, sort_order=SortOrder.DESC)
        pagination = PaginationParams(page=1, per_page=limit)

        products, _ = await self.get_products(filters, sort, pagination)
        return products

    async def bulk_operation(self, request: BulkOperationRequest) -> BulkOperationResult:
        """Perform bulk operations on products."""
        async for db in self._get_session():
            result = BulkOperationResult(
                operation=request.operation,
                total_products=len(request.product_ids),
                successful=0,
                failed=0,
                errors=[],
                updated_product_ids=[]
            )

            for product_id in request.product_ids:
                try:
                    if request.operation == BulkOperationType.DELETE:
                        success = await self.delete_product(product_id, soft_delete=True)
                    elif request.operation == BulkOperationType.ACTIVATE:
                        await db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(is_active=True)
                        )
                        success = True
                    elif request.operation == BulkOperationType.DEACTIVATE:
                        await db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(is_active=False)
                        )
                        success = True
                    elif request.operation == BulkOperationType.SET_IN_STOCK:
                        await db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(in_stock=True)
                        )
                        success = True
                    elif request.operation == BulkOperationType.SET_OUT_OF_STOCK:
                        await db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(in_stock=False)
                        )
                        success = True
                    elif request.operation == BulkOperationType.SET_FEATURED:
                        await db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(is_featured=True)
                        )
                        success = True
                    elif request.operation == BulkOperationType.UNSET_FEATURED:
                        await db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(is_featured=False)
                        )
                        success = True
                    elif request.operation == BulkOperationType.UPDATE_CATEGORY:
                        await db.execute(
                            update(Product)
                            .where(Product.id == product_id)
                            .values(category_id=request.category_id)
                        )
                        success = True
                    elif request.operation == BulkOperationType.UPDATE_PRICES:
                        if request.price_multiplier:
                            await db.execute(
                                update(Product)
                                .where(Product.id == product_id)
                                .values(
                                    price=Product.price * request.price_multiplier,
                                    discount_price=(
                                        Product.discount_price * request.price_multiplier
                                        if Product.discount_price.is_not(None)
                                        else None
                                    )
                                )
                            )
                        elif request.discount_percentage:
                            discount_multiplier = 1 - (request.discount_percentage / 100)
                            await db.execute(
                                update(Product)
                                .where(Product.id == product_id)
                                .values(discount_price=Product.price * discount_multiplier)
                            )
                        success = True
                    else:
                        success = False
                        result.errors.append(f"Unknown operation: {request.operation}")

                    if success:
                        result.successful += 1
                        result.updated_product_ids.append(product_id)
                    else:
                        result.failed += 1

                except Exception as e:
                    result.failed += 1
                    result.errors.append(f"Product {product_id}: {str(e)}")

            await db.commit()
            return result

    async def update_popularity_score(self, product_id: int, increment: int = 1) -> bool:
        """Update product popularity score."""
        async for db in self._get_session():
            result = await db.execute(
                update(Product)
                .where(Product.id == product_id)
                .values(popularity_score=Product.popularity_score + increment)
            )
            await db.commit()
            return result.rowcount > 0

    # Legacy methods for backward compatibility
    async def get_all_products(self) -> List[Product]:
        """Get all active products (legacy method)."""
        filters = ProductFilters(is_active=True)
        products, _ = await self.get_products(filters)
        return products

    async def get_products_by_category(self, category_id: int) -> List[Product]:
        """Get products by category (legacy method)."""
        filters = ProductFilters(category_id=category_id, is_active=True)
        products, _ = await self.get_products(filters)
        return products