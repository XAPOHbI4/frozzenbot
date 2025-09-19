/**
 * Typed API Client for WebApp (JavaScript with TypeScript annotations in comments)
 * Imports types from the TypeScript definitions
 */

// Import types (this would work with a build process that strips types)
// import { WebAppApiClient, LocalCartManager } from '../src/services/apiClient';
// import { WebAppConfig } from '../src/types';

/**
 * WebApp API Client wrapper for vanilla JavaScript
 * Provides type safety through JSDoc comments
 */
class WebAppAPI {
  constructor(config) {
    this.baseURL = config.API_BASE_URL;
    this.config = config;
    this.cartManager = new LocalCartManager(config.STORAGE_KEYS.CART);
  }

  /**
   * Make a typed API request
   * @param {string} endpoint
   * @param {RequestInit} options
   * @returns {Promise<any>}
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    // Add Telegram WebApp auth if available
    if (window.Telegram?.WebApp?.initData) {
      defaultHeaders['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData;
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Handle API response format
      if (data.data !== undefined) {
        return data.data;
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Get all products
   * @returns {Promise<{products: Product[]}>}
   */
  async getProducts() {
    return this.request('/api/products/');
  }

  /**
   * Get single product by ID
   * @param {number} id
   * @returns {Promise<Product>}
   */
  async getProduct(id) {
    return this.request(`/api/products/${id}`);
  }

  /**
   * Get all categories
   * @returns {Promise<{categories: Category[]}>}
   */
  async getCategories() {
    return this.request('/api/categories/');
  }

  /**
   * Create a new order
   * @param {OrderCreateRequest} orderData
   * @returns {Promise<Order>}
   */
  async createOrder(orderData) {
    return this.request('/api/orders/', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  }

  /**
   * Get order by ID
   * @param {number} id
   * @returns {Promise<Order>}
   */
  async getOrder(id) {
    return this.request(`/api/orders/${id}`);
  }

  /**
   * Get current user
   * @returns {Promise<TelegramUser|null>}
   */
  async getCurrentUser() {
    try {
      return this.request('/api/users/me');
    } catch (error) {
      return null;
    }
  }

  /**
   * Register new user
   * @param {UserCreateRequest} userData
   * @returns {Promise<TelegramUser>}
   */
  async registerUser(userData) {
    return this.request('/api/users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }
}

/**
 * Local Cart Manager for vanilla JavaScript
 */
class LocalCartManager {
  constructor(storageKey = 'frozen_food_cart') {
    this.storageKey = storageKey;
  }

  /**
   * Get cart from localStorage
   * @returns {LocalCart}
   */
  getCart() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Error loading cart from storage:', error);
    }

    return {
      items: [],
      total: 0,
      count: 0,
      updatedAt: new Date().toISOString(),
    };
  }

  /**
   * Save cart to localStorage
   * @param {LocalCart} cart
   */
  saveCart(cart) {
    try {
      cart.updatedAt = new Date().toISOString();
      localStorage.setItem(this.storageKey, JSON.stringify(cart));
    } catch (error) {
      console.error('Error saving cart to storage:', error);
    }
  }

  /**
   * Add item to cart
   * @param {Product} product
   * @param {number} quantity
   * @returns {LocalCart}
   */
  addItem(product, quantity = 1) {
    const cart = this.getCart();
    const existingItemIndex = cart.items.findIndex(
      item => item.productId === product.id
    );

    if (existingItemIndex >= 0) {
      cart.items[existingItemIndex].quantity += quantity;
      cart.items[existingItemIndex].total =
        cart.items[existingItemIndex].quantity * cart.items[existingItemIndex].price;
    } else {
      const newItem = {
        id: Date.now(),
        productId: product.id,
        name: product.name,
        price: product.price,
        quantity,
        total: product.price * quantity,
        image: product.image_url,
      };
      cart.items.push(newItem);
    }

    this.updateCartTotals(cart);
    this.saveCart(cart);
    return cart;
  }

  /**
   * Update item quantity
   * @param {number} productId
   * @param {number} quantity
   * @returns {LocalCart}
   */
  updateItemQuantity(productId, quantity) {
    const cart = this.getCart();
    const itemIndex = cart.items.findIndex(item => item.productId === productId);

    if (itemIndex >= 0) {
      if (quantity <= 0) {
        cart.items.splice(itemIndex, 1);
      } else {
        cart.items[itemIndex].quantity = quantity;
        cart.items[itemIndex].total = cart.items[itemIndex].price * quantity;
      }
    }

    this.updateCartTotals(cart);
    this.saveCart(cart);
    return cart;
  }

  /**
   * Remove item from cart
   * @param {number} productId
   * @returns {LocalCart}
   */
  removeItem(productId) {
    const cart = this.getCart();
    cart.items = cart.items.filter(item => item.productId !== productId);

    this.updateCartTotals(cart);
    this.saveCart(cart);
    return cart;
  }

  /**
   * Clear entire cart
   * @returns {LocalCart}
   */
  clearCart() {
    const cart = {
      items: [],
      total: 0,
      count: 0,
      updatedAt: new Date().toISOString(),
    };

    this.saveCart(cart);
    return cart;
  }

  /**
   * Update cart totals
   * @param {LocalCart} cart
   */
  updateCartTotals(cart) {
    cart.total = cart.items.reduce((sum, item) => sum + item.total, 0);
    cart.count = cart.items.reduce((sum, item) => sum + item.quantity, 0);
  }

  /**
   * Convert cart to order items format
   * @returns {Array<{product_id: number, quantity: number, price: number}>}
   */
  convertToOrderItems() {
    const cart = this.getCart();
    return cart.items.map(item => ({
      product_id: item.productId,
      quantity: item.quantity,
      price: item.price,
    }));
  }
}

// Export for global use
window.WebAppAPI = WebAppAPI;
window.LocalCartManager = LocalCartManager;