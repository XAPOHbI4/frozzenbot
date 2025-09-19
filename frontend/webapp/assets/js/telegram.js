// Telegram WebApp Integration
class TelegramWebApp {
    constructor() {
        this.webApp = window.Telegram?.WebApp;
        this.isAvailable = !!this.webApp;
        this.user = null;
        this.theme = 'light';

        this.init();
    }

    init() {
        if (!this.isAvailable) {
            console.warn('Telegram WebApp is not available. Running in development mode.');
            this.setupDevelopmentMode();
            return;
        }

        try {
            // Initialize Telegram WebApp
            this.webApp.ready();
            this.webApp.expand();

            // Get user data
            this.user = this.webApp.initDataUnsafe?.user;

            // Setup theme
            this.setupTheme();

            // Setup main button
            this.setupMainButton();

            // Setup back button
            this.setupBackButton();

            // Setup other features
            this.setupHapticFeedback();

            console.log('Telegram WebApp initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Telegram WebApp:', error);
        }
    }

    setupDevelopmentMode() {
        // Mock Telegram WebApp for development
        console.log('Running in development mode - Telegram WebApp features disabled');

        // Create mock user for testing
        this.user = {
            id: 123456789,
            first_name: 'Test',
            username: 'testuser'
        };

        // Apply light theme by default
        document.documentElement.setAttribute('data-theme', 'light');
    }

    setupTheme() {
        if (!this.isAvailable) return;

        // Apply Telegram theme
        const themeParams = this.webApp.themeParams;
        const isDark = themeParams.bg_color === '#17212b' || themeParams.bg_color === '#1c1c1d';

        this.theme = isDark ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', this.theme);

        // Set CSS variables for Telegram theme
        if (themeParams.bg_color) {
            document.documentElement.style.setProperty('--tg-bg-color', themeParams.bg_color);
        }
        if (themeParams.text_color) {
            document.documentElement.style.setProperty('--tg-text-color', themeParams.text_color);
        }
        if (themeParams.hint_color) {
            document.documentElement.style.setProperty('--tg-hint-color', themeParams.hint_color);
        }
        if (themeParams.button_color) {
            document.documentElement.style.setProperty('--tg-button-color', themeParams.button_color);
        }
        if (themeParams.button_text_color) {
            document.documentElement.style.setProperty('--tg-button-text-color', themeParams.button_text_color);
        }

        // Listen for theme changes
        this.webApp.onEvent('themeChanged', () => {
            this.setupTheme();
        });
    }

    setupMainButton() {
        if (!this.isAvailable) return;

        const mainButton = this.webApp.MainButton;

        // Configure main button
        mainButton.text = window.AppConfig.TELEGRAM.MAIN_BUTTON_TEXT;
        mainButton.color = this.webApp.themeParams.button_color;
        mainButton.textColor = this.webApp.themeParams.button_text_color;

        // Handle main button click
        mainButton.onClick(() => {
            this.handleMainButtonClick();
        });

        // Initially hide main button
        mainButton.hide();

        // Show main button when cart has items that meet minimum order
        if (window.cartService) {
            window.cartService.addEventListener((summary) => {
                if (summary.isMinOrderMet && summary.totalItems > 0) {
                    mainButton.text = `Заказать за ${summary.formattedTotal}`;
                    mainButton.show();
                } else {
                    mainButton.hide();
                }
            });
        }
    }

    setupBackButton() {
        if (!this.isAvailable) return;

        const backButton = this.webApp.BackButton;

        if (window.AppConfig.TELEGRAM.BACK_BUTTON_ENABLED) {
            backButton.show();

            backButton.onClick(() => {
                this.handleBackButtonClick();
            });
        }
    }

    setupHapticFeedback() {
        if (!this.isAvailable) return;

        // Haptic feedback is handled in individual actions
        // This method can be extended for global haptic feedback setup
    }

    handleMainButtonClick() {
        // Trigger checkout process
        if (window.cartUI) {
            window.cartUI.handleCheckout();
        }
    }

    handleBackButtonClick() {
        // Handle back navigation
        // In a single-page app like this, we might close modals or return to previous state

        // Close any open modals
        const openModals = document.querySelectorAll('.modal.show');
        if (openModals.length > 0) {
            openModals.forEach(modal => {
                modal.classList.remove('show');
            });
            return;
        }

        // Otherwise close the WebApp
        this.close();
    }

    // Public methods for interaction

    showMainButton(text, callback) {
        if (!this.isAvailable) return;

        const mainButton = this.webApp.MainButton;
        mainButton.text = text;
        mainButton.show();

        if (callback) {
            mainButton.onClick(callback);
        }
    }

    hideMainButton() {
        if (!this.isAvailable) return;
        this.webApp.MainButton.hide();
    }

    triggerHaptic(type = 'light') {
        if (!this.isAvailable) return;

        try {
            switch (type) {
                case 'light':
                    this.webApp.HapticFeedback.impactOccurred('light');
                    break;
                case 'medium':
                    this.webApp.HapticFeedback.impactOccurred('medium');
                    break;
                case 'heavy':
                    this.webApp.HapticFeedback.impactOccurred('heavy');
                    break;
                case 'success':
                    this.webApp.HapticFeedback.notificationOccurred('success');
                    break;
                case 'warning':
                    this.webApp.HapticFeedback.notificationOccurred('warning');
                    break;
                case 'error':
                    this.webApp.HapticFeedback.notificationOccurred('error');
                    break;
            }
        } catch (error) {
            console.warn('Haptic feedback not available:', error);
        }
    }

    close() {
        if (!this.isAvailable) return;
        this.webApp.close();
    }

    sendData(data) {
        if (!this.isAvailable) return;

        try {
            this.webApp.sendData(JSON.stringify(data));
        } catch (error) {
            console.error('Failed to send data to Telegram:', error);
        }
    }

    // Validate initData (should be done on backend)
    validateInitData() {
        if (!this.isAvailable) return null;

        return {
            initData: this.webApp.initData,
            initDataUnsafe: this.webApp.initDataUnsafe,
            isValid: this.webApp.initData.length > 0
        };
    }

    // Get user information
    getUserInfo() {
        return {
            user: this.user,
            theme: this.theme,
            platform: this.webApp?.platform || 'unknown',
            version: this.webApp?.version || 'unknown'
        };
    }
}

// Initialize Telegram WebApp
window.telegramWebApp = new TelegramWebApp();