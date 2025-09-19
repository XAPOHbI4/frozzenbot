// Re-export shared types for WebApp
export * from '../../../../shared/types';

// WebApp specific types
export interface WebAppConfig {
  API_BASE_URL: string;
  MIN_ORDER_AMOUNT: number;
  CURRENCY: string;
  DEFAULT_PRODUCT_IMAGE: string;
  STORAGE_KEYS: {
    CART: string;
    USER_PREFERENCES: string;
  };
  API_ENDPOINTS: {
    PRODUCTS: string;
    CATEGORIES: string;
    USERS_ME: string;
  };
  TELEGRAM: {
    MAIN_BUTTON_TEXT: string;
    BACK_BUTTON_ENABLED: boolean;
  };
  UI: {
    LOADING_DELAY: number;
    ANIMATION_DURATION: number;
    CART_UPDATE_ANIMATION: number;
  };
}

// Cart specific types for WebApp
export interface LocalCartItem {
  id: number;
  productId: number;
  name: string;
  price: number;
  quantity: number;
  total: number;
  image?: string;
}

export interface LocalCart {
  items: LocalCartItem[];
  total: number;
  count: number;
  updatedAt: string;
}

// WebApp utilities
export interface Utils {
  formatPrice: (price: number) => string;
  formatWeight: (weight: number) => string;
  debounce: (func: Function, wait: number) => Function;
  showToast: (message: string, type?: 'info' | 'success' | 'error') => void;
  generateId: () => string;
}

// Product display specific types
export interface ProductDisplayData {
  id: number;
  name: string;
  description: string;
  price: number;
  formattedPrice: string;
  weight?: number;
  formattedWeight?: string;
  categoryId?: number;
  categoryName?: string;
  image?: string;
  isActive: boolean;
  inCart?: boolean;
  cartQuantity?: number;
}

// Order form types for WebApp
export interface OrderFormData {
  customerName: string;
  customerPhone: string;
  deliveryAddress?: string;
  notes?: string;
  paymentMethod: 'card' | 'cash';
}

export interface OrderFormErrors {
  customerName?: string;
  customerPhone?: string;
  deliveryAddress?: string;
  general?: string;
}