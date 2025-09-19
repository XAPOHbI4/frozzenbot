/**
 * Payment Summary Component
 */

import React from 'react';
import { LocalCart } from '../../types';
import { PaymentService } from '../../services/paymentService';

interface PaymentSummaryProps {
  cart: LocalCart;
  selectedPaymentMethod: string;
  className?: string;
}

export const PaymentSummary: React.FC<PaymentSummaryProps> = ({
  cart,
  selectedPaymentMethod,
  className = '',
}) => {
  const deliveryFee = 0; // Free delivery for now
  const serviceFee = 0; // No service fee
  const totalAmount = cart.total + deliveryFee + serviceFee;

  const isMinOrderMet = totalAmount >= 1500;
  const minOrderShortage = isMinOrderMet ? 0 : 1500 - totalAmount;

  return (
    <div className={`payment-summary bg-gray-50 rounded-lg p-4 ${className}`}>
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Итого к оплате
      </h3>

      <div className="space-y-3">
        {/* Cart Items Summary */}
        <div className="flex justify-between items-center">
          <span className="text-gray-600">
            Товары ({cart.count} {cart.count === 1 ? 'товар' : cart.count < 5 ? 'товара' : 'товаров'})
          </span>
          <span className="font-medium">
            {PaymentService.formatAmount(cart.total)}
          </span>
        </div>

        {/* Delivery Fee */}
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Доставка</span>
          <span className={`font-medium ${deliveryFee === 0 ? 'text-green-600' : ''}`}>
            {deliveryFee === 0 ? 'Бесплатно' : PaymentService.formatAmount(deliveryFee)}
          </span>
        </div>

        {/* Service Fee */}
        {serviceFee > 0 && (
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Сервисный сбор</span>
            <span className="font-medium">
              {PaymentService.formatAmount(serviceFee)}
            </span>
          </div>
        )}

        <hr className="border-gray-200" />

        {/* Total */}
        <div className="flex justify-between items-center text-lg font-semibold">
          <span>Всего</span>
          <span className={isMinOrderMet ? 'text-gray-900' : 'text-red-600'}>
            {PaymentService.formatAmount(totalAmount)}
          </span>
        </div>

        {/* Payment Method Info */}
        <div className="mt-4 pt-3 border-t border-gray-200">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Способ оплаты</span>
            <span className="font-medium">
              {selectedPaymentMethod === 'telegram' ? 'Telegram Payments' : 'Наличными при получении'}
            </span>
          </div>
        </div>

        {/* Minimum Order Warning */}
        {!isMinOrderMet && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <div className="text-red-500 mt-0.5">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <div className="text-sm text-red-700">
                <div className="font-medium">Минимальная сумма заказа не достигнута</div>
                <div>
                  Добавьте товары на {PaymentService.formatAmount(minOrderShortage)} для оформления заказа
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Order Validation */}
        {isMinOrderMet && cart.items.length > 0 && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <div className="text-green-500">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <div className="text-sm text-green-700 font-medium">
                Заказ готов к оформлению
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Cart Items List */}
      {cart.items.length > 0 && (
        <div className="mt-6">
          <h4 className="text-md font-medium mb-3 text-gray-800">
            Состав заказа
          </h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {cart.items.map((item) => (
              <div
                key={item.id}
                className="flex justify-between items-center text-sm py-1"
              >
                <div className="flex-1 pr-2">
                  <span className="text-gray-700">{item.name}</span>
                  <span className="text-gray-500 ml-1">× {item.quantity}</span>
                </div>
                <span className="font-medium text-gray-900">
                  {PaymentService.formatAmount(item.total)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentSummary;