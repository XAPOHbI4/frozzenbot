// Shopping Cart Management
class CartService {
    constructor() {
        this.storageKey = window.AppConfig.STORAGE_KEYS.CART;
        this.minOrderAmount = window.AppConfig.MIN_ORDER_AMOUNT;
        this.items = this.loadCart();
        this.listeners = [];
    }

    // Load cart from localStorage
    loadCart() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            return saved ? JSON.parse(saved) : [];
        } catch (error) {
            console.error('Failed to load cart:', error);
            return [];
        }
    }

    // Save cart to localStorage
    saveCart() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.items));
            this.notifyListeners();
        } catch (error) {
            console.error('Failed to save cart:', error);
        }
    }

    // Add event listener for cart changes
    addEventListener(listener) {
        this.listeners.push(listener);
    }

    // Notify all listeners about cart changes
    notifyListeners() {
        this.listeners.forEach(listener => {
            try {
                listener(this.getCartSummary());
            } catch (error) {
                console.error('Cart listener error:', error);
            }
        });
    }

    // Add product to cart
    addProduct(product, quantity = 1) {
        const existingItem = this.items.find(item => item.product.id === product.id);

        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.items.push({
                id: window.Utils.generateId(),
                product: { ...product },
                quantity: quantity,
                addedAt: new Date().toISOString()
            });
        }

        this.saveCart();

        // Show feedback
        if (window.Telegram?.WebApp?.HapticFeedback) {
            window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
        }

        window.Utils.showToast(`${product.name} добавлен в корзину`, 'success');
    }

    // Remove product from cart
    removeProduct(productId) {
        this.items = this.items.filter(item => item.product.id !== productId);
        this.saveCart();
    }

    // Update quantity of product in cart
    updateQuantity(productId, newQuantity) {
        if (newQuantity <= 0) {
            this.removeProduct(productId);
            return;
        }

        const item = this.items.find(item => item.product.id === productId);
        if (item) {
            item.quantity = newQuantity;
            this.saveCart();
        }
    }

    // Get cart items
    getItems() {
        return this.items;
    }

    // Get cart summary
    getCartSummary() {
        const totalItems = this.items.reduce((sum, item) => sum + item.quantity, 0);
        const totalAmount = this.items.reduce((sum, item) =>
            sum + (item.product.price * item.quantity), 0
        );

        return {
            items: this.items,
            totalItems,
            totalAmount,
            formattedTotal: window.Utils.formatPrice(totalAmount),
            isMinOrderMet: totalAmount >= this.minOrderAmount,
            missingAmount: Math.max(0, this.minOrderAmount - totalAmount),
            formattedMissingAmount: window.Utils.formatPrice(
                Math.max(0, this.minOrderAmount - totalAmount)
            )
        };
    }

    // Clear cart
    clear() {
        this.items = [];
        this.saveCart();
    }

    // Check if cart is empty
    isEmpty() {
        return this.items.length === 0;
    }
}

// Cart UI Manager
class CartUI {
    constructor(cartService) {
        this.cart = cartService;
        this.elements = {
            cartBottom: document.getElementById('cart-bottom'),
            cartCount: document.getElementById('cart-count'),
            cartTotal: document.getElementById('cart-total'),
            viewCartBtn: document.getElementById('view-cart-btn'),
            cartModal: document.getElementById('cart-modal'),
            closeCartBtn: document.getElementById('close-cart'),
            cartItems: document.getElementById('cart-items'),
            summaryTotal: document.getElementById('summary-total'),
            finalTotal: document.getElementById('final-total'),
            minOrderWarning: document.getElementById('min-order-warning'),
            checkoutBtn: document.getElementById('checkout-btn')
        };

        this.init();
    }

    init() {
        // Subscribe to cart changes
        this.cart.addEventListener((summary) => {
            this.updateCartBottom(summary);
            this.updateCartModal(summary);
        });

        // Event listeners
        this.elements.viewCartBtn?.addEventListener('click', () => this.showCartModal());
        this.elements.closeCartBtn?.addEventListener('click', () => this.hideCartModal());
        this.elements.checkoutBtn?.addEventListener('click', () => this.handleCheckout());

        // Close modal on backdrop click
        this.elements.cartModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.cartModal) {
                this.hideCartModal();
            }
        });

        // Initial update
        this.updateCartBottom(this.cart.getCartSummary());
    }

    // Update cart bottom bar
    updateCartBottom(summary) {
        if (!this.elements.cartBottom) return;

        if (summary.totalItems === 0) {
            this.elements.cartBottom.style.display = 'none';
            return;
        }

        this.elements.cartBottom.style.display = 'flex';

        if (this.elements.cartCount) {
            this.elements.cartCount.textContent = summary.totalItems;
        }

        if (this.elements.cartTotal) {
            this.elements.cartTotal.textContent = summary.formattedTotal;
        }
    }

    // Update cart modal content
    updateCartModal(summary) {
        if (!this.elements.cartItems) return;

        // Clear existing items
        this.elements.cartItems.innerHTML = '';

        // Add cart items
        summary.items.forEach(item => {
            const itemElement = this.createCartItemElement(item);
            this.elements.cartItems.appendChild(itemElement);
        });

        // Update summary
        if (this.elements.summaryTotal) {
            this.elements.summaryTotal.textContent = summary.formattedTotal;
        }

        if (this.elements.finalTotal) {
            this.elements.finalTotal.textContent = summary.formattedTotal;
        }

        // Update minimum order warning
        if (this.elements.minOrderWarning) {
            if (!summary.isMinOrderMet && summary.totalAmount > 0) {
                this.elements.minOrderWarning.style.display = 'block';
                this.elements.minOrderWarning.innerHTML =
                    `⚠️ Минимальная сумма заказа: ${window.Utils.formatPrice(this.cart.minOrderAmount)}<br>` +
                    `Добавьте еще товаров на: ${summary.formattedMissingAmount}`;
            } else {
                this.elements.minOrderWarning.style.display = 'none';
            }
        }

        // Update checkout button
        if (this.elements.checkoutBtn) {
            this.elements.checkoutBtn.disabled = !summary.isMinOrderMet || summary.totalItems === 0;

            if (summary.isMinOrderMet && summary.totalItems > 0) {
                this.elements.checkoutBtn.textContent = `Заказать за ${summary.formattedTotal}`;
            } else {
                this.elements.checkoutBtn.textContent = 'Оформить заказ';
            }
        }
    }

    // Create cart item element
    createCartItemElement(item) {
        const div = document.createElement('div');
        div.className = 'cart-item';

        div.innerHTML = `
            <div class="cart-item-image">
                ${window.AppConfig.DEFAULT_PRODUCT_IMAGE}
            </div>
            <div class="cart-item-info">
                <div class="cart-item-name">${item.product.name}</div>
                <div class="cart-item-price">${item.product.formattedPrice} × ${item.quantity}</div>
            </div>
            <div class="quantity-controls">
                <button class="quantity-btn decrease" data-product-id="${item.product.id}">−</button>
                <span class="quantity">${item.quantity}</span>
                <button class="quantity-btn increase" data-product-id="${item.product.id}">+</button>
            </div>
        `;

        // Add event listeners for quantity controls
        const decreaseBtn = div.querySelector('.decrease');
        const increaseBtn = div.querySelector('.increase');

        decreaseBtn.addEventListener('click', () => {
            this.cart.updateQuantity(item.product.id, item.quantity - 1);
        });

        increaseBtn.addEventListener('click', () => {
            this.cart.updateQuantity(item.product.id, item.quantity + 1);
        });

        return div;
    }

    // Show cart modal
    showCartModal() {
        if (this.elements.cartModal) {
            this.elements.cartModal.classList.add('show');
            this.updateCartModal(this.cart.getCartSummary());
        }
    }

    // Hide cart modal
    hideCartModal() {
        if (this.elements.cartModal) {
            this.elements.cartModal.classList.remove('show');
        }
    }

    // Handle checkout
    handleCheckout() {
        const summary = this.cart.getCartSummary();

        if (!summary.isMinOrderMet) {
            window.Utils.showToast(
                `Минимальная сумма заказа: ${window.Utils.formatPrice(this.cart.minOrderAmount)}`,
                'warning'
            );
            return;
        }

        // Show order form
        this.showOrderForm(summary);
    }

    // Show order form modal
    showOrderForm(cartSummary) {
        // Close cart modal first
        this.hideCartModal();

        // Create order form modal HTML
        const orderFormHtml = `
            <div class="modal-overlay" id="order-modal-overlay">
                <div class="modal" id="order-modal">
                    <div class="modal-header">
                        <h2>Оформление заказа</h2>
                        <button class="modal-close" id="order-modal-close">&times;</button>
                    </div>

                    <div class="modal-body">
                        <div class="order-summary">
                            <h3>Ваш заказ:</h3>
                            <div id="order-items-list"></div>
                            <div class="order-total">
                                <strong>Итого: ${cartSummary.formattedTotal}</strong>
                            </div>
                        </div>

                        <form id="order-form" class="order-form">
                            <div class="form-group">
                                <label for="customer-name">Имя *</label>
                                <input type="text" id="customer-name" required
                                       placeholder="Введите ваше имя">
                            </div>

                            <div class="form-group">
                                <label for="customer-phone">Телефон *</label>
                                <input type="tel" id="customer-phone" required
                                       placeholder="+7 (999) 123-45-67">
                            </div>

                            <div class="form-group">
                                <label for="delivery-address">Адрес доставки</label>
                                <textarea id="delivery-address" rows="3"
                                         placeholder="Укажите адрес доставки (необязательно)"></textarea>
                            </div>

                            <div class="form-group">
                                <label for="order-notes">Примечания к заказу</label>
                                <textarea id="order-notes" rows="2"
                                         placeholder="Дополнительные пожелания (необязательно)"></textarea>
                            </div>

                            <div class="form-group">
                                <label>Способ оплаты</label>
                                <div class="payment-methods">
                                    <label class="radio-option">
                                        <input type="radio" name="payment-method" value="card" checked>
                                        <span>💳 Банковская карта</span>
                                    </label>
                                    <label class="radio-option">
                                        <input type="radio" name="payment-method" value="cash">
                                        <span>💵 Наличные при получении</span>
                                    </label>
                                </div>
                            </div>

                            <div class="form-actions">
                                <button type="button" class="btn btn-secondary" id="cancel-order">
                                    Отмена
                                </button>
                                <button type="submit" class="btn btn-primary" id="submit-order">
                                    <span class="btn-text">Оформить заказ</span>
                                    <span class="btn-loading" style="display: none;">Отправка...</span>
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Add to DOM
        document.body.insertAdjacentHTML('beforeend', orderFormHtml);

        // Fill order items
        this.fillOrderItems(cartSummary);

        // Setup event listeners
        this.setupOrderFormListeners();

        // Try to pre-fill user data from Telegram
        this.prefillUserData();
    }

    // Fill order items list
    fillOrderItems(cartSummary) {
        const itemsList = document.getElementById('order-items-list');
        if (!itemsList) return;

        const itemsHtml = cartSummary.items.map(item => `
            <div class="order-item">
                <span class="item-name">${item.product.name}</span>
                <span class="item-details">${item.quantity} шт. × ${window.Utils.formatPrice(item.product.price)}</span>
                <span class="item-total">${window.Utils.formatPrice(item.total)}</span>
            </div>
        `).join('');

        itemsList.innerHTML = itemsHtml;
    }

    // Setup order form event listeners
    setupOrderFormListeners() {
        // Close modal events
        const closeBtn = document.getElementById('order-modal-close');
        const cancelBtn = document.getElementById('cancel-order');
        const overlay = document.getElementById('order-modal-overlay');

        [closeBtn, cancelBtn].forEach(btn => {
            btn?.addEventListener('click', () => this.hideOrderForm());
        });

        overlay?.addEventListener('click', (e) => {
            if (e.target === overlay) this.hideOrderForm();
        });

        // Form submission
        const form = document.getElementById('order-form');
        form?.addEventListener('submit', (e) => this.handleOrderSubmit(e));
    }

    // Pre-fill user data from Telegram WebApp
    prefillUserData() {
        try {
            if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
                const user = window.Telegram.WebApp.initDataUnsafe.user;

                const nameField = document.getElementById('customer-name');
                if (nameField && user.first_name) {
                    const fullName = user.last_name ?
                        `${user.first_name} ${user.last_name}` : user.first_name;
                    nameField.value = fullName;
                }
            }
        } catch (error) {
            console.error('Error prefilling user data:', error);
        }
    }

    // Handle order form submission
    async handleOrderSubmit(e) {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-order');
        const btnText = submitBtn?.querySelector('.btn-text');
        const btnLoading = submitBtn?.querySelector('.btn-loading');

        try {
            // Show loading state
            if (submitBtn) submitBtn.disabled = true;
            if (btnText) btnText.style.display = 'none';
            if (btnLoading) btnLoading.style.display = 'inline';

            // Collect form data
            const orderData = this.collectOrderData();

            // Validate
            if (!this.validateOrderData(orderData)) {
                return;
            }

            // Submit order
            const result = await this.submitOrder(orderData);

            if (result.success) {
                // Show success
                window.Utils.showToast('Заказ успешно оформлен!', 'success');

                // Clear cart
                this.cart.clearCart();

                // Hide form
                this.hideOrderForm();

                // Show success modal with order details
                this.showOrderSuccess(result.order);
            } else {
                throw new Error(result.message || 'Ошибка при оформлении заказа');
            }

        } catch (error) {
            console.error('Order submission error:', error);
            window.Utils.showToast(
                error.message || 'Ошибка при оформлении заказа',
                'error'
            );
        } finally {
            // Reset button state
            if (submitBtn) submitBtn.disabled = false;
            if (btnText) btnText.style.display = 'inline';
            if (btnLoading) btnLoading.style.display = 'none';
        }
    }

    // Collect order data from form
    collectOrderData() {
        const cartSummary = this.cart.getCartSummary();

        // Get Telegram user ID
        let telegramId = null;
        try {
            if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
                telegramId = window.Telegram.WebApp.initDataUnsafe.user.id;
            }
        } catch (error) {
            console.error('Error getting Telegram ID:', error);
        }

        const paymentMethodEl = document.querySelector('input[name="payment-method"]:checked');

        return {
            telegram_id: telegramId,
            total_amount: cartSummary.total,
            customer_name: document.getElementById('customer-name')?.value.trim() || '',
            customer_phone: document.getElementById('customer-phone')?.value.trim() || '',
            delivery_address: document.getElementById('delivery-address')?.value.trim() || null,
            notes: document.getElementById('order-notes')?.value.trim() || null,
            payment_method: paymentMethodEl?.value || 'card',
            items: cartSummary.items.map(item => ({
                product_id: item.product.id,
                quantity: item.quantity
            }))
        };
    }

    // Validate order data
    validateOrderData(data) {
        if (!data.customer_name) {
            window.Utils.showToast('Пожалуйста, укажите ваше имя', 'error');
            document.getElementById('customer-name')?.focus();
            return false;
        }

        if (!data.customer_phone) {
            window.Utils.showToast('Пожалуйста, укажите ваш телефон', 'error');
            document.getElementById('customer-phone')?.focus();
            return false;
        }

        if (!data.telegram_id) {
            window.Utils.showToast('Ошибка: не удалось определить пользователя Telegram', 'error');
            return false;
        }

        if (!data.items || data.items.length === 0) {
            window.Utils.showToast('Корзина пуста', 'error');
            return false;
        }

        return true;
    }

    // Submit order to API
    async submitOrder(orderData) {
        const response = await fetch(`${window.AppConfig.API_BASE_URL}/api/orders/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || `Server error: ${response.status}`);
        }

        return result;
    }

    // Show order success modal
    showOrderSuccess(order) {
        const successHtml = `
            <div class="modal-overlay" id="success-modal-overlay">
                <div class="modal success-modal" id="success-modal">
                    <div class="modal-header">
                        <h2>✅ Заказ оформлен!</h2>
                    </div>

                    <div class="modal-body">
                        <div class="success-content">
                            <p><strong>Номер заказа:</strong> #${order.id}</p>
                            <p><strong>Сумма:</strong> ${order.formatted_total}</p>
                            <p><strong>Статус:</strong> ${order.status_display}</p>

                            <div class="success-message">
                                <p>📞 Мы свяжемся с вами для подтверждения заказа</p>
                                <p>⏰ Время приготовления: 30-45 минут</p>
                            </div>

                            <button class="btn btn-primary" id="close-success">
                                Понятно
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', successHtml);

        // Setup close event
        document.getElementById('close-success')?.addEventListener('click', () => {
            this.hideSuccessModal();
        });
    }

    // Hide order form
    hideOrderForm() {
        const modal = document.getElementById('order-modal-overlay');
        modal?.remove();
    }

    // Hide success modal
    hideSuccessModal() {
        const modal = document.getElementById('success-modal-overlay');
        modal?.remove();
    }
}

// Initialize cart services
window.cartService = new CartService();
window.cartUI = new CartUI(window.cartService);