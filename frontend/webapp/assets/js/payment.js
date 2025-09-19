// Payment Service for Telegram WebApp
class PaymentService {
    constructor() {
        this.api = window.api;
        this.currentOrder = null;
        this.currentPayment = null;
        this.paymentListeners = [];
    }

    // Payment status constants
    static PaymentStatus = {
        PENDING: 'pending',
        SUCCESS: 'success',
        FAILED: 'failed',
        REFUNDED: 'refunded'
    };

    // Payment method constants
    static PaymentMethods = {
        TELEGRAM: 'telegram',
        CARD: 'card',
        CASH: 'cash'
    };

    // Add payment status listener
    addEventListener(listener) {
        this.paymentListeners.push(listener);
    }

    // Notify all listeners about payment status changes
    notifyListeners(paymentData) {
        this.paymentListeners.forEach(listener => {
            try {
                listener(paymentData);
            } catch (error) {
                console.error('Payment listener error:', error);
            }
        });
    }

    // Create order and initiate payment
    async createOrderAndPay(orderData, paymentMethod = PaymentService.PaymentMethods.TELEGRAM) {
        try {
            // Create order first
            const orderResponse = await this.api.createOrder({
                ...orderData,
                payment_method: paymentMethod
            });

            if (!orderResponse.success) {
                throw new Error(orderResponse.message || 'Failed to create order');
            }

            this.currentOrder = orderResponse.order;

            // If payment method is cash, skip payment processing
            if (paymentMethod === PaymentService.PaymentMethods.CASH) {
                return {
                    success: true,
                    order: this.currentOrder,
                    payment: null,
                    message: 'Заказ создан. Оплата наличными при получении.'
                };
            }

            // If payment was created automatically by backend
            if (orderResponse.payment) {
                this.currentPayment = orderResponse.payment;

                // Initiate Telegram payment for card/telegram payments
                if (paymentMethod !== PaymentService.PaymentMethods.CASH) {
                    return await this.initiateTelegramPayment();
                }
            }

            return {
                success: true,
                order: this.currentOrder,
                payment: this.currentPayment,
                message: 'Заказ создан успешно.'
            };

        } catch (error) {
            console.error('Failed to create order and initiate payment:', error);
            throw error;
        }
    }

    // Initiate Telegram payment using WebApp API
    async initiateTelegramPayment() {
        if (!this.currentOrder || !this.currentPayment) {
            throw new Error('No active order or payment to process');
        }

        try {
            // Check if Telegram WebApp is available
            if (!window.Telegram?.WebApp) {
                throw new Error('Telegram WebApp не доступен');
            }

            const tg = window.Telegram.WebApp;

            // Prepare invoice data
            const invoiceData = {
                title: `Заказ #${this.currentOrder.id}`,
                description: `Оплата заказа на сумму ${this.currentOrder.formatted_total}`,
                payload: `order_${this.currentOrder.id}_payment_${this.currentPayment.id}`,
                currency: 'RUB',
                prices: [{
                    label: `Заказ #${this.currentOrder.id}`,
                    amount: Math.round(this.currentOrder.total_amount * 100) // Convert to kopecks
                }]
            };

            // Show invoice using Telegram WebApp
            const result = await this.showTelegramInvoice(invoiceData);

            if (result.success) {
                // Start polling for payment status
                this.startPaymentStatusPolling();

                return {
                    success: true,
                    order: this.currentOrder,
                    payment: this.currentPayment,
                    message: 'Платеж инициирован. Ожидание подтверждения.'
                };
            } else {
                throw new Error(result.error || 'Не удалось инициировать платеж');
            }

        } catch (error) {
            console.error('Failed to initiate Telegram payment:', error);
            throw error;
        }
    }

    // Show Telegram invoice (simulated for now, actual implementation would use Telegram Bot)
    async showTelegramInvoice(invoiceData) {
        try {
            const tg = window.Telegram.WebApp;

            // For now, show a modal asking user to confirm payment
            // In real implementation, this would trigger Telegram's native payment UI
            const userConfirmed = await this.showPaymentConfirmationModal(invoiceData);

            if (userConfirmed) {
                // Simulate payment processing
                setTimeout(() => {
                    this.simulatePaymentResult(true);
                }, 2000);

                return { success: true };
            } else {
                return {
                    success: false,
                    error: 'Payment cancelled by user'
                };
            }

        } catch (error) {
            console.error('Error showing Telegram invoice:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Show payment confirmation modal (mock UI for development)
    async showPaymentConfirmationModal(invoiceData) {
        return new Promise((resolve) => {
            const modalHtml = `
                <div class="modal-overlay" id="payment-confirmation-overlay">
                    <div class="modal payment-modal" id="payment-confirmation-modal">
                        <div class="modal-header">
                            <h2>💳 Подтверждение оплаты</h2>
                        </div>
                        <div class="modal-body">
                            <div class="payment-info">
                                <h3>${invoiceData.title}</h3>
                                <p>${invoiceData.description}</p>
                                <div class="payment-amount">
                                    <strong>К оплате: ${window.Utils.formatPrice(invoiceData.prices[0].amount / 100)}</strong>
                                </div>
                                <div class="payment-method-info">
                                    <p>🔒 Безопасная оплата через Telegram</p>
                                    <p>💳 Принимаются карты Visa, MasterCard, МИР</p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-secondary" id="cancel-payment">
                                Отмена
                            </button>
                            <button class="btn btn-primary" id="confirm-payment">
                                💳 Оплатить
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHtml);

            const confirmBtn = document.getElementById('confirm-payment');
            const cancelBtn = document.getElementById('cancel-payment');
            const overlay = document.getElementById('payment-confirmation-overlay');

            const cleanup = () => {
                overlay?.remove();
            };

            confirmBtn?.addEventListener('click', () => {
                cleanup();
                resolve(true);
            });

            cancelBtn?.addEventListener('click', () => {
                cleanup();
                resolve(false);
            });

            overlay?.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    cleanup();
                    resolve(false);
                }
            });
        });
    }

    // Start polling payment status from backend
    startPaymentStatusPolling() {
        if (!this.currentOrder) return;

        const pollInterval = setInterval(async () => {
            try {
                const statusResponse = await this.api.getPaymentStatus(this.currentOrder.id);

                if (statusResponse.status !== PaymentService.PaymentStatus.PENDING) {
                    clearInterval(pollInterval);
                    this.handlePaymentStatusUpdate(statusResponse);
                }
            } catch (error) {
                console.error('Error polling payment status:', error);
                // Continue polling on error
            }
        }, 2000);

        // Stop polling after 5 minutes
        setTimeout(() => {
            clearInterval(pollInterval);
        }, 300000);
    }

    // Handle payment status update
    handlePaymentStatusUpdate(statusResponse) {
        const paymentData = {
            order: this.currentOrder,
            payment: statusResponse,
            status: statusResponse.status
        };

        // Notify listeners
        this.notifyListeners(paymentData);

        // Show appropriate UI
        if (statusResponse.status === PaymentService.PaymentStatus.SUCCESS) {
            this.showPaymentSuccessModal(paymentData);
        } else if (statusResponse.status === PaymentService.PaymentStatus.FAILED) {
            this.showPaymentFailedModal(paymentData);
        }
    }

    // Simulate payment result (for development)
    simulatePaymentResult(success) {
        if (!this.currentOrder || !this.currentPayment) return;

        // Simulate webhook call to backend
        const webhookData = {
            order_id: this.currentOrder.id,
            status: success ? 'success' : 'failed',
            amount: this.currentOrder.total_amount,
            transaction_id: 'sim_' + Date.now(),
            payment_method: 'telegram',
            metadata: {
                simulated: true,
                timestamp: new Date().toISOString()
            }
        };

        // Send webhook to backend
        this.api.sendPaymentWebhook(webhookData).catch(error => {
            console.error('Failed to send simulated webhook:', error);
        });
    }

    // Show payment success modal
    showPaymentSuccessModal(paymentData) {
        const modalHtml = `
            <div class="modal-overlay" id="payment-success-overlay">
                <div class="modal success-modal" id="payment-success-modal">
                    <div class="modal-header">
                        <h2>✅ Оплата успешна!</h2>
                    </div>
                    <div class="modal-body">
                        <div class="success-content">
                            <div class="success-icon">💳</div>
                            <p><strong>Заказ #${paymentData.order.id}</strong></p>
                            <p><strong>Сумма:</strong> ${paymentData.order.formatted_total}</p>
                            ${paymentData.payment.transaction_id ?
                                `<p><strong>ID транзакции:</strong> ${paymentData.payment.transaction_id}</p>` : ''
                            }

                            <div class="success-message">
                                <p>🎉 Спасибо за покупку!</p>
                                <p>📞 Мы свяжемся с вами для подтверждения</p>
                                <p>⏰ Время приготовления: 30-45 минут</p>
                            </div>

                            <button class="btn btn-primary" id="close-payment-success">
                                Отлично!
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        document.getElementById('close-payment-success')?.addEventListener('click', () => {
            document.getElementById('payment-success-overlay')?.remove();
        });

        // Clear current order/payment
        this.currentOrder = null;
        this.currentPayment = null;
    }

    // Show payment failed modal
    showPaymentFailedModal(paymentData) {
        const modalHtml = `
            <div class="modal-overlay" id="payment-failed-overlay">
                <div class="modal error-modal" id="payment-failed-modal">
                    <div class="modal-header">
                        <h2>❌ Ошибка оплаты</h2>
                    </div>
                    <div class="modal-body">
                        <div class="error-content">
                            <div class="error-icon">💳</div>
                            <p><strong>Заказ #${paymentData.order.id}</strong></p>
                            <p><strong>Сумма:</strong> ${paymentData.order.formatted_total}</p>

                            <div class="error-message">
                                <p>Не удалось обработать платеж.</p>
                                <p>Попробуйте еще раз или обратитесь в поддержку.</p>
                            </div>

                            <div class="modal-actions">
                                <button class="btn btn-secondary" id="close-payment-failed">
                                    Закрыть
                                </button>
                                <button class="btn btn-primary" id="retry-payment">
                                    Попробовать снова
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        document.getElementById('close-payment-failed')?.addEventListener('click', () => {
            document.getElementById('payment-failed-overlay')?.remove();
        });

        document.getElementById('retry-payment')?.addEventListener('click', () => {
            document.getElementById('payment-failed-overlay')?.remove();
            // Retry payment
            this.initiateTelegramPayment().catch(error => {
                window.Utils.showToast('Ошибка повторной попытки оплаты', 'error');
            });
        });
    }

    // Get current order
    getCurrentOrder() {
        return this.currentOrder;
    }

    // Get current payment
    getCurrentPayment() {
        return this.currentPayment;
    }

    // Check payment status manually
    async checkPaymentStatus(orderId) {
        try {
            return await this.api.getPaymentStatus(orderId);
        } catch (error) {
            console.error('Failed to check payment status:', error);
            throw error;
        }
    }

    // Get payment details
    async getPaymentDetails(paymentId) {
        try {
            return await this.api.getPaymentDetails(paymentId);
        } catch (error) {
            console.error('Failed to get payment details:', error);
            throw error;
        }
    }
}

// Global payment service instance
window.paymentService = new PaymentService();