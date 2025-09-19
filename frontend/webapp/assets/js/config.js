// Application Configuration
window.AppConfig = {
    API_BASE_URL: 'http://localhost:8000',
    MIN_ORDER_AMOUNT: 1500,
    CURRENCY: '₽',

    // Default product image placeholder
    DEFAULT_PRODUCT_IMAGE: '🍽️',

    // Local storage keys
    STORAGE_KEYS: {
        CART: 'frozen_food_cart',
        USER_PREFERENCES: 'frozen_food_preferences'
    },

    // API Endpoints
    API_ENDPOINTS: {
        PRODUCTS: '/api/products/',
        CATEGORIES: '/api/categories/',
        USERS_ME: '/api/users/me'
    },

    // Telegram WebApp Configuration
    TELEGRAM: {
        MAIN_BUTTON_TEXT: 'Оформить заказ',
        BACK_BUTTON_ENABLED: true
    },

    // UI Configuration
    UI: {
        LOADING_DELAY: 1000, // Minimum loading time for UX
        ANIMATION_DURATION: 300,
        CART_UPDATE_ANIMATION: 200
    }
};

// Utility Functions
window.Utils = {
    formatPrice: (price) => {
        return Math.round(price) + window.AppConfig.CURRENCY;
    },

    formatWeight: (weight) => {
        if (!weight) return '';
        if (weight >= 1000) {
            return Math.round(weight / 1000) + 'кг';
        }
        return weight + 'г';
    },

    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    showToast: (message, type = 'info') => {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--tg-button-color);
            color: var(--tg-button-text-color);
            padding: 12px 16px;
            border-radius: 8px;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    },

    generateId: () => {
        return Math.random().toString(36).substr(2, 9);
    }
};