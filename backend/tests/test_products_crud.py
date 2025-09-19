#!/usr/bin/env python3
"""
Test suite for Products CRUD API (BE-005)
Tests all endpoints for the FrozenBot Products CRUD API
"""

import asyncio
import json
import aiohttp
import pytest
from typing import Dict, Any, List, Optional

# Test configuration
BASE_URL = "http://localhost:8000/api/products"
HEADERS = {"Content-Type": "application/json"}

class ProductsCRUDTester:
    """Test class for Products CRUD API functionality."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.created_products: List[int] = []  # Track created products for cleanup

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup created products
        await self.cleanup_created_products()
        if self.session:
            await self.session.close()

    async def cleanup_created_products(self):
        """Clean up products created during testing."""
        for product_id in self.created_products:
            try:
                await self.delete_product(product_id, hard_delete=True)
            except Exception as e:
                print(f"Warning: Failed to cleanup product {product_id}: {e}")
        self.created_products.clear()

    # Helper methods
    def get_sample_product_data(self, name_suffix: str = "") -> Dict[str, Any]:
        """Get sample product data for testing."""
        return {
            "name": f"Test Product {name_suffix}",
            "description": f"Test product description {name_suffix}",
            "price": 100.50,
            "discount_price": 85.0,
            "is_active": True,
            "in_stock": True,
            "weight": 500,
            "sort_order": 1,
            "category_id": 1,
            "slug": f"test-product-{name_suffix.lower().replace(' ', '-')}",
            "meta_title": f"Test Product {name_suffix} - Buy Online",
            "meta_description": f"High quality test product {name_suffix}",
            "sku": f"TEST{name_suffix.upper()}001",
            "stock_quantity": 100,
            "min_stock_level": 10,
            "is_featured": True,
            "calories_per_100g": 250,
            "protein_per_100g": 12.5,
            "fat_per_100g": 8.0,
            "carbs_per_100g": 35.0
        }

    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        async with self.session.post(
            self.base_url,
            json=product_data,
            headers=HEADERS
        ) as response:
            if response.status == 201:
                result = await response.json()
                self.created_products.append(result["id"])
                return result
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create product: {response.status} - {error_text}")

    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get product by ID."""
        async with self.session.get(f"{self.base_url}/{product_id}") as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get product: {response.status} - {error_text}")

    async def update_product(self, product_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update product."""
        async with self.session.put(
            f"{self.base_url}/{product_id}",
            json=update_data,
            headers=HEADERS
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to update product: {response.status} - {error_text}")

    async def delete_product(self, product_id: int, hard_delete: bool = False) -> bool:
        """Delete product."""
        url = f"{self.base_url}/{product_id}"
        if hard_delete:
            url += "?hard_delete=true"

        async with self.session.delete(url) as response:
            if response.status == 204:
                if product_id in self.created_products:
                    self.created_products.remove(product_id)
                return True
            else:
                error_text = await response.text()
                raise Exception(f"Failed to delete product: {response.status} - {error_text}")

    async def get_products_list(self, **params) -> Dict[str, Any]:
        """Get products list with optional parameters."""
        query_params = {k: v for k, v in params.items() if v is not None}
        async with self.session.get(self.base_url, params=query_params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get products list: {response.status} - {error_text}")

    async def search_products(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search products."""
        async with self.session.get(
            f"{self.base_url}/search",
            params={"q": query, "limit": limit}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to search products: {response.status} - {error_text}")

    async def bulk_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform bulk operation."""
        async with self.session.post(
            f"{self.base_url}/bulk",
            json=operation_data,
            headers=HEADERS
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to perform bulk operation: {response.status} - {error_text}")

    # Test methods
    async def test_create_product(self) -> bool:
        """Test product creation."""
        print("🧪 Testing product creation...")

        product_data = self.get_sample_product_data("Create Test")
        product = await self.create_product(product_data)

        # Verify created product
        assert product["name"] == product_data["name"]
        assert product["price"] == product_data["price"]
        assert product["discount_price"] == product_data["discount_price"]
        assert product["sku"] == product_data["sku"]
        assert product["slug"] == product_data["slug"]
        assert product["is_featured"] == product_data["is_featured"]
        assert product["stock_quantity"] == product_data["stock_quantity"]

        print(f"✅ Product created successfully with ID: {product['id']}")
        return True

    async def test_get_product(self) -> bool:
        """Test getting product by ID."""
        print("🧪 Testing get product by ID...")

        # Create a test product first
        product_data = self.get_sample_product_data("Get Test")
        created_product = await self.create_product(product_data)

        # Get the product
        retrieved_product = await self.get_product(created_product["id"])

        # Verify retrieved product
        assert retrieved_product["id"] == created_product["id"]
        assert retrieved_product["name"] == product_data["name"]
        assert retrieved_product["price"] == product_data["price"]

        print(f"✅ Product retrieved successfully: {retrieved_product['name']}")
        return True

    async def test_update_product(self) -> bool:
        """Test product update."""
        print("🧪 Testing product update...")

        # Create a test product first
        product_data = self.get_sample_product_data("Update Test")
        created_product = await self.create_product(product_data)

        # Update the product
        update_data = {
            "name": "Updated Test Product",
            "price": 150.75,
            "discount_price": 120.0,
            "is_featured": False
        }
        updated_product = await self.update_product(created_product["id"], update_data)

        # Verify updates
        assert updated_product["name"] == update_data["name"]
        assert updated_product["price"] == update_data["price"]
        assert updated_product["discount_price"] == update_data["discount_price"]
        assert updated_product["is_featured"] == update_data["is_featured"]

        print(f"✅ Product updated successfully: {updated_product['name']}")
        return True

    async def test_delete_product(self) -> bool:
        """Test product deletion."""
        print("🧪 Testing product deletion...")

        # Create a test product first
        product_data = self.get_sample_product_data("Delete Test")
        created_product = await self.create_product(product_data)

        # Delete the product
        success = await self.delete_product(created_product["id"])
        assert success

        # Verify product is deleted (should return 404)
        try:
            await self.get_product(created_product["id"])
            assert False, "Product should not be found after deletion"
        except Exception as e:
            assert "404" in str(e)

        print("✅ Product deleted successfully")
        return True

    async def test_products_list_pagination(self) -> bool:
        """Test products list with pagination."""
        print("🧪 Testing products list pagination...")

        # Create multiple test products
        created_ids = []
        for i in range(5):
            product_data = self.get_sample_product_data(f"Pagination {i}")
            product = await self.create_product(product_data)
            created_ids.append(product["id"])

        # Test pagination
        page1 = await self.get_products_list(page=1, per_page=2)
        assert len(page1["items"]) <= 2
        assert page1["page"] == 1
        assert page1["per_page"] == 2

        # Test page 2 if there are more items
        if page1["pages"] > 1:
            page2 = await self.get_products_list(page=2, per_page=2)
            assert page2["page"] == 2

        print("✅ Pagination tested successfully")
        return True

    async def test_products_filtering(self) -> bool:
        """Test products filtering."""
        print("🧪 Testing products filtering...")

        # Create test products with different attributes
        featured_product = self.get_sample_product_data("Featured")
        featured_product["is_featured"] = True
        created_featured = await self.create_product(featured_product)

        regular_product = self.get_sample_product_data("Regular")
        regular_product["is_featured"] = False
        created_regular = await self.create_product(regular_product)

        # Test featured filter
        featured_results = await self.get_products_list(is_featured=True)
        featured_ids = [p["id"] for p in featured_results["items"]]
        assert created_featured["id"] in featured_ids

        # Test price filter
        price_results = await self.get_products_list(min_price=100, max_price=200)
        assert len(price_results["items"]) >= 2

        print("✅ Filtering tested successfully")
        return True

    async def test_products_sorting(self) -> bool:
        """Test products sorting."""
        print("🧪 Testing products sorting...")

        # Create products with different prices
        products_data = []
        for i, price in enumerate([50.0, 150.0, 100.0]):
            product_data = self.get_sample_product_data(f"Sort {i}")
            product_data["price"] = price
            product = await self.create_product(product_data)
            products_data.append((product["id"], price))

        # Test sorting by price ascending
        sorted_asc = await self.get_products_list(sort_by="price", sort_order="asc")
        prices = [p["price"] for p in sorted_asc["items"]]
        assert prices == sorted(prices), f"Prices not sorted ascending: {prices}"

        # Test sorting by price descending
        sorted_desc = await self.get_products_list(sort_by="price", sort_order="desc")
        prices_desc = [p["price"] for p in sorted_desc["items"]]
        assert prices_desc == sorted(prices_desc, reverse=True), f"Prices not sorted descending: {prices_desc}"

        print("✅ Sorting tested successfully")
        return True

    async def test_search_products(self) -> bool:
        """Test products search."""
        print("🧪 Testing products search...")

        # Create searchable products
        search_product = self.get_sample_product_data("Searchable Broccoli")
        search_product["description"] = "Fresh frozen broccoli from our farm"
        created_product = await self.create_product(search_product)

        # Test search by name
        search_results = await self.search_products("Broccoli")
        found_ids = [p["id"] for p in search_results]
        assert created_product["id"] in found_ids

        # Test search by description
        desc_results = await self.search_products("frozen")
        found_ids_desc = [p["id"] for p in desc_results]
        assert created_product["id"] in found_ids_desc

        print("✅ Search tested successfully")
        return True

    async def test_bulk_operations(self) -> bool:
        """Test bulk operations."""
        print("🧪 Testing bulk operations...")

        # Create multiple products for bulk operations
        product_ids = []
        for i in range(3):
            product_data = self.get_sample_product_data(f"Bulk {i}")
            product = await self.create_product(product_data)
            product_ids.append(product["id"])

        # Test bulk deactivate
        bulk_data = {
            "product_ids": product_ids,
            "operation": "deactivate"
        }
        result = await self.bulk_operation(bulk_data)
        assert result["successful"] == len(product_ids)
        assert result["failed"] == 0

        # Verify products are deactivated
        for product_id in product_ids:
            product = await self.get_product(product_id)
            assert product["is_active"] == False

        # Test bulk activate
        bulk_data["operation"] = "activate"
        result = await self.bulk_operation(bulk_data)
        assert result["successful"] == len(product_ids)

        print("✅ Bulk operations tested successfully")
        return True

    async def test_product_statistics(self) -> bool:
        """Test product statistics endpoint."""
        print("🧪 Testing product statistics...")

        # Get statistics
        async with self.session.get(f"{self.base_url}/stats") as response:
            if response.status == 200:
                stats = await response.json()

                # Verify statistics structure
                required_fields = [
                    "total_products", "active_products", "inactive_products",
                    "in_stock", "out_of_stock", "featured", "on_sale"
                ]

                for field in required_fields:
                    assert field in stats
                    assert isinstance(stats[field], int)

                print(f"✅ Statistics retrieved successfully: {stats}")
                return True
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get statistics: {response.status} - {error_text}")

    async def test_special_endpoints(self) -> bool:
        """Test special endpoints (featured, sale, etc.)."""
        print("🧪 Testing special endpoints...")

        # Create a featured product
        featured_data = self.get_sample_product_data("Featured Special")
        featured_data["is_featured"] = True
        featured_product = await self.create_product(featured_data)

        # Create a sale product
        sale_data = self.get_sample_product_data("Sale Special")
        sale_data["price"] = 100.0
        sale_data["discount_price"] = 80.0
        sale_product = await self.create_product(sale_data)

        # Test featured products endpoint
        async with self.session.get(f"{self.base_url}/featured") as response:
            if response.status == 200:
                featured_products = await response.json()
                featured_ids = [p["id"] for p in featured_products]
                assert featured_product["id"] in featured_ids
            else:
                raise Exception(f"Failed to get featured products: {response.status}")

        # Test sale products endpoint
        async with self.session.get(f"{self.base_url}/sale") as response:
            if response.status == 200:
                sale_products = await response.json()
                sale_ids = [p["id"] for p in sale_products]
                assert sale_product["id"] in sale_ids
            else:
                raise Exception(f"Failed to get sale products: {response.status}")

        print("✅ Special endpoints tested successfully")
        return True

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        tests = [
            ("Create Product", self.test_create_product),
            ("Get Product", self.test_get_product),
            ("Update Product", self.test_update_product),
            ("Delete Product", self.test_delete_product),
            ("Products List Pagination", self.test_products_list_pagination),
            ("Products Filtering", self.test_products_filtering),
            ("Products Sorting", self.test_products_sorting),
            ("Search Products", self.test_search_products),
            ("Bulk Operations", self.test_bulk_operations),
            ("Product Statistics", self.test_product_statistics),
            ("Special Endpoints", self.test_special_endpoints)
        ]

        results = {}
        total_tests = len(tests)
        passed_tests = 0

        print(f"\n🚀 Starting Products CRUD API Test Suite ({total_tests} tests)")
        print("=" * 60)

        for test_name, test_method in tests:
            try:
                print(f"\n📋 Running: {test_name}")
                result = await test_method()
                results[test_name] = result
                if result:
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                results[test_name] = False
                print(f"❌ {test_name}: FAILED - {str(e)}")

        print("\n" + "=" * 60)
        print(f"🏁 Test Results: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Products CRUD API is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the implementation.")

        return results


async def main():
    """Main test runner."""
    print("🧪 Products CRUD API Test Suite")
    print("Testing BE-005: Products CRUD API for FrozenBot")
    print("=" * 60)

    try:
        async with ProductsCRUDTester() as tester:
            results = await tester.run_all_tests()

            # Print detailed results
            print("\n📊 Detailed Test Results:")
            for test_name, result in results.items():
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"  - {test_name}: {status}")

    except Exception as e:
        print(f"❌ Test suite failed to run: {e}")
        return False

    return True


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())