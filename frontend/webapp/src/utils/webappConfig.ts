/**
 * WebApp Configuration and Setup
 * Telegram WebApp specific configuration
 */

import { WebAppConfig } from '../types';
import { setupTelegramWebApp, getTelegramUser, isTelegramWebApp } from './telegram';

// Default configuration
const defaultConfig: WebAppConfig = {
  API_BASE_URL: process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000'
    : 'https://api.frozenbot.example.com',
  MIN_ORDER_AMOUNT: 1500,
  CURRENCY: 'RUB',
  DEFAULT_PRODUCT_IMAGE: '/images/placeholder-product.jpg',
  STORAGE_KEYS: {
    CART: 'frozen_food_cart',
    USER_PREFERENCES: 'frozen_food_prefs',
  },
  API_ENDPOINTS: {
    PRODUCTS: '/api/products/',
    CATEGORIES: '/api/categories/',
    USERS_ME: '/api/users/me',
  },
  TELEGRAM: {
    MAIN_BUTTON_TEXT: 'Продолжить',
    BACK_BUTTON_ENABLED: true,
  },
  UI: {
    LOADING_DELAY: 300,
    ANIMATION_DURATION: 200,
    CART_UPDATE_ANIMATION: 150,
  },
};

// WebApp initialization
export const initializeWebApp = async (): Promise<{
  config: WebAppConfig;
  telegramUser: any;
  isTelegram: boolean;
}> => {
  const isTelegram = isTelegramWebApp();
  let telegramUser = null;

  if (isTelegram) {
    // Setup Telegram WebApp
    const tg = setupTelegramWebApp();
    if (tg) {
      // Get user data
      telegramUser = getTelegramUser();

      // Configure theme
      if (tg.colorScheme === 'dark') {
        document.body.classList.add('dark-theme');
      }

      // Set appropriate colors
      const primaryColor = '#007bff';
      const backgroundColor = tg.colorScheme === 'dark' ? '#1f2937' : '#ffffff';

      tg.setHeaderColor(primaryColor);
      tg.setBackgroundColor(backgroundColor);

      // Enable closing confirmation for important actions
      tg.enableClosingConfirmation();

      console.log('Telegram WebApp initialized:', {
        version: tg.version,
        platform: tg.platform,
        colorScheme: tg.colorScheme,
        user: telegramUser,
      });
    }
  }

  return {
    config: defaultConfig,
    telegramUser,
    isTelegram,
  };
};

// Utility to show notifications using Telegram or fallback
export const showNotification = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
  if (isTelegramWebApp() && window.Telegram?.WebApp) {
    // Use Telegram alert for important messages
    window.Telegram.WebApp.showAlert(message);
  } else {
    // Fallback to browser alert
    alert(message);
  }
};

// Utility to get device info
export const getDeviceInfo = () => {
  const isTelegram = isTelegramWebApp();

  if (isTelegram && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    return {
      platform: tg.platform,
      version: tg.version,
      colorScheme: tg.colorScheme,
      viewportHeight: tg.viewportHeight,
      isExpanded: tg.isExpanded,
      isTelegram: true,
    };
  }

  return {
    platform: 'web',
    version: 'unknown',
    colorScheme: 'light',
    viewportHeight: window.innerHeight,
    isExpanded: true,
    isTelegram: false,
  };
};

// Format currency based on config
export const formatCurrency = (amount: number, currency: string = defaultConfig.CURRENCY): string => {
  const formatters = {
    RUB: (amt: number) => `${amt.toLocaleString('ru-RU')} ₽`,
    USD: (amt: number) => `$${amt.toLocaleString('en-US')}`,
    EUR: (amt: number) => `€${amt.toLocaleString('de-DE')}`,
  };

  const formatter = formatters[currency as keyof typeof formatters];
  return formatter ? formatter(amount) : `${amount} ${currency}`;
};

// Format weight
export const formatWeight = (weight: number): string => {
  if (weight >= 1000) {
    return `${(weight / 1000).toFixed(1)} кг`;
  }
  return `${weight} г`;
};

// Debounce utility
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void => {
  let timeoutId: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), wait);
  };
};

// Generate unique ID
export const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export default {
  initializeWebApp,
  defaultConfig,
  showNotification,
  getDeviceInfo,
  formatCurrency,
  formatWeight,
  debounce,
  generateId,
};