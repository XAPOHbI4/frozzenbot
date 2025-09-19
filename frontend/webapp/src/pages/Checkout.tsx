/**
 * Checkout Page Component
 */

import React, { useState, useEffect } from 'react';
import {
  PaymentMethodSelector,
  PaymentSummary,
  PaymentButton,
  PaymentStatus,
} from '../components/Payment';
import usePayment from '../hooks/usePayment';
import { PaymentService } from '../services/paymentService';
import { WebAppApiClient, LocalCartManager } from '../services/apiClient';
import { LocalCart, OrderCreateRequest, TelegramUser } from '../types';

interface CustomerFormData {
  name: string;
  phone: string;
  address: string;
  notes: string;
}

interface CheckoutProps {
  apiClient: WebAppApiClient;
  cartManager: LocalCartManager;
  className?: string;
}

export const Checkout: React.FC<CheckoutProps> = ({
  apiClient,
  cartManager,
  className = '',
}) => {
  // Payment hook
  const paymentService = new PaymentService(apiClient);
  const payment = usePayment(paymentService);

  // Component state
  const [cart, setCart] = useState<LocalCart>(() => cartManager.getCart());
  const [currentUser, setCurrentUser] = useState<TelegramUser | null>(null);
  const [customerForm, setCustomerForm] = useState<CustomerFormData>({
    name: '',
    phone: '',
    address: '',
    notes: '',
  });
  const [formErrors, setFormErrors] = useState<Partial<CustomerFormData>>({});
  const [step, setStep] = useState<'form' | 'payment' | 'status'>('form');

  // Load user data and cart on mount
  useEffect(() => {
    loadUserData();
    loadCartData();
  }, []);

  // Auto-fill form with Telegram user data
  useEffect(() => {
    if (currentUser && !customerForm.name) {
      const fullName = [currentUser.first_name, currentUser.last_name]
        .filter(Boolean)
        .join(' ');

      setCustomerForm(prev => ({
        ...prev,
        name: fullName,
        phone: currentUser.phone_number || '',
      }));
    }
  }, [currentUser, customerForm.name]);

  const loadUserData = async () => {
    try {
      const user = await apiClient.getCurrentUser();
      setCurrentUser(user);
    } catch (error) {
      console.error('Failed to load user data:', error);
    }
  };

  const loadCartData = () => {
    const currentCart = cartManager.getCart();
    setCart(currentCart);
  };

  const validateForm = (): boolean => {
    const errors: Partial<CustomerFormData> = {};

    if (!customerForm.name.trim()) {
      errors.name = 'Введите имя';
    }

    if (!customerForm.phone.trim()) {
      errors.phone = 'Введите номер телефона';
    } else if (!/^\+?[7-8][\d\s\-\(\)]{10,}$/.test(customerForm.phone)) {
      errors.phone = 'Введите корректный номер телефона';
    }

    if (!customerForm.address.trim()) {
      errors.address = 'Введите адрес доставки';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleFormChange = (field: keyof CustomerFormData, value: string) => {
    setCustomerForm(prev => ({ ...prev, [field]: value }));

    // Clear error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleProceedToPayment = () => {
    if (validateForm() && cart.total >= 1500) {
      setStep('payment');
    }
  };

  const handleCreateOrder = async () => {
    if (!validateForm()) return;

    try {
      payment.clearError();

      const orderData: OrderCreateRequest = {
        telegram_id: currentUser?.id || 0, // This should be telegram_id from user
        customer_name: customerForm.name,
        customer_phone: customerForm.phone,
        delivery_address: customerForm.address,
        notes: customerForm.notes || undefined,
        payment_method: payment.selectedMethod,
      };

      await payment.createOrderWithPayment(orderData);

      // Clear cart on successful order creation
      cartManager.clearCart();
      setCart({ items: [], total: 0, count: 0, updatedAt: new Date().toISOString() });

      setStep('status');
    } catch (error) {
      console.error('Failed to create order:', error);
    }
  };

  const handleRetryPayment = async () => {
    if (payment.order) {
      try {
        await payment.initiateTelegramPayment(payment.order);
      } catch (error) {
        console.error('Failed to retry payment:', error);
      }
    }
  };

  const handleViewOrder = (orderId: number) => {
    // In a real app, navigate to order details
    console.log(`Viewing order ${orderId}`);

    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.close();
    }
  };

  const handleBackToCart = () => {
    // In a real app, navigate back to cart
    console.log('Back to cart');
    setStep('form');
  };

  if (cart.items.length === 0 && step === 'form') {
    return (
      <div className={`checkout-empty ${className}`}>
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🛒</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Корзина пуста
          </h2>
          <p className="text-gray-600 mb-6">
            Добавьте товары в корзину для оформления заказа
          </p>
          <button
            onClick={handleBackToCart}
            className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-6 rounded-lg font-medium transition-colors duration-200"
          >
            Вернуться к покупкам
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`checkout ${className}`}>
      <div className="max-w-md mx-auto bg-white min-h-screen">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 z-10">
          <div className="flex items-center space-x-3">
            {step !== 'form' && (
              <button
                onClick={() => setStep(step === 'status' ? 'payment' : 'form')}
                className="text-gray-600 hover:text-gray-800"
                disabled={payment.loading}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="m15 18-6-6 6-6"/>
                </svg>
              </button>
            )}
            <h1 className="text-lg font-semibold text-gray-800">
              {step === 'form' && 'Оформление заказа'}
              {step === 'payment' && 'Способ оплаты'}
              {step === 'status' && 'Статус платежа'}
            </h1>
          </div>
        </div>

        <div className="p-4 space-y-6">
          {/* Step 1: Customer Information Form */}
          {step === 'form' && (
            <>
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-gray-800">
                  Контактная информация
                </h2>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Имя *
                  </label>
                  <input
                    type="text"
                    value={customerForm.name}
                    onChange={(e) => handleFormChange('name', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      formErrors.name ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Введите ваше имя"
                  />
                  {formErrors.name && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Номер телефона *
                  </label>
                  <input
                    type="tel"
                    value={customerForm.phone}
                    onChange={(e) => handleFormChange('phone', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      formErrors.phone ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="+7 (900) 123-45-67"
                  />
                  {formErrors.phone && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.phone}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Адрес доставки *
                  </label>
                  <textarea
                    value={customerForm.address}
                    onChange={(e) => handleFormChange('address', e.target.value)}
                    rows={3}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      formErrors.address ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Город, улица, дом, квартира"
                  />
                  {formErrors.address && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.address}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Комментарий к заказу
                  </label>
                  <textarea
                    value={customerForm.notes}
                    onChange={(e) => handleFormChange('notes', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Дополнительные пожелания"
                  />
                </div>
              </div>

              <PaymentSummary cart={cart} selectedPaymentMethod={payment.selectedMethod} />

              <button
                onClick={handleProceedToPayment}
                disabled={cart.total < 1500}
                className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors duration-200 ${
                  cart.total >= 1500
                    ? 'bg-blue-500 hover:bg-blue-600 text-white'
                    : 'bg-gray-300 cursor-not-allowed text-gray-500'
                }`}
              >
                {cart.total >= 1500
                  ? `Продолжить (${PaymentService.formatAmount(cart.total)})`
                  : `Минимум ${PaymentService.formatAmount(1500 - cart.total)} для заказа`}
              </button>
            </>
          )}

          {/* Step 2: Payment Method Selection */}
          {step === 'payment' && (
            <>
              <PaymentMethodSelector
                methods={payment.paymentMethods}
                selectedMethod={payment.selectedMethod}
                onMethodSelect={payment.selectPaymentMethod}
                disabled={payment.loading}
              />

              <PaymentSummary cart={cart} selectedPaymentMethod={payment.selectedMethod} />

              {payment.error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-700">{payment.error}</p>
                </div>
              )}

              <PaymentButton
                amount={cart.total}
                paymentMethod={payment.selectedMethod}
                loading={payment.loading}
                onPayment={handleCreateOrder}
              />
            </>
          )}

          {/* Step 3: Payment Status */}
          {step === 'status' && payment.paymentStatus && (
            <PaymentStatus
              status={payment.paymentStatus}
              onRetry={handleRetryPayment}
              onViewOrder={handleViewOrder}
            />
          )}

          {/* Order Created but No Payment Status Yet */}
          {step === 'status' && payment.order && !payment.paymentStatus && (
            <div className="text-center py-8">
              <div className="text-green-500 text-4xl mb-4">✅</div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                Заказ создан успешно!
              </h2>
              <p className="text-gray-600 mb-4">
                Заказ #{payment.order.id} принят в обработку
              </p>
              <button
                onClick={() => handleViewOrder(payment.order!.id)}
                className="bg-green-500 hover:bg-green-600 text-white py-2 px-6 rounded-lg font-medium transition-colors duration-200"
              >
                Закрыть
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Checkout;