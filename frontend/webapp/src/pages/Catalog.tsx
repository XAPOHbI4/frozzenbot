/**
 * Product Catalog Page Component
 * FE-003 Implementation: Product catalog WebApp with categories
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Product, Category, LocalCart } from '../types';
import { WebAppApiClient, LocalCartManager } from '../services/apiClient';
import { useCatalog } from '../hooks/useCatalog';
import { ProductCard } from '../components/Product/ProductCard';
import { CategoryFilter } from '../components/Category/CategoryFilter';
import { CartSidebar } from '../components/Cart/CartSidebar';
import { setupTelegramWebApp, telegramHapticFeedback } from '../utils/telegram';
import './Catalog.css';

interface CatalogProps {
  apiClient: WebAppApiClient;
  cartManager: LocalCartManager;
  onNavigateToCheckout: () => void;
  className?: string;
}

export const Catalog: React.FC<CatalogProps> = ({
  apiClient,
  cartManager,
  onNavigateToCheckout,
  className = '',
}) => {
  const {
    products,
    categories,
    selectedCategoryId,
    loading,
    error,
    setSelectedCategory,
    loadProducts,
    loadCategories,
  } = useCatalog(apiClient);

  const [cart, setCart] = useState<LocalCart>(() => cartManager.getCart());
  const [showCart, setShowCart] = useState<boolean>(false);

  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = setupTelegramWebApp();
    if (tg) {
      // Set theme colors for catalog
      tg.setHeaderColor('#007bff');
      tg.setBackgroundColor('#f8f9fa');

      // Setup back button if needed
      if (tg.BackButton) {
        tg.BackButton.show();
        tg.BackButton.onClick(() => {
          // Handle back navigation
          if (showCart) {
            setShowCart(false);
          } else {
            tg.close();
          }
        });
      }
    }

    return () => {
      // Cleanup
      if (tg?.BackButton) {
        tg.BackButton.hide();
      }
    };
  }, [showCart]);

  // Load initial data
  useEffect(() => {
    loadCategories();
    loadProducts();
  }, [loadCategories, loadProducts]);

  // Sync cart changes
  const handleCartUpdate = useCallback((updatedCart: LocalCart) => {
    setCart(updatedCart);
    telegramHapticFeedback.selection();
  }, []);

  // Add product to cart
  const handleAddToCart = useCallback((product: Product, quantity: number = 1) => {
    const updatedCart = cartManager.addItem(product, quantity);
    handleCartUpdate(updatedCart);
    telegramHapticFeedback.impact('light');
  }, [cartManager, handleCartUpdate]);

  // Update product quantity in cart
  const handleUpdateQuantity = useCallback((productId: number, quantity: number) => {
    const updatedCart = cartManager.updateItemQuantity(productId, quantity);
    handleCartUpdate(updatedCart);

    if (quantity === 0) {
      telegramHapticFeedback.impact('medium');
    } else {
      telegramHapticFeedback.selection();
    }
  }, [cartManager, handleCartUpdate]);

  // Remove product from cart
  const handleRemoveFromCart = useCallback((productId: number) => {
    const updatedCart = cartManager.removeItem(productId);
    handleCartUpdate(updatedCart);
    telegramHapticFeedback.impact('medium');
  }, [cartManager, handleCartUpdate]);

  // Handle category selection
  const handleCategorySelect = useCallback((categoryId: number | null) => {
    setSelectedCategory(categoryId);
    telegramHapticFeedback.selection();
  }, [setSelectedCategory]);

  // Handle checkout navigation
  const handleCheckout = useCallback(() => {
    if (cart.total >= 1500) {
      telegramHapticFeedback.impact('medium');
      onNavigateToCheckout();
    } else {
      telegramHapticFeedback.notification('warning');
    }
  }, [cart.total, onNavigateToCheckout]);

  // Handle cart toggle
  const handleCartToggle = useCallback(() => {
    setShowCart(!showCart);
    telegramHapticFeedback.selection();
  }, [showCart]);

  // Get product quantity in cart
  const getProductQuantityInCart = useCallback((productId: number): number => {
    const item = cart.items.find(item => item.productId === productId);
    return item?.quantity || 0;
  }, [cart.items]);

  // Filter products by selected category
  const filteredProducts = selectedCategoryId
    ? products.filter(product => product.category_id === selectedCategoryId)
    : products;

  // Get selected category name
  const selectedCategoryName = selectedCategoryId
    ? categories.find(cat => cat.id === selectedCategoryId)?.name || 'Все товары'
    : 'Все товары';

  if (error) {
    return (
      <div className={`catalog-error ${className}`}>
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2 className="error-title">Ошибка загрузки каталога</h2>
          <p className="error-message">{error}</p>
          <button
            onClick={() => {
              loadCategories();
              loadProducts();
            }}
            className="error-retry-btn"
          >
            Повторить попытку
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`catalog ${className} ${showCart ? 'catalog--cart-open' : ''}`}>
      {/* Header */}
      <div className="catalog-header">
        <div className="catalog-header__content">
          <h1 className="catalog-title">Замороженные продукты</h1>

          {/* Cart Toggle Button */}
          <button
            onClick={handleCartToggle}
            className="catalog-cart-toggle"
            disabled={cart.count === 0}
          >
            <span className="cart-icon">🛒</span>
            {cart.count > 0 && (
              <span className="cart-badge">{cart.count}</span>
            )}
          </button>
        </div>

        {/* Category Filter */}
        <CategoryFilter
          categories={categories}
          selectedCategoryId={selectedCategoryId}
          onCategorySelect={handleCategorySelect}
          loading={loading}
        />
      </div>

      {/* Main Content */}
      <div className="catalog-main">
        {/* Products Section */}
        <div className="catalog-content">
          <div className="catalog-section-header">
            <h2 className="catalog-section-title">{selectedCategoryName}</h2>
            <span className="catalog-products-count">
              {filteredProducts.length} {filteredProducts.length === 1 ? 'товар' : 'товаров'}
            </span>
          </div>

          {loading ? (
            <div className="catalog-loading">
              <div className="loading-spinner"></div>
              <p>Загрузка каталога...</p>
            </div>
          ) : (
            <div className="catalog-products-grid">
              {filteredProducts.map(product => (
                <ProductCard
                  key={product.id}
                  product={product}
                  quantity={getProductQuantityInCart(product.id)}
                  onAddToCart={handleAddToCart}
                  onUpdateQuantity={handleUpdateQuantity}
                  onRemoveFromCart={handleRemoveFromCart}
                />
              ))}

              {filteredProducts.length === 0 && !loading && (
                <div className="catalog-empty">
                  <div className="empty-icon">📦</div>
                  <h3>Товары не найдены</h3>
                  <p>В данной категории пока нет доступных товаров</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Cart Sidebar */}
        <CartSidebar
          cart={cart}
          isOpen={showCart}
          onClose={() => setShowCart(false)}
          onUpdateQuantity={handleUpdateQuantity}
          onRemoveItem={handleRemoveFromCart}
          onCheckout={handleCheckout}
          minOrderAmount={1500}
        />
      </div>

      {/* Mobile Cart Overlay */}
      {showCart && (
        <div
          className="catalog-cart-overlay"
          onClick={() => setShowCart(false)}
        />
      )}

      {/* Fixed Bottom Bar for Mobile */}
      {cart.count > 0 && !showCart && (
        <div className="catalog-bottom-bar">
          <button onClick={handleCartToggle} className="bottom-bar-cart-btn">
            <span className="cart-info">
              <span className="cart-count">{cart.count} товаров</span>
              <span className="cart-total">{cart.total.toLocaleString('ru-RU')} ₽</span>
            </span>
            <span className="cart-arrow">→</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default Catalog;