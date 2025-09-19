// Main Application Controller
class App {
    constructor() {
        this.isInitialized = false;
        this.elements = {
            loadingScreen: document.getElementById('loading-screen'),
            app: document.getElementById('app')
        };

        this.init();
    }

    async init() {
        try {
            console.log('🚀 Initializing FrozenFood WebApp...');

            // Show minimum loading time for better UX
            const startTime = Date.now();

            // Initialize all services in parallel
            await Promise.all([
                this.initializeServices(),
                this.waitForMinimumLoading(startTime)
            ]);

            // Hide loading screen and show app
            this.showApp();

            // Setup global error handlers
            this.setupErrorHandlers();

            // Log success
            console.log('✅ FrozenFood WebApp initialized successfully');

            this.isInitialized = true;

        } catch (error) {
            console.error('❌ Failed to initialize app:', error);
            this.showError('Ошибка загрузки приложения. Попробуйте обновить страницу.');
        }
    }

    async initializeServices() {
        // Services are already initialized through their script includes
        // This method can be used for additional async initialization

        // Validate Telegram WebApp
        if (window.telegramWebApp) {
            const userInfo = window.telegramWebApp.getUserInfo();
            console.log('Telegram User:', userInfo.user);
            console.log('Theme:', userInfo.theme);
        }

        // Validate API connection
        try {
            await window.api.getCategories();
            console.log('✅ Backend API connection successful');
        } catch (error) {
            console.warn('⚠️ Backend API connection failed, using fallback data');
        }

        // Initialize cart from storage
        const cartSummary = window.cartService.getCartSummary();
        console.log(`Cart initialized with ${cartSummary.totalItems} items`);
    }

    async waitForMinimumLoading(startTime) {
        const elapsed = Date.now() - startTime;
        const minimumTime = window.AppConfig.UI.LOADING_DELAY;

        if (elapsed < minimumTime) {
            await new Promise(resolve => setTimeout(resolve, minimumTime - elapsed));
        }
    }

    showApp() {
        if (this.elements.loadingScreen) {
            this.elements.loadingScreen.style.opacity = '0';
            setTimeout(() => {
                this.elements.loadingScreen.style.display = 'none';
            }, 300);
        }

        if (this.elements.app) {
            this.elements.app.style.display = 'block';
            // Trigger animations
            setTimeout(() => {
                this.elements.app.style.opacity = '1';
            }, 100);
        }
    }

    showError(message) {
        if (this.elements.loadingScreen) {
            this.elements.loadingScreen.innerHTML = `
                <div style="text-align: center; color: var(--danger, #dc2626);">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <h3>Ошибка загрузки</h3>
                    <p style="margin: 16px 0; color: var(--tg-hint-color, #666);">${message}</p>
                    <button onclick="window.location.reload()" style="
                        background: var(--tg-button-color, #2481cc);
                        color: var(--tg-button-text-color, white);
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 16px;
                        cursor: pointer;
                    ">
                        Обновить страницу
                    </button>
                </div>
            `;
        }
    }

    setupErrorHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);

            if (!this.isInitialized) {
                this.showError('Произошла ошибка при загрузке приложения');
            } else {
                window.Utils.showToast('Произошла ошибка. Попробуйте обновить страницу.', 'error');
            }
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);

            if (!this.isInitialized) {
                this.showError('Произошла ошибка при загрузке данных');
            } else {
                window.Utils.showToast('Ошибка загрузки данных', 'error');
            }
        });

        // Network error detection
        window.addEventListener('online', () => {
            window.Utils.showToast('Подключение восстановлено', 'success');
            if (window.productsManager) {
                window.productsManager.refresh();
            }
        });

        window.addEventListener('offline', () => {
            window.Utils.showToast('Нет подключения к интернету', 'warning');
        });
    }

    // Public methods for external access

    refresh() {
        if (window.productsManager) {
            window.productsManager.refresh();
        }
    }

    clearCache() {
        try {
            localStorage.removeItem(window.AppConfig.STORAGE_KEYS.CART);
            localStorage.removeItem(window.AppConfig.STORAGE_KEYS.USER_PREFERENCES);
            window.Utils.showToast('Кэш очищен', 'success');
        } catch (error) {
            console.error('Failed to clear cache:', error);
            window.Utils.showToast('Ошибка очистки кэша', 'error');
        }
    }

    getAppInfo() {
        return {
            version: '1.0.0',
            initialized: this.isInitialized,
            telegram: window.telegramWebApp?.getUserInfo() || null,
            cart: window.cartService?.getCartSummary() || null,
            products: window.productsManager?.products?.length || 0
        };
    }
}

// Initialize app when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new App();
    });
} else {
    window.app = new App();
}

// Add some helpful development utilities
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.dev = {
        clearCart: () => window.cartService?.clear(),
        addTestProduct: () => {
            const testProduct = {
                id: 999,
                name: 'Test Product',
                price: 100,
                formattedPrice: '100₽'
            };
            window.cartService?.addProduct(testProduct);
        },
        getAppInfo: () => window.app?.getAppInfo(),
        triggerHaptic: (type) => window.telegramWebApp?.triggerHaptic(type)
    };

    console.log('🔧 Development utilities available at window.dev');
}