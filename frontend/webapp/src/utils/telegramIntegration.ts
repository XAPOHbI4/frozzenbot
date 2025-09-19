/**
 * Enhanced Telegram WebApp Integration
 * Advanced features and event handling
 */

import {
  setupTelegramWebApp,
  getTelegramUser,
  isTelegramWebApp,
  telegramHapticFeedback,
  telegramMainButton,
  telegramBackButton
} from './telegram';

// Advanced Telegram Integration Class
export class TelegramWebAppIntegration {
  private tg: any;
  private initialized: boolean = false;
  private eventHandlers: Map<string, Function[]> = new Map();

  constructor() {
    this.init();
  }

  private init() {
    if (!isTelegramWebApp()) {
      console.warn('Not running in Telegram WebApp environment');
      return;
    }

    this.tg = setupTelegramWebApp();
    if (this.tg) {
      this.setupEventListeners();
      this.initialized = true;
      console.log('Telegram WebApp Integration initialized');
    }
  }

  private setupEventListeners() {
    if (!this.tg) return;

    // Theme change handler
    this.tg.onEvent('themeChanged', () => {
      this.emit('themeChanged', {
        colorScheme: this.tg.colorScheme,
        themeParams: this.tg.themeParams,
      });
    });

    // Viewport change handler
    this.tg.onEvent('viewportChanged', () => {
      this.emit('viewportChanged', {
        height: this.tg.viewportHeight,
        stableHeight: this.tg.viewportStableHeight,
        isExpanded: this.tg.isExpanded,
      });
    });

    // Main button events
    this.tg.MainButton.onClick(() => {
      this.emit('mainButtonClicked', {});
    });

    // Back button events
    this.tg.BackButton.onClick(() => {
      this.emit('backButtonClicked', {});
    });
  }

  // Event system
  on(event: string, handler: Function) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: Function) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  // Haptic feedback methods
  haptic = {
    impact: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') => {
      telegramHapticFeedback.impact(style);
    },

    notification: (type: 'error' | 'success' | 'warning') => {
      telegramHapticFeedback.notification(type);
    },

    selection: () => {
      telegramHapticFeedback.selection();
    },

    // Enhanced feedback for specific actions
    addToCart: () => {
      this.haptic.impact('light');
    },

    removeFromCart: () => {
      this.haptic.impact('medium');
    },

    checkout: () => {
      this.haptic.impact('heavy');
    },

    success: () => {
      this.haptic.notification('success');
    },

    error: () => {
      this.haptic.notification('error');
    },

    warning: () => {
      this.haptic.notification('warning');
    }
  };

  // Main button control
  mainButton = {
    show: (text: string, callback: () => void) => {
      telegramMainButton.show(text, callback);
    },

    hide: () => {
      telegramMainButton.hide();
    },

    setProgress: (show: boolean) => {
      telegramMainButton.setProgress(show);
    },

    enable: () => {
      telegramMainButton.enable();
    },

    disable: () => {
      telegramMainButton.disable();
    },

    setText: (text: string) => {
      if (this.tg?.MainButton) {
        this.tg.MainButton.setText(text);
      }
    },

    setColor: (color: string) => {
      if (this.tg?.MainButton) {
        this.tg.MainButton.color = color;
      }
    }
  };

  // Back button control
  backButton = {
    show: (callback: () => void) => {
      telegramBackButton.show(callback);
    },

    hide: () => {
      telegramBackButton.hide();
    }
  };

  // UI methods
  ui = {
    showAlert: (message: string, callback?: () => void) => {
      if (this.tg) {
        this.tg.showAlert(message, callback);
      } else {
        alert(message);
        callback?.();
      }
    },

    showConfirm: (message: string, callback: (confirmed: boolean) => void) => {
      if (this.tg) {
        this.tg.showConfirm(message, callback);
      } else {
        const confirmed = confirm(message);
        callback(confirmed);
      }
    },

    showPopup: (params: {
      title?: string;
      message: string;
      buttons: Array<{ id: string; type?: 'default' | 'ok' | 'close' | 'cancel' | 'destructive'; text: string }>;
    }, callback?: (buttonId: string) => void) => {
      if (this.tg) {
        this.tg.showPopup(params, callback);
      } else {
        // Fallback for non-Telegram environments
        const result = confirm(params.message);
        callback?.(result ? 'ok' : 'cancel');
      }
    },

    setHeaderColor: (color: string) => {
      if (this.tg) {
        this.tg.setHeaderColor(color);
      }
    },

    setBackgroundColor: (color: string) => {
      if (this.tg) {
        this.tg.setBackgroundColor(color);
      }
    },

    expand: () => {
      if (this.tg) {
        this.tg.expand();
      }
    },

    close: () => {
      if (this.tg) {
        this.tg.close();
      }
    }
  };

  // User data
  getUserData() {
    return getTelegramUser();
  }

  // Theme data
  getTheme() {
    if (!this.tg) return null;

    return {
      colorScheme: this.tg.colorScheme,
      themeParams: this.tg.themeParams,
      headerColor: this.tg.headerColor,
      backgroundColor: this.tg.backgroundColor,
    };
  }

  // Viewport data
  getViewport() {
    if (!this.tg) return null;

    return {
      height: this.tg.viewportHeight,
      stableHeight: this.tg.viewportStableHeight,
      isExpanded: this.tg.isExpanded,
    };
  }

  // Check if initialized
  isInitialized() {
    return this.initialized;
  }

  // Check if running in Telegram
  isTelegram() {
    return isTelegramWebApp();
  }
}

// Global instance
export const telegramIntegration = new TelegramWebAppIntegration();

// Helper functions for common use cases
export const enhancedTelegramUtils = {
  // Shopping cart actions
  handleAddToCart: () => {
    telegramIntegration.haptic.addToCart();
  },

  handleRemoveFromCart: () => {
    telegramIntegration.haptic.removeFromCart();
  },

  handleCheckout: () => {
    telegramIntegration.haptic.checkout();
  },

  // Navigation feedback
  handleNavigation: () => {
    telegramIntegration.haptic.selection();
  },

  // Success/Error feedback
  showSuccess: (message: string, callback?: () => void) => {
    telegramIntegration.haptic.success();
    telegramIntegration.ui.showAlert(`✅ ${message}`, callback);
  },

  showError: (message: string, callback?: () => void) => {
    telegramIntegration.haptic.error();
    telegramIntegration.ui.showAlert(`❌ ${message}`, callback);
  },

  showWarning: (message: string, callback?: () => void) => {
    telegramIntegration.haptic.warning();
    telegramIntegration.ui.showAlert(`⚠️ ${message}`, callback);
  },

  // Confirmation with haptic
  confirm: (message: string): Promise<boolean> => {
    return new Promise((resolve) => {
      telegramIntegration.ui.showConfirm(message, (confirmed) => {
        if (confirmed) {
          telegramIntegration.haptic.selection();
        }
        resolve(confirmed);
      });
    });
  },

  // Setup checkout flow
  setupCheckoutFlow: (onCheckout: () => void) => {
    telegramIntegration.mainButton.show('Оформить заказ', () => {
      telegramIntegration.haptic.checkout();
      onCheckout();
    });
  },

  // Setup back navigation
  setupBackNavigation: (onBack: () => void) => {
    telegramIntegration.backButton.show(() => {
      telegramIntegration.haptic.selection();
      onBack();
    });
  }
};

export default telegramIntegration;