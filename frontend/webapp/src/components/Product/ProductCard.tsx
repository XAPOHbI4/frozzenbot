/**
 * Product Card Component
 * Displays product information with add to cart functionality
 */

import React, { memo } from 'react';
import { Product } from '../../types';
import { telegramHapticFeedback } from '../../utils/telegram';
import './ProductCard.css';

interface ProductCardProps {
  product: Product;
  quantity: number;
  onAddToCart: (product: Product, quantity?: number) => void;
  onUpdateQuantity: (productId: number, quantity: number) => void;
  onRemoveFromCart: (productId: number) => void;
  disabled?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = memo(({
  product,
  quantity,
  onAddToCart,
  onUpdateQuantity,
  onRemoveFromCart,
  disabled = false,
}) => {
  const handleAddToCart = () => {
    if (disabled || !product.is_active || !product.in_stock) return;
    onAddToCart(product);
    telegramHapticFeedback.impact('light');
  };

  const handleIncrement = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (disabled) return;

    if (quantity === 0) {
      onAddToCart(product);
    } else {
      onUpdateQuantity(product.id, quantity + 1);
    }
    telegramHapticFeedback.selection();
  };

  const handleDecrement = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (disabled || quantity === 0) return;

    if (quantity === 1) {
      onRemoveFromCart(product.id);
      telegramHapticFeedback.impact('medium');
    } else {
      onUpdateQuantity(product.id, quantity - 1);
      telegramHapticFeedback.selection();
    }
  };

  const formatPrice = (price: number): string => {
    return `${price.toLocaleString('ru-RU')} ₽`;
  };

  const getAvailabilityStatus = () => {
    if (!product.is_active) return { text: 'Недоступен', className: 'unavailable' };
    if (!product.in_stock) return { text: 'Нет в наличии', className: 'out-of-stock' };
    return { text: 'В наличии', className: 'available' };
  };

  const status = getAvailabilityStatus();
  const isDisabled = disabled || !product.is_active || !product.in_stock;

  return (
    <div className={`product-card ${isDisabled ? 'product-card--disabled' : ''} ${quantity > 0 ? 'product-card--in-cart' : ''}`}>
      {/* Product Image */}
      <div className="product-card__image-container">
        <img
          src={product.image_url || '/images/placeholder-product.jpg'}
          alt={product.name}
          className="product-card__image"
          loading="lazy"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/images/placeholder-product.jpg';
          }}
        />

        {/* Availability Badge */}
        <div className={`product-card__availability ${status.className}`}>
          {status.text}
        </div>

        {/* In Cart Badge */}
        {quantity > 0 && (
          <div className="product-card__cart-badge">
            <span className="cart-badge-text">{quantity}</span>
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className="product-card__info">
        <div className="product-card__header">
          <h3 className="product-card__name" title={product.name}>
            {product.name}
          </h3>

          {product.weight && (
            <span className="product-card__weight">
              {product.formatted_weight || `${product.weight}г`}
            </span>
          )}
        </div>

        {product.description && (
          <p className="product-card__description" title={product.description}>
            {product.description}
          </p>
        )}

        <div className="product-card__footer">
          <div className="product-card__price-section">
            <span className="product-card__price">
              {product.formatted_price || formatPrice(product.price)}
            </span>
          </div>

          {/* Add to Cart / Quantity Controls */}
          <div className="product-card__actions">
            {quantity === 0 ? (
              <button
                onClick={handleAddToCart}
                disabled={isDisabled}
                className="product-card__add-btn"
                aria-label={`Добавить ${product.name} в корзину`}
              >
                <span className="add-btn-icon">+</span>
                <span className="add-btn-text">В корзину</span>
              </button>
            ) : (
              <div className="product-card__quantity-controls">
                <button
                  onClick={handleDecrement}
                  disabled={disabled}
                  className="quantity-btn quantity-btn--decrease"
                  aria-label="Уменьшить количество"
                >
                  -
                </button>

                <span className="quantity-display">
                  {quantity}
                </span>

                <button
                  onClick={handleIncrement}
                  disabled={disabled}
                  className="quantity-btn quantity-btn--increase"
                  aria-label="Увеличить количество"
                >
                  +
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Product Card Overlay for Click */}
      <div
        className="product-card__overlay"
        onClick={handleAddToCart}
        role="button"
        tabIndex={isDisabled ? -1 : 0}
        aria-label={`Добавить ${product.name} в корзину`}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleAddToCart();
          }
        }}
      />
    </div>
  );
});

ProductCard.displayName = 'ProductCard';

export default ProductCard;