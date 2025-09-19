/**
 * Cart Sidebar Component
 * Displays cart items, total, and checkout functionality
 */

import React, { memo } from 'react';
import { LocalCart, LocalCartItem } from '../../types';
import { telegramHapticFeedback } from '../../utils/telegram';
import './CartSidebar.css';

interface CartSidebarProps {
  cart: LocalCart;
  isOpen: boolean;
  onClose: () => void;
  onUpdateQuantity: (productId: number, quantity: number) => void;
  onRemoveItem: (productId: number) => void;
  onCheckout: () => void;
  minOrderAmount: number;
  disabled?: boolean;
}

export const CartSidebar: React.FC<CartSidebarProps> = memo(({
  cart,
  isOpen,
  onClose,
  onUpdateQuantity,
  onRemoveItem,
  onCheckout,
  minOrderAmount,
  disabled = false,
}) => {
  const formatPrice = (price: number): string => {
    return `${price.toLocaleString('ru-RU')} ₽`;
  };

  const handleQuantityChange = (productId: number, newQuantity: number) => {
    if (disabled) return;

    if (newQuantity <= 0) {
      onRemoveItem(productId);
      telegramHapticFeedback.impact('medium');
    } else {
      onUpdateQuantity(productId, newQuantity);
      telegramHapticFeedback.selection();
    }
  };

  const handleCheckout = () => {
    if (disabled || cart.total < minOrderAmount) {
      if (cart.total < minOrderAmount) {
        telegramHapticFeedback.notification('warning');
      }
      return;
    }

    onCheckout();
    telegramHapticFeedback.impact('medium');
  };

  const handleClose = () => {
    if (disabled) return;
    onClose();
    telegramHapticFeedback.selection();
  };

  const isCheckoutDisabled = disabled || cart.total < minOrderAmount;
  const remainingAmount = Math.max(0, minOrderAmount - cart.total);

  return (
    <>
      {/* Cart Sidebar */}
      <div className={`cart-sidebar ${isOpen ? 'cart-sidebar--open' : ''}`}>
        <div className="cart-sidebar__header">
          <div className="cart-header__title">
            <h2>Заказ</h2>
            <span className="cart-header__count">
              {cart.count} {cart.count === 1 ? 'товар' : 'товаров'}
            </span>
          </div>

          <button
            onClick={handleClose}
            disabled={disabled}
            className="cart-header__close"
            aria-label="Закрыть корзину"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div className="cart-sidebar__content">
          {cart.items.length === 0 ? (
            <div className="cart-sidebar__empty">
              <div className="empty-cart-icon">🛒</div>
              <h3>Корзина пуста</h3>
              <p>Добавьте товары для оформления заказа</p>
            </div>
          ) : (
            <>
              {/* Cart Items */}
              <div className="cart-sidebar__items">
                {cart.items.map((item: LocalCartItem) => (
                  <CartItem
                    key={item.productId}
                    item={item}
                    onQuantityChange={handleQuantityChange}
                    onRemove={() => onRemoveItem(item.productId)}
                    disabled={disabled}
                  />
                ))}
              </div>

              {/* Cart Summary */}
              <div className="cart-sidebar__summary">
                <div className="cart-summary__details">
                  <div className="summary-row">
                    <span>Товаров на сумму:</span>
                    <span className="summary-price">{formatPrice(cart.total)}</span>
                  </div>

                  {/* Minimum Order Warning */}
                  {remainingAmount > 0 && (
                    <div className="summary-warning">
                      <span className="warning-icon">⚠️</span>
                      <span>
                        Доберите на {formatPrice(remainingAmount)} для оформления заказа
                      </span>
                    </div>
                  )}

                  <div className="summary-total">
                    <span>Итого:</span>
                    <span className="total-price">{formatPrice(cart.total)}</span>
                  </div>
                </div>

                {/* Checkout Button */}
                <button
                  onClick={handleCheckout}
                  disabled={isCheckoutDisabled}
                  className={`cart-sidebar__checkout-btn ${
                    isCheckoutDisabled ? 'checkout-btn--disabled' : ''
                  }`}
                >
                  {remainingAmount > 0
                    ? `Минимальный заказ ${formatPrice(minOrderAmount)}`
                    : `Заказать за ${formatPrice(cart.total)}`
                  }
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Mobile Overlay */}
      {isOpen && <div className="cart-sidebar__overlay" onClick={handleClose} />}
    </>
  );
});

CartSidebar.displayName = 'CartSidebar';

// Cart Item Component
interface CartItemProps {
  item: LocalCartItem;
  onQuantityChange: (productId: number, quantity: number) => void;
  onRemove: () => void;
  disabled?: boolean;
}

const CartItem: React.FC<CartItemProps> = memo(({
  item,
  onQuantityChange,
  onRemove,
  disabled = false,
}) => {
  const formatPrice = (price: number): string => {
    return `${price.toLocaleString('ru-RU')} ₽`;
  };

  const handleIncrement = () => {
    if (disabled) return;
    onQuantityChange(item.productId, item.quantity + 1);
  };

  const handleDecrement = () => {
    if (disabled) return;
    onQuantityChange(item.productId, item.quantity - 1);
  };

  const handleRemove = () => {
    if (disabled) return;
    onRemove();
    telegramHapticFeedback.impact('medium');
  };

  return (
    <div className="cart-item">
      <div className="cart-item__image-container">
        <img
          src={item.image || '/images/placeholder-product.jpg'}
          alt={item.name}
          className="cart-item__image"
          loading="lazy"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/images/placeholder-product.jpg';
          }}
        />
      </div>

      <div className="cart-item__details">
        <h4 className="cart-item__name" title={item.name}>
          {item.name}
        </h4>

        <div className="cart-item__price-info">
          <span className="item-unit-price">{formatPrice(item.price)} за шт.</span>
          <span className="item-total-price">{formatPrice(item.total)}</span>
        </div>

        <div className="cart-item__controls">
          <div className="cart-item__quantity-controls">
            <button
              onClick={handleDecrement}
              disabled={disabled}
              className="quantity-btn quantity-btn--decrease"
              aria-label="Уменьшить количество"
            >
              -
            </button>

            <span className="quantity-display">
              {item.quantity}
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

          <button
            onClick={handleRemove}
            disabled={disabled}
            className="cart-item__remove-btn"
            aria-label="Удалить товар"
            title="Удалить товар"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              <path d="M10 11v6M14 11v6"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
});

CartItem.displayName = 'CartItem';

export default CartSidebar;