/**
 * Payment Service for WebApp - handles Telegram Payments integration
 */

import { Order, OrderCreateRequest, Payment, PaymentStatus } from '../types';
import { WebAppApiClient } from './apiClient';

export interface PaymentMethod {
  id: 'telegram' | 'cash';
  name: string;
  description: string;
  enabled: boolean;
}

export interface PaymentInitRequest {
  orderId: number;
  paymentMethod: string;
  returnUrl?: string;
}

export interface PaymentStatusResponse {
  paymentId: number;
  status: PaymentStatus;
  orderId: number;
  amount: number;
  createdAt: string;
  telegramChargeId?: string;
  errorMessage?: string;
}

export interface TelegramInvoiceParams {
  title: string;
  description: string;
  payload: string;
  providerToken: string;
  currency: string;
  prices: Array<{
    label: string;
    amount: number; // в копейках
  }>;
}

export class PaymentService {
  private apiClient: WebAppApiClient;
  private minOrderAmount: number = 1500; // 1500₽

  constructor(apiClient: WebAppApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Get available payment methods
   */
  getPaymentMethods(): PaymentMethod[] {
    return [
      {
        id: 'telegram',
        name: 'Telegram Payments',
        description: 'Оплата картой через Telegram',
        enabled: true,
      },
      {
        id: 'cash',
        name: 'Наличными при получении',
        description: 'Оплата наличными курьеру',
        enabled: true,
      },
    ];
  }

  /**
   * Validate order amount
   */
  validateOrderAmount(amount: number): { valid: boolean; error?: string } {
    if (amount < this.minOrderAmount) {
      return {
        valid: false,
        error: `Минимальная сумма заказа ${this.minOrderAmount}₽`,
      };
    }
    return { valid: true };
  }

  /**
   * Create order and initiate payment flow
   */
  async createOrderWithPayment(
    orderData: OrderCreateRequest,
    paymentMethod: string
  ): Promise<{ order: Order; paymentRequired: boolean }> {
    try {
      // Validate order amount
      const validation = this.validateOrderAmount(orderData.total_amount);
      if (!validation.valid) {
        throw new Error(validation.error);
      }

      // Create order
      const order = await this.apiClient.createOrder({
        ...orderData,
        payment_method: paymentMethod,
      });

      // Return order with payment requirement info
      const paymentRequired = paymentMethod === 'telegram';

      return {
        order,
        paymentRequired,
      };
    } catch (error) {
      console.error('Failed to create order:', error);
      throw error;
    }
  }

  /**
   * Initiate Telegram Payment
   */
  async initiateTelegramPayment(order: Order): Promise<void> {
    if (!window.Telegram?.WebApp) {
      throw new Error('Telegram WebApp not available');
    }

    try {
      // Prepare invoice data
      const invoiceParams: TelegramInvoiceParams = {
        title: `Заказ #${order.id}`,
        description: this.generatePaymentDescription(order),
        payload: `order_${order.id}_payment_${Date.now()}`,
        providerToken: '381764678:TEST:100', // Test provider token
        currency: 'RUB',
        prices: [
          {
            label: 'Замороженные продукты',
            amount: Math.round(order.total_amount * 100), // конвертируем в копейки
          },
        ],
      };

      console.log('Initiating Telegram payment with params:', invoiceParams);

      // Open Telegram Invoice
      window.Telegram.WebApp.openInvoice(
        this.buildInvoiceUrl(invoiceParams),
        (status: string) => {
          console.log('Payment callback:', status);
          this.handlePaymentCallback(order.id, status);
        }
      );
    } catch (error) {
      console.error('Failed to initiate Telegram payment:', error);
      throw error;
    }
  }

  /**
   * Handle payment callback from Telegram
   */
  private handlePaymentCallback(orderId: number, status: string): void {
    console.log(`Payment callback for order ${orderId}: ${status}`);

    if (status === 'paid') {
      // Payment successful
      this.onPaymentSuccess(orderId);
    } else if (status === 'cancelled') {
      // Payment cancelled
      this.onPaymentCancelled(orderId);
    } else {
      // Payment failed
      this.onPaymentFailed(orderId, status);
    }
  }

  /**
   * Check payment status
   */
  async checkPaymentStatus(orderId: number): Promise<PaymentStatusResponse> {
    try {
      return await this.apiClient.makeRequest<PaymentStatusResponse>(
        `/api/payments/${orderId}/status`
      );
    } catch (error) {
      console.error('Failed to check payment status:', error);
      throw error;
    }
  }

  /**
   * Get payment details
   */
  async getPaymentDetails(paymentId: number): Promise<Payment> {
    try {
      return await this.apiClient.makeRequest<Payment>(
        `/api/payments/${paymentId}/details`
      );
    } catch (error) {
      console.error('Failed to get payment details:', error);
      throw error;
    }
  }

  /**
   * Generate payment description
   */
  private generatePaymentDescription(order: Order): string {
    const itemCount = order.items?.length || 0;
    return `${itemCount} товара на сумму ${order.formatted_total || order.total_amount}₽`;
  }

  /**
   * Build Telegram invoice URL
   */
  private buildInvoiceUrl(params: TelegramInvoiceParams): string {
    const urlParams = new URLSearchParams({
      title: params.title,
      description: params.description,
      payload: params.payload,
      provider_token: params.providerToken,
      currency: params.currency,
      prices: JSON.stringify(params.prices),
    });

    return `https://core.telegram.org/bots/api#sendinvoice?${urlParams.toString()}`;
  }

  /**
   * Payment success handler
   */
  private onPaymentSuccess(orderId: number): void {
    console.log(`Payment successful for order ${orderId}`);

    // Show success message
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showAlert(
        '✅ Платеж успешно обработан!\nВаш заказ подтвержден.',
        () => {
          // Redirect to order status
          this.redirectToOrderStatus(orderId);
        }
      );
    }

    // Trigger custom event
    window.dispatchEvent(
      new CustomEvent('paymentSuccess', {
        detail: { orderId },
      })
    );
  }

  /**
   * Payment cancelled handler
   */
  private onPaymentCancelled(orderId: number): void {
    console.log(`Payment cancelled for order ${orderId}`);

    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showAlert(
        'Платеж отменен.\nВы можете попробовать оплатить позже.'
      );
    }

    // Trigger custom event
    window.dispatchEvent(
      new CustomEvent('paymentCancelled', {
        detail: { orderId },
      })
    );
  }

  /**
   * Payment failed handler
   */
  private onPaymentFailed(orderId: number, error: string): void {
    console.log(`Payment failed for order ${orderId}: ${error}`);

    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showAlert(
        `Ошибка при обработке платежа: ${error}\nПопробуйте еще раз или обратитесь в поддержку.`
      );
    }

    // Trigger custom event
    window.dispatchEvent(
      new CustomEvent('paymentFailed', {
        detail: { orderId, error },
      })
    );
  }

  /**
   * Redirect to order status page
   */
  private redirectToOrderStatus(orderId: number): void {
    // In a real app, this would navigate to the order status page
    console.log(`Redirecting to order status for order ${orderId}`);

    if (window.Telegram?.WebApp) {
      // Close WebApp or navigate
      window.Telegram.WebApp.close();
    }
  }

  /**
   * Format amount for display
   */
  static formatAmount(amount: number, currency: string = 'RUB'): string {
    if (currency === 'RUB') {
      return `${amount.toLocaleString('ru-RU')}₽`;
    }
    return `${amount.toLocaleString()} ${currency}`;
  }

  /**
   * Convert rubles to kopecks for Telegram API
   */
  static rublesToKopecks(rubles: number): number {
    return Math.round(rubles * 100);
  }

  /**
   * Convert kopecks to rubles
   */
  static kopecksToRubles(kopecks: number): number {
    return kopecks / 100;
  }
}

export default PaymentService;