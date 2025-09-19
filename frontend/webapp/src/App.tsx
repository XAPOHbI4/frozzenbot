/**
 * Main App Component
 * FrozenBot WebApp with routing and Telegram integration
 */

import React, { useState, useEffect, useCallback } from 'react';
import { WebAppApiClient, LocalCartManager } from './services/apiClient';
import { setupTelegramWebApp, getTelegramUser } from './utils/telegram';
import { WebAppConfig } from './types';
import Catalog from './pages/Catalog';
import Checkout from './pages/Checkout';
import './styles/App.css';

// WebApp configuration
const config: WebAppConfig = {
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

type AppPage = 'catalog' | 'checkout';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<AppPage>('catalog');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize services
  const [apiClient] = useState(() => new WebAppApiClient(config));
  const [cartManager] = useState(() => new LocalCartManager(config.STORAGE_KEYS.CART));

  // Initialize Telegram WebApp
  useEffect(() => {
    let mounted = true;

    const initializeApp = async () => {
      try {
        setIsLoading(true);

        // Setup Telegram WebApp
        const tg = setupTelegramWebApp();
        if (tg) {
          console.log('Telegram WebApp initialized:', {
            version: tg.version,
            platform: tg.platform,
            colorScheme: tg.colorScheme,
            user: getTelegramUser(),
          });

          // Set initial theme
          if (tg.colorScheme === 'dark') {
            document.body.classList.add('dark-theme');
          }

          // Handle theme changes
          tg.onEvent('themeChanged', () => {
            if (tg.colorScheme === 'dark') {
              document.body.classList.add('dark-theme');
            } else {
              document.body.classList.remove('dark-theme');
            }
          });

          // Handle viewport changes
          tg.onEvent('viewportChanged', () => {
            console.log('Viewport changed:', {
              height: tg.viewportHeight,
              stableHeight: tg.viewportStableHeight,
              isExpanded: tg.isExpanded,
            });
          });
        } else {
          console.warn('Running outside Telegram WebApp environment');
        }

        // Simulate loading delay for better UX
        await new Promise(resolve => setTimeout(resolve, config.UI.LOADING_DELAY));

        if (mounted) {
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Failed to initialize app:', err);
        if (mounted) {
          setError('Не удалось инициализировать приложение');
          setIsLoading(false);
        }
      }
    };

    initializeApp();

    return () => {
      mounted = false;
    };
  }, []);

  // Navigation handlers
  const handleNavigateToCheckout = useCallback(() => {
    setCurrentPage('checkout');
  }, []);

  const handleNavigateToList = useCallback(() => {
    setCurrentPage('catalog');
  }, []);

  // Error handler
  const handleRetry = useCallback(() => {
    setError(null);
    setIsLoading(true);
    // Re-initialize the app
    window.location.reload();
  }, []);

  // Loading screen
  if (isLoading) {
    return (
      <div className="app app--loading">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <h2 className="loading-title">Загружаем каталог...</h2>
          <p className="loading-subtitle">Подготавливаем свежие предложения</p>
        </div>
      </div>
    );
  }

  // Error screen
  if (error) {
    return (
      <div className="app app--error">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2 className="error-title">Произошла ошибка</h2>
          <p className="error-message">{error}</p>
          <button onClick={handleRetry} className="error-retry-btn">
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  // Main app
  return (
    <div className="app">
      {currentPage === 'catalog' && (
        <Catalog
          apiClient={apiClient}
          cartManager={cartManager}
          onNavigateToCheckout={handleNavigateToCheckout}
        />
      )}

      {currentPage === 'checkout' && (
        <Checkout
          apiClient={apiClient}
          cartManager={cartManager}
        />
      )}

      {/* Global app notifications could go here */}
    </div>
  );
};

export default App;