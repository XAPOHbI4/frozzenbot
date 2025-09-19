/**
 * React hook for payment functionality
 */

import { useState, useCallback, useEffect } from 'react';
import { Order, OrderCreateRequest } from '../types';
import { PaymentService, PaymentMethod, PaymentStatusResponse } from '../services/paymentService';

export interface PaymentState {
  loading: boolean;
  error: string | null;
  order: Order | null;
  paymentStatus: PaymentStatusResponse | null;
  selectedMethod: string;
}

export interface PaymentActions {
  selectPaymentMethod: (method: string) => void;
  createOrderWithPayment: (orderData: OrderCreateRequest) => Promise<void>;
  initiateTelegramPayment: (order: Order) => Promise<void>;
  checkPaymentStatus: (orderId: number) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export function usePayment(paymentService: PaymentService) {
  const [state, setState] = useState<PaymentState>({
    loading: false,
    error: null,
    order: null,
    paymentStatus: null,
    selectedMethod: 'telegram', // default to Telegram payments
  });

  // Get available payment methods
  const paymentMethods: PaymentMethod[] = paymentService.getPaymentMethods();

  // Select payment method
  const selectPaymentMethod = useCallback((method: string) => {
    setState(prev => ({
      ...prev,
      selectedMethod: method,
      error: null,
    }));
  }, []);

  // Create order with payment
  const createOrderWithPayment = useCallback(async (orderData: OrderCreateRequest) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await paymentService.createOrderWithPayment(
        orderData,
        state.selectedMethod
      );

      setState(prev => ({
        ...prev,
        loading: false,
        order: result.order,
      }));

      // If payment is required and method is Telegram, initiate payment
      if (result.paymentRequired && state.selectedMethod === 'telegram') {
        await initiateTelegramPayment(result.order);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Ошибка при создании заказа',
      }));
      throw error;
    }
  }, [state.selectedMethod, paymentService]);

  // Initiate Telegram payment
  const initiateTelegramPayment = useCallback(async (order: Order) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      await paymentService.initiateTelegramPayment(order);
      setState(prev => ({ ...prev, loading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Ошибка при инициации платежа',
      }));
      throw error;
    }
  }, [paymentService]);

  // Check payment status
  const checkPaymentStatus = useCallback(async (orderId: number) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const status = await paymentService.checkPaymentStatus(orderId);
      setState(prev => ({
        ...prev,
        loading: false,
        paymentStatus: status,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Ошибка при проверке статуса платежа',
      }));
      throw error;
    }
  }, [paymentService]);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Reset state
  const reset = useCallback(() => {
    setState({
      loading: false,
      error: null,
      order: null,
      paymentStatus: null,
      selectedMethod: 'telegram',
    });
  }, []);

  // Listen to payment events
  useEffect(() => {
    const handlePaymentSuccess = (event: CustomEvent) => {
      console.log('Payment success event:', event.detail);
      if (state.order && event.detail.orderId === state.order.id) {
        checkPaymentStatus(event.detail.orderId);
      }
    };

    const handlePaymentCancelled = (event: CustomEvent) => {
      console.log('Payment cancelled event:', event.detail);
      setState(prev => ({
        ...prev,
        error: 'Платеж был отменен',
      }));
    };

    const handlePaymentFailed = (event: CustomEvent) => {
      console.log('Payment failed event:', event.detail);
      setState(prev => ({
        ...prev,
        error: `Ошибка платежа: ${event.detail.error}`,
      }));
    };

    window.addEventListener('paymentSuccess', handlePaymentSuccess as EventListener);
    window.addEventListener('paymentCancelled', handlePaymentCancelled as EventListener);
    window.addEventListener('paymentFailed', handlePaymentFailed as EventListener);

    return () => {
      window.removeEventListener('paymentSuccess', handlePaymentSuccess as EventListener);
      window.removeEventListener('paymentCancelled', handlePaymentCancelled as EventListener);
      window.removeEventListener('paymentFailed', handlePaymentFailed as EventListener);
    };
  }, [state.order, checkPaymentStatus]);

  // Validate current order amount
  const validateOrderAmount = useCallback((amount: number) => {
    return paymentService.validateOrderAmount(amount);
  }, [paymentService]);

  // Get payment method by ID
  const getPaymentMethod = useCallback((methodId: string): PaymentMethod | undefined => {
    return paymentMethods.find(method => method.id === methodId);
  }, [paymentMethods]);

  const actions: PaymentActions = {
    selectPaymentMethod,
    createOrderWithPayment,
    initiateTelegramPayment,
    checkPaymentStatus,
    clearError,
    reset,
  };

  return {
    ...state,
    ...actions,
    paymentMethods,
    validateOrderAmount,
    getPaymentMethod,
  };
}

export default usePayment;